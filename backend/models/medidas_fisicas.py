"""Complemento técnico versionado, sem migração ou inferência pelo nome comercial.

O mesmo JSON é consumido pelo catálogo demonstrativo. Exige categoria, fabricante,
modelo E part number exatos; revisões semelhantes não herdam medidas.
"""
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def manifesto():
    caminho = Path(__file__).resolve().parents[2] / "frontend/data/medidas-fisicas.json"
    return json.loads(caminho.read_text(encoding="utf-8"))["pecas"]


def completar_medidas(dados):
    for ficha in manifesto():
        if (all(str(dados.get(campo, "")).casefold() == ficha[campo].casefold()
                for campo in ("categoria", "fabricante", "modelo"))
                and dados.get("part_number") in ficha["part_numbers"]):
            return {**dados, **deepcopy(ficha["medidas"]), "fonte_medidas": ficha["fonte"]}
    return dados
