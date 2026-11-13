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


def test_tarefa_concluida_zera_contador_de_limitacoes(banco):
    app,repo=banco
    agora=datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=1)
    for _ in range(3):
        repo.suspender('shopee',agora,espera=1,rate_limit=True)
    assert repo.limitacoes('shopee')==3
    repo.normalizar_limitacoes('shopee')
    assert repo.limitacoes('shopee')==0
    controle=ControleRequisicoesMarketplaceService('shopee',repo,relogio=lambda:agora+timedelta(seconds=5))
    with pytest.raises(FalhaMarketplace) as erro:
        controle.executar(Mock(side_effect=FalhaMarketplace(429)))
    assert erro.value.espera==60


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


def test_enfileirar_sem_categoria_percorre_todas_e_so_pecas_aprovadas_e_completas(banco):
    import json
    from commands.marketplaces import registrar_comandos_marketplaces
    from models import Processador, Fonte
    app, repo = banco
    db.create_all()
    cpu = dict(fabricante='AMD', soquete='AM4', nucleo=6, thread=12, clockbase=3.6, clockmax=4.2, consumo_energia=65)
    db.session.add_all([
        Processador(modelo='Ryzen 5 5500', status_validacao='aprovado', **cpu),
        Processador(modelo='Ryzen 5 5600', status_validacao='legado', **cpu),
        Processador(modelo='Ryzen 5 4500', status_validacao='em_revisao', **cpu),
        Fonte(fabricante='Corsair', modelo='CV550', potencia_w=550, consumo_energia=0, status_validacao='aprovado')])
    db.session.commit()
    registrar_comandos_marketplaces(app)
    runner = app.test_cli_runner()
    simulado = json.loads(runner.invoke(args=['marketplaces-enfileirar-ofertas', '--loja', 'shopee', '--execucao', 'todas']).output)
    assert simulado['simulacao'] is True and simulado['por_categoria']['processador'] == 2
    assert simulado['tarefas'] == sum(simulado['por_categoria'].values()) and repo.resumo() == []
    aplicado = json.loads(runner.invoke(args=['marketplaces-enfileirar-ofertas', '--loja', 'shopee', '--execucao', 'todas', '--aplicar']).output)
    assert aplicado['tarefas'] == simulado['tarefas'] and TarefaMarketplace.query.count() == aplicado['tarefas']
    runner.invoke(args=['marketplaces-enfileirar-ofertas', '--loja', 'shopee', '--execucao', 'todas', '--aplicar'])
    assert TarefaMarketplace.query.count() == aplicado['tarefas']
    uma = json.loads(runner.invoke(args=['marketplaces-enfileirar-ofertas', '--loja', 'shopee', '--categoria', 'processador', '--execucao', 'so-cpu']).output)
    assert uma['tarefas'] == 2 and list(uma['por_categoria']) == ['processador']
    assert runner.invoke(args=['marketplaces-enfileirar-ofertas', '--loja', 'shopee', '--peca-id', '1', '--execucao', 'x']).exit_code != 0


def test_404_nao_envenena_as_proximas_chamadas_da_tarefa(banco):
    _, repo = banco
    agora = datetime.now(timezone.utc).replace(tzinfo=None)+timedelta(seconds=1)
    controle = ControleRequisicoesMarketplaceService('mercado_livre', repo, relogio=lambda: agora, dormir=lambda _: None)
    with pytest.raises(FalhaMarketplace) as erro:
        controle.executar(Mock(side_effect=FalhaMarketplace(404)))
    assert erro.value.status == 404 and controle.erro is None
    agora += timedelta(seconds=2)
    assert controle.executar(Mock(return_value={'ok': True})) == {'ok': True}
    agora += timedelta(seconds=2)
    with pytest.raises(FalhaMarketplace):
        controle.executar(Mock(side_effect=FalhaMarketplace(400)))
    assert controle.erro is not None


def test_perifericos_saem_da_fila_antes_das_demais_categorias(banco):
    app, repo = banco
    repo.enfileirar('shopee', 'a', 'ofertas', {'categoria': 'fan', 'peca_id': 1})
    repo.enfileirar('shopee', 'b', 'ofertas', {'categoria': 'monitor', 'peca_id': 2})
    repo.enfileirar('shopee', 'c', 'ofertas', {'categoria': 'gabinete', 'peca_id': 3})
    repo.enfileirar('shopee', 'd', 'ofertas', {'categoria': 'mouse', 'peca_id': 4})
    agora = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=1)
    ordem = []
    for _ in range(4):
        tarefa = repo.reservar('shopee', agora)
        ordem.append(tarefa['dados']['categoria'])
        repo.finalizar(tarefa, 'concluida')
    assert ordem == ['monitor', 'mouse', 'fan', 'gabinete']


def _worker_com_status(repo, agora, status):
    def executar(dados):
        raise FalhaMarketplace(status)
    return ProcessarFilaMarketplaceService({('mercado_livre', 'ofertas'): executar}, repo, relogio=lambda: agora[0], trava=trava,
        controle=ControleRequisicoesMarketplaceService('mercado_livre', repo, relogio=lambda: agora[0]))


def test_403_isolado_falha_so_a_tarefa_e_nao_bloqueia_a_loja(banco):
    app, repo = banco
    agora = [datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=1)]
    worker = _worker_com_status(repo, agora, 403)
    worker.enfileirar('mercado_livre', 'ofertas', {'peca_id': 1}, execucao='t')
    assert worker.executar('mercado_livre')['status'] == 'falhou'
    assert db.session.execute(db.select(LimiteMarketplace.bloqueado).filter_by(loja='mercado_livre')).scalar() is False


def test_terceiro_403_seguido_bloqueia_a_loja(banco):
    app, repo = banco
    agora = [datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=1)]
    worker = _worker_com_status(repo, agora, 403)
    for i in range(3):
        worker.enfileirar('mercado_livre', 'ofertas', {'peca_id': i}, execucao='t')
    resultados = []
    for _ in range(3):
        agora[0] += timedelta(seconds=2)
        resultados.append(worker.executar('mercado_livre')['status'])
    assert resultados == ['falhou', 'falhou', 'bloqueada']


def test_tarefa_concluida_entre_403_zera_a_contagem(banco):
    app, repo = banco
    agora = [datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=1)]
    erros = [FalhaMarketplace(403), FalhaMarketplace(403), None, FalhaMarketplace(403)]
    def executar(dados):
        erro = erros.pop(0)
        if erro:
            raise erro
        return {'ok': True}
    worker = ProcessarFilaMarketplaceService({('mercado_livre', 'ofertas'): executar}, repo, relogio=lambda: agora[0], trava=trava,
        controle=ControleRequisicoesMarketplaceService('mercado_livre', repo, relogio=lambda: agora[0]))
    for i in range(4):
        worker.enfileirar('mercado_livre', 'ofertas', {'peca_id': i}, execucao='t')
    resultados = []
    for _ in range(4):
        agora[0] += timedelta(seconds=2)
        resultados.append(worker.executar('mercado_livre')['status'])
    assert resultados == ['falhou', 'falhou', 'concluida', 'falhou']


def test_403_gerado_pela_flag_de_bloqueio_nao_vira_falha_da_tarefa(banco):
    app, repo = banco
    agora = [datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=1)]
    controle = ControleRequisicoesMarketplaceService('mercado_livre', repo, relogio=lambda: agora[0])
    def executar(dados):
        repo.suspender('mercado_livre', agora[0], bloquear=True)
        return controle.executar(lambda: {})
    worker = ProcessarFilaMarketplaceService({('mercado_livre', 'ofertas'): executar}, repo,
        relogio=lambda: agora[0], trava=trava, controle=controle)
    ident = worker.enfileirar('mercado_livre', 'ofertas', {'peca_id': 1}, execucao='t')
    assert worker.executar('mercado_livre')['status'] == 'pendente'
    assert db.session.get(TarefaMarketplace, ident).status == 'pendente'
