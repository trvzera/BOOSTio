import json
import time

import click
import requests
from sqlalchemy.exc import SQLAlchemyError

from services.peca_service.migrar_links_service import MigrarLinksService
from services.peca_service.popular_pecas_service import PopularPecasService
from services.peca_service.atualizar_precos_service import AtualizarPrecosService
from services.peca_service.salvar_peca_service import SalvarPecaService
from services.peca_service.restaurar_links_kabum_service import RestaurarLinksKabumService
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.peca_service.atualizar_imagem_peca_service import AtualizarImagemPecaService
from services.peca_service.auditar_catalogo_service import AuditarCatalogoService
from services.peca_service.cadastrar_complementares_service import CadastrarComplementaresService


def registrar_comandos_precos(app):
    @app.cli.command("mercadolivre-tokens-configurar")
    @click.option("--validade-segundos", default=0, type=click.IntRange(min=0),
                  help="Validade restante do access token; zero renova na próxima consulta.")
    def configurar_tokens_mercado_livre(validade_segundos):
        """Registra o par OAuth obtido em autorização, sem exibir credenciais."""
        from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService
        service = TokenMercadoLivreService()
        access = click.prompt("Access token", hide_input=True)
        refresh = click.prompt("Refresh token", hide_input=True)
        try:
            dados = {"access_token": service._credencial(access),
                     "refresh_token": service._credencial(refresh),
                     "expires_at": time.time() + validade_segundos,
                     "renovacao_pendente": False}
            with service.repository.bloquear():
                service.repository.ler()
                service.repository.salvar(dados)
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else "Falha ao registrar credenciais no banco") from None
        click.echo("Credenciais OAuth registradas com segurança.")

    @app.cli.command("mercadolivre-tokens-transferir")
    @click.option("--arquivo", required=True, type=click.Path(exists=True, dir_okay=False))
    @click.option("--remover-arquivo", is_flag=True, help="Remove o arquivo após verificar os tokens no banco.")
    def transferir_tokens_mercado_livre(arquivo, remover_arquivo):
        from services.mercadolivre_service.transferir_tokens_mercado_livre_service import TransferirTokensMercadoLivreService
        try:
            resultado = TransferirTokensMercadoLivreService().executar(arquivo, remover_arquivo=remover_arquivo)
            click.echo(json.dumps(resultado, ensure_ascii=False))
        except (ValueError, SQLAlchemyError, OSError):
            raise click.ClickException("Transferência interrompida; confira esquema, chave, identidade e arquivo. A origem não é usada automaticamente.") from None

    @app.cli.command("pecas-complementares")
    @click.option("--simular", is_flag=True, help="Lista o lote sem gravar dados nem consultar lojas.")
    def complementares(simular):
        """Adiciona apenas fans/periféricos/gabinete revisados, sem alterar preços existentes."""
        click.echo(json.dumps(CadastrarComplementaresService().executar(simular=simular), ensure_ascii=False))

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
        try:
            click.echo(json.dumps(AtualizarPrecosService().executar(limite, intervalo), ensure_ascii=False))
        except ValueError as erro:
            raise click.ClickException(str(erro)) from erro
        except SQLAlchemyError as erro:
            raise click.ClickException("Não foi possível atualizar preços no banco.") from erro

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
