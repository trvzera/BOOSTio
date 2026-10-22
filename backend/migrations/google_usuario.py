from sqlalchemy import inspect, text

from models import db


def migrar_google_usuario():
    with db.engine.begin() as conexao:
        colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("usuario")}
        if "google_sub" not in colunas:
            conexao.execute(text('ALTER TABLE usuario ADD COLUMN google_sub VARCHAR(255)'))
        conexao.execute(text(
            'CREATE UNIQUE INDEX IF NOT EXISTS ix_usuario_google_sub ON usuario (google_sub)'
        ))
