import os
import requests
from models import TokensMeli
from .salvar_tokens_service import SalvarTokensMeliService


class RefreshTokenMercadoLivreService:

    def executar(self, refresh_token=None):

        if refresh_token is None:
            tokens = TokensMeli.buscar_atual()
            if tokens is None:
                raise ValueError("Nenhum refresh token do Mercado Livre foi salvo")
            refresh_token = tokens.refresh_token

        url = "https://api.mercadolibre.com/oauth/token"

        dados = {
            "grant_type": "refresh_token",
            "client_id": os.getenv("ML_CLIENT_ID"),
            "client_secret": os.getenv("ML_CLIENT_SECRET"),
            "refresh_token": refresh_token
        }

        response = requests.post(
            url,
            data=dados,
            headers={
                "accept": "application/json",
                "content-type": "application/x-www-form-urlencoded"
            },
            timeout=15,
        )

        response.raise_for_status()

        novos_tokens = response.json()
        SalvarTokensMeliService().executar(novos_tokens)

        return novos_tokens
