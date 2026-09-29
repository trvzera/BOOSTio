from apify_client import ApifyClient
from dotenv import load_dotenv
import os


load_dotenv()

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

class PichauScrapingService:
  def __init__(self):
    self.client = client

  def executar(self):
    run_input = {
      "term": None,
      "maxItems": None,
      "maxPages": None,
      "startPage": None,
      "maxRuntimeSecs": None,
      "requestTimeoutSecs": None,
      "failOnNoResults": None,
    }

    #Chama a API do Apify para executar o ator "latinamericadata/pichau-brasil" com os parâmetros fornecidos.
    run = self.client.actor("latinamericadata/pichau-brasil").call(run_input=run_input)

    itens_totais = []

    #Itera sobre os itens retornados pelo ator e imprime cada item.
    for item in self.client.dataset(run.default_dataset_id).iterate_items():
      print(item)
      itens_totais.append(item)

    return itens_totais
