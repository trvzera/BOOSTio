"""Alarga vinculo_mercado_livre.criterio (VARCHAR(20) -> VARCHAR(100)); repetível e sem perda de dados."""
from sqlalchemy import inspect, text
from models import db

TAMANHO = 100


def preparar_vinculos_criterio(*, simular=False):
    dialecto = db.engine.dialect.name
    if dialecto not in ('sqlite', 'mysql'):
        raise ValueError('Banco não suportado')
    inspetor = inspect(db.engine)
    if not inspetor.has_table('vinculo_mercado_livre'):
        raise ValueError('Prepare as ofertas do Mercado Livre antes (mercadolivre-vinculos-preparar)')
    coluna = next((c for c in inspetor.get_columns('vinculo_mercado_livre') if c['name'] == 'criterio'), None)
    if coluna is None:
        raise ValueError('Tabela de vínculos incompatível; revise o schema antes de migrar')
    atual = getattr(coluna['type'], 'length', None)
    if dialecto == 'sqlite' or (atual is not None and atual >= TAMANHO):
        return {'simulacao': simular, 'alteracoes': []}
    ddl = f'ALTER TABLE `vinculo_mercado_livre` MODIFY COLUMN `criterio` VARCHAR({TAMANHO}) NOT NULL'
    if not simular:
        with db.engine.begin() as conn:
            conn.execute(text(ddl))
    return {'simulacao': simular, 'alteracoes': [ddl]}
