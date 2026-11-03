import json
import signal
from threading import Event
import click
from sqlalchemy.exc import SQLAlchemyError
from models import EstadoCatalogo
from repositories.controle_catalogo_repository import RepositorioControleCatalogo
from services.mercadolivre_service.processar_catalogo_service import ProcessarCatalogoService


def registrar_comandos_catalogo(app):
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
            trabalhos=ProcessarCatalogoService.ler_plano(plano)
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
            trabalho=next((t for t in ProcessarCatalogoService.ler_plano(plano) if t['nome']==nome),None)
            if trabalho is None:raise ValueError('Nome ausente no plano')
            repo=RepositorioControleCatalogo()
            with repo.bloquear() as adquirido:
                if not adquirido:raise ValueError('Worker em execução; tente depois')
                repo.verificar_esquema([trabalho]);EstadoCatalogo.reiniciar(trabalho)
            click.echo(json.dumps({'reiniciado':nome}))
        except (ValueError,OSError,SQLAlchemyError):raise click.ClickException('Não foi possível reiniciar o trabalho; confira plano e trava') from None
