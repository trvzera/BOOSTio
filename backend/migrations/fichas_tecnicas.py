"""Fila técnica aditiva, sem alterar peças, usuários ou builds."""
from sqlalchemy import inspect
from models import db, FichaTecnicaCatalogo, RevisaoFichaTecnica


def preparar_fichas_tecnicas(*, simular=True):
    if db.engine.dialect.name not in ('sqlite','mysql'):raise ValueError('Banco não suportado')
    insp=inspect(db.engine);tabelas=(FichaTecnicaCatalogo,RevisaoFichaTecnica)
    for modelo in tabelas:
        if insp.has_table(modelo.__tablename__) and {c['name'] for c in insp.get_columns(modelo.__tablename__)}!=set(modelo.__table__.columns.keys()):
            raise ValueError('Esquema de fichas técnicas incompatível')
    faltantes=[m for m in tabelas if not insp.has_table(m.__tablename__)]
    if not simular:
        with db.engine.begin() as conn:
            for modelo in faltantes:modelo.__table__.create(conn)
    return dict(simulacao=simular,criadas=[m.__tablename__ for m in faltantes])
