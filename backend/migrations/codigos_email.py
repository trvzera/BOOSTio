from sqlalchemy import inspect, text

from models import db


def migrar_codigos_email():
    if db.engine.dialect.name != "sqlite":
        raise ValueError("Esta migração é específica para o SQLite do projeto")
    with db.engine.begin() as conexao:
        colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("codigo")}
        if "tentativas" not in colunas:
            conexao.execute(text('ALTER TABLE "codigo" ADD COLUMN "tentativas" INTEGER NOT NULL DEFAULT 0'))
        if "email_destino" not in colunas:
            conexao.execute(text('ALTER TABLE "codigo" ADD COLUMN "email_destino" VARCHAR(150)'))
            # Não é possível saber qual endereço recebeu códigos emitidos antes desta migração.
            conexao.execute(text('UPDATE "codigo" SET "usado" = 1'))
