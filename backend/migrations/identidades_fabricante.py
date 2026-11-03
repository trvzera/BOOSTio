from sqlalchemy import inspect, text
from models import db, IdentidadeFabricante


def preparar_identidades_fabricante():
    if db.engine.dialect.name not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado')
    inspetor = inspect(db.engine)
    tabela = IdentidadeFabricante.__table__
    if inspetor.has_table(tabela.name):
        colunas = {c['name'] for c in inspetor.get_columns(tabela.name)}
        esperadas = {c.name for c in tabela.columns}
        if colunas == esperadas - {'gtin'}:
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE identidade_fabricante ADD COLUMN gtin VARCHAR(14) NULL'))
            return {'criadas': [], 'alteracoes': ['gtin']}
        if colunas != esperadas:
            raise ValueError('Tabela de identidades incompatível; revise a migração')
        return {'criadas': []}
    tabela.create(bind=db.engine, checkfirst=True)
    return {'criadas': [tabela.name]}
