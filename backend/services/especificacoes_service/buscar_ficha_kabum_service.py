"""Reaproveita a leitura pública de páginas; não executa scripts do site."""
import json
from html.parser import HTMLParser
from models.medidas_fisicas import produto_kabum
from services.preco_service.buscar_pagina_kabum_service import BuscarPaginaKabumService


class _ScriptsJson(HTMLParser):
    def __init__(self):
        super().__init__(); self.ler = False; self.partes = []; self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == 'script' and dict(attrs).get('type') in ('application/json', 'application/ld+json'):
            self.ler = True; self.partes = []

    def handle_data(self, texto):
        if self.ler:
            self.partes.append(texto)

    def handle_endtag(self, tag):
        if tag == 'script' and self.ler:
            self.scripts.append(''.join(self.partes)); self.ler = False


class BuscarFichaKabumService:
    def __init__(self, paginas=None):
        self.paginas = paginas or BuscarPaginaKabumService()

    def executar(self, url):
        codigo = produto_kabum(url)
        if codigo is None:
            raise ValueError('URL original da KaBuM inválida')
        parser = _ScriptsJson(); parser.feed(self.paginas.executar(url))
        encontrados = {}
        def visitar(dados, profundidade=0):
            if profundidade > 40:
                raise ValueError('Documento estruturado excessivamente profundo')
            if isinstance(dados, dict):
                if str(dados.get('id')) == codigo and isinstance(dados.get('technicalInformation'), dict):
                    assinatura = json.dumps(dados, sort_keys=True, ensure_ascii=False)
                    encontrados[assinatura] = dados
                for valor in dados.values():
                    visitar(valor, profundidade + 1)
            elif isinstance(dados, list):
                for valor in dados:
                    visitar(valor, profundidade + 1)
        for script in parser.scripts:
            try:
                dados = json.loads(script)
            except ValueError:
                continue
            visitar(dados)
        if len(encontrados) != 1:
            raise ValueError('Ficha técnica original ausente ou ambígua na página')
        return next(iter(encontrados.values()))
