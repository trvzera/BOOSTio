from sqlalchemy import inspect
from models import db, HistoricoPreco


def preparar_historico_precos():
    if db.engine.dialect.name not in ("sqlite", "mysql"):
        raise ValueError("Banco não suportado para histórico de preços")
    inspetor = inspect(db.engine)
    if not inspetor.has_table("consulta_preco"):
        raise ValueError("Prepare as tabelas de coleta antes do histórico de preços")
    if inspetor.has_table(HistoricoPreco.__tablename__):
        colunas = {c["name"] for c in inspetor.get_columns(HistoricoPreco.__tablename__)}
        if colunas != {c.name for c in HistoricoPreco.__table__.columns}:
            raise ValueError("Tabela de histórico incompatível; revise a migração")
        return {"criada": False, "mensagem": "Histórico de preços já preparado"}
    HistoricoPreco.__table__.create(bind=db.engine, checkfirst=True)
    return {"criada": True, "mensagem": "Histórico preparado para as próximas coletas"}
