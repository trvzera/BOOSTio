from sqlalchemy import inspect
from models import db, AutorizacaoMercadoLivre


def preparar_autorizacao_mercado_livre():
    if db.engine.dialect.name not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado')
    tabela = AutorizacaoMercadoLivre.__table__
    inspetor = inspect(db.engine)
    if inspetor.has_table(tabela.name):
        if {c['name'] for c in inspetor.get_columns(tabela.name)} != {c.name for c in tabela.columns}:
            raise ValueError('Tabela de autorização incompatível')
        return {'criadas': []}
    tabela.create(bind=db.engine, checkfirst=True)
    return {'criadas': [tabela.name]}
