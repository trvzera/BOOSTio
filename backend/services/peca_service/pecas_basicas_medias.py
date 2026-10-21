import json
from datetime import datetime
from pathlib import Path

from .modelos_pecas import MODELOS_PECAS


def pecas_basicas_medias():
    caminho = Path(__file__).resolve().parents[2] / "data" / "pecas_basicas_medias.json"
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    coletado_em = datetime.fromisoformat(dados["coletado_em"]).replace(tzinfo=None)
    por_tabela = {modelo.__tablename__: modelo for modelo in MODELOS_PECAS}
    return {
        por_tabela[tabela]: [dict(item, preco_atualizado_em=coletado_em) for item in itens]
        for tabela, itens in dados["pecas"].items()
    }
