from services.build_service.constantes_build import EXTRAS_PROPRIOS
import logging
from decimal import Decimal
from math import isfinite

from models.build_salva import MODELOS

logger = logging.getLogger(__name__)


def validar_orcamento(valor):
  if isinstance(valor, bool):
    raise ValueError("O orçamento deve ser um número positivo")
  try:
    orcamento = float(valor)
  except (TypeError, ValueError, OverflowError) as erro:
    raise ValueError("O orçamento deve ser um número positivo") from erro
  if not isfinite(orcamento) or not 0 < orcamento <= 1000000:
    raise ValueError("O orçamento deve ser um número positivo")
  if Decimal(str(orcamento)) != Decimal(str(orcamento)).quantize(Decimal("0.01")):
    raise ValueError("O orçamento deve ter no máximo duas casas decimais")
  return orcamento


def validar_rede(rede):
  if not isinstance(rede, dict) or rede.get("tipo", "indefinido") not in ("wifi", "cabo", "indefinido"):
    raise ValueError("Dados de rede inválidos")
  if rede.get("possuiAcessorio") is not None and type(rede["possuiAcessorio"]) is not bool:
    raise ValueError("Informe se já possui o acessório de rede")
  for campo, maximo in (("velocidadeMbps", 100000), ("comprimentoCaboM", 1000)):
    valor = rede.get(campo)
    if valor is not None and (type(valor) not in (int, float) or not isfinite(valor) or not 0 < valor <= maximo):
      raise ValueError("Medida de rede inválida: " + campo)


def validar_prioridade_montagem(dados):
  prioridade = dados.get("prioridade_montagem", "custo_beneficio")
  if prioridade not in ("custo_beneficio", "desempenho"):
    raise ValueError("A prioridade da montagem deve ser custo_beneficio ou desempenho")
  return prioridade


def validar_textos_pedido(dados):
  for campo, limite in (("nome", 100), ("descricao", 300), ("utilidade", 120)):
    valor = dados[campo]
    if not isinstance(valor, str) or not valor.strip() or len(valor) > limite:
      raise ValueError(f"{campo} deve ser um texto de até {limite} caracteres")


def pecas_proprias(valor):
  if not isinstance(valor, dict) or set(valor) - (set(MODELOS) | set(EXTRAS_PROPRIOS)):
    raise ValueError("Categoria de peça própria inválida")
  if any(not isinstance(modelo, str) or not modelo.strip() or len(modelo.strip()) > 120 for modelo in valor.values()):
    raise ValueError("Informe o modelo de cada peça própria em até 120 caracteres")
  return {tipo: modelo.strip() for tipo, modelo in valor.items()}
