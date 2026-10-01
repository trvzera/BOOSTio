from datetime import datetime, timedelta, timezone

from models import TokensMeli
from utils.validacoes import validacao_campos


class SalvarTokensMeliService:
    def executar(self, dados: dict) -> TokensMeli:
        validacao_campos(dados, ["access_token", "refresh_token", "expires_in"])

        if not isinstance(dados["access_token"], str) or not isinstance(dados["refresh_token"], str):
            raise ValueError("Tokens do Mercado Livre inválidos")

        try:
            segundos_ate_expirar = int(dados["expires_in"])
        except (TypeError, ValueError) as erro:
            raise ValueError("Prazo de expiração do token inválido") from erro

        if segundos_ate_expirar <= 0:
            raise ValueError("Prazo de expiração do token inválido")

        tokens = TokensMeli.buscar_atual() or TokensMeli()
        tokens.access_token = dados["access_token"]
        tokens.refresh_token = dados["refresh_token"]
        tokens.data_expiracao = datetime.now(timezone.utc) + timedelta(seconds=segundos_ate_expirar)
        tokens.salvar()

        return tokens
