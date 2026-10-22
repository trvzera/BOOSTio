from sqlalchemy import inspect, text

from models import db


def migrar_sessao_usuario():
    with db.engine.begin() as conexao:
        colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("usuario")}
        if "versao_sessao" not in colunas:
            conexao.execute(text(
                "ALTER TABLE usuario ADD COLUMN versao_sessao INTEGER NOT NULL DEFAULT 1"
            ))
