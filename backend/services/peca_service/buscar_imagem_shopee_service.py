import re
from urllib.parse import urlsplit

from services.shopee_service.cliente_service import ClienteShopeeService
from .baixar_imagem_segura import baixar_imagem_segura


class BuscarImagemShopeeService:
    """Foto principal do anúncio da Shopee já associado à peça, vinda da API de afiliados."""
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
        return baixar_imagem_segura(imagem, "da Shopee")

    @classmethod
    def _url_permitida(cls, url):
        if not isinstance(url, str):
            return False
        partes = urlsplit(url)
        return (partes.scheme == "https" and bool(partes.hostname) and cls.HOSTS.fullmatch(partes.hostname) is not None
                and not partes.username and not partes.password and partes.port in (None, 443))
