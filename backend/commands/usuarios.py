import json

import click
from sqlalchemy.exc import SQLAlchemyError

from models import Usuario
from services.usuario_service.alterar_administrador_service import AlterarAdministradorService


def registrar_comandos_usuarios(app):
    def _alterar(email, administrador):
        try:
            click.echo(json.dumps(AlterarAdministradorService().executar(email, administrador), ensure_ascii=False))
        except ValueError as erro:
            raise click.ClickException(str(erro)) from erro
        except SQLAlchemyError as erro:
            raise click.ClickException("Falha no banco; rode usuarios-admin-preparar e tente de novo") from erro

    @app.cli.command("usuario-promover-admin")
    @click.option("--email", required=True)
    def promover(email):
        """Torna a conta administradora e encerra as sessões dela (precisa entrar de novo)."""
        _alterar(email, True)

    @app.cli.command("usuario-remover-admin")
    @click.option("--email", required=True)
    def remover(email):
        """Retira o papel de administrador e encerra as sessões da conta."""
        _alterar(email, False)

    @app.cli.command("usuario-listar-admins")
    def listar():
        """Mostra quem é administrador."""
        try:
            click.echo(json.dumps([{"id": u.id, "nome": u.nome, "email": u.email}
                                   for u in Usuario.listar_administradores()], ensure_ascii=False))
        except SQLAlchemyError as erro:
            raise click.ClickException("Falha no banco; rode usuarios-admin-preparar") from erro
