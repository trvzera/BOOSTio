from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor
from flask import Flask
from unittest.mock import Mock
import pytest
from models import db
from models.tarefa_marketplace import TarefaMarketplace, LimiteMarketplace
from migrations.fila_marketplaces import preparar_fila_marketplaces
from repositories.fila_marketplace_repository import RepositorioFilaMarketplace
from services.marketplace_service.processar_fila_service import ProcessarFilaMarketplaceService
from services.marketplace_service.controle_requisicoes_service import ControleRequisicoesMarketplaceService
from services.marketplace_service.erros import FalhaMarketplace


@pytest.fixture
def banco(tmp_path):
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///'+str(tmp_path/'fila.db'), SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    with app.app_context():
        preparar_fila_marketplaces(simular=False)
        repo = RepositorioFilaMarketplace()
        repo.inicializar()
        yield app, repo
        db.session.remove()
        db.engine.dispose()


@contextmanager
def trava(_):
    yield True


def test_migracao_simulada_e_repetivel_preserva_dados(banco):
    app, repo = banco
    ident = repo.enfileirar('shopee', 'chave', 'ofertas', {'consulta':'SSD'})
    assert preparar_fila_marketplaces()['tabelas'] == []
    assert preparar_fila_marketplaces(simular=False)['tabelas'] == []
    assert db.session.get(TarefaMarketplace, ident).dados == {'consulta':'SSD'}


def test_idempotencia_persistencia_e_recuperacao_crash(banco):
    app, repo = banco
    executar = Mock(return_value={'associadas':1})
    worker = ProcessarFilaMarketplaceService({('shopee','teste'):executar}, repo, trava=trava)
    ident = worker.enfileirar('shopee','teste',{'consulta':'SSD'},execucao='teste')
    assert worker.enfileirar('shopee','teste',{'consulta':'SSD'},execucao='teste') == ident
    primeira = repo.reservar('shopee',datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=1))
    assert primeira['id'] == ident
    # Nova instância, como após reiniciar o processo; tarefa em execução recuperada.
    worker.relogio=lambda:datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=1)
    assert worker.executar('shopee')['status'] == 'concluida'
    assert worker.executar('shopee')['status'] == 'aguardando'
    executar.assert_called_once()
    with pytest.raises(RuntimeError):
        repo.finalizar(primeira, 'concluida')


def test_intervalo_atomico_entre_processos_e_lojas_independentes(banco):
    app, repo = banco
    agora = datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=2)
    def reservar(_):
        with app.app_context():
            return repo.intervalo('shopee', agora, 1)
    with ThreadPoolExecutor(max_workers=4) as pool:
        resultados = list(pool.map(reservar, range(4)))
    assert resultados.count(0) == 1
    assert repo.intervalo('mercado_livre',agora,1) == 0


@pytest.mark.parametrize('status,espera', [(429,60),(429,120),(503,5),(400,0),(401,0)])
def test_erros_fila_e_retomada_automatica(banco,status,espera):
    app, repo = banco
    agora = [datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=1)]
    chamada=Mock(side_effect=[FalhaMarketplace(status,120 if espera==120 else None), {'ok':True}])
    controle=ControleRequisicoesMarketplaceService('shopee',repo,relogio=lambda:agora[0])
    def executar(_):return controle.executar(chamada)
    worker=ProcessarFilaMarketplaceService({('shopee','teste'):executar},repo,relogio=lambda:agora[0],trava=trava,controle=controle)
    worker.enfileirar('shopee','teste',{},execucao='teste')
    resultado=worker.executar('shopee')
    esperado='bloqueada' if status==401 else 'falhou' if status==400 else 'pendente'
    assert resultado['status']==esperado
    if esperado!='pendente':
        assert worker.executar('shopee')['status']=='aguardando'
        chamada.assert_called_once()
        return
    assert worker.executar('shopee')['status']=='aguardando'
    agora[0]+=timedelta(seconds=espera+1)
    worker.controle=ControleRequisicoesMarketplaceService('shopee',repo,relogio=lambda:agora[0])
    # Handler recebe o controle do novo ciclo, assim como o cliente HTTP real.
    from services.marketplace_service.controle_requisicoes_service import executar_requisicao
    worker.executores[('shopee','teste')]=lambda _:executar_requisicao(chamada, loja='shopee')
    assert worker.executar('shopee')['status']=='concluida'
    assert chamada.call_count==2


def test_429_repetido_backoff_e_nao_encurta_retry_after(banco):
    app,repo=banco
    agora=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=1)
    for minimo in (60,120,240):
        controle=ControleRequisicoesMarketplaceService('shopee',repo,relogio=lambda:agora)
        with pytest.raises(FalhaMarketplace) as erro:
            controle.executar(Mock(side_effect=FalhaMarketplace(429)))
        assert erro.value.espera==minimo
        agora+=timedelta(seconds=minimo+1)
    repo.suspender('shopee',agora,espera=1000)
    repo.suspender('shopee',agora,espera=60)
    assert repo.intervalo('shopee',agora,1)==1000


def test_nao_permite_intervalo_menor_que_um_segundo(banco):
    for valor in (0,.5,float('inf'),float('nan')):
        with pytest.raises(ValueError):ControleRequisicoesMarketplaceService('shopee',banco[1],intervalo=valor)


def test_tarefa_nao_roda_em_dois_workers_simultaneos(banco):
    app, repo = banco
    from threading import Event
    pronto, liberar = Event(), Event()
    def executor(_):
        pronto.set()
        assert liberar.wait(5)
        return {'ok':True}
    worker = ProcessarFilaMarketplaceService({('shopee','teste'):executor},repo)
    worker.enfileirar('shopee','teste',{},execucao='concorrencia')
    def executar():
        with app.app_context():return worker.executar('shopee')
    with ThreadPoolExecutor(max_workers=2) as pool:
        primeira=pool.submit(executar)
        assert pronto.wait(5)
        segunda=pool.submit(executar)
        assert segunda.result(timeout=5)['status']=='ocupado'
        liberar.set()
        assert primeira.result(timeout=5)['status']=='concluida'


def test_renovacao_manual_reativa_somente_marketplace_bloqueado(banco):
    app, repo=banco
    agora=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=1)
    repo.suspender('shopee',agora,bloquear=True)
    assert repo.intervalo('shopee',agora,1) is None
    assert repo.intervalo('mercado_livre',agora,1)==0
    repo.reativar('shopee',agora)
    assert repo.intervalo('shopee',agora,1)==0


def test_cli_prepara_simula_enfileiramento_e_nao_inicia_worker(banco):
    from commands.marketplaces import registrar_comandos_marketplaces
    app, repo=banco
    registrar_comandos_marketplaces(app)
    runner=app.test_cli_runner()
    assert runner.invoke(args=['marketplaces-fila-preparar']).exit_code==0
    assert runner.invoke(args=['marketplaces-fila-resumo']).exit_code==0
    assert repo.resumo()==[]


@pytest.mark.parametrize('erro',[__import__('requests').Timeout(),__import__('requests').ConnectionError()])
def test_falhas_de_rede_sao_temporarias_sem_expor_payload(banco,erro):
    controle=ControleRequisicoesMarketplaceService('shopee',banco[1])
    with pytest.raises(FalhaMarketplace) as falha:
        controle.executar(Mock(side_effect=erro))
    assert falha.value.temporaria and falha.value.status is None
