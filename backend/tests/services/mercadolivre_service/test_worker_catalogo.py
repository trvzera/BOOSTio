from services.catalogo_service.ler_plano_catalogo_service import ler_plano
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

import pytest
from flask import Flask
from models import db, EstadoCatalogo, ProdutoPendente, HD, Oferta, HistoricoOferta, ControleColeta
from repositories.controle_catalogo_repository import RepositorioControleCatalogo
from services.mercadolivre_service.processar_catalogo_service import ProcessarCatalogoService, ControleRequisicoesCatalogo
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService
from services.mercadolivre_service.controle_requisicoes_service import ErroMercadoLivre


@pytest.fixture
def banco(tmp_path):
    app=Flask(__name__);app.config.update(SQLALCHEMY_DATABASE_URI=f'sqlite:///{tmp_path / "catalogo.db"}',
        MERCADO_LIVRE_CLIENT_ID='123',MERCADO_LIVRE_CONTA_ID='42')
    db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        yield app
        db.session.remove();db.engine.dispose()


def plano(tmp_path, **extras):
    arquivo=tmp_path/'plano.json'
    arquivo.write_text(json.dumps(dict(versao=1,trabalhos=[{**dict(nome='hd',categoria='hd',consulta='Seagate Exos',max_paginas=3,max_anuncios=20,max_requisicoes=20,intervalo=0.1),**extras}])))
    return ler_plano(arquivo)


def api(self,caminho,token,params=None):
    produto=dict(id='MLB99',name='Seagate Exos 8TB',status='active',domain_id='MLB-HARD_DRIVES_AND_SSDS',attributes=[
        dict(id=k,value_name=v) for k,v in [('BRAND','Seagate'),('MODEL','ST8000NM017B'),('MPN','ST8000NM017B'),('CAPACITY','8 TB'),('DRIVE_STORAGE_TYPE','HDD'),('HARD_DRIVE_AND_SSD_POWER_CONSUMPTION','7 W')]])
    if caminho=='/products/MLB99':return produto
    linha=produto if caminho=='/products/search' else dict(item_id='MLB10',seller_id=7,site_id='MLB',currency_id='BRL',price=100,condition='new',available_quantity=3)
    return {'paging':{'offset':0,'total':1},'results':[linha]}


def liberar_agenda():
    e=EstadoCatalogo.query.one();e.proxima_execucao=datetime(2000,1,1);db.session.commit()


def test_worker_percorre_fases_retoma_e_so_publica_com_opcao(banco,tmp_path):
    trabalhos=plano(tmp_path)
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch.object(TokenMercadoLivreService,'executar',return_value='teste'),patch('services.mercadolivre_service.processar_catalogo_service.ControleRequisicoesCatalogo') as cls:
        cls.side_effect=lambda *args: ControleRequisicoesCatalogo(*args)
        for fase in ('descoberta','classificacao','enriquecimento','importacao'):
            r=ProcessarCatalogoService().executar(trabalhos,simular=False,permitir_novos=True)
            assert r['status']=='concluido' and r['fase']==fase, r
            if fase!='importacao':liberar_agenda()
    assert ProdutoPendente.query.one().status=='importado'
    assert HD.query.count()==Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==1
    e=EstadoCatalogo.query.one()
    assert e.fase=='descoberta' and e.cursor_fila==0 and e.cursor_descoberta is None
    assert ProcessarCatalogoService().executar(trabalhos,simular=False)['status']=='aguardando'


def test_simulacao_nao_avanca_estado_ou_fila(banco,tmp_path):
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch.object(TokenMercadoLivreService,'executar',return_value='teste'):
        assert ProcessarCatalogoService().executar(plano(tmp_path),simular=True)['status']=='concluido'
    assert EstadoCatalogo.query.count()==ProdutoPendente.query.count()==0


def test_trava_impede_segundo_worker_e_libera_em_erro(banco,tmp_path):
    um,dois=RepositorioControleCatalogo(),RepositorioControleCatalogo()
    with um.bloquear() as ok:
        assert ok
        with dois.bloquear() as ok2:assert not ok2
        assert ProcessarCatalogoService().executar(plano(tmp_path))['status']=='ocupado'
    with dois.bloquear() as ok:assert ok
    with pytest.raises(RuntimeError):dois.verificar()


def test_429_agenda_retry_e_preserva_cursor(banco,tmp_path):
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',side_effect=ErroMercadoLivre(429,'100')), \
        patch.object(TokenMercadoLivreService,'executar',return_value='teste'):
        r=ProcessarCatalogoService().executar(plano(tmp_path),simular=False)
    assert r['status']=='falha'
    e=EstadoCatalogo.query.one();assert e.tentativas==1 and e.fase=='descoberta'
    assert e.proxima_execucao>datetime.now()+timedelta(seconds=50)


def test_mudar_plano_nao_reutiliza_cursor_sem_reinicio(banco,tmp_path):
    primeiro=plano(tmp_path);EstadoCatalogo.obter(primeiro[0])
    novo=plano(tmp_path,consulta='Seagate Barracuda')
    with pytest.raises(ValueError,match='Plano mudou'):EstadoCatalogo.obter(novo[0])
    EstadoCatalogo.reiniciar(novo[0])
    assert EstadoCatalogo.obter(novo[0]).cursor_descoberta is None


@pytest.mark.parametrize('extras',[dict(max_requisicoes=0),dict(origem='html'),dict(nome='repetir\n'),dict(dominio='https://example.test'),dict(periodo_segundos=1)])
def test_plano_invalido_nao_inicia(banco,tmp_path,extras):
    with pytest.raises(ValueError):plano(tmp_path,**extras)
    assert EstadoCatalogo.query.count()==0


def test_cli_nao_habilita_novos_por_padrao(banco,tmp_path):
    from commands.catalogo import registrar_comandos_catalogo
    registrar_comandos_catalogo(banco)
    trabalhos=plano(tmp_path);arquivo=tmp_path/'plano.json'
    with patch.object(ProcessarCatalogoService,'executar',return_value={'status':'concluido'}) as executar:
        r=banco.test_cli_runner().invoke(args=['catalogo-worker','--plano',str(arquivo),'--uma-vez'],env={'CATALOGO_PERMITIR_NOVOS':'false'})
    assert r.exit_code==0 and executar.call_args.kwargs=={'simular':True,'permitir_novos':False}


def test_trava_libera_quando_etapa_lanca_erro(banco):
    repo=RepositorioControleCatalogo()
    with pytest.raises(ValueError):
        with repo.bloquear() as adquirido:
            assert adquirido
            raise ValueError('teste')
    with RepositorioControleCatalogo().bloquear() as adquirido:assert adquirido


def test_ambiguidade_nao_bloqueia_importacao_do_lote(banco,tmp_path):
    trabalhos=plano(tmp_path)
    for _ in range(2):
        db.session.add(HD(fabricante='Seagate',modelo='Exos 8TB',part_number='ST8000NM017B',preco=100,consumo_energia=7,capacidade_gb=8000,status_validacao='aprovado'))
    db.session.commit()
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch.object(TokenMercadoLivreService,'executar',return_value='teste'):
        for fase in ('descoberta','classificacao','enriquecimento','importacao'):
            r=ProcessarCatalogoService().executar(trabalhos,simular=False,permitir_novos=True)
            assert r['status']=='concluido' and r['fase']==fase,r
            if fase!='importacao':liberar_agenda()
    assert r['resumo']['revisao']==1 and r['resumo']['falhas']==0
    assert EstadoCatalogo.query.one().fase=='descoberta'
    assert ProdutoPendente.query.one().status=='em_revisao'
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==0 and HD.query.count()==2
