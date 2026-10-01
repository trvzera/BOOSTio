import requests
import os
from dotenv import load_dotenv
from models import TokensMeli
from datetime import datetime
from services.mercadolivre_scapring_service.refresh_token_service import RefreshTokenMercadoLivreService

load_dotenv()

class MercadoLivreScapringService:
  def executar(self, termo_busca: str):

    token = TokensMeli.buscar_atual()

    if token.data_expiracao < datetime.now():
      RefreshTokenMercadoLivreService().executar(token.refresh_token)

    # URL oficial do Mercado Livre Brasil bem estruturada
    url = "https://api.mercadolibre.com/sites/MLB/items/bulk?ids=MLB48991061"
    # url = "https://api.mercadolibre.com/sites/MLB/search"
    # url = "https://api.mercadolibre.com/products/search"

    headers = {
      "Authorization": f"Bearer {os.getenv('access_token')}"
    }

    params = {
        "status": "active",
        "site_id": "MLB",
        "q": "Ryzen 7 5700G",
        "domain_id": "MLB48991061"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers
    )

    dados = response.json()
    print(dados)
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
  
