"""Código comercial completo em comum; não trata capacidade ou família como SKU."""
import re
from .normalizar_produto import nome


class CompararCodigoModeloService:
    @staticmethod
    def extrair(texto, categoria):
        tokens = set(re.findall(r'(?<![a-z0-9/_.-])[a-z][a-z0-9]*(?:[-./][a-z0-9]+)*(?![a-z0-9/_.-])', nome(texto)))
        resultado = set()
        for token in tokens:
            if len(token) < 4 or not re.search(r'\d', token):
                continue
            if re.match(r'^(?:ddr|gddr|wifi|cl\d|lga|am[2345]|cat[5678]|usb|pc[345]-|seed-|kabum-|rede-)', token):
                continue
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
            (produto.modelo or '', *produto.modelos_alternativos)))
        for declarado in (produto.modelo or '', *produto.modelos_alternativos):
            if codigo(declarado) in locais:
                remotos.add(codigo(declarado))
        comuns = locais & remotos
        return next(iter(comuns)) if len(comuns) == 1 else None
