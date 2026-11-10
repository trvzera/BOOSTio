from utils.colunas_antigas import COLUNAS_ANTIGAS_DA_PECA
"""Permite ausência de cotação e consumo, preservando linhas, índices e FKs."""
from sqlalchemy import inspect, MetaData, Table, select
from sqlalchemy.schema import CreateTable, CreateColumn
from models import db
from models.modelos_pecas import MODELOS_PECAS
from .fichas_tecnicas import preparar_fichas_tecnicas

CAMPOS_NULOS=('consumo_energia',)


def preparar_catalogo_tecnico(*, simular=True, campos_por_tabela=None):
    dialecto=db.engine.dialect.name
    if dialecto not in ('sqlite','mysql'):raise ValueError('Banco não suportado')
    fila=preparar_fichas_tecnicas(simular=True)
    insp=inspect(db.engine);alteracoes=[];tabelas=[]
    for modelo in MODELOS_PECAS:
        nome=modelo.__tablename__
        if not insp.has_table(nome):continue
        colunas={c['name']:c for c in insp.get_columns(nome)}
        esperadas=set(modelo.__table__.columns.keys())
        if set(colunas)-COLUNAS_ANTIGAS_DA_PECA not in (esperadas,esperadas-{'ficha_montagem_validada'}):
            raise ValueError(f'Prepare o esquema anterior com catalogo-preparar: {nome}')
        campos=tuple(dict.fromkeys((*CAMPOS_NULOS, *(campos_por_tabela or {}).get(nome, ()))))
        mudar=[c for c in campos if not colunas[c]['nullable']]
        flag='ficha_montagem_validada' not in colunas
        if mudar or flag:
            tabelas.append((nome,mudar,flag))
            alteracoes.append(dict(tabela=nome,permitir_ausencia=mudar,adicionar_controle_montagem=flag))
    resultado=dict(simulacao=simular,alteracoes=alteracoes,tabelas_criadas=fila['criadas'])
    if simular:return resultado
    if dialecto=='mysql':
        # MySQL confirma DDL implicitamente; preflight integral acima e reexecução
        # repetível protegem uma execução parcialmente concluída. Backup é externo.
        with db.engine.begin() as conn:
            quote=conn.dialect.identifier_preparer.quote
            for nome,mudar,flag in tabelas:
                tabela=Table(nome,MetaData(),autoload_with=conn)
                for campo in mudar:
                    coluna=tabela.c[campo];coluna.nullable=True
                    definicao=str(CreateColumn(coluna).compile(dialect=conn.dialect))
                    conn.exec_driver_sql(f'ALTER TABLE {quote(nome)} MODIFY COLUMN {definicao}')
                if flag:conn.exec_driver_sql(f'ALTER TABLE {quote(nome)} ADD COLUMN ficha_montagem_validada BOOLEAN NULL')
        preparar_fichas_tecnicas(simular=False)
        return resultado
    with db.engine.connect() as conn:
        chaves=conn.exec_driver_sql('PRAGMA foreign_keys').scalar_one();conn.commit()
        conn.exec_driver_sql('PRAGMA foreign_keys=OFF');conn.commit()
        try:
            conn.exec_driver_sql('BEGIN IMMEDIATE')
            if conn.exec_driver_sql('PRAGMA foreign_key_check').first():
                raise ValueError('Banco já possui referências inválidas; revise antes de migrar')
            quote=conn.dialect.identifier_preparer.quote
            for nome,mudar,flag in tabelas:
                if not mudar:
                    if flag:conn.exec_driver_sql(f'ALTER TABLE {quote(nome)} ADD COLUMN ficha_montagem_validada BOOLEAN NULL')
                    continue
                extras=conn.exec_driver_sql("SELECT sql FROM sqlite_master WHERE tbl_name=? AND type IN ('index','trigger') AND sql IS NOT NULL",(nome,)).scalars().all()
                original=Table(nome,MetaData(),autoload_with=conn)
                temporaria=original.to_metadata(MetaData(),name='__tecnico_'+nome)
                for campo in mudar:temporaria.c[campo].nullable=True
                if flag:
                    from sqlalchemy import Column,Boolean
                    temporaria.append_column(Column('ficha_montagem_validada',Boolean(),nullable=True))
                conn.execute(CreateTable(temporaria))
                campos=', '.join(quote(c.name) for c in original.columns)
                conn.exec_driver_sql(f'INSERT INTO {quote(temporaria.name)} ({campos}) SELECT {campos} FROM {quote(nome)}')
                conn.exec_driver_sql(f'DROP TABLE {quote(nome)}')
                conn.exec_driver_sql(f'ALTER TABLE {quote(temporaria.name)} RENAME TO {quote(nome)}')
                for ddl in extras:conn.exec_driver_sql(ddl)
            from models import FichaTecnicaCatalogo, RevisaoFichaTecnica, ControleColeta
            for modelo in (ControleColeta,FichaTecnicaCatalogo,RevisaoFichaTecnica):modelo.__table__.create(conn,checkfirst=True)
            if conn.execute(select(ControleColeta.id).where(ControleColeta.id==1)).first() is None:
                conn.execute(ControleColeta.__table__.insert().values(id=1,versao=0))
            if conn.exec_driver_sql('PRAGMA foreign_key_check').first():raise ValueError('Referências divergentes após migração')
            conn.commit()
        except Exception:
            conn.rollback();raise
        finally:
            conn.exec_driver_sql(f'PRAGMA foreign_keys={int(chaves)}');conn.commit()
    return resultado
