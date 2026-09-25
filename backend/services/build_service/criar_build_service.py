from models import Build,Usuario
from utils.validacoes import validacao_campos

from llm_service.llm_service import LLMService



class CriarBuildService:
  def executar(self, usuario_id,dados):
    validacao_campos(dados, ["nome", "descricao","utilidade","orcamento"])

    usuario = Usuario.buscar_por_id(usuario_id)
    if not usuario:
      raise ValueError("Usuario não encontrado")

    # Criação do prompt para o LLM

    #Falta filtrar as pecas do db de acordo com o orçamento e utilidade, e passar para o prompt
    prompt = f"Crie uma build de PC com o nome '{dados['nome']}', descrição '{dados['descricao']}', utilidade '{dados['utilidade']}' e orçamento de {dados['orcamento']}. Forneça os detalhes da build em formato JSON."
    
    llm_service = LLMService()
    dados_finais = llm_service.executar(prompt) 

    validacao_campos(dados_finais, ["nome", "descricao", "utilidade", "orcamento", "componentes"])
    return dados_finais