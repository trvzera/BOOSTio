"""Fotos locais com proveniência de catálogo, sem alterar o banco ou inferir IDs."""
import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def referencias():
    arquivo = Path(__file__).resolve().parents[2] / "frontend/data/imagens-referencia.json"
    return json.loads(arquivo.read_text(encoding="utf-8"))


def imagem_referencia(dados):
    for codigo in (dados.get('referencia_interna'), dados.get('part_number')):
        ficha = referencias().get(codigo)
        if ficha and all(dados.get(campo) == ficha.get(campo) for campo in ('categoria', 'fabricante', 'modelo')):
            return ficha['imagem']
    return None
