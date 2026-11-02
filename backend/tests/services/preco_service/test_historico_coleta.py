from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
import requests
from flask import Flask
from sqlalchemy import event

from models import db, PlacaVideo, ConsultaPreco, ControleColeta, HistoricoPreco
from commands.banco import registrar_comandos_banco
from migrations.historico_precos import preparar_historico_precos
from services.peca_service import atualizar_precos_service as coleta
from services.preco_service.buscar_preco_kabum_service import BuscarPrecoKabumService

URL="https://www.kabum.com.br/produto/123/placa"
DATA_ANTIGA=datetime(2026,1,1)


@pytest.fixture
def banco(tmp_path):
    app=Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{tmp_path / "historico.db"}'
    db.init_app(app)
    registrar_comandos_banco(app)
    with app.app_context():
        db.create_all()
        ControleColeta.inicializar()
        p=PlacaVideo(fabricante='Teste',modelo='GPU',memoria_gb=8,consumo_energia=65,
                    preco=100,esgotado=False,kabum_external=URL,preco_atualizado_em=DATA_ANTIGA)
        db.session.add(p);db.session.commit()
        yield app,p
        db.session.remove();db.engine.dispose()


def executar(mocker,resultado,dia=0):
    instante=datetime(2026,11,2,12,tzinfo=timezone.utc)+timedelta(days=dia)
    class Relogio:
        @staticmethod
        def now(tz=None):
            return instante.astimezone(tz) if tz else instante.replace(tzinfo=None)
    mocker.patch.object(coleta,'datetime',Relogio)
    buscar=mocker.patch.object(BuscarPrecoKabumService,'executar',return_value=resultado)
    return coleta.AtualizarPrecosService().executar(intervalo=0),buscar


def test_preco_igual_registra_historico_sem_update_da_peca(banco,mocker):
    _,p=banco
    data_geral=p.atualizado_em
    atualizacoes=[]
    def capturar(conn,cursor,statement,*args):
        if statement.lower().startswith('update placa_video '):atualizacoes.append(statement)
    event.listen(db.engine,'before_cursor_execute',capturar)
    try:r,_=executar(mocker,{'preco':Decimal('100.00'),'esgotado':False})
    finally:event.remove(db.engine,'before_cursor_execute',capturar)
    assert atualizacoes==[]
    assert p.preco==100 and p.preco_atualizado_em==DATA_ANTIGA and p.atualizado_em==data_geral
    assert r['historicos']==r['inalteradas']==1 and r['atualizadas']==0
    h=HistoricoPreco.query.one()
    assert h.preco==Decimal('100.00') and h.coletado_em==datetime(2026,11,2,12)
    assert (h.tabela_peca,h.peca_id,h.loja,h.produto_id_loja,h.url)==('placa_video',p.id,'kabum','123',URL)
    assert db.session.get(ConsultaPreco,h.consulta_id).status=='concluida'


def test_preco_alterado_grava_peca_e_observacao_na_mesma_data(banco,mocker):
    _,p=banco
    r,_=executar(mocker,{'preco':Decimal('89.90'),'esgotado':False})
    h=HistoricoPreco.query.one()
    assert p.preco==89.90 and p.preco_atualizado_em==h.coletado_em
    assert h.preco==Decimal('89.90')
    assert r['atualizadas']==r['historicos']==r['precos_alterados']==1
    assert r['estoques_alterados']==0


def test_estoque_muda_com_preco_igual_sem_mudar_data_do_preco(banco,mocker):
    _,p=banco
    p.esgotado=True;db.session.commit()
    r,_=executar(mocker,{'preco':Decimal('100.00'),'esgotado':False})
    assert p.esgotado is False and p.preco_atualizado_em==DATA_ANTIGA
    assert r['estoques_alterados']==r['atualizadas']==r['historicos']==1
    assert r['precos_alterados']==0


def test_esgotado_registra_sem_preco_e_preserva_valor_anterior(banco,mocker):
    _,p=banco
    r,_=executar(mocker,{'preco':None,'esgotado':True})
    h=HistoricoPreco.query.one()
    assert h.preco is None and h.esgotado is True
    assert p.preco==100 and p.preco_atualizado_em==DATA_ANTIGA and p.esgotado is True
    assert r['estoques_alterados']==1 and r['precos_alterados']==0


def test_mesmo_preco_em_dias_diferentes_gera_observacoes_distintas(banco,mocker):
    _,p=banco
    executar(mocker,{'preco':Decimal('100.00'),'esgotado':False})
    r,_=executar(mocker,{'preco':Decimal('100.00'),'esgotado':False},dia=1)
    assert HistoricoPreco.query.count()==2 and r['historicos']==1
    assert p.preco_atualizado_em==DATA_ANTIGA
    r,buscar=executar(mocker,{'preco':Decimal('100.00'),'esgotado':False},dia=1)
    assert r['consultas']==0 and HistoricoPreco.query.count()==2
    buscar.assert_not_called()


@pytest.mark.parametrize('valor',[Decimal('0'),Decimal('-1'),Decimal('NaN'),Decimal('Infinity'),None])
def test_cotacao_invalida_nao_cria_historico_nem_muda_peca(banco,mocker,valor):
    _,p=banco
    r,_=executar(mocker,{'preco':valor,'esgotado':False})
    assert r['falhas']==1 and r['historicos']==r['atualizadas']==0
    assert HistoricoPreco.query.count()==0 and p.preco==100
    assert p.preco_atualizado_em==DATA_ANTIGA
    assert ConsultaPreco.query.one().status=='falha'


def test_falha_rede_nao_e_historico_de_preco(banco,mocker):
    _,p=banco
    mocker.patch.object(BuscarPrecoKabumService,'executar',side_effect=requests.ConnectionError('rede'))
    r=coleta.AtualizarPrecosService().executar(intervalo=0)
    assert r['falhas']==1 and HistoricoPreco.query.count()==0 and p.preco==100


def test_erro_persistencia_reverte_preco_historico_e_status(banco,mocker):
    _,p=banco
    def falhar(session):
        if any(isinstance(x,HistoricoPreco) for x in session.new):raise RuntimeError('falha simulada')
    event.listen(db.session(),'before_commit',falhar)
    try:
        with pytest.raises(RuntimeError,match='falha simulada'):
            executar(mocker,{'preco':Decimal('80.00'),'esgotado':False})
    finally:event.remove(db.session(),'before_commit',falhar)
    assert HistoricoPreco.query.count()==0 and p.preco==100
    assert p.preco_atualizado_em==DATA_ANTIGA
    assert ConsultaPreco.query.one().status=='reservada'


def test_link_trocado_durante_rede_nao_grava_cotacao_antiga(banco,mocker):
    _,p=banco
    def trocar(url):
        p.kabum_external='https://www.kabum.com.br/produto/456/outra'
        db.session.commit()
        return {'preco':Decimal('80.00'),'esgotado':False}
    mocker.patch.object(BuscarPrecoKabumService,'executar',side_effect=trocar)
    r=coleta.AtualizarPrecosService().executar(intervalo=0)
    assert r['ignoradas']==1 and HistoricoPreco.query.count()==0 and p.preco==100


def test_migracao_cria_so_historico_preserva_pecas_e_e_repetivel(banco):
    app,p=banco
    ident=p.id
    db.session.remove();HistoricoPreco.__table__.drop(db.engine)
    assert preparar_historico_precos()['criada'] is True
    assert preparar_historico_precos()['criada'] is False
    assert PlacaVideo.buscar_por_id(ident).preco==100
    r=app.test_cli_runner().invoke(args=['historico-precos-preparar'])
    assert r.exit_code==0,r.output


def test_sem_tabela_interrompe_antes_de_consultar_loja(banco,mocker):
    _,p=banco
    db.session.remove();HistoricoPreco.__table__.drop(db.engine)
    buscar=mocker.patch.object(BuscarPrecoKabumService,'executar')
    with pytest.raises(ValueError,match='historico-precos-preparar'):
        coleta.AtualizarPrecosService().executar()
    buscar.assert_not_called()
    assert ConsultaPreco.query.count()==0


def test_compara_preco_em_centavos_sem_falso_update_de_float(banco,mocker):
    _,p=banco
    p.preco=0.1+0.2;db.session.commit()
    r,_=executar(mocker,{'preco':Decimal('0.30'),'esgotado':False})
    assert r['precos_alterados']==0 and r['historicos']==1
    assert p.preco_atualizado_em==DATA_ANTIGA
    assert HistoricoPreco.query.one().preco==Decimal('0.30')


def test_tentativa_finalizada_nao_consulta_loja_nem_duplica_historico(banco,mocker):
    executar(mocker,{'preco':Decimal('100.00'),'esgotado':False})
    c=ConsultaPreco.query.one()
    buscar=mocker.patch.object(BuscarPrecoKabumService,'executar')
    assert coleta.AtualizarPrecosService()._consultar(c,{}) is True
    buscar.assert_not_called()
    assert c.status=='concluida' and HistoricoPreco.query.count()==1
