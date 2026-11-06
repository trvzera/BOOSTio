from services.build_service.constantes_build import PERIFERICOS
import logging
from decimal import Decimal, ROUND_DOWN
from math import isfinite


logger = logging.getLogger(__name__)


def dividir_orcamento(orcamento, percentual):
  total = Decimal(str(orcamento)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
  perifericos = (total * percentual / 100).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
  return total - perifericos, perifericos


def resumo_custos(build, catalogo):
  itens = []
  if not isinstance(build, dict) or not isinstance(build.get("componentes"), list):
    return {"itens": [], "pc": 0, "perifericos": 0}
  pc, perifericos = Decimal(0), Decimal(0)
  for item in build["componentes"]:
    if not isinstance(item, dict) or not isinstance(item.get("tipo"), str) or type(item.get("id")) is not int:
      continue
    quantidade = item.get("quantidade", 1)
    peca = next((p for p in catalogo.get(item["tipo"], []) if p["id"] == item["id"]), None)
    if peca is None or type(quantidade) is not int or not 1 <= quantidade <= 64:
      continue
    preco = peca.get("preco")
    if type(preco) not in (int, float, Decimal) or not isfinite(preco) or preco <= 0:
      continue
    subtotal = Decimal(str(preco)) * quantidade
    if item["tipo"] in PERIFERICOS:
      perifericos += subtotal
    else:
      pc += subtotal
    itens.append({"tipo": item["tipo"], "id": item["id"], "quantidade": quantidade, "subtotal": float(subtotal)})
  return {"itens": itens, "pc": float(pc), "perifericos": float(perifericos)}
