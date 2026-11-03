import json

import click
from sqlalchemy.exc import SQLAlchemyError

from migrations.ofertas_mercado_livre import preparar_ofertas_mercado_livre
from services.mercadolivre_service.atualizar_ofertas_service import AtualizarOfertasMercadoLivreService


def registrar_comandos_mercadolivre(app):
    @app.cli.command('mercadolivre-ofertas-preparar')
    def preparar():
        """Cria tabelas de ofertas; faça backup antes em bancos existentes."""
        try:
            click.echo(json.dumps(preparar_ofertas_mercado_livre(), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Falha ao preparar ofertas') from None

    @app.cli.command('mercadolivre-ofertas-atualizar')
    @click.option('--aplicar', is_flag=True, help='Grava vínculos comprovados, ofertas e histórico. Padrão: simulação.')
    @click.option('--categoria')
    @click.option('--peca-id', type=click.IntRange(min=1))
    @click.option('--depois-id', default=0, type=click.IntRange(min=0), help='Continua uma categoria após este ID.')
    @click.option('--limite-pecas', default=20, type=click.IntRange(1, 5000), show_default=True)
    @click.option('--ofertas-por-peca', default=5, type=click.IntRange(1, 20), show_default=True)
    @click.option('--max-requisicoes', default=100, type=click.IntRange(min=1), show_default=True)
    @click.option('--intervalo', default=1.0, type=click.FloatRange(min=0.1), show_default=True)
    def atualizar(aplicar, categoria, peca_id, depois_id, limite_pecas, ofertas_por_peca, max_requisicoes, intervalo):
        """Busca e atualiza ofertas sem criar componentes ou misturar preços da KaBuM."""
        try:
            resultado = AtualizarOfertasMercadoLivreService().executar(
                categoria=categoria, peca_id=peca_id, depois_id=depois_id, limite_pecas=limite_pecas,
                limite_ofertas=ofertas_por_peca, max_requisicoes=max_requisicoes,
                intervalo=intervalo, simular=not aplicar)
            click.echo(json.dumps(resultado, ensure_ascii=False))
            if resultado['interrompido']:
                raise click.ClickException('Execução interrompida; consulte o resumo antes de repetir')
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Banco indisponível para ofertas; execute mercadolivre-ofertas-preparar') from None

    @app.cli.command('mercadolivre-vincular')
    @click.option('--categoria', required=True)
    @click.option('--peca-id', required=True, type=click.IntRange(min=1))
    @click.option('--catalogo-id', required=True)
    @click.option('--revisado', is_flag=True, required=True,
                  help='Confirma revisão manual de modelo, variante e especificações do catálogo.')
    def vincular(categoria, peca_id, catalogo_id, revisado):
        """Registra uma associação explicitamente revisada; não cadastra ofertas."""
        try:
            click.echo(json.dumps(AtualizarOfertasMercadoLivreService().vincular_revisado(categoria, peca_id, catalogo_id), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Não foi possível registrar o vínculo') from None
