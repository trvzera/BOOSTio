import re
from urllib.parse import urlsplit

import requests

from services.shopee_service.cliente_service import ClienteShopeeService


class BuscarImagemShopeeService:
    """Foto principal do anúncio da Shopee já associado à peça, vinda da API de afiliados."""
    TAMANHO_MAXIMO = 5 * 1024 * 1024
    EXTENSOES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    HOSTS = re.compile(r"([a-z0-9-]+\.)*(susercontent\.com|shopee\.com\.br)")

    def __init__(self, cliente=None):
        self.cliente = cliente

    def executar(self, vendedor_id, item_id):
        cliente = self.cliente or ClienteShopeeService()
        anuncios = cliente.consultar_imagem(vendedor_id, item_id)["nodes"]
        imagem = next((a.get("imageUrl") for a in anuncios if isinstance(a, dict)
                       and str(a.get("shopId")) == str(vendedor_id) and str(a.get("itemId")) == str(item_id)), None)
        if not self._url_permitida(imagem):
            raise ValueError("Anúncio da Shopee sem imagem principal válida")
        resposta = requests.get(imagem, timeout=(10, 30), stream=True, allow_redirects=False,
                                headers={"User-Agent": "Mozilla/5.0"})
        try:
            resposta.raise_for_status()
            if resposta.is_redirect:
                raise ValueError("A imagem redirecionou para outro endereço")
            tipo = resposta.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if tipo not in self.EXTENSOES:
                raise ValueError("A resposta da Shopee não é uma imagem suportada")
            partes, tamanho = [], 0
            for bloco in resposta.iter_content(64 * 1024):
                tamanho += len(bloco)
                if tamanho > self.TAMANHO_MAXIMO:
                    raise ValueError("Imagem da Shopee maior que 5 MB")
                partes.append(bloco)
        finally:
            resposta.close()
        conteudo = b"".join(partes)
        if not self._imagem_valida(conteudo, tipo):
            raise ValueError("O arquivo retornado não corresponde ao formato da imagem")
        return conteudo, self.EXTENSOES[tipo]

    @classmethod
    def _url_permitida(cls, url):
        if not isinstance(url, str):
            return False
        partes = urlsplit(url)
        return (partes.scheme == "https" and bool(partes.hostname) and cls.HOSTS.fullmatch(partes.hostname) is not None
                and not partes.username and not partes.password and partes.port in (None, 443))

    @staticmethod
    def _imagem_valida(conteudo, tipo):
        return (tipo == "image/jpeg" and conteudo.startswith(b"\xff\xd8\xff")
                or tipo == "image/png" and conteudo.startswith(b"\x89PNG\r\n\x1a\n")
                or tipo == "image/webp" and conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WEBP")
