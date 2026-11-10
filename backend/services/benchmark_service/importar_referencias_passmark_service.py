"""Snapshots ehan03/passmark com associações explícitas e auditáveis, sem fuzzy match."""
import csv
import hashlib
import io
import json
import re
from collections import defaultdict
from pathlib import Path

from .importar_benchmarks_service import CONFIG, ImportarBenchmarksService, normalizar_nome, pontuacao

FONTE = 'https://github.com/ehan03/passmark'
ASSOCIACOES = Path(__file__).resolve().parents[2] / 'data/benchmarks/passmark_associacoes.json'
COLUNAS = {
    'cpu': 'id name description cpu_class socket clock_speed turbo_speed cores threads total_cores primary_cores secondary_cores performance_cores efficient_cores typical_tdp tdp_down tdp_up cache_per_cpu_package cache_per_effective_cpu_package memory_support other_names first_seen_on_charts cpu_mark_per_dollar_price overall_rank last_price_change multi_thread_rating single_thread_rating num_samples margin_for_error integer_math floating_point_math find_prime_numbers random_string_sorting data_encryption data_compression physics extended_instructions relative_gaming_score'.split(),
    'gpu': 'id name bus_interface max_memory_size core_clock memory_clock directx_version opengl_version max_tdp category other_names first_benchmarked g3d_mark_per_dollar_price overall_rank last_price_change g3d_mark g2d_mark num_samples directx_9 directx_10 directx_11 directx_12 gpu_compute'.split(),
}
METRICAS = {'cpu': {'multi_thread_rating': 'benchmark_multi_core', 'single_thread_rating': 'benchmark_single_thread'},
            'gpu': {'g2d_mark': 'benchmark_g2d', 'g3d_mark': 'benchmark_g3d'}}


class ImportarReferenciasPassmarkService:
    def __init__(self, associacoes=ASSOCIACOES):
        self.associacoes = Path(associacoes)

    def _associacoes(self):
        bruto = self.associacoes.read_bytes()
        dados = json.loads(bruto)
        if not isinstance(dados, dict) or dados.get('versao') != 1 or dados.get('fonte') != FONTE or not isinstance(dados.get('associacoes'), list):
            raise ValueError('Arquivo de associações PassMark inválido')
        indice = defaultdict(list)
        for a in dados['associacoes']:
            if (not isinstance(a, dict) or a.get('tipo') not in METRICAS or type(a.get('fonte_id')) is not int
                or a['fonte_id'] <= 0 or any(not isinstance(a.get(k), str) or not a[k].strip()
                                          for k in ('fabricante','modelo','fonte_nome'))
                or a.get('escopo') != ('modelo_cpu' if a['tipo']=='cpu' else 'referencia_chip_gpu')
                or (a['tipo']=='gpu' and (type(a.get('memoria_gb')) is not int or a['memoria_gb'] <= 0))):
                raise ValueError('Associação PassMark incompleta; revise o arquivo antes de importar')
            indice[self._chave(a['tipo'], a['fabricante'], a['modelo'])].append(a)
        return indice, hashlib.sha256(bruto).hexdigest()

    @staticmethod
    def _identidade(tipo, nome):
        nome = normalizar_nome(nome)
        nome = re.sub(r"\b(i[3579])\s*-\s*(?=\d)", r"\1", nome)
        padrao = (r"\b(?:core (?:i[3579]\d{3,5}[a-z0-9]*|ultra [3579] \d{3}[a-z0-9]*)|ryzen [3579] (?:pro )?\d{4,5}[a-z0-9]*|athlon \d{4}[a-z0-9]*|ryzen threadripper (?:pro )?\d{4}[a-z0-9]*|(?:pentium|celeron) [a-z]\d{3,4}[a-z]*)\b"
                  if tipo == 'cpu' else r"\b(?:rtx|gtx|gt|rx|r[579]|arc a|hd|quadro [a-z]?|firepro [a-z]?)\s*\d{3,4}(?:\s*(?:ti|super|xtx|xt|x))?\b")
        identidades = {re.sub(r'\s+', '', x) for x in re.findall(padrao, nome)}
        if len(identidades) != 1:
            return None
        termos = ('2048sp','mobile','laptop','max q','max-q','oem','es','qs') + (('pro',) if tipo == 'cpu' else ())
        variante = tuple(termo for termo in termos
                         if re.search(r'(?<!\w)' + re.escape(termo) + r'(?!\w)', nome))
        # OEM de embalagem em CPU não muda o modelo; GPU OEM pode ser outra variante.
        if tipo == 'cpu':
            variante = tuple(x for x in variante if x != 'oem')
        return next(iter(identidades)), variante

    @classmethod
    def _validar_identidade(cls, tipo, peca, associacao):
        origem = cls._identidade(tipo, associacao['fonte_nome'])
        destino = cls._identidade(tipo, peca.modelo)
        if origem is None or origem != destino:
            return False
        if tipo == 'gpu':
            capacidades = re.findall(r'\b(\d+)\s*gb\b', associacao['fonte_nome'], re.I)
            if capacidades and set(map(int, capacidades)) != {peca.memoria_gb}:
                return False
        return True

    @classmethod
    def _por_identidade(cls, tipo, peca, ids):
        """IDs da fonte com o mesmo chip e a mesma variante (Ti, SUPER, XT, mobile...) do cadastro.

        CPU: identificada pelo nome do modelo. GPU: pelo `modelo_referencia`, porque o nome
        comercial do anúncio traz marca, cooler e overclock. Sem identidade clara, não casa."""
        nome = peca.modelo_referencia if tipo == 'gpu' else peca.modelo
        identidade = cls._identidade(tipo, nome) if nome else None
        if identidade is None:
            return set()
        achados = set()
        for ident, grupo in ids.items():
            fonte = cls._identidade(tipo, grupo[0]['nome'])
            if fonte != identidade:
                continue
            capacidades = re.findall(r'\b(\d+)\s*gb\b', grupo[0]['nome'], re.I)
            if tipo == 'gpu' and capacidades and set(map(int, capacidades)) != {peca.memoria_gb}:
                continue
            achados.add(ident)
        if len(achados) > 1:
            # Vários da mesma família (ex.: RX 5700 XT e RX 5700 XT 50th Anniversary): vale o que tem exatamente o nome do cadastro.
            exatos = {i for i in achados if cls._nome_basico(ids[i][0]['nome']) == cls._nome_basico(nome)}
            if len(exatos) > 1 and tipo == 'gpu':
                # Entre cópias do mesmo nome, vale a que cita a mesma memória do cadastro.
                exatos = {i for i in exatos if {int(x) for x in re.findall(r'\b(\d+)\s*gb\b', ids[i][0]['nome'], re.I)} == {peca.memoria_gb}}
            if len(exatos) == 1:
                return exatos
        return achados

    @staticmethod
    def _nome_basico(nome):
        nome = normalizar_nome(nome)
        nome = re.sub(r'@.*$', '', nome)
        nome = re.sub(r'\b\d+\s*gb\b', '', nome)
        nome = re.sub(r'\b(?:geforce|radeon|nvidia|amd|intel)\b', '', nome)
        return re.sub(r'[^a-z0-9]', '', nome)

    @staticmethod
    def _chave(tipo, fabricante, modelo):
        return tipo, normalizar_nome(fabricante), normalizar_nome(modelo)

    def _ler(self, caminho, tipo):
        bruto = Path(caminho).read_bytes()
        try:
            leitor = csv.DictReader(io.StringIO(bruto.decode('utf-8-sig'), newline=''), strict=True)
            cab = leitor.fieldnames
            if not cab or len(cab) != len(set(cab)) or set(cab) != set(COLUNAS[tipo]):
                raise ValueError(f'Cabeçalho inesperado no snapshot PassMark {tipo}')
            ids, nomes = defaultdict(list), defaultdict(set)
            invalidas = 0
            for r in leitor:
                if None in r or any(v is None for v in r.values()):
                    raise ValueError(f'Número de colunas inválido: {tipo}, linha {leitor.line_num}')
                ident = r['id']
                if not ident.isascii() or not ident.isdecimal() or int(ident) <= 0:
                    raise ValueError(f'ID de origem inválido: {tipo}, linha {leitor.line_num}')
                nome = r['name']
                erro = None
                valores = {}
                try:
                    if not nome.strip() or len(nome) > 255 or any(ord(x)<32 for x in nome):
                        raise ValueError('nome inválido')
                    for origem, destino in METRICAS[tipo].items():
                        valor = r[origem].strip()
                        valores[destino] = pontuacao('' if valor.casefold() in ('na', 'n/a') else valor)
                    if not any(v is not None for v in valores.values()):
                        raise ValueError('sem pontuação')
                except ValueError as e:
                    erro = str(e)
                    invalidas += 1
                ids[int(ident)].append(dict(nome=nome, valores=valores, erro=erro, linha=leitor.line_num))
                nomes[normalizar_nome(nome)].add(int(ident))
            duplicadas = sum(len(g)-1 for g in ids.values() if not any(x['erro'] for x in g)
                             and all(x['nome']==g[0]['nome'] and x['valores']==g[0]['valores'] for x in g))
            return ids, nomes, dict(duplicadas_equivalentes=duplicadas, sha256=hashlib.sha256(bruto).hexdigest(), linhas=sum(map(len,ids.values())),
                                    fonte=f'{FONTE}/blob/main/data/raw/{tipo}/{"cpus" if tipo=="cpu" else "gpus"}.csv',
                                    linhas_invalidas=invalidas)
        except (UnicodeError, csv.Error) as e:
            raise ValueError(f'Formato inválido no snapshot PassMark {tipo}') from e

    def executar(self, cpu=None, gpu=None, simular=False, lote=100):
        if not cpu and not gpu:
            raise ValueError('Informe ao menos um CSV de CPU ou GPU')
        if type(lote) is not int or lote < 1:
            raise ValueError('O lote deve ser positivo')
        aliases, sha_alias = self._associacoes()
        # Todos os arquivos e associações são lidos antes de confirmar qualquer lote.
        fontes = [(t,*self._ler(p,t)) for t,p in (('cpu',cpu),('gpu',gpu)) if p]
        contadores = ('atualizadas','propostas','inalteradas','nao_encontradas','ambiguas','invalidas')
        resumo = dict(simulacao=simular, fonte=FONTE, associacoes_sha256=sha_alias,
                      **{k:0 for k in contadores}, duplicadas=0, detalhes=[], arquivos={}, por_tipo={})
        planos = []
        for tipo, ids, nomes, arquivo in fontes:
            classe, _, teste, _ = CONFIG[tipo]
            resumo['arquivos'][tipo] = arquivo
            resumo['duplicadas'] += arquivo['duplicadas_equivalentes']
            parcial = resumo['por_tipo'][tipo] = {k:0 for k in contadores}
            pecas = classe.mostrar_pecas()
            catalogo = defaultdict(list)
            for p in pecas:
                catalogo[self._chave(tipo,p.fabricante,p.modelo)].append(p.id)
            for p in pecas:
                chave = self._chave(tipo,p.fabricante,p.modelo)
                detalhe = dict(tipo=tipo,id=p.id,modelo=p.modelo)
                def registrar(status, motivo=None):
                    resumo[status] += 1
                    parcial[status] += 1
                    resumo['detalhes'].append({**detalhe,'status':status,**({'motivo':motivo} if motivo else {})})
                associadas = aliases.get(chave, [])
                if len(associadas) > 1 or (associadas and len(catalogo[chave]) != 1):
                    registrar('ambiguas','múltiplos cadastros ou associações para o mesmo nome comercial')
                    continue
                if associadas:
                    a = associadas[0]
                    if tipo=='gpu' and p.memoria_gb != a['memoria_gb']:
                        registrar('invalidas','VRAM do cadastro difere da associação revisada')
                        continue
                    if not self._validar_identidade(tipo,p,a):
                        registrar('invalidas','identidade, sufixos ou variante da associação não conferem')
                        continue
                    ident = a['fonte_id']
                    detalhe.update(fonte_id=ident,associacao=a['escopo'])
                    grupo = ids.get(ident, [])
                    if not grupo:
                        registrar('nao_encontradas','ID revisado ausente no snapshot')
                        continue
                    if any(r['nome'] != a['fonte_nome'] for r in grupo):
                        registrar('ambiguas','nome da referência mudou; revisar associação')
                        continue
                else:
                    candidatos = set()
                    for nome in (p.modelo, f'{p.fabricante} {p.modelo}'):
                        candidatos |= nomes.get(normalizar_nome(nome), set())
                    associacao = 'nome_exato_normalizado'
                    if candidatos and len(catalogo[chave]) != 1:
                        registrar('ambiguas','múltiplos cadastros com o mesmo nome comercial')
                        continue
                    if not candidatos:
                        candidatos = self._por_identidade(tipo, p, ids)
                        associacao = 'identidade_do_modelo'
                    if len(candidatos) != 1:
                        registrar('ambiguas' if candidatos else 'nao_encontradas', 'sem referência única revisada ou exata')
                        continue
                    ident = next(iter(candidatos))
                    grupo = ids[ident]
                    detalhe.update(fonte_id=ident,associacao=associacao)
                r = grupo[0]
                if any(x['erro'] for x in grupo):
                    registrar('invalidas','entrada de origem inválida; benchmark anterior preservado')
                    continue
                if any(x['nome'] != r['nome'] or x['valores'] != r['valores'] for x in grupo[1:]):
                    registrar('ambiguas','ID de origem duplicado com dados conflitantes')
                    continue
                if len(nomes[normalizar_nome(r['nome'])]) > 1:
                    registrar('ambiguas','múltiplos IDs na fonte para o mesmo nome')
                    continue
                detalhe.update(nome=r['nome'],linhas=[x['linha'] for x in grupo])
                dados = {k:v for k,v in r['valores'].items() if v is not None}
                if len(dados) < len(METRICAS[tipo]) and (p.benchmark_teste not in (None,teste) or p.benchmark_versao is not None):
                    registrar('invalidas','métricas parciais de teste diferente')
                    continue
                dados.update(benchmark_teste=teste,benchmark_versao=None,benchmark_nome_fonte=r['nome'],
                             benchmark_fonte=arquivo['fonte'],benchmark_referencia_em=None)
                mudancas={k:v for k,v in dados.items() if getattr(p,k)!=v}
                if not mudancas:
                    registrar('inalteradas')
                    continue
                detalhe['alteracoes']={k:{'antes':str(getattr(p,k)) if getattr(p,k) is not None else None,
                                          'depois':str(v) if v is not None else None} for k,v in mudancas.items()}
                registrar('propostas')
                planos.append((classe,p.id,mudancas))
        return resumo if simular else ImportarBenchmarksService._persistir(planos,resumo,lote)
