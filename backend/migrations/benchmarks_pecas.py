"""Migração incremental; banco-preparar cria o backup antes de aplicá-la."""
from sqlalchemy import inspect, text
from models import db


CAMPOS = {
    "benchmark_teste": "VARCHAR(120)", "benchmark_versao": "VARCHAR(60)",
    "benchmark_nome_fonte": "VARCHAR(255)", "benchmark_fonte": "TEXT",
    "benchmark_atualizado_em": "DATETIME", "benchmark_referencia_em": "DATE",
}


def migrar_benchmarks_pecas():
    if db.engine.dialect.name != "sqlite":
        raise ValueError("Esta migração é específica para o SQLite do projeto")
    with db.engine.begin() as conexao:
        # DDL também deve ser atômico no sqlite3 (BEGIN não é implícito para ALTER).
        conexao.exec_driver_sql("BEGIN IMMEDIATE")
        for tabela, metricas in (("processador", ("multi_core", "single_thread")),
                                 ("placa_video", ("g2d", "g3d"))):
            existentes = {c["name"] for c in inspect(conexao).get_columns(tabela)}
            campos = {**CAMPOS, **{f"benchmark_{m}": "NUMERIC(14, 2)" for m in metricas}}
            for nome, tipo in campos.items():
                if nome not in existentes:
                    conexao.execute(text(f'ALTER TABLE "{tabela}" ADD COLUMN "{nome}" {tipo}'))
