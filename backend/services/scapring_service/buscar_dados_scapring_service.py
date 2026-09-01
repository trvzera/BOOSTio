import requests
from bs4 import BeautifulSoup

class BuscarDadosScapringService:
  def executar(self,url):
    headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    lojas = {
      "terabyteshop": self._pega_dados_terabyte,
      "kabum": self._pega_preco_kabum,
    }
    
    dados = False

    for loja in lojas:
      if loja in url:
        dados = lojas[loja](headers,url)
        break

    if not dados:
      raise ValueError("Url inválida")

    
    return dados

  def _pega_preco_kabum(self,headers,url:str) -> str:

    response = requests.get(url, headers=headers)
    site = BeautifulSoup(response.text, "html.parser")

    
    preco = site.find("h4").text
    preco = preco.replace("R$","")


    preco = site.find("h4").text
    return preco
  
  
  def _pega_dados_terabyte(self,headers, url: str) -> dict:
    response = requests.get(url, headers=headers)
    site = BeautifulSoup(response.text, "html.parser")

    dados = {
      "preco_a_vista": self._tratar_preco(self._extrair_texto_por_id(site, "valVista")),
      "partnumber": self._tratar_partnumber(self._extrair_texto_por_id(site, "partnumber")),
    }

    return dados


  @staticmethod
  def _tratar_preco(texto: str | None) -> float | None:
    if texto is None:
        return None
    texto_limpo = texto.replace("R$", "").replace(".", "").replace(",", ".").strip()
    return float(texto_limpo)


  @staticmethod
  def _tratar_partnumber(texto: str | None) -> str | None:
      if texto is None:
          return None
      return texto.replace("COD: ", "").strip()


  @staticmethod
  def _extrair_texto_por_id(site: BeautifulSoup, id_elemento: str) -> str | None:
    elemento = site.find(id=id_elemento)
    return elemento.get_text(strip=True) if elemento else None



