import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

import requests

from services.preco_service.validar_link_service import ValidarLinkService
from services.preco_service.buscar_pagina_kabum_service import BuscarPaginaKabumService


class _MetadadosProduto(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metadados = {}
        self.scripts = []
        self._partes = None

    def handle_starttag(self, tag, attrs):
        atributos = dict(attrs)
        if tag == "meta":
            chave = atributos.get("property") or atributos.get("name")
            if chave in ("og:image", "og:url"):
                self.metadados[chave] = atributos.get("content")
        elif tag == "link" and "canonical" in atributos.get("rel", "").split():
            self.metadados["canonical"] = atributos.get("href")
        elif tag == "script" and atributos.get("type", "").lower() == "application/ld+json":
            self._partes = []

    def handle_data(self, data):
        if self._partes is not None:
            self._partes.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._partes is not None:
            self.scripts.append("".join(self._partes))
            self._partes = None


class BuscarImagemKabumService:
    TAMANHO_MAXIMO = 5 * 1024 * 1024

    def executar(self, url):
        ValidarLinkService().executar(url)
        codigo = self._codigo(url)
        imagem = self._imagem_do_anuncio(BuscarPaginaKabumService().executar(url), codigo)
        resposta_imagem = requests.get(imagem, timeout=(10, 30), stream=True,
                                      allow_redirects=False,
                                      headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.kabum.com.br/"})
        resposta_imagem.raise_for_status()
        if resposta_imagem.is_redirect:
            raise ValueError("A imagem redirecionou para outro endereço")
        tipo = resposta_imagem.headers.get("Content-Type", "").split(";", 1)[0].lower()
        extensoes = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
        if tipo not in extensoes:
            raise ValueError("A resposta do anúncio não é uma imagem suportada")
        partes = []
        tamanho = 0
        for bloco in resposta_imagem.iter_content(64 * 1024):
            tamanho += len(bloco)
            if tamanho > self.TAMANHO_MAXIMO:
                raise ValueError("Imagem do anúncio maior que 5 MB")
            partes.append(bloco)
        conteudo = b"".join(partes)
        if not self._imagem_valida(conteudo, tipo):
            raise ValueError("O arquivo retornado não corresponde ao formato da imagem")
        return conteudo, extensoes[tipo]

    @staticmethod
    def _codigo(url):
        return re.match(r"/produto/(\d+)(?:/|$)", urlsplit(url).path).group(1)

    @staticmethod
    def _produtos(dados):
        if isinstance(dados, list):
            for item in dados:
                yield from BuscarImagemKabumService._produtos(item)
        elif isinstance(dados, dict):
            tipo = dados.get("@type")
            if tipo == "Product" or isinstance(tipo, list) and "Product" in tipo:
                yield dados
            if "@graph" in dados:
                yield from BuscarImagemKabumService._produtos(dados["@graph"])

    @classmethod
    def _imagem_do_anuncio(cls, html, codigo):
        parser = _MetadadosProduto()
        parser.feed(html)
        for script in parser.scripts:
            try:
                dados = json.loads(script)
            except json.JSONDecodeError:
                continue
            for produto in cls._produtos(dados):
                identificadores = (produto.get("sku"), produto.get("productID"))
                urls = (produto.get("@id"), produto.get("url"))
                if not (any(str(id_) == codigo for id_ in identificadores if id_ is not None)
                        or any(cls._codigo_identificado(url) == codigo for url in urls)):
                    continue
                imagens = produto.get("image")
                if not isinstance(imagens, list):
                    imagens = [imagens]
                for imagem in imagens:
                    if isinstance(imagem, dict):
                        imagem = imagem.get("url") or imagem.get("contentUrl")
                    if cls._imagem_do_produto(imagem, codigo):
                        return imagem
        if any(cls._codigo_identificado(parser.metadados.get(chave)) == codigo
               for chave in ("og:url", "canonical")):
            imagem = parser.metadados.get("og:image")
            if cls._imagem_do_produto(imagem, codigo):
                return imagem
        raise ValueError("Imagem principal do produto não encontrada nos metadados da KaBuM")

    @staticmethod
    def _codigo_identificado(url):
        if not isinstance(url, str):
            return None
        partes = urlsplit(url)
        if partes.hostname not in {"kabum.com.br", "www.kabum.com.br"}:
            return None
        achado = re.match(r"/produto/(\d+)(?:/|$)", partes.path)
        return achado.group(1) if achado else None

    @staticmethod
    def _imagem_do_produto(url, codigo):
        if not isinstance(url, str):
            return False
        partes = urlsplit(url)
        return (partes.scheme == "https" and partes.hostname == "images.kabum.com.br"
                and not partes.username and not partes.password and partes.port in (None, 443)
                and (partes.path.startswith(f"/produtos/fotos/{codigo}/")
                     or partes.path.startswith(f"/produtos/fotos/sync_mirakl/{codigo}/")))

    @staticmethod
    def _imagem_valida(conteudo, tipo):
        return (tipo == "image/jpeg" and conteudo.startswith(b"\xff\xd8\xff")
                or tipo == "image/png" and conteudo.startswith(b"\x89PNG\r\n\x1a\n")
                or tipo == "image/webp" and conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WEBP")
