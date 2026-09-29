from apify_client import ApifyClient
from dotenv import load_dotenv
import os


load_dotenv()

client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

class KabumScrapingService:
    def __init__(self):
        self.client = client

    def executar(self):
      run_input = {
        "termos": ["mouse gamer"],
        "categoria": None,
        "maxItems": None,
        "proxyConfiguration": None,
      }   

      #Chama a API do Apify para executar o ator "latinamericadata/kabum-brasil" com os parâmetros fornecidos.
      run = self.client.actor("latinamericadata/kabum-brasil").call(run_input=run_input)  

      itens_totais = []

      #Itera sobre os itens retornados pelo ator e imprime cada item.
      for item in self.client.dataset(run.default_dataset_id).iterate_items():
        print(item)
        itens_totais.append(item)

      return itens_totais
