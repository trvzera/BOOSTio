import requests
import os
from dotenv import load_dotenv
from models import TokensMeli
from datetime import datetime, timedelta, timezone
from services.mercadolivre_scapring_service.refresh_token_service import RefreshTokenMercadoLivreService

load_dotenv()

class MercadoLivreScapringService:
  def executar(self, termo_busca: str):
    token = self._obter_token_atual()

    url = "https://api.mercadolibre.com/products/search"

    headers = {
      "Authorization": f"Bearer {token.access_token}"
    }

    params = {
        "status": "active",
        "site_id": "MLB",
        "q": termo_busca.strip(),
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=15,
    )

    status = response.status_code
    tipo_conteudo = response.headers.get("Content-Type", "não informado")
    
    if not response.ok:
      raise requests.HTTPError(
        f"Consulta ao Mercado Livre falhou: HTTP {status}; Content-Type: {tipo_conteudo}",
        response=response,
      )

    dados = response.json()

    if not dados:
      raise ValueError("A resposta da API está vazia")

    return dados
  
  def _obter_token_atual(self):
    token = TokensMeli.buscar_atual()
    
    if token is None:
      RefreshTokenMercadoLivreService().executar(os.getenv("refresh_token"))
      token = TokensMeli.buscar_atual()
    
    data_expiracao = token.data_expiracao
    
    # Verificação se esta em UTC
    if data_expiracao.tzinfo is None:
      data_expiracao = data_expiracao.replace(tzinfo=timezone.utc)
    
    if data_expiracao <= datetime.now(timezone.utc) + timedelta(minutes=1):
      RefreshTokenMercadoLivreService().executar(token.refresh_token)
      token = TokensMeli.buscar_atual()

    return token