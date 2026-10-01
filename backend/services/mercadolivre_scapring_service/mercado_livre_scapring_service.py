import requests
import os
from dotenv import load_dotenv
from models import TokensMeli
from datetime import datetime, timedelta, timezone
from services.mercadolivre_scapring_service.refresh_token_service import RefreshTokenMercadoLivreService

load_dotenv()

class MercadoLivreScapringService:
  def executar(self, termo_busca: str):

    if not isinstance(termo_busca, str) or not termo_busca.strip():
      raise ValueError("Informe um termo para buscar no Mercado Livre")

    token = TokensMeli.buscar_atual()

    if token is None:
      refresh_token_inicial = os.getenv("refresh_token")
      if not refresh_token_inicial:
        raise ValueError("Nenhum token salvo e nenhum refresh_token configurado no .env. Autorize a integração primeiro")

      # Renova o token inicial para obter a expiração real e persistir o novo par.
      RefreshTokenMercadoLivreService().executar(refresh_token_inicial)
      token = TokensMeli.buscar_atual()

    data_expiracao = token.data_expiracao
    # O SQLite pode devolver a data sem fuso, embora tenha sido salva em UTC.
    if data_expiracao.tzinfo is None:
      data_expiracao = data_expiracao.replace(tzinfo=timezone.utc)

    if data_expiracao <= datetime.now(timezone.utc) + timedelta(minutes=1):
      RefreshTokenMercadoLivreService().executar(token.refresh_token)
      token = TokensMeli.buscar_atual()

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

    try:
      dados = response.json()
    except requests.exceptions.JSONDecodeError as erro:
      raise ValueError(
        f"Mercado Livre retornou uma resposta sem JSON válido: HTTP {status}; "
        f"Content-Type: {tipo_conteudo}; tamanho: {len(response.content)} bytes"
      ) from erro

    print(dados)
    return dados
    # for produto in dados["results"]:
    #   print(
    #       produto["id"],
    #       "|",
    #       produto["domain_id"],
    #       "|",
    #       produto["name"]
    #   )


        
    # produtos = dados.get("results")
            
    # if produtos:
    #   for produto in produtos:
    #     titulo = produto.get("title")
    #     preco = produto.get("price")
    #     link = produto.get("permalink")                  
    #     print(f"Produto: {titulo}")
    #     print(f"Preço: R$ {preco}")
    #     print(f"Link: {link}")
    #     print("-" * 50)
    # else:
    #   print("Nenhum produto encontrado para este termo.")
                
    # return produtos
  
  # def _token_valido(self):
  
