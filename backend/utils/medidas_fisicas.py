import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import re
from urllib.parse import urlsplit


@lru_cache(maxsize=1)
def manifesto():
    caminho = Path(__file__).resolve().parents[2] / "frontend/data/medidas-fisicas.json"
    return json.loads(caminho.read_text(encoding="utf-8"))["pecas"]


def produto_kabum(link):
    if (not isinstance(link, str) or re.search(r"[\s\\]", link)
            or not re.match(r"https://(?:www\.)?kabum\.com\.br(?::443)?/", link, re.I)):
        return None
    try:
        url = urlsplit(link)
        if (url.scheme != "https" or url.hostname not in ("kabum.com.br", "www.kabum.com.br")
                or url.username is not None or url.password is not None or url.port not in (None, 443)):
            return None
        produto = re.fullmatch(r"/produto/([1-9][0-9]*)(?:/[a-zA-Z0-9_-]+)?/?", url.path)
        return produto[1] if produto else None
    except ValueError:
        return None


def corresponde(dados, ficha):
    if dados.get("categoria") != ficha["categoria"]:
        return False
    nomes = lambda referencia: all(
        str(dados.get(campo, "")).casefold() == referencia[campo].casefold()
        for campo in ("fabricante", "modelo"))
    referencias = {dados.get('part_number'), dados.get('referencia_interna')} - {None}
    if nomes(ficha) and referencias.intersection(ficha["part_numbers"]):
        return True
    return any(nomes(alias) and alias["part_number"] in referencias
               and produto_kabum(dados.get("link")) == alias["produto_kabum"]
               for alias in ficha.get("aliases_catalogo", []))


def completar_medidas(dados):
    for ficha in manifesto():
        if corresponde(dados, ficha):
            origem = {"fonte_medidas": ficha["fonte"]}
            if ficha.get("verificado_em"):
                origem.update(modelo_ficha_tecnica=ficha["modelo"],
                              ficha_tecnica_verificada_em=ficha["verificado_em"])
            return {**dados, **deepcopy(ficha["medidas"]), **origem}
    return dados
