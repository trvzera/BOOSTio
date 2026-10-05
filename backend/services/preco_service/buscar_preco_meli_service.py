from decimal import Decimal, InvalidOperation

from .brightdata_service import BrightDataService
from .validar_link_service import ValidarLinkService


class BuscarPrecoMeliService:
    def executar(self, url: str, snapshot_id: str | None = None):
        validador = ValidarLinkService()
        validador.executar(url, "meli")
        anuncio_id = validador._anuncio_id(url)
        # Consultar o anúncio diretamente evita a seleção automática de outro vendedor no catálogo.
        url_anuncio = f"https://produto.mercadolivre.com.br/MLB-{anuncio_id[3:]}-_JM"
        dados = BrightDataService().executar(url_anuncio, snapshot_id)
        retornado = str(dados.get("item_id") or dados.get("product_id") or "").replace("-", "")
        if retornado != anuncio_id:
            raise ValueError("A coleta não confirmou o ID do anúncio solicitado; preço preservado")
        if not isinstance(dados.get("in_stock"), bool):
            raise ValueError("A coleta não informou a disponibilidade do anúncio")
        if not dados["in_stock"]:
            return {"preco": None, "esgotado": True}
        if dados.get("currency") != "BRL":
            raise ValueError("O preço coletado não está em reais")
        try:
            preco = Decimal(str(dados.get("final_price")))
        except InvalidOperation:
            raise ValueError("Preço ausente ou inválido na coleta") from None
        if not preco.is_finite() or preco <= 0:
            raise ValueError("Preço ausente ou inválido na coleta")
        return {"preco": preco, "esgotado": False}
