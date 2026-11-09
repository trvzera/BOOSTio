"""Migração aditiva e repetível; preserva anúncios e todas as tabelas anteriores."""
from sqlalchemy import inspect
from models import db
from models.tarefa_marketplace import TarefaMarketplace, LimiteMarketplace


def preparar_fila_marketplaces(*, simular=True):
    if db.engine.dialect.name not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado para a fila')
    novas = []
    inspetor = inspect(db.engine)
    for modelo in (TarefaMarketplace, LimiteMarketplace):
        if inspetor.has_table(modelo.__tablename__):
            colunas = {c['name'] for c in inspetor.get_columns(modelo.__tablename__)}
            if colunas != set(modelo.__table__.columns.keys()):
                raise ValueError('Esquema da fila incompatível; revise a migração')
        else:
            novas.append(modelo.__tablename__)
            if not simular:
                modelo.__table__.create(db.engine, checkfirst=True)
    return {'simulacao': simular, 'tabelas': novas}
