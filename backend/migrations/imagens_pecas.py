from sqlalchemy import inspect, text

from models import db
from services.peca_service.modelos_pecas import MODELOS_PECAS


def migrar_imagens_pecas():
    if db.engine.dialect.name != "sqlite":
        raise ValueError("Esta migração é específica para o SQLite do projeto")
    with db.engine.begin() as conexao:
        for classe in MODELOS_PECAS:
            tabela = classe.__tablename__
            colunas = {coluna["name"] for coluna in inspect(conexao).get_columns(tabela)}
            if "imagem_url" not in colunas:
                conexao.execute(text(f'ALTER TABLE "{tabela}" ADD COLUMN imagem_url TEXT'))
