import os
import requests


class RenovarTokenMercadoLivreService:

    def executar(self, refresh_token):

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
            }
        )

        response.raise_for_status()

        return response.json()