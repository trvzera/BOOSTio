"""Fila administrativa durável, sem endpoint público."""
import json
import signal
from threading import Event
import click
from sqlalchemy.exc import SQLAlchemyError
from migrations.fila_marketplaces import preparar_fila_marketplaces
from repositories.fila_marketplace_repository import RepositorioFilaMarketplace
from repositories.controle_catalogo_repository import RepositorioControleCatalogo
from services.marketplace_service.controle_requisicoes_service import agora_utc
from services.marketplace_service.processar_fila_service import ProcessarFilaMarketplaceService, LOJAS
from services.marketplace_service.executores_service import executores_disponiveis
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem


def registrar_comandos_marketplaces(app):
    @app.cli.command('admin-pendencias-sugerir')
    @click.option('--limite', type=click.IntRange(1, 5000), default=20, show_default=True,
                  help='Máximo de pendências a analisar; a IA recebe 20 por requisição, com espera e nova tentativa em caso de limite.')
    @click.option('--loja', type=click.Choice(LOJAS))
    @click.option('--categoria', type=click.Choice([m.__tablename__ for m in MODELOS_PECAS]))
    @click.option('--refazer', is_flag=True, help='Analisa de novo pendências que já têm sugestão.')
    @click.option('--aplicar', is_flag=True, help='Chama a IA e grava as sugestões; padrão só conta o que analisaria.')
    @click.option('--decidir', is_flag=True, help='A IA aceita (peça indicada) ou rejeita (nenhuma serve) quando a confiança alcança o mínimo.')
    @click.option('--confianca-minima', type=click.IntRange(50, 100), default=90, show_default=True)
    def sugerir_pendencias(limite, loja, categoria, refazer, aplicar, decidir, confianca_minima):
        """A IA sugere a peça de cada pendência aberta; com --decidir ela também aceita ou rejeita os casos claros."""
        from services.admin_service.sugerir_pendencia_service import SugerirPendenciaService
        try:
            resumo = SugerirPendenciaService(tentativas_transitorias=3, espera=30).executar(limite=limite, loja=loja, categoria=categoria,
                                                        refazer=refazer, simular=not aplicar,
                                                        decidir=decidir, confianca_minima=confianca_minima)
        except (ValueError, RuntimeError, SQLAlchemyError) as erro:
            raise click.ClickException(str(erro) if isinstance(erro, (ValueError, RuntimeError)) else 'Confira o banco de dados') from None
        click.echo(json.dumps(resumo, ensure_ascii=False))

    @app.cli.command('shopee-descobrir')
    @click.option('--categoria', type=click.Choice([m.__tablename__ for m in MODELOS_PECAS]), required=True)
    @click.option('--termo', required=True)
    @click.option('--paginas', type=click.IntRange(1, 100), default=1)
    @click.option('--execucao', required=True)
    @click.option('--gravar-catalogo', is_flag=True, help='Grava pendências e importa somente associações comprovadas.')
    @click.option('--permitir-novos', is_flag=True, help='Exige ficha técnica completa e validada.')
    @click.option('--aplicar', is_flag=True, help='Insere tarefas na fila; padrão somente mostra os parâmetros.')
    def descobrir(categoria, termo, paginas, execucao, gravar_catalogo, permitir_novos, aplicar):
        dados = dict(categoria=categoria, termo=termo, pagina=1, limite=20,
            max_paginas=paginas, execucao=execucao, simular=not gravar_catalogo,
            importar=gravar_catalogo, permitir_novos=permitir_novos)
        if aplicar:
            fila = ProcessarFilaMarketplaceService(executores_disponiveis())
            identificador = fila.enfileirar('shopee', 'descoberta', dados, execucao=execucao)
            click.echo(json.dumps(dict(tarefa=identificador)))
        else:
            click.echo(json.dumps(dict(simulacao=True, parametros=dados)))

    @app.cli.command('marketplaces-fila-preparar')
    @click.option('--aplicar', is_flag=True)
    def preparar(aplicar):
        try:
            resumo = preparar_fila_marketplaces(simular=not aplicar)
            if aplicar:
                RepositorioFilaMarketplace().inicializar()
            click.echo(json.dumps(resumo))
        except (ValueError, SQLAlchemyError):
            raise click.ClickException('Falha ao preparar fila; revise o esquema') from None

    @app.cli.command('marketplaces-fila-resumo')
    def resumo():
        click.echo(json.dumps(RepositorioFilaMarketplace().resumo()))

    @app.cli.command('marketplaces-enfileirar-ofertas')
    @click.option('--loja', type=click.Choice(LOJAS), required=True)
    @click.option('--categoria', type=click.Choice([m.__tablename__ for m in MODELOS_PECAS]), default=None,
                  help='Uma categoria. Omitida, percorre todas as categorias do banco.')
    @click.option('--peca-id', type=click.IntRange(1), default=None)
    @click.option('--execucao', required=True, help='Mesma identificação evita duplicatas na reexecução.')
    @click.option('--gravar-ofertas', is_flag=True, help='As tarefas gravarão ofertas; padrão só simula a importação.')
    @click.option('--aplicar', is_flag=True, help='Grava tarefas na fila; sem esta opção somente conta as propostas.')
    def enfileirar(loja, categoria, peca_id, execucao, gravar_ofertas, aplicar):
        """Uma tarefa por peça aprovada e com o mínimo técnico; sem --categoria, todas as categorias."""
        worker = ProcessarFilaMarketplaceService(executores_disponiveis())
        if (loja, 'ofertas') not in worker.executores:
            raise click.ClickException('Adaptador de ofertas ainda indisponível para esta loja')
        if peca_id and not categoria:
            raise click.ClickException('--peca-id exige --categoria')
        modelos = [m for m in MODELOS_PECAS if categoria in (None, m.__tablename__)]
        por_categoria = {}
        for modelo in modelos:
            por_categoria[modelo.__tablename__] = _enfileirar_categoria(
                worker, loja, modelo, peca_id, execucao, gravar_ofertas, aplicar)
        click.echo(json.dumps(dict(simulacao=not aplicar, tarefas=sum(por_categoria.values()),
                                   por_categoria=por_categoria, gravar_ofertas=gravar_ofertas)))

    @app.cli.command('marketplaces-worker')
    @click.option('--uma-vez', is_flag=True)
    def executar(uma_vez):
        parada = Event()
        anteriores = {}
        try:
            for sig in (signal.SIGTERM, signal.SIGINT):
                anteriores[sig] = signal.getsignal(sig)
                signal.signal(sig, lambda *_: parada.set())
            worker = ProcessarFilaMarketplaceService(executores_disponiveis())
            if uma_vez:
                for loja in LOJAS:
                    click.echo(json.dumps(worker.executar(loja)))
            else:
                worker.acompanhar(parada=parada)
        except (ValueError, RuntimeError, SQLAlchemyError):
            raise click.ClickException('Worker interrompido; confira esquema e configuração. Progresso preservado') from None
        finally:
            for sig, anterior in anteriores.items():
                signal.signal(sig, anterior)

    @app.cli.command('marketplaces-fila-reativar')
    @click.option('--loja', type=click.Choice(LOJAS), required=True)
    def reativar(loja):
        repo = RepositorioControleCatalogo(escopo='fila_'+loja)
        with repo.bloquear() as adquirido:
            if not adquirido:
                raise click.ClickException('Marketplace em execução; repita após concluir a tarefa')
            RepositorioFilaMarketplace().reativar(loja, agora_utc())
        click.echo(json.dumps(dict(loja=loja, reativado=True)))


def _enfileirar_categoria(worker, loja, modelo, peca_id, execucao, gravar_ofertas, aplicar):
    """Só peças publicáveis: oferta de peça não aprovada nunca é gravada, então não vale a requisição."""
    quantidade, depois = 0, 0
    while True:
        pecas = [modelo.buscar_por_id(peca_id)] if peca_id else modelo.lote_para_ofertas(depois, 100)
        pecas = [p for p in pecas if p is not None]
        if not pecas:
            break
        for peca in pecas:
            if not peca.publicavel or pendencias_para_montagem(peca):
                continue
            quantidade += 1
            if aplicar:
                worker.enfileirar(loja, 'ofertas', dict(categoria=modelo.__tablename__, peca_id=peca.id,
                    simular=not gravar_ofertas, limite_ofertas=1), execucao=execucao)
        depois = pecas[-1].id
        if peca_id:
            break
    return quantidade
