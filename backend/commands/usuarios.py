import base64
import json
import secrets

import click
from sqlalchemy.exc import SQLAlchemyError

from models import db, Usuario, FatorAdmin
from services.usuario_service.fator_admin_service import cifra, intervalo_valido
from services.usuario_service.alterar_administrador_service import AlterarAdministradorService


def registrar_comandos_usuarios(app):
    @app.cli.command("admin-2fa-preparar")
    def preparar_fatores():
        """Cria a tabela dos autenticadores em bancos existentes."""
        FatorAdmin.__table__.create(db.engine, checkfirst=True)

    @app.cli.command("admin-2fa-configurar")
    @click.option("--email", required=True)
    def configurar_fator(email):
        """Cadastra ou substitui o autenticador no console privado do operador."""
        usuario = Usuario.buscar_por_email(email.strip().lower())
        if not usuario or not usuario.ativo or not usuario.administrador:
            raise click.ClickException("Conta administrativa ativa não encontrada.")
        try:
            criptografia = cifra()
        except ValueError as erro:
            raise click.ClickException(str(erro)) from None
        segredo = secrets.token_bytes(20)
        click.echo("Adicione a chave ao autenticador como código baseado em tempo:")
        click.echo(base64.b32encode(segredo).decode("ascii"))
        codigo = click.prompt("Código de seis dígitos", type=str, hide_input=True)
        intervalo = intervalo_valido(segredo, codigo)
        if intervalo is None:
            raise click.ClickException("Código inválido. Cadastro cancelado.")
        db.session.merge(FatorAdmin(usuario_id=usuario.id, segredo_cifrado=criptografia.encrypt(segredo),
                                   ultimo_intervalo=intervalo, sessao_hash=None))
        usuario.versao_sessao = Usuario.versao_sessao + 1
        db.session.commit()
        click.echo("Autenticador cadastrado. Use o próximo código para entrar.")

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
