from sqlalchemy import inspect, text

from models import db


def migrar_rede_build():
    if db.engine.dialect.name != "sqlite":
        raise ValueError("Esta migração é específica para o SQLite do projeto")
    with db.engine.begin() as conexao:
        colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("build")}
        for nome in ("adaptador_wifi_id", "cabo_rede_id"):
            if nome not in colunas:
                conexao.execute(text(f'ALTER TABLE "build" ADD COLUMN "{nome}" INTEGER'))
