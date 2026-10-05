import time
from .consultar_api_service import ConsultarApiMercadoLivreService


class MercadoLivreScapringService:
  def executar(self, termos_busca: list[str] | None = None, produto_id: str | None = None):
    if not termos_busca:
      if not produto_id:
        raise ValueError("Informe os termos de busca ou o ID do produto de catálogo")
      return [ConsultarApiMercadoLivreService().executar(f"/products/{produto_id}")]

    dados_totais = []

    
    for indice, termo in enumerate(termos_busca):
      if indice:
        time.sleep(1)
      params = {
          "status": "active",
          "site_id": "MLB",
          "q": termo.strip(),
      }

      dados = ConsultarApiMercadoLivreService().executar("/products/search", params)

      produtos = dados.get("results", [])
      if not produtos:
        print("A resposta da API esta vazia")
        continue

      dados_totais.append(produtos[0])
    
    return dados_totais
