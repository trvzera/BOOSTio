import json
import sqlite3

import click
from sqlalchemy.exc import SQLAlchemyError

from services.configuracao_service.preparar_banco_service import PrepararBancoService


def registrar_comandos_banco(app):
    @app.cli.command("banco-preparar")
    def preparar():
        """Cria tabelas e aplica migrações explicitamente, sem coletar preços."""
        try:
            click.echo(json.dumps(PrepararBancoService().executar(), ensure_ascii=False))
        except (ValueError, OSError, sqlite3.Error, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro)) from erro
