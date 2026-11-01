import json
import sqlite3

import click
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect

from services.configuracao_service.preparar_banco_service import PrepararBancoService
from migrations.benchmarks_mysql import atualizar_benchmarks_mysql
from models import db, PreferenciasUso


def registrar_comandos_banco(app):
    @app.cli.command("banco-atualizar-mysql")
    @click.option("--aplicar", is_flag=True, help="Aplica o plano; exige backup e escritores parados.")
    def atualizar_mysql(aplicar):
        """Simula por padrão a migração aditiva de benchmarks para MySQL existente."""
        try:
            click.echo(json.dumps(atualizar_benchmarks_mysql(simular=not aplicar), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException("Atualização interrompida. " + (str(erro) if isinstance(erro, ValueError) else "Falha no MySQL; confira o esquema e o backup antes de repetir.")) from erro

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
