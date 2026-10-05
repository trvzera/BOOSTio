from decimal import Decimal, InvalidOperation

from .consultar_api_service import ConsultarApiMercadoLivreService


class PrecoMercadoLivreIndisponivelError(ValueError):
    pass


class BuscarPrecoMercadoLivreService:
    """Consulta o preço de venda de um anúncio específico, sem frete."""

    def executar(self, anuncio_id: str) -> Decimal:
        dados = ConsultarApiMercadoLivreService().executar(
            f"/items/{anuncio_id}/sale_price",
            {"context": "channel_marketplace"},
        )
        return self._obter_preco(dados)

    def _obter_preco(self, dados):
        # Uma resposta sem preço nunca deve substituir o valor salvo por zero.
        try:
            preco = Decimal(str(dados.get("amount")))
        except (InvalidOperation, ValueError):
            raise PrecoMercadoLivreIndisponivelError(
                "O Mercado Livre não retornou um preço de venda válido"
            ) from None

        if not preco.is_finite() or preco <= 0:
            raise PrecoMercadoLivreIndisponivelError("Preço de venda indisponível")
        if dados.get("currency_id") != "BRL":
            raise PrecoMercadoLivreIndisponivelError("O preço retornado não está em reais")
        return preco
