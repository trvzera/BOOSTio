import json

import click
from sqlalchemy.exc import SQLAlchemyError

from migrations.ofertas_mercado_livre import preparar_ofertas_mercado_livre
from services.mercadolivre_service.atualizar_ofertas_service import AtualizarOfertasMercadoLivreService


def registrar_comandos_mercadolivre(app):
    @app.cli.command('mercadolivre-importar-pendencias')
    @click.option('--limite', default=20, type=click.IntRange(1, 200))
    @click.option('--depois-id', default=0, type=click.IntRange(min=0))
    @click.option('--max-requisicoes', default=50, type=click.IntRange(min=1))
    @click.option('--intervalo', default=1.0, type=click.FloatRange(min=0.1))
    @click.option('--permitir-novos', is_flag=True, help='Permite criar componentes com identidade e ficha completas.')
    @click.option('--aplicar', is_flag=True)
    def importar_pendencias(max_requisicoes, intervalo, aplicar, **opcoes):
        from services.mercadolivre_service.importar_produto_service import ImportarProdutoService
        from services.mercadolivre_service.controle_requisicoes_service import ControleRequisicoesService
        try:
            resumo=ImportarProdutoService(controle=ControleRequisicoesService(max_requisicoes,intervalo)).executar_lote(simular=not aplicar,**opcoes)
            click.echo(json.dumps(resumo,ensure_ascii=False))
            if resumo['falhas']:raise click.ClickException('Há importações não confirmadas; consulte o resumo')
        except (ValueError,SQLAlchemyError):
            raise click.ClickException('Falha ao importar pendências; confira o resumo e a preparação do banco') from None

    @app.cli.command('mercadolivre-enriquecer')
    @click.option('--limite', default=20, type=click.IntRange(1, 200))
    @click.option('--depois-id', default=0, type=click.IntRange(min=0))
    @click.option('--max-requisicoes', default=30, type=click.IntRange(min=1))
    @click.option('--intervalo', default=1.0, type=click.FloatRange(min=0.1))
    @click.option('--benchmark-cpu', type=click.Path(exists=True,dir_okay=False))
    @click.option('--benchmark-gpu', type=click.Path(exists=True,dir_okay=False))
    @click.option('--aplicar', is_flag=True)
    def enriquecer(benchmark_cpu, benchmark_gpu, aplicar, **opcoes):
        from services.mercadolivre_service.enriquecer_produto_service import EnriquecerProdutoService
        from services.mercadolivre_service.enriquecer_pendencias_service import EnriquecerPendenciasService
        from services.mercadolivre_service.consultar_benchmark_catalogo_service import ConsultarBenchmarkCatalogoService
        try:
            service=EnriquecerPendenciasService(enriquecedor=EnriquecerProdutoService(ConsultarBenchmarkCatalogoService(benchmark_cpu,benchmark_gpu)))
            resumo=service.executar(simular=not aplicar,**opcoes)
            click.echo(json.dumps(resumo,ensure_ascii=False))
            if resumo['interrompido'] or resumo['falhas']:raise click.ClickException('Há falhas de enriquecimento; consulte o resumo')
        except (ValueError,OSError,SQLAlchemyError):
            raise click.ClickException('Falha ao enriquecer; confira esquema, fontes e snapshots') from None

    @app.cli.command('mercadolivre-classificar')
    @click.option('--limite', default=20, type=click.IntRange(1, 200))
    @click.option('--depois-id', default=0, type=click.IntRange(min=0))
    @click.option('--aplicar', is_flag=True)
    def classificar(limite, depois_id, aplicar):
        from services.mercadolivre_service.classificar_pendencias_service import ClassificarPendenciasService
        try:
            resumo = ClassificarPendenciasService().executar(limite=limite, depois_id=depois_id, simular=not aplicar)
            click.echo(json.dumps(resumo, ensure_ascii=False))
            if resumo['falhas']:
                raise click.ClickException('Há falhas de classificação; consulte o resumo')
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Prepare o banco antes de classificar') from None

    @app.cli.command('mercadolivre-descobrir')
    @click.option('--categoria', required=True)
    @click.option('--consulta', required=True, help='Palavras-chave; exemplo: memória DDR4 Kingston.')
    @click.option('--origem', type=click.Choice(['catalogo', 'anuncios']), default='catalogo', show_default=True)
    @click.option('--categoria-ml', default=None, help='ID MLB oficial, somente para origem anuncios.')
    @click.option('--dominio', default=None, help='Domínio MLB oficial, somente para origem catalogo.')
    @click.option('--max-paginas', default=5, type=click.IntRange(1, 100), show_default=True)
    @click.option('--max-anuncios', default=100, type=click.IntRange(1, 5000), show_default=True)
    @click.option('--max-requisicoes', default=30, type=click.IntRange(min=1), show_default=True)
    @click.option('--intervalo', default=1.0, type=click.FloatRange(min=0.1), show_default=True)
    @click.option('--aplicar', is_flag=True, help='Grava somente a fila de pendências e a auditoria. Padrão: simulação.')
    def descobrir(aplicar, **parametros):
        from services.mercadolivre_service.descobrir_produtos_service import DescobrirProdutosService
        try:
            resumo = DescobrirProdutosService().executar(simular=not aplicar, **parametros)
            click.echo(json.dumps(resumo, ensure_ascii=False))
            if resumo['interrompido']:
                raise click.ClickException('Descoberta interrompida; consulte o resumo antes de repetir')
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Prepare o esquema com catalogo-preparar antes da descoberta') from None

    @app.cli.command('mercadolivre-autorizacao-preparar')
    def preparar_autorizacao():
        from migrations.autorizacao_mercado_livre import preparar_autorizacao_mercado_livre
        try:
            click.echo(json.dumps(preparar_autorizacao_mercado_livre(), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Falha ao preparar autorização') from None

    @app.cli.command('mercadolivre-conectar')
    def conectar():
        """Gera link administrativo de uso único, válido por dez minutos. Não compartilhe."""
        from services.mercadolivre_service.autorizar_conta_service import AutorizarContaMercadoLivreService
        try:
            click.echo(AutorizarContaMercadoLivreService().convite())
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Prepare a tabela com mercadolivre-autorizacao-preparar') from None

    @app.cli.command('mercadolivre-identidades-preparar')
    def preparar_identidades():
        """Migração aditiva do cadastro de MPNs revisados."""
        from migrations.identidades_fabricante import preparar_identidades_fabricante
        try:
            click.echo(json.dumps(preparar_identidades_fabricante(), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Falha ao preparar identidades') from None

    @app.cli.command('mercadolivre-identidades-importar')
    @click.option('--arquivo', type=click.Path(exists=True, dir_okay=False),
                  default='data/identidades-fabricante-revisadas.json', show_default=True)
    @click.option('--aplicar', is_flag=True, help='Grava MPNs do manifesto revisado. Padrão: simulação.')
    def importar_identidades(arquivo, aplicar):
        """Preenche códigos reais sem trocar referências internas ou criar peças."""
        from services.mercadolivre_service.importar_identidades_service import ImportarIdentidadesService
        try:
            click.echo(json.dumps(ImportarIdentidadesService().executar(arquivo, simular=not aplicar), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Falha no banco; execute mercadolivre-identidades-preparar') from None

    @app.cli.command('mercadolivre-validar')
    def validar():
        """Confere configuração, schema e tokens sem rede ou gravação."""
        from services.mercadolivre_service.validar_integracao_service import ValidarIntegracaoMercadoLivreService
        try:
            click.echo(json.dumps(ValidarIntegracaoMercadoLivreService().executar(), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Banco indisponível para validar Mercado Livre') from None

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
