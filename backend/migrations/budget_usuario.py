"""Adiciona o budget ao SQLite sem recriar tabelas nem alterar usuários existentes."""
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import click


def migrar_budget(caminho):
    caminho = Path(caminho).resolve()
    # mode=rw não cria um banco vazio se o caminho estiver incorreto.
    with closing(sqlite3.connect(caminho.as_uri() + "?mode=rw", uri=True, timeout=10)) as conexao:
        colunas = {linha[1] for linha in conexao.execute("PRAGMA table_info(usuario)")}
        if not colunas:
            raise ValueError("Tabela usuario não encontrada. Inicialize o banco antes de migrar.")
        alteracoes = {
            # Bancos anteriores ao login Google também precisam deste campo do modelo.
            "login_google": "ALTER TABLE usuario ADD COLUMN login_google BOOLEAN NOT NULL DEFAULT 0",
            "budget": "ALTER TABLE usuario ADD COLUMN budget NUMERIC(12, 2)",
            "usar_budget": "ALTER TABLE usuario ADD COLUMN usar_budget BOOLEAN NOT NULL DEFAULT 0",
        }
        pendentes = [nome for nome in alteracoes if nome not in colunas]
        if not pendentes:
            return {"colunas": [], "backup": None}

        data = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup = caminho.with_name(f"{caminho.stem}.antes-budget-{data}-{uuid4().hex[:8]}.db")
        backup.touch(mode=0o600, exist_ok=False)
        with closing(sqlite3.connect(backup)) as destino:
            conexao.backup(destino)
        # Transação explícita: ou todas as colunas são adicionadas, ou nenhuma.
        conexao.execute("BEGIN IMMEDIATE")
        try:
            for nome in pendentes:
                conexao.execute(alteracoes[nome])
            conexao.commit()
        except Exception:
            conexao.rollback()
            raise
    return {"colunas": pendentes, "backup": str(backup)}


def registrar_migracao_budget(app, db):
    @app.cli.command("migrar-budget")
    def comando():
        """Atualiza um SQLite existente, criando backup antes da alteração."""
        if db.engine.dialect.name != "sqlite" or not db.engine.url.database or db.engine.url.database == ":memory:":
            raise click.ClickException("Esta migração atende apenas bancos SQLite em arquivo.")
        try:
            resultado = migrar_budget(db.engine.url.database)
        except (ValueError, OSError, sqlite3.Error) as erro:
            raise click.ClickException(str(erro)) from erro
        if resultado["backup"]:
            click.echo(f"Backup: {resultado['backup']}")
            click.echo("Colunas adicionadas: " + ", ".join(resultado["colunas"]))
        else:
            click.echo("O banco já possui as colunas de budget. Nenhuma alteração realizada.")
