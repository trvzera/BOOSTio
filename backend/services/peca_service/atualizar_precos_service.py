from models import Peca

class AtualizarPrecosService:
  def executar(self,dados:dict,url:str):
    peca = Peca.buscar_por_url(url)

    peca.atualizar_preco(dados.get("preco"))

    return peca
