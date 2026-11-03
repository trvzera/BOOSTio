from copy import deepcopy
from datetime import datetime
from unittest.mock import Mock

import pytest
from flask import Flask
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from models import db, HD, Oferta, HistoricoOferta, ProdutoPendente, IdentidadeFabricante, ControleColeta, VinculoMercadoLivre
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.importar_produto_service import ImportarProdutoService


def produto():
    return dict(id='MLB99',name='Seagate Exos 8TB',status='active',domain_id='MLB-HARD_DRIVES_AND_SSDS',attributes=[
        dict(id=k,value_name=v) for k,v in [('BRAND','Seagate'),('MODEL','ST8000NM017B'),('MPN','ST8000NM017B'),
        ('CAPACITY','8 TB'),('DRIVE_STORAGE_TYPE','HDD'),('HARD_DRIVE_AND_SSD_POWER_CONSUMPTION','7 W')]])


@pytest.fixture
def banco():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        p=ProdutoPendente(loja='mercado_livre',produto_id_loja='MLB10',vendedor_id='7',titulo='Seagate Exos 8TB',
            url='https://produto.mercadolivre.com.br/MLB-10-_JM',categoria_sugerida='hd',coletado_em=datetime(2026,11,3),
            dados_originais={'catalogo':{'id':'MLB99'},'anuncio':{'price':1,'available_quantity':1}})
        db.session.add(p);db.session.commit()
        yield p
        db.session.remove();db.engine.dispose()


def service(**extras):
    cliente=BuscarOfertasMercadoLivreService();cliente._consultar=Mock(return_value=produto())
    raw=dict(item_id='MLB10',seller_id=7,site_id='MLB',currency_id='BRL',price=999.90,condition='new',available_quantity=3)
    cliente.executar=Mock(return_value={'ofertas':[cliente._normalizar({**raw,**extras},'MLB99')]})
    tokens=Mock();tokens.executar.return_value='teste'
    return ImportarProdutoService(cliente=cliente,tokens=tokens)


def local(**extras):
    p=HD(**{**dict(fabricante='Seagate',modelo='Exos 8TB',part_number='ST8000NM017B',consumo_energia=7,preco=500,capacidade_gb=8000,status_validacao='aprovado'),**extras})
    db.session.add(p);db.session.commit();return p


def test_novo_atomico_simulacao_permissao_e_idempotencia(banco):
    s=service()
    assert s.executar(banco.id)['acao']=='revisao'
    assert s.executar(banco.id,permitir_novos=True)['acao']=='proposta'
    assert HD.query.count()==Oferta.query.count()==HistoricoOferta.query.count()==0
    r=s.executar(banco.id,simular=False,permitir_novos=True)
    assert r['novo_componente'] and r['acao']=='importada'
    assert HD.query.count()==Oferta.query.count()==HistoricoOferta.query.count()==IdentidadeFabricante.query.count()==1
    novo=HD.query.one()
    assert novo.status_validacao=='aprovado' and novo.preco==999.90 and novo.velocidade_rpm is None
    assert banco.status=='importado' and banco.oferta_id==Oferta.query.one().id
    assert Oferta.query.one().esgotado is False
    antes=(Oferta.query.one().atualizado_em,HistoricoOferta.query.one().id)
    assert s.executar(banco.id,simular=False,permitir_novos=True)['acao']=='inalterada'
    assert (Oferta.query.one().atualizado_em,HistoricoOferta.query.one().id)==antes
    novo.preco=900;db.session.commit()
    assert IdentidadeFabricante.buscar(novo) is not None


def test_existente_recebe_oferta_sem_alterar_peca_ou_desativar_outras(banco):
    p=local()
    db.session.add(Oferta(tabela_peca='hd',peca_id=p.id,loja='outra',produto_id_loja='1',preco=400,url='https://example.test'))
    db.session.commit()
    r=service().executar(banco.id,simular=False)
    assert r['acao']=='importada' and not r['novo_componente']
    assert HD.query.count()==1 and p.preco==500
    assert Oferta.query.count()==2 and all(o.ativa for o in Oferta.query.all())


def test_ambiguidades_e_incompletos_nao_publicam(banco):
    local();local()
    resultado=service().executar(banco.id,simular=False,permitir_novos=True)
    assert resultado['acao']=='revisao' and 'Vários candidatos' in resultado['motivo']
    assert banco.status=='em_revisao'
    assert Oferta.query.count()==0


def test_estoque_antigo_nao_e_reaproveitado_e_vendedor_mudou(banco):
    s=service(available_quantity=None)
    assert s.executar(banco.id,simular=False,permitir_novos=True)['acao']=='revisao'
    assert HD.query.count()==0
    with pytest.raises(ValueError,match='Vendedor mudou'):
        service(seller_id=8).executar(banco.id,simular=False,permitir_novos=True)


def test_falha_no_historico_reverte_componente_identidade_vinculo_e_oferta(banco):
    def falhar(conn,cursor,statement,*args):
        if statement.lower().startswith('insert into historico_oferta'):
            raise OperationalError('falha controlada',{},None)
    event.listen(db.engine,'before_cursor_execute',falhar)
    try:
        with pytest.raises(OperationalError):service().executar(banco.id,simular=False,permitir_novos=True)
    finally:event.remove(db.engine,'before_cursor_execute',falhar)
    assert HD.query.count()==Oferta.query.count()==HistoricoOferta.query.count()==IdentidadeFabricante.query.count()==VinculoMercadoLivre.query.count()==0
    assert ProdutoPendente.query.one().status=='pendente'
