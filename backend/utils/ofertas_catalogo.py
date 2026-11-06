from math import isfinite
import re
from urllib.parse import urlsplit


def ofertas_catalogo(dados):
  """Expõe a última cotação coletada, nunca o preço inicial da seed como oferta."""
  link, preco = dados.get("link"), dados.get("preco")
  if not isinstance(link, str) or not dados.get("preco_atualizado_em"):
    return []
  if type(preco) not in (int, float) or not isfinite(preco) or preco <= 0:
    return []
  try:
    partes = urlsplit(link)
    if (partes.scheme != "https" or partes.hostname not in {"kabum.com.br", "www.kabum.com.br"}
        or partes.username or partes.password or partes.port not in (None, 443)
        or not re.match(r"^/produto/\d+(?:/|$)", partes.path)):
      return []
  except ValueError:
    return []
  return [{"loja": "kabum", "url": link, "preco": preco,
           "atualizadoEm": dados["preco_atualizado_em"], "esgotado": bool(dados.get("esgotado"))}]

