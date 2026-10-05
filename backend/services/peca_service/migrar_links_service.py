from sqlalchemy import inspect, text

from models import db
from .modelos_pecas import MODELOS_PECAS


class MigrarLinksService:
    """Migração incremental do SQLite: mantém registros e transfere links antigos."""

    def executar(self):
        if db.engine.dialect.name != "sqlite":
            raise ValueError("Esta migração é específica para o SQLite do projeto")
        db.create_all()
        with db.engine.begin() as conexao:
            conexao.exec_driver_sql("BEGIN IMMEDIATE")
            for classe in MODELOS_PECAS:
                tabela = classe.__tablename__
                colunas = {c["name"] for c in inspect(conexao).get_columns(tabela)}
                for nome, tipo in {"kabum_external": "TEXT", "meli_external": "TEXT", "preco_atualizado_em": "DATETIME"}.items():
                    if nome not in colunas:
                        conexao.execute(text(f'ALTER TABLE "{tabela}" ADD COLUMN {nome} {tipo}'))
                if "link" in colunas:
                    conexao.execute(text(f'''UPDATE "{tabela}" SET kabum_external = link
                        WHERE kabum_external IS NULL AND
                        (link LIKE 'https://www.kabum.com.br/produto/%' OR link LIKE 'https://kabum.com.br/produto/%')'''))
                    conexao.execute(text(f'''UPDATE "{tabela}" SET meli_external = link
                        WHERE meli_external IS NULL AND
                        (link LIKE 'https://www.mercadolivre.com.br/%' OR link LIKE 'https://produto.mercadolivre.com.br/%')'''))
                    restantes = conexao.execute(text(f'''SELECT count(*) FROM "{tabela}"
                        WHERE link IS NOT NULL AND link != ''
                        AND kabum_external IS NULL AND meli_external IS NULL
                        AND link NOT LIKE 'https://www.kabum.com.br/busca/%' ''')).scalar()
                    if restantes:
                        raise ValueError(f"Há links não reconhecidos em {tabela}; revise antes de migrar")
                    conexao.execute(text(f'ALTER TABLE "{tabela}" DROP COLUMN link'))
            conexao.execute(text("INSERT OR IGNORE INTO controle_coleta (id, versao) VALUES (1, 0)"))
