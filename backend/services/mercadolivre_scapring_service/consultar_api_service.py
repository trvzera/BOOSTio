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

class ConsultarApiMercadoLivreService:
  def executar(self, caminho: str, params: dict | None = None):
    response = self._requisitar_com_tentativas(
      f"https://api.mercadolibre.com{caminho}", params
    )
    return self._tratar_resposta(response)

  def _tratar_resposta(self, response):
    if not response.ok:
      tipo_conteudo = response.headers.get("Content-Type", "não informado")
      detalhe = ""
      if response.status_code == 403:
        detalhe = "; acesso ao recurso negado pela API do Mercado Livre"
      elif response.status_code == 404:
        detalhe = "; recurso ou preço não encontrado; confira se o ID é de anúncio"
      raise requests.HTTPError(
        f"Consulta ao Mercado Livre falhou: HTTP {response.status_code}; Content-Type: {tipo_conteudo}{detalhe}",
        response=response,
      )
    try:
      dados = response.json()
    except requests.exceptions.JSONDecodeError:
      raise ValueError("O Mercado Livre retornou uma resposta sem JSON válido") from None
    if not isinstance(dados, dict):
      raise ValueError("O Mercado Livre retornou uma resposta em formato inesperado")
    return dados

  def _requisitar_com_tentativas(self, url, params):
    token_renovado = False
    for tentativa in range(3):
      token = self._obter_token_atual()
      response = requests.get(
        url, params=params,
        headers={"Authorization": f"Bearer {token.access_token}"}, timeout=15,
      )
      if response.status_code == 401 and not token_renovado:
        RefreshTokenMercadoLivreService().executar(token.refresh_token)
        token_renovado = True
        token = TokensMeli.buscar_atual()
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
