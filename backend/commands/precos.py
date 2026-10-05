import json

import click

from models import db
from services.peca_service.migrar_links_service import MigrarLinksService
from services.peca_service.popular_pecas_service import PopularPecasService
from services.peca_service.atualizar_precos_service import AtualizarPrecosService
from services.peca_service.salvar_peca_service import SalvarPecaService
from services.peca_service.modelos_pecas import MODELOS_PECAS


def registrar_comandos_precos(app):
    @app.cli.command("precos-migrar")
    def migrar():
        MigrarLinksService().executar()
        click.echo("Migração dos links e controle de consultas concluída.")

    @app.cli.command("pecas-popular")
    def popular():
        PopularPecasService().executar()

    @app.cli.command("peca-links")
    @click.argument("tabela", type=click.Choice([c.__tablename__ for c in MODELOS_PECAS]))
    @click.argument("peca_id", type=int)
    @click.option("--meli", default=None, help="URL do anúncio. String vazia remove o vínculo.")
    @click.option("--kabum", default=None, help="URL KaBuM; coleta desativada por enquanto.")
    def links(tabela, peca_id, meli, kabum):
        classe = next(c for c in MODELOS_PECAS if c.__tablename__ == tabela)
        dados = {f"{loja}_external": url for loja, url in (("meli", meli), ("kabum", kabum)) if url is not None}
        if not dados:
            raise click.UsageError("Informe --meli ou --kabum")
        SalvarPecaService().executar(classe, dados, peca_id)
        click.echo("Links atualizados.")

    @app.cli.command("precos-atualizar")
    @click.option("--limite", default=140, type=click.IntRange(1, 140))
    def atualizar(limite):
        click.echo(json.dumps(AtualizarPrecosService().executar(limite), ensure_ascii=False))
