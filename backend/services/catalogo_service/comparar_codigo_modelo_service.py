"""Código comercial completo em comum; não trata capacidade ou família como SKU."""
import re
from .normalizar_produto import nome


class CompararCodigoModeloService:
    @staticmethod
    def variantes_armazenamento(peca, produto):
        """Códigos completos de discos não são intercambiáveis pela mesma linha."""
        if peca.__tablename__ not in ('ssd','hd'):
            return dict(conflitos=[],pendencias=[])
        from .conferir_especificacoes_service import valores
        padrao = r'(?<![a-z0-9])(?:st\d{3,5}[a-z]{2}\d{3,4}(?:-[a-z0-9]+)*|wd\d{2,5}[a-z]{3,6}(?:-[a-z0-9]+)*|wds\d[a-z0-9]{5,}(?:-[a-z0-9]+)*|mz[-/][a-z0-9]+(?:[-/][a-z0-9]+)*)(?![a-z0-9])'
        def extrair(textos):
            return set(re.findall(padrao,nome(' '.join(v for v in textos if isinstance(v,str)))))
        locais = extrair([peca.modelo,getattr(peca,'part_number',None),getattr(peca,'codigo_modelo_fabricante',None)])
        remotos = extrair([produto.titulo,produto.modelo,*produto.modelos_alternativos,*valores(produto.identificadores.get('mpn'))])
        conflitos=[];pendencias=[]
        if locais and remotos and not locais & remotos:
            conflitos.append('codigo_armazenamento_divergente')
        if len(locais)>1 or len(remotos)>1:
            pendencias.append('codigos_armazenamento_multiplos')
        modelo=nome(peca.modelo);interface=nome(getattr(peca,'interface','') or '')
        if re.search(r'\bsas(?:\s*[123])?\b',modelo) and 'sata' in interface:
            conflitos.append('interface_local_inconsistente')
        if re.search(r'\bsata\b',modelo) and re.search(r'\bsas\b',interface):
            conflitos.append('interface_local_inconsistente')
        return dict(conflitos=conflitos,pendencias=pendencias)

    @staticmethod
    def extrair(texto, categoria):
        normalizado = nome(texto)
        # A normalização de nomes separa RTX4060 para comparar chips. Dentro
        # de um SKU hifenizado, preserve DUAL-RTX4060-O8G-EVO inteiro.
        normalizado = re.sub(r'(?<=[/-])(rtx|gtx|rx)\s+(?=\d)', r'\1', normalizado)
        tokens = set(re.findall(r'(?<![a-z0-9/_.-])[a-z][a-z0-9]*(?:[-./][a-z0-9]+)*(?![a-z0-9/_.-])', normalizado))
        resultado = set()
        for token in tokens:
            if len(token) < 4 or not re.search(r'\d', token):
                continue
            if re.match(r'^(?:ddr|gddr|wifi|cl\d|lga|am[2345]|cat[5678]|usb|pcie|nvme|sata|gen\d|pc[345]-|seed-|kabum-|rede-)', token):
                continue
            if re.fullmatch(r'[a-z]{1,4}\d{0,2}\.\d{1,2}', token):
                continue  # Versão de linha/protocolo não identifica um SKU completo.
            if categoria == 'placa_mae' and re.fullmatch(r'[abhxzwq]\d{3}[a-z]?', token):
                continue
            if re.fullmatch(r'(?:rtx|gtx|rx|arc)\d+[a-z]*|(?:ryzen|corei|i)[3579]|[a-z]*\d+(?:gb|tb|mhz|hz|mm|cm|mbps)', token):
                continue
            resultado.add(token)
        return resultado

    def executar(self, peca, produto):
        if peca.__tablename__ in ('placa_mae', 'placa_video'):
            linhas = {'prime','tuf','rog','strix','aorus','aero','pro','dual','phoenix','ventus','eagle','windforce'}
            local = set(re.findall(r'\b[a-z]+\b', nome(peca.modelo))) & linhas
            remoto = set(re.findall(r'\b[a-z]+\b', nome(' '.join([produto.titulo, produto.modelo or '', *produto.modelos_alternativos])))) & linhas
            if local != remoto:
                return None
        locais = self.extrair(peca.modelo, peca.__tablename__)
        from .normalizar_produto import codigo
        from utils.codigos_peca import codigo_interno
        for declarado in (getattr(peca, 'codigo_modelo_fabricante', None), getattr(peca, 'part_number', None)):
            if declarado and not codigo_interno(declarado):
                locais.add(codigo(declarado))
        remotos = set().union(*(self.extrair(v, peca.__tablename__) for v in
            (produto.titulo, produto.modelo or '', *produto.modelos_alternativos)))
        for declarado in (produto.modelo or '', *produto.modelos_alternativos):
            if codigo(declarado) in locais:
                remotos.add(codigo(declarado))
        comuns = locais & remotos
        return next(iter(comuns)) if len(comuns) == 1 else None
