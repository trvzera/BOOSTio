import json
import re
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit

from .validar_link_service import ValidarLinkService
from .buscar_pagina_kabum_service import BuscarPaginaKabumService


class _DadosEstruturados(HTMLParser):
    def __init__(self):
        super().__init__()
        self._script = False
        self._partes = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("type", "").lower() == "application/ld+json":
            self._script = True
            self._partes = []

    def handle_data(self, data):
        if self._script:
            self._partes.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._script:
            self.scripts.append("".join(self._partes))
            self._script = False


class BuscarPrecoKabumService:
    """Lê somente a oferta estruturada do anúncio solicitado na KaBuM!."""

    def executar(self, url: str):
        ValidarLinkService().executar(url)
        codigo = re.match(r"/produto/(\d+)(?:/|$)", urlsplit(url).path).group(1)
        parser = _DadosEstruturados()
        parser.feed(BuscarPaginaKabumService().executar(url))
        produtos = []
        for script in parser.scripts:
            try:
                dados = json.loads(script)
            except json.JSONDecodeError:
                continue
            produtos.extend(self._produtos(dados))
        for produto in produtos:
            identificador = produto.get("sku") or produto.get("productID")
            url_produto = produto.get("url")
            codigo_url = re.search(r"/produto/(\d+)(?:/|$)", urlsplit(url_produto).path) if isinstance(url_produto, str) else None
            if identificador is not None and str(identificador) != codigo:
                continue
            if codigo_url and codigo_url.group(1) != codigo:
                continue
            if identificador is None and codigo_url is None:
                continue
            ofertas = produto.get("offers")
            if isinstance(ofertas, list):
                ofertas = ofertas[0] if len(ofertas) == 1 else None
            if not isinstance(ofertas, dict):
                continue
            disponibilidade = ofertas.get("availability")
            if not isinstance(disponibilidade, str):
                raise ValueError("Disponibilidade da KaBuM ausente ou desconhecida")
            disponibilidade = disponibilidade.rsplit("/", 1)[-1]
            if disponibilidade == "OutOfStock":
                return {"preco": None, "esgotado": True}
            if disponibilidade != "InStock":
                raise ValueError("Disponibilidade da KaBuM ausente ou desconhecida")
            if ofertas.get("priceCurrency") != "BRL":
                raise ValueError("A oferta da KaBuM não informou preço em reais")
            try:
                preco = Decimal(str(ofertas.get("price")))
            except InvalidOperation:
                raise ValueError("Preço ausente ou inválido na KaBuM") from None
            if not preco.is_finite() or preco <= 0:
                raise ValueError("Preço ausente ou inválido na KaBuM")
            return {"preco": preco, "esgotado": False}
        raise ValueError("Oferta estruturada do produto não encontrada na página da KaBuM")

    def _produtos(self, dados):
        if isinstance(dados, list):
            for item in dados:
                yield from self._produtos(item)
        elif isinstance(dados, dict):
            tipo = dados.get("@type")
            if tipo == "Product" or isinstance(tipo, list) and "Product" in tipo:
                yield dados
            if "@graph" in dados:
                yield from self._produtos(dados["@graph"])
