import re
from urllib.parse import urlsplit, unquote
from defusedxml.ElementTree import fromstring
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError
from services.catalogo_service.normalizar_produto import codigo, nome
from services.catalogo_service.conferir_especificacoes_service import valores
from .consultar_paginas_service import DOMINIOS


class DescobrirFichaFabricanteService:
    def __init__(self,paginas):
        self.paginas=paginas

    def executar(self, fabricante, produto):
        chaves=[*valores(produto.identificadores.get('mpn')),produto.modelo,*produto.modelos_alternativos]
        chaves.extend(re.findall(r'\b[a-zA-Z]{1,3}\d{3,5}[a-zA-Z0-9]*\b',produto.titulo))
        chaves={codigo(v) for v in chaves if v and len(codigo(v))>=4 and re.search(r'\d',codigo(v))}
        if not chaves:
            return []
        regras=self.paginas.regras(fabricante)
        mapas=regras.site_maps() or []
        def prioridade(u):
            caminho=urlsplit(u).path
            return (not any(v in caminho for v in ('us-','/en-us/','/en-in/','/en-ph/')), 'products' not in caminho, u)
        mapas=sorted(mapas,key=prioridade)
        vistos=set();encontrados=set()
        while mapas and len(vistos)<8:
            url=mapas.pop(0)
            if url in vistos:continue
            try:self.paginas.validar(url,fabricante)
            except ValueError:continue
            vistos.add(url)
            try:
                raiz=fromstring(self.paginas.executar(url,fabricante))
            except (ParseError,DefusedXmlException):
                raise ValueError('Sitemap oficial inválido ou inseguro') from None
            locais=[e.text for e in raiz.iter() if e.tag.rsplit('}',1)[-1]=='loc' and e.text]
            if raiz.tag.rsplit('}',1)[-1]=='sitemapindex':
                mapas.extend(locais)
                mapas.sort(key=prioridade)
                continue
            for destino in locais:
                p=urlsplit(destino)
                if p.hostname!=DOMINIOS[fabricante]:continue
                caminho=nome(unquote(p.path))
                segmentos={codigo(v) for v in unquote(p.path).split('/')}
                corresponde = bool(segmentos & chaves) if fabricante=='corsair' else any(
                    re.search(r'(?<![a-z0-9])'+re.escape(c)+r'(?![a-z0-9])',caminho) for c in chaves)
                if corresponde:
                    encontrados.add(destino)
                    if len(encontrados)>5:return []
        ingles=[u for u in encontrados if '/us/en/' in u or re.search(r'/en(?:-|/)',urlsplit(u).path)]
        return sorted(ingles or encontrados)
