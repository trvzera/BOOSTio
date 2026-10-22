import json
import time

import click
import requests

from services.peca_service.migrar_links_service import MigrarLinksService
from services.peca_service.popular_pecas_service import PopularPecasService
from services.peca_service.atualizar_precos_service import AtualizarPrecosService
from services.peca_service.salvar_peca_service import SalvarPecaService
from services.peca_service.restaurar_links_kabum_service import RestaurarLinksKabumService
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.peca_service.atualizar_imagem_peca_service import AtualizarImagemPecaService
from services.peca_service.auditar_catalogo_service import AuditarCatalogoService


def registrar_comandos_precos(app):
    @app.cli.command("catalogo-auditar")
    @click.option("--amostras", default=5, type=click.IntRange(0, 20), show_default=True)
    def auditar(amostras):
        """Valida catálogo e arquivos locais, sem alterar dados ou consultar lojas."""
        click.echo(json.dumps(AuditarCatalogoService().executar(amostras), ensure_ascii=False))

    @app.cli.command("pecas-restaurar-links")
    def restaurar_links():
        """Repõe links conhecidos da seed sem sobrescrever os links atuais."""
        click.echo(json.dumps(RestaurarLinksKabumService().executar(), ensure_ascii=False))

    @app.cli.command("precos-migrar")
    def migrar():
        MigrarLinksService().executar()
        click.echo("Migração dos links e controle de consultas concluída.")

    @app.cli.command("pecas-popular")
    @click.option("--atualizar-precos", is_flag=True, help="Consulta preços após cadastrar; por padrão, apenas cadastra.")
    @click.option("--limite", type=click.IntRange(min=1), help="Quantidade máxima de preços; omitido, percorre todas as peças elegíveis.")
    @click.option("--intervalo", default=1.0, type=click.FloatRange(min=0), show_default=True,
                  help="Segundos entre requisições à KaBuM.")
    def popular(limite, intervalo, atualizar_precos):
        resumo = PopularPecasService().executar(limite=limite, intervalo=intervalo, atualizar_precos=atualizar_precos)
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

    @app.cli.command("pecas-imagens")
    @click.option("--limite", type=click.IntRange(min=1), help="Quantidade máxima de anúncios; omitido, percorre todas as peças sem foto.")
    @click.option("--intervalo", default=0.5, type=click.FloatRange(min=0), show_default=True,
                  help="Segundos entre anúncios da KaBuM.")
    @click.option("--categoria", multiple=True, type=click.Choice([c.__tablename__ for c in MODELOS_PECAS]),
                  help="Restringe a coleta a uma ou mais categorias; omitido, percorre todas.")
    def imagens(limite, intervalo, categoria):
        """Baixa a foto principal validada dos anúncios cadastrados."""
        resumo = {"consultas": 0, "salvas": 0, "falhas": 0, "bloqueada": False}
        servico = AtualizarImagemPecaService()
        for classe in MODELOS_PECAS:
            if categoria and classe.__tablename__ not in categoria:
                continue
            for peca in classe.sem_imagem_com_link():
                if limite is not None and resumo["consultas"] >= limite:
                    break
                if resumo["consultas"] and intervalo:
                    time.sleep(intervalo)
                resumo["consultas"] += 1
                try:
                    servico.executar(peca)
                    resumo["salvas"] += 1
                except requests.HTTPError as erro:
                    resumo["falhas"] += 1
                    status = erro.response.status_code if erro.response is not None else 0
                    click.echo(f"{classe.__tablename__}:{peca.id}: HTTP {status}", err=True)
                    if status in (401, 403, 429) or status >= 500:
                        resumo["bloqueada"] = True
                        break
                except (requests.RequestException, ValueError, OSError) as erro:
                    resumo["falhas"] += 1
                    click.echo(f"{classe.__tablename__}:{peca.id}: {erro}", err=True)
                if resumo["consultas"] % 25 == 0:
                    click.echo(json.dumps(resumo, ensure_ascii=False))
            if resumo["bloqueada"] or limite is not None and resumo["consultas"] >= limite:
                break
        resumo["manifesto"] = servico.exportar_manifesto()
        click.echo(json.dumps(resumo, ensure_ascii=False))
