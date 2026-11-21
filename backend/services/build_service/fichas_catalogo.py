"""Fichas das peças no formato que vai para o catálogo da IA."""
from decimal import Decimal

from services.build_service.constantes_build import CAMPOS_PECAS
from services.build_service.preferencias_cores_service import PreferenciasCoresService
from services.build_service.preferencias_gabinete_service import PreferenciasGabineteService


def campos_pecas(peca):
  return campos_catalogo({**peca.to_catalogo(), "id": peca.id})


def campos_catalogo(dados):
  dados = dict(dados)
  dados.update(PreferenciasCoresService.metadados(dados))
  if dados.get("categoria") == "gabinete":
    dados.update({chave + "_referencia": valor for chave, valor in PreferenciasGabineteService.identificar(dados).items() if valor})
  return {
    campo: float(valor) if isinstance(valor, Decimal) else valor for campo in CAMPOS_PECAS
    if (valor := dados.get(campo)) is not None
  }
