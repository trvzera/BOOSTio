"""Fotos locais com proveniência de catálogo, sem alterar o banco ou inferir IDs."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def referencias():
    arquivo = Path(__file__).resolve().parents[2] / "frontend/data/imagens-referencia.json"
    return json.loads(arquivo.read_text(encoding="utf-8"))


def imagem_referencia(dados):
    ficha = referencias().get(dados.get("part_number"))
    if not ficha or any(dados.get(campo) != ficha.get(campo) for campo in ("categoria", "fabricante", "modelo")):
        return None
    return ficha["imagem"]
