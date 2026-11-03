"""Decisões explicáveis, sem associação aproximada nem criação de componentes."""
import re
from .identidade_produto import nome, codigo, gtin, atributos, numero, variante

# Domínios observados nos snapshots oficiais preservados no projeto.
DOMINIOS = {
    'processador': 'MLB-COMPUTER_PROCESSORS', 'placa_video': 'MLB-GRAPHICS_CARDS',
    'memoria_ram': 'MLB-RAM_MEMORY_MODULES', 'placa_mae': 'MLB-COMPUTER_MOTHERBOARDS',
    'ssd': 'MLB-HARD_DRIVES_AND_SSDS', 'hd': 'MLB-HARD_DRIVES_AND_SSDS',
    'mouse': 'MLB-COMPUTER_MICE',
}
CAMPOS = {
    'processador': [('soquete', 'COMPATIBLE_SOCKETS', None), ('nucleo', 'CPU_CORES_NUMBER', 'numero'), ('thread', 'CPU_THREADS_NUMBER', 'numero')],
    'placa_video': [('memoria_gb', 'MEMORY_SIZE', 'gb'), ('tipo_memoria', 'GRAPHICS_MEMORY_TYPE', None)],
    'memoria_ram': [('capacidade_gb', 'RAM_MEMORY_MODULE_TOTAL_CAPACITY', 'gb'), ('ddr', 'RAM_MEMORY_MODULE_TYPE', 'ddr'), ('frequencia_mhz', 'RAM_MEMORY_MODULE_SPEED', 'mhz')],
    'placa_mae': [('socket', 'SOCKET', None), ('tipo_memoria', 'SUPPORTED_RAM_MEMORY_TYPE', 'ddr')],
    'ssd': [('capacidade_gb', 'CAPACITY', 'gb')], 'hd': [('capacidade_gb', 'CAPACITY', 'gb')],
}


class CompararProdutosService:
    def avaliar(self, peca, produto, *, identidade=None):
        categoria = peca.__tablename__
        conflitos, pendencias, provas = [], [], []
        if not isinstance(produto, dict):
            return self._resultado('rejeitada', ['formato_invalido'], [], [])
        if not isinstance(produto.get('id'), str) or not re.fullmatch(r'MLB[0-9]+', produto['id']):
            pendencias.append('identificacao_externa_invalida')
        titulo = produto.get('name') or produto.get('title')
        a = atributos(produto)
        texto = nome(titulo)
        if not texto:
            pendencias.append('nome_ausente')
        if produto.get('status') != 'active':
            pendencias.append('estado_ativo_nao_comprovado')
        dominio = produto.get('domain_id')
        if categoria not in DOMINIOS or not dominio:
            pendencias.append('categoria_nao_comprovada')
        elif dominio != DOMINIOS[categoria]:
            conflitos.append('categoria_incompativel')
        if re.search(r'\b(combo|upgrade|sucata|defeito)\b|somente (?:a )?(?:caixa|embalagem)', texto):
            conflitos.append('produto_composto_ou_inadequado')
        kit = bool(re.search(r'\bkit\b|\d+\s*[x×]\s*\d+\s*gb', texto))
        if kit and categoria != 'memoria_ram':
            conflitos.append('kit_nao_suportado')
        localnome = nome(peca.modelo)
        if categoria in ('processador', 'placa_video'):
            laptop = lambda t: bool(re.search(r'\b(notebook|laptop|mobile)\b', t))
            if laptop(texto) != laptop(localnome):
                conflitos.append('desktop_notebook_divergentes')
            lv, rv = variante(categoria, localnome), variante(categoria, texto)
            if not rv and categoria == 'processador':
                modelos = a.get('MODEL', set())
                if len(modelos) == 1 and re.fullmatch(r'\d{3,5}(?:x3d|[a-z]{1,3})?', next(iter(modelos))):
                    rv = next(iter(modelos))
            if lv and rv and lv != rv:
                conflitos.append('modelo_ou_sufixo_divergente')
        marca = lambda v: {'wd':'western digital'}.get(nome(v), nome(v))
        marcas = {marca(v) for v in a.get('BRAND', set())}
        if marca(peca.fabricante) not in marcas:
            (conflitos if marcas else pendencias).append('marca_divergente' if marcas else 'marca_ausente')
        elif len(marcas) != 1:
            pendencias.append('marcas_multiplas')
        identidade = identidade or {}
        mpn = identidade.get('mpn', getattr(peca, 'part_number', None))
        if mpn and re.match(r'^(SEED|DEMO|BOOSTIO|REDE|KABUM)[-_]', str(mpn), re.I):
            mpn = None
        remotos = set().union(*(a.get(k, set()) for k in ('MPN', 'MANUFACTURER_PART_NUMBER', 'PART_NUMBER')))
        remotos = {codigo(v) for v in remotos}
        if mpn and remotos:
            if codigo(mpn) not in remotos:
                conflitos.append('mpn_divergente')
            elif len(remotos) != 1:
                pendencias.append('mpns_multiplos')
            else:
                provas.append('mpn')
        gtin_local = identidade.get('gtin', getattr(peca, 'gtin', None))
        gtins = {gtin(v) for v in a.get('GTIN', set()) | a.get('EAN', set()) | a.get('UPC', set())}
        if None in gtins:
            pendencias.append('gtin_remoto_invalido')
        gtins.discard(None)
        if gtin_local:
            canonico = gtin(gtin_local)
            if canonico is None:
                pendencias.append('gtin_local_invalido')
            elif gtins and canonico not in gtins:
                conflitos.append('gtin_divergente')
            elif gtins == {canonico}:
                provas.append('gtin')
            elif gtins:
                pendencias.append('gtins_multiplos')
        for campo, atributo, unidade in CAMPOS.get(categoria, []):
            local = getattr(peca, campo, None)
            valores = a.get(atributo, set())
            if local is None or not valores:
                continue
            if unidade in ('gb', 'mhz', 'numero'):
                converter = lambda v: numero(v, None if unidade == 'numero' else unidade)
            elif campo in ('socket', 'soquete'):
                from utils.sockets import normalizar_socket
                converter = normalizar_socket
            elif unidade == 'ddr':
                converter = lambda v: (re.search(r'ddr\s*([345])', nome(str(v))).group(1) if re.search(r'ddr\s*([345])', nome(str(v))) else None)
            else:
                converter = lambda v: nome(str(v)).replace(' ', '').replace('-', '')
            esperado, observados = converter(local), {converter(v) for v in valores}
            if esperado is None or None in observados:
                pendencias.append(f'especificacao_nao_interpretada:{campo}')
            elif observados != {esperado}:
                conflitos.append(f'especificacao_divergente:{campo}')
        if categoria in ('ssd', 'hd') and a.get('DRIVE_STORAGE_TYPE') and { {'hdd':'hd'}.get(v, v) for v in a['DRIVE_STORAGE_TYPE'] } != {categoria}:
            conflitos.append('tipo_armazenamento_divergente')
        if categoria == 'memoria_ram':
            modulos = set()
            for valor in a.get('RAM_MEMORY_MODULES', set()) | {texto}:
                m = re.search(r'\b(\d+)\s*[x×]\s*(\d+)\s*gb', valor)
                if m:
                    modulos.add(int(m[1]))
                elif valor in a.get('RAM_MEMORY_MODULES', set()) and numero(valor) is not None:
                    modulos.add(int(numero(valor)))
            quantidade = getattr(peca, 'quantidade_pentes', None)
            if modulos and modulos != {quantidade}:
                conflitos.append('quantidade_modulos_divergente')
            if kit and not modulos:
                pendencias.append('kit_sem_quantidade_comprovada')
            formato = a.get('RAM_MEMORY_FORMAT', set())
            if any('so' in v.replace('-', '') and 'dimm' in v for v in formato) and not re.search(r'notebook|laptop|so.?dimm', localnome):
                pendencias.append('formato_notebook_nao_comprovado_localmente')
        if categoria in ('memoria_ram', 'placa_video', 'ssd', 'hd'):
            capacidades = {numero(m[0] + m[1], 'gb') for m in re.findall(r'\b(\d+(?:[.,]\d+)?)\s*(gb|tb)\b', texto)}
            kit_cap = re.search(r'\b(\d+)\s*[x×]\s*(\d+)\s*gb', texto)
            if kit_cap and categoria == 'memoria_ram':
                capacidades = {numero(str(int(kit_cap[1]) * int(kit_cap[2])))}
            localcap = getattr(peca, 'memoria_gb' if categoria == 'placa_video' else 'capacidade_gb', None)
            if capacidades and localcap is not None and numero(str(localcap)) not in capacidades:
                conflitos.append('capacidade_no_titulo_divergente')
            elif len(capacidades) > 1:
                pendencias.append('capacidades_multiplas_no_titulo')
        if categoria == 'memoria_ram':
            ddrs = set(re.findall(r'ddr\s*([345])', texto))
            localddr = re.search(r'ddr\s*([345])', nome(getattr(peca, 'ddr', '')))
            if ddrs and localddr and ddrs != {localddr[1]}:
                conflitos.append('ddr_no_titulo_divergente')
        if categoria == 'memoria_ram' and re.search(r'notebook|laptop|so.?dimm', localnome) and a.get('RAM_MEMORY_FORMAT') == {'dimm'}:
            conflitos.append('formato_desktop_divergente')
        if mpn and str(mpn).upper().endswith('BOX') and (re.search(r'\b(oem|tray)\b', texto) or a.get('IS_OEM', set()) & {'sim','yes','true'}):
            conflitos.append('embalagem_box_oem_divergente')
        if not provas:
            pendencias.append('identificador_forte_ausente')
        status = 'rejeitada' if conflitos else 'ambigua' if pendencias else 'confirmada'
        return self._resultado(status, conflitos, pendencias, provas)

    @staticmethod
    def _resultado(status, conflitos, pendencias, provas):
        return dict(classificacao=status, conflitos=sorted(set(conflitos)),
                    pendencias=sorted(set(pendencias)), evidencias=sorted(set(provas)))

    def selecionar(self, pecas, produto, *, identidades=None, completo=True):
        resultados = []
        for peca in pecas:
            r = self.avaliar(peca, produto, identidade=(identidades or {}).get(peca.id))
            resultados.append(dict(peca=f'{peca.__tablename__}:{peca.id}', **r))
        confirmados = [r for r in resultados if r['classificacao'] == 'confirmada']
        ambiguos = [r for r in resultados if r['classificacao'] == 'ambigua']
        unica = len(confirmados) == 1 and not ambiguos and completo
        return dict(classificacao='confirmada' if unica else 'ambigua' if confirmados or ambiguos or not completo else 'rejeitada',
                    peca=confirmados[0]['peca'] if unica else None,
                    busca_completa=completo, candidatos=resultados)
