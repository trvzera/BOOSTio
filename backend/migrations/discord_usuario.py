from sqlalchemy import inspect, text

from models import Usuario, db


def preparar_discord_usuario():
    with db.engine.begin() as conexao:
        colunas = {coluna["name"] for coluna in inspect(conexao).get_columns("usuario")}
        criadas = []
        for nome, tipo in (("discord_id", "VARCHAR(20)"), ("discord_username", "VARCHAR(80)")):
            if nome not in colunas:
                conexao.execute(text(f"ALTER TABLE usuario ADD COLUMN {nome} {tipo}"))
                criadas.append(nome)
        indice = next(indice for indice in Usuario.__table__.indexes if indice.name == "ix_usuario_discord_id")
        indice.create(conexao, checkfirst=True)
        return criadas
