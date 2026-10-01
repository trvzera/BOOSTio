import requests
import os
import time
import random
from email.utils import parsedate_to_datetime
from dotenv import load_dotenv
from models import TokensMeli
from datetime import datetime, timedelta, timezone
from services.mercadolivre_scapring_service.refresh_token_service import RefreshTokenMercadoLivreService

load_dotenv()

class MercadoLivreScapringService:
  def executar(self, termos_busca: list[str] | None = None, produto_id: str | None = None):
    if not termos_busca:
      if not produto_id:
        raise ValueError("Informe os termos de busca ou o ID do produto de catálogo")
      url = f"https://api.mercadolibre.com/products/{produto_id}"
      response = self._requisitar_com_tentativas(url, None)
      return [self._tratar_resposta(response)]

    url = "https://api.mercadolibre.com/products/search"
    dados_totais = []

    
    for indice, termo in enumerate(termos_busca):
      if indice:
        time.sleep(1)
      params = {
          "status": "active",
          "site_id": "MLB",
          "q": termo.strip(),
      }

      response = self._requisitar_com_tentativas(url, params)

      dados = self._tratar_resposta(response)

      produtos = dados.get("results", [])
      if not produtos:
        print("A resposta da API esta vazia")
        continue

      dados_totais.append(produtos[0])
    
    return dados_totais 

  def _tratar_resposta(self, response):
    if not response.ok:
      tipo_conteudo = response.headers.get("Content-Type", "não informado")
      raise requests.HTTPError(
        f"Consulta ao Mercado Livre falhou: HTTP {response.status_code}; Content-Type: {tipo_conteudo}",
        response=response,
      )
    return response.json()

  def _requisitar_com_tentativas(self, url, params):
    for tentativa in range(3):
      token = self._obter_token_atual()
      response = requests.get(
        url, params=params,
        headers={"Authorization": f"Bearer {token.access_token}"}, timeout=15,
      )
      if response.status_code != 429:
        return response

      espera = self._tempo_espera(response, tentativa)
      if tentativa == 2 or espera > 60:
        raise requests.HTTPError(
          f"Limite de requisições do Mercado Livre (HTTP 429). "
          f"Tente novamente em pelo menos {espera:.0f} segundos.",
          response=response,
        )
      time.sleep(espera)

  def _tempo_espera(self, response, tentativa):
    retry_after = response.headers.get("Retry-After", "")
    if retry_after.isdigit():
      return max(1, int(retry_after))
    if retry_after:
      try:
        data = parsedate_to_datetime(retry_after)
        return max(1, (data - datetime.now(timezone.utc)).total_seconds())
      except (TypeError, ValueError, OverflowError):
        pass
    return 2 ** (tentativa + 1) + random.uniform(0, 1)
  
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
