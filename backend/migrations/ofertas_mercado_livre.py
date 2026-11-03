"""Cria somente as tabelas necessárias; não coleta nem importa dados."""
from sqlalchemy import inspect
from models import db, Oferta, VinculoMercadoLivre, HistoricoOferta, ControleColeta


def preparar_ofertas_mercado_livre():
    if db.engine.dialect.name not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado para ofertas')
    inspetor = inspect(db.engine)
    if not inspetor.has_table(ControleColeta.__tablename__):
        raise ValueError('Prepare as tabelas de coleta antes das ofertas')
    tabelas = (Oferta, VinculoMercadoLivre, HistoricoOferta)
    # Validar todas antes de criar qualquer uma.
    for modelo in tabelas:
        if inspetor.has_table(modelo.__tablename__):
            colunas = {c['name'] for c in inspetor.get_columns(modelo.__tablename__)}
            if colunas != {c.name for c in modelo.__table__.columns}:
                raise ValueError('Tabela de ofertas incompatível; revise a migração')
    criadas = []
    for modelo in tabelas:
        if not inspetor.has_table(modelo.__tablename__):
            modelo.__table__.create(bind=db.engine, checkfirst=True)
            criadas.append(modelo.__tablename__)
    ControleColeta.inicializar()
    return {'criadas': criadas}
