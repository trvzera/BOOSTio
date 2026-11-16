import re
from urllib.parse import urlsplit

import requests

from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService


class BuscarImagemMercadoLivreService:
    """Foto oficial do produto de catálogo vinculado, nunca a miniatura de um anúncio de vendedor."""
    TAMANHO_MAXIMO = 5 * 1024 * 1024
    EXTENSOES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}

    def __init__(self, cliente=None, token=None):
        self.cliente = cliente or BuscarOfertasMercadoLivreService()
        self.token = token

    def executar(self, catalogo_id):
        BuscarOfertasMercadoLivreService._validar_id(catalogo_id, "produto de catálogo")
        token = self.token or TokenMercadoLivreService().executar()
        produto = self.cliente._consultar(f"/products/{catalogo_id}", token)
        if produto.get("id") != catalogo_id:
            raise ValueError("Produto de catálogo diferente do vinculado")
        imagem = self._imagem_do_catalogo(produto)
        resposta = requests.get(imagem, timeout=(10, 30), stream=True, allow_redirects=False,
                                headers={"User-Agent": "Mozilla/5.0"})
        try:
            resposta.raise_for_status()
            if resposta.is_redirect:
                raise ValueError("A imagem redirecionou para outro endereço")
            tipo = resposta.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if tipo not in self.EXTENSOES:
                raise ValueError("A resposta do catálogo não é uma imagem suportada")
            partes, tamanho = [], 0
            for bloco in resposta.iter_content(64 * 1024):
                tamanho += len(bloco)
                if tamanho > self.TAMANHO_MAXIMO:
                    raise ValueError("Imagem do catálogo maior que 5 MB")
                partes.append(bloco)
        finally:
            resposta.close()
        conteudo = b"".join(partes)
        if not self._imagem_valida(conteudo, tipo):
            raise ValueError("O arquivo retornado não corresponde ao formato da imagem")
        return conteudo, self.EXTENSOES[tipo]

    @classmethod
    def _imagem_do_catalogo(cls, produto):
        for foto in produto.get("pictures") or []:
            url = foto.get("url") if isinstance(foto, dict) else None
            if cls._url_permitida(url):
                return url
        raise ValueError("Catálogo do Mercado Livre sem imagem principal válida")

    @staticmethod
    def _url_permitida(url):
        if not isinstance(url, str):
            return False
        partes = urlsplit(url)
        return (partes.scheme == "https" and bool(partes.hostname)
                and re.fullmatch(r"([a-z0-9-]+\.)*mlstatic\.com", partes.hostname) is not None
                and not partes.username and not partes.password and partes.port in (None, 443))

    @staticmethod
    def _imagem_valida(conteudo, tipo):
        return (tipo == "image/jpeg" and conteudo.startswith(b"\xff\xd8\xff")
                or tipo == "image/png" and conteudo.startswith(b"\x89PNG\r\n\x1a\n")
                or tipo == "image/webp" and conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WEBP")
