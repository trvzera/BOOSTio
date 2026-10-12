import json

import click

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
    @click.option("--limite", type=click.IntRange(min=1), help="Quantidade máxima de preços; omitido, percorre todas as peças elegíveis.")
    @click.option("--intervalo", default=1.0, type=click.FloatRange(min=0), show_default=True,
                  help="Segundos entre requisições à KaBuM.")
    def popular(limite, intervalo):
        resumo = PopularPecasService().executar(limite=limite, intervalo=intervalo)
        click.echo(json.dumps(resumo, ensure_ascii=False))

    @app.cli.command("peca-links")
    @click.argument("tabela", type=click.Choice([c.__tablename__ for c in MODELOS_PECAS]))
    @click.argument("peca_id", type=int)
    @click.option("--kabum", required=True, help="URL do produto; string vazia remove o vínculo.")
    def links(tabela, peca_id, kabum):
        classe = next(c for c in MODELOS_PECAS if c.__tablename__ == tabela)
        SalvarPecaService().executar(classe, {"kabum_external": kabum}, peca_id)
        click.echo("Links atualizados.")

    @app.cli.command("precos-atualizar")
    @click.option("--limite", type=click.IntRange(min=1), help="Quantidade máxima; omitido, percorre todas as peças elegíveis.")
    @click.option("--intervalo", default=1.0, type=click.FloatRange(min=0), show_default=True,
                  help="Segundos entre requisições à KaBuM.")
    def atualizar(limite, intervalo):
        click.echo(json.dumps(AtualizarPrecosService().executar(limite, intervalo), ensure_ascii=False))
