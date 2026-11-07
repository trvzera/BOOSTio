import json
import sqlite3

import click
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect

from services.configuracao_service.preparar_banco_service import PrepararBancoService
from migrations.benchmarks_mysql import atualizar_benchmarks_mysql
from migrations.historico_precos import preparar_historico_precos
from migrations.tokens_integracao import preparar_tokens_integracao
from models import db, PreferenciasUso


def registrar_comandos_banco(app):
    @app.cli.command("catalogo-preparar")
    @click.option("--aplicar", is_flag=True, help="Aplica a migração aditiva. Padrão: simulação.")
    def preparar_catalogo(aplicar):
        from migrations.catalogo_automatizado import preparar_catalogo_automatizado
        try:
            click.echo(json.dumps(preparar_catalogo_automatizado(simular=not aplicar), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else "Falha ao preparar catálogo; não reinicie antes de conferir o esquema") from None

    @app.cli.command("usuarios-admin-preparar")
    @click.option("--aplicar", is_flag=True, help="Adiciona a coluna; sem esta opção apenas simula.")
    def preparar_admin(aplicar):
        """Adiciona usuario.administrador; faça backup antes em bancos existentes."""
        from migrations.administrador_usuario import preparar_administrador_usuario
        try:
            click.echo(json.dumps(preparar_administrador_usuario(simular=not aplicar), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else "Falha ao preparar o papel de administrador.") from erro

    @app.cli.command("integracoes-tokens-preparar")
    def preparar_tokens():
        """Cria somente a tabela de tokens; faça backup antes em bancos existentes."""
        try:
            click.echo(json.dumps(preparar_tokens_integracao(), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            mensagem = str(erro) if isinstance(erro, ValueError) else "Falha ao preparar tokens de integração."
            raise click.ClickException(mensagem) from None

    @app.cli.command("historico-precos-preparar")
    def preparar_historico():
        """Cria somente o histórico; faça backup antes em bancos existentes."""
        try:
            click.echo(json.dumps(preparar_historico_precos(), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else "Falha ao preparar o histórico de preços.") from erro

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
