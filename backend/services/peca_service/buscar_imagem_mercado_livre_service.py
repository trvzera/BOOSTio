import re
from urllib.parse import urlsplit

from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService
from .baixar_imagem_segura import baixar_imagem_segura


class BuscarImagemMercadoLivreService:
    """Foto oficial do produto de catálogo vinculado, nunca a miniatura de um anúncio de vendedor."""

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
        return baixar_imagem_segura(imagem, "do catálogo")

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
