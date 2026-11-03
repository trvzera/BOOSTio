from sqlalchemy import inspect
from models import db, IdentidadeFabricante


def preparar_identidades_fabricante():
    if db.engine.dialect.name not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado')
    inspetor = inspect(db.engine)
    tabela = IdentidadeFabricante.__table__
    if inspetor.has_table(tabela.name):
        if {c['name'] for c in inspetor.get_columns(tabela.name)} != {c.name for c in tabela.columns}:
            raise ValueError('Tabela de identidades incompatível; revise a migração')
        return {'criadas': []}
    tabela.create(bind=db.engine, checkfirst=True)
    return {'criadas': [tabela.name]}
