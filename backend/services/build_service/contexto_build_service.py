from services.build_service.catalogo_geracao_service import campos_pecas
import logging

from models.build_salva import MODELOS

logger = logging.getLogger(__name__)


def obter_detalhes_proprias(proprias):
  detalhes = {}
  for tipo, nome in proprias.items():
    peca = MODELOS[tipo].buscar_por_nome(nome) if tipo in MODELOS else None
    especificacoes = campos_pecas(peca) if peca else {}
    especificacoes.pop("id", None)
    especificacoes.pop("preco", None)
    detalhes[tipo] = {"modelo_informado": nome, "especificacoes_confirmadas": especificacoes}
  return detalhes
