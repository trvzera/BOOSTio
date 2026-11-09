"""Acrescenta a ficha revisada sem apagar vínculos ou ofertas existentes."""
from sqlalchemy import inspect, text
from models import db, VinculoMercadoLivre


def preparar_vinculos_revisados():
    if db.engine.dialect.name not in ('sqlite','mysql'):
        raise ValueError('Banco não suportado')
    inspetor=inspect(db.engine)
    if not inspetor.has_table('vinculo_mercado_livre'):
        from migrations.ofertas_mercado_livre import preparar_ofertas_mercado_livre
        return preparar_ofertas_mercado_livre()
    colunas={c['name'] for c in inspetor.get_columns('vinculo_mercado_livre')}
    esperadas={c.name for c in VinculoMercadoLivre.__table__.columns}
    if colunas not in (esperadas, esperadas - {'especificacoes_revisadas'}):
        raise ValueError('Tabela de vínculos incompatível; revise o schema antes de migrar')
    if 'especificacoes_revisadas' in colunas:
        return {'alteracoes':[]}
    ddl='ALTER TABLE `vinculo_mercado_livre` ADD COLUMN `especificacoes_revisadas` JSON NULL'
    with db.engine.begin() as conn:conn.execute(text(ddl))
    return {'alteracoes':[ddl]}
