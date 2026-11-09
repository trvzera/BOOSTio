from services.catalogo_service.ler_plano_catalogo_service import ler_plano
import json
import signal
from threading import Event
import click
from sqlalchemy.exc import SQLAlchemyError
from models import EstadoCatalogo
from repositories.controle_catalogo_repository import RepositorioControleCatalogo
from services.mercadolivre_service.processar_catalogo_service import ProcessarCatalogoService


def registrar_comandos_catalogo(app):
    @app.cli.command('catalogo-aprovar-lote')
    @click.option('--categoria')
    @click.option('--limite', type=click.IntRange(1), default=None,
                  help='Aprova no máximo N peças por categoria, sorteadas entre as aprováveis (amostra).')
    @click.option('--semente', type=int, default=None, help='Repete o mesmo sorteio.')
    @click.option('--exigir-identificador', is_flag=True, help='Só aprova quem tem part number ou código do fabricante.')
    @click.option('--reverter', is_flag=True, help='Volta para revisão as aprovadas por esta regra que ainda não têm oferta.')
    @click.option('--aplicar', is_flag=True, help='Grava; sem esta opção só simula e mostra os números.')
    def aprovar_lote(categoria, limite, semente, exigir_identificador, reverter, aplicar):
        """Aprova peças importadas que passam nas regras de identidade, ficha mínima e duplicata."""
        from services.catalogo_service.aprovar_em_lote_service import AprovarEmLoteService
        try:
            servico = AprovarEmLoteService()
            resumo = (servico.reverter(categoria=categoria, simular=not aplicar) if reverter else
                      servico.executar(categoria=categoria, limite=limite, semente=semente,
                                       exigir_identificador=exigir_identificador, simular=not aplicar))
            click.echo(json.dumps(resumo, ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Confira o banco de dados') from None

    @app.cli.command('catalogo-gpus-converter-referencias')
    @click.option('--pasta', required=True, type=click.Path(exists=True, file_okay=False))
    @click.option('--aplicar', is_flag=True)
    def converter_referencias_gpu(pasta, aplicar):
        """Revisa GPUs genéricas pela oferta original; simula por padrão."""
        from services.especificacoes_service.converter_referencias_gpu_service import ConverterReferenciasGpuService
        try:
            resumo = ConverterReferenciasGpuService().executar(pasta, simular=not aplicar)
            click.echo(json.dumps(resumo, ensure_ascii=False))
        except (ValueError, SQLAlchemyError):
            raise click.ClickException('Confira as fichas e prepare o esquema com catalogo-preparar') from None

    @app.cli.command('catalogo-fichas-originais')
    @click.option('--pasta', required=True, type=click.Path(exists=True, file_okay=False))
    @click.option('--categoria')
    @click.option('--aplicar', is_flag=True)
    def fichas_originais(pasta, categoria, aplicar):
        """Confere fichas locais contra a oferta original. Simula por padrão."""
        from services.especificacoes_service.preencher_fichas_originais_service import PreencherFichasOriginaisService
        try:
            resumo = PreencherFichasOriginaisService().executar(pasta, categoria=categoria, simular=not aplicar)
            click.echo(json.dumps(resumo, ensure_ascii=False))
            if resumo['falhas']:
                raise click.ClickException('Lote contém falhas; confira o resumo antes de repetir')
        except (ValueError, SQLAlchemyError):
            raise click.ClickException('Confira a pasta e prepare o esquema com catalogo-preparar') from None

    @app.cli.command('catalogo-planejar-pecas')
    @click.option('--categoria', required=True)
    @click.option('--limite', default=100, type=click.IntRange(1, 500))
    @click.option('--depois-id', default=0, type=click.IntRange(min=0))
    @click.option('--resultados', default=10, type=click.IntRange(1, 100))
    def planejar_pecas(categoria, limite, depois_id, resultados):
        """Gera pesquisas específicas por peça, sem chamadas externas."""
        from services.catalogo_service.planejar_descoberta_service import PlanejarDescobertaService
        try:
            click.echo(json.dumps(PlanejarDescobertaService().por_peca(categoria=categoria,
                limite=limite, depois_id=depois_id, resultados=resultados), ensure_ascii=False, indent=2))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Confira o esquema do catálogo') from None

    @app.cli.command('catalogo-especificacoes-preencher')
    @click.option('--limite', default=100, type=click.IntRange(1, 200))
    @click.option('--depois-id', default=0, type=click.IntRange(min=0))
    @click.option('--categoria')
    @click.option('--aplicar', is_flag=True)
    def preencher_especificacoes(limite, depois_id, categoria, aplicar):
        """Usa fichas já coletadas. Não cria peças, ofertas nem faz chamadas externas."""
        from services.catalogo_service.preencher_especificacoes_service import PreencherEspecificacoesService
        from services.mercadolivre_service.classificar_pendencias_service import ClassificarPendenciasService
        try:
            resumo = PreencherEspecificacoesService(ClassificarPendenciasService.normalizar).executar(
                limite=limite, depois_id=depois_id, categoria=categoria, simular=not aplicar)
            click.echo(json.dumps(resumo, ensure_ascii=False))
            if resumo['falhas']:
                raise click.ClickException('Lote contém falhas; consulte o resumo antes de continuar')
        except (ValueError, SQLAlchemyError):
            raise click.ClickException('Confira os dados e execute catalogo-preparar antes de preencher') from None

    @app.cli.command('catalogo-identificadores-separar')
    @click.option('--aplicar', is_flag=True)
    def separar_identificadores(aplicar):
        """Separa MPN, referência do catálogo e ID da loja. Simula por padrão."""
        from services.catalogo_service.separar_identificadores_service import SepararIdentificadoresService
        try:
            click.echo(json.dumps(SepararIdentificadoresService().executar(simular=not aplicar), ensure_ascii=False))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, ValueError) else 'Prepare o esquema com catalogo-preparar') from None

    @app.cli.command('catalogo-planejar')
    @click.option('--limite', default=100, type=click.IntRange(1, 100), show_default=True)
    @click.option('--marcas-por-categoria', default=5, type=click.IntRange(1, 50), show_default=True)
    @click.option('--todas-as-marcas', is_flag=True, help='Inclui todas as marcas válidas do banco.')
    def planejar(limite, marcas_por_categoria, todas_as_marcas):
        """Gera JSON de pesquisas por categoria/marca, sem chamadas externas."""
        from services.catalogo_service.planejar_descoberta_service import PlanejarDescobertaService
        try:
            click.echo(json.dumps(PlanejarDescobertaService().executar(limite=limite, marcas_por_categoria=None if todas_as_marcas else marcas_por_categoria), ensure_ascii=False, indent=2))
        except (ValueError, SQLAlchemyError) as erro:
            raise click.ClickException('Não foi possível gerar o plano; confira o catálogo e o esquema') from erro

    @app.cli.command('catalogo-worker')
    @click.option('--plano', required=True, type=click.Path(exists=True,dir_okay=False))
    @click.option('--uma-vez', is_flag=True, help='Processa uma etapa limitada e encerra.')
    @click.option('--aplicar', is_flag=True, help='Confirma fila, checkpoints e importações comprovadas.')
    @click.option('--permitir-novos', is_flag=True, envvar='CATALOGO_PERMITIR_NOVOS')
    @click.option('--sondagem', default=60, type=click.IntRange(5,60))
    def executar(plano,uma_vez,aplicar,permitir_novos,sondagem):
        if not aplicar and not uma_vez:raise click.ClickException('Use --uma-vez para simular sem avançar checkpoints')
        parada=Event();anteriores={}
        try:
            trabalhos=ler_plano(plano)
            for sig in (signal.SIGTERM,signal.SIGINT):
                anteriores[sig]=signal.getsignal(sig)
                signal.signal(sig,lambda *_:parada.set())
            service=ProcessarCatalogoService(parada=parada)
            while not parada.is_set():
                resumo=service.executar(trabalhos,simular=not aplicar,permitir_novos=permitir_novos)
                click.echo(json.dumps(resumo,ensure_ascii=False))
                if uma_vez:
                    if resumo['status']=='falha':raise click.ClickException('Etapa não concluída; consulte resumo e checkpoint')
                    break
                parada.wait(sondagem)
        except (ValueError,OSError,RuntimeError,SQLAlchemyError):
            raise click.ClickException('Worker interrompido; confira plano, esquema, acesso e trava') from None
        finally:
            for sig,anterior in anteriores.items():signal.signal(sig,anterior)

    @app.cli.command('catalogo-worker-reiniciar')
    @click.option('--plano',required=True,type=click.Path(exists=True,dir_okay=False))
    @click.option('--nome',required=True)
    def reiniciar(plano,nome):
        try:
            trabalho=next((t for t in ler_plano(plano) if t['nome']==nome),None)
            if trabalho is None:raise ValueError('Nome ausente no plano')
            repo=RepositorioControleCatalogo()
            with repo.bloquear() as adquirido:
                if not adquirido:raise ValueError('Worker em execução; tente depois')
                repo.verificar_esquema([trabalho]);EstadoCatalogo.reiniciar(trabalho)
            click.echo(json.dumps({'reiniciado':nome}))
        except (ValueError,OSError,SQLAlchemyError):raise click.ClickException('Não foi possível reiniciar o trabalho; confira plano e trava') from None
