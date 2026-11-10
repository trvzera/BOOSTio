from sqlalchemy import inspect
from models import db, TokenIntegracao


def preparar_tokens_integracao():
    if db.engine.dialect.name not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado para tokens de integração')
    inspetor = inspect(db.engine)
    if inspetor.has_table(TokenIntegracao.__tablename__):
        colunas = {c['name'] for c in inspetor.get_columns(TokenIntegracao.__tablename__)}
        if colunas != {c.name for c in TokenIntegracao.__table__.columns}:
            raise ValueError('Tabela de tokens incompatível; revise a migração')
        return {'criada': False, 'mensagem': 'Tabela de tokens já preparada'}
    TokenIntegracao.__table__.create(bind=db.engine, checkfirst=True)
    return {'criada': True, 'mensagem': 'Tabela de tokens de integração preparada'}
