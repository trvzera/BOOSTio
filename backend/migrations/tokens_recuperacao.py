from sqlalchemy import inspect, text

from models import db


def migrar_tokens_recuperacao():
    with db.engine.begin() as conexao:
        colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("token_recuperacao")}
        legado = "email_destino" not in colunas or "versao_sessao" not in colunas
        if "email_destino" not in colunas:
            conexao.execute(text("ALTER TABLE token_recuperacao ADD COLUMN email_destino VARCHAR(150)"))
        if "versao_sessao" not in colunas:
            conexao.execute(text("ALTER TABLE token_recuperacao ADD COLUMN versao_sessao INTEGER"))
        if legado:
            conexao.execute(text("UPDATE token_recuperacao SET usado = TRUE"))
        conexao.execute(text(
            "CREATE INDEX IF NOT EXISTS ix_token_recuperacao_token_hash ON token_recuperacao (token_hash)"
        ))
