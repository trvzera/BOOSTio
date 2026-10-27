import json
import sqlite3

import click
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect

from services.configuracao_service.preparar_banco_service import PrepararBancoService
from models import db, PreferenciasUso


def registrar_comandos_banco(app):
    @app.cli.command("preferencias-preparar")
    def preparar_preferencias():
        """Cria apenas a tabela de preferências; preserva tabelas e contas existentes."""
        try:
            if not inspect(db.engine).has_table("usuario"):
                raise click.ClickException("Inicialize o banco antes de preparar as preferências.")
            PreferenciasUso.__table__.create(bind=db.engine, checkfirst=True)
            click.echo("Tabela de preferências pronta. Nenhuma conta foi alterada.")
        except SQLAlchemyError as erro:
            raise click.ClickException("Não foi possível preparar as preferências.") from erro

    @app.cli.command("banco-preparar")
    def preparar():
        """Cria tabelas e aplica migrações explicitamente, sem coletar preços."""
        try:
            click.echo(json.dumps(PrepararBancoService().executar(), ensure_ascii=False))
        except (ValueError, OSError, sqlite3.Error, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro)) from erro
