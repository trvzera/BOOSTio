import logging
from .planejamento_geracao import orientar_falha

logger = logging.getLogger("services.build_service.criar_build_service")

class ErroGeracaoBuild(ValueError):
  def __init__(self, motivo, orcamento=None, percentual=0, custos=None):
    mensagem, self.geracao = orientar_falha(motivo, orcamento, percentual, custos)
    super().__init__(mensagem)
    self.motivo = str(motivo)
