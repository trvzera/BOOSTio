from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from flask import Flask
from sqlalchemy import event

from models import db, Processador, Oferta, HistoricoOferta, VinculoMercadoLivre, ControleColeta
from services.mercadolivre_service.atualizar_ofertas_service import AtualizarOfertasMercadoLivreService as Service
from services.mercadolivre_service.associar_catalogo_service import AssociarCatalogoService
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.controle_requisicoes_service import ControleRequisicoesService, ErroMercadoLivre
from utils.identidade_peca import assinatura_peca, assinatura_catalogo

CAT='MLB123'

def produto(**changes):
    return {'id':CAT,'name':'AMD Ryzen 5 5500 BOX','status':'active','domain_id':'MLB-COMPUTER_PROCESSORS',
        'attributes':[{'id':'BRAND','value_name':'AMD'},{'id':'MPN','value_name':'100-100000457BOX'}],**changes}

def anuncio(id='MLB11',vendedor=1,preco=100,condicao='new'):
    return {'item_id':id,'seller_id':vendedor,'price':preco,'site_id':'MLB','currency_id':'BRL','condition':condicao}

class SemPausa(ControleRequisicoesService):
    def __init__(self, limite=100, intervalo=1):
        super().__init__(limite,intervalo,dormir=lambda _:None,relogio=lambda:0)

@pytest.fixture
def banco(monkeypatch):
    app=Flask(__name__); app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
    db.init_app(app)
    monkeypatch.setattr('services.mercadolivre_service.atualizar_ofertas_service.ControleRequisicoesService',SemPausa)
    with app.app_context():
        db.create_all(); ControleColeta.inicializar()
        p=Processador(fabricante='AMD',modelo='Ryzen 5 5500',part_number='100-100000457BOX',soquete='AM4',
            nucleo=6,thread=12,clockbase=3.6,clockmax=4.2,consumo_energia=65,preco=600,esgotado=False)
        db.session.add(p);db.session.commit()
        yield app,p
        db.session.remove();db.engine.dispose()


def executar(p,prod=None,ofertas=None,**opcoes):
    prod=prod or produto(); ofertas=ofertas if ofertas is not None else [anuncio()]
    def api(self,path,token,params=None):
        if path=='/products/search': return {'paging':{'total':1},'results':[prod]}
        if path==f'/products/{CAT}': return prod
        if path==f'/products/{CAT}/items': return {'paging':{'total':len(ofertas),'offset':0},'results':ofertas}
        raise AssertionError(path)
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch('services.mercadolivre_service.atualizar_ofertas_service.TokenMercadoLivreService') as tokens:
        tokens.return_value.executar.return_value='token'
        return Service().executar(categoria='processador',peca_id=p.id,**opcoes)


def test_simulacao_nao_grava_e_retorna_propostas(banco):
    _,p=banco
    r=executar(p)
    assert r['associadas']==1 and r['requisicoes']==3
    assert r['detalhes'][0]['ofertas'][0]['acao']=='criada'
    assert Oferta.query.count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==0


def test_importacao_idempotente_preserva_peca_e_afiliado(banco):
    _,p=banco
    antes=(p.preco,p.esgotado,p.preco_atualizado_em)
    r=executar(p,simular=False)
    assert r['associadas']==1
    o=Oferta.query.one();o.url_afiliado='https://exemplo.test/afiliado';db.session.commit()
    r=executar(p,simular=False)
    assert r['requisicoes']==2 and r['detalhes'][0]['ofertas'][0]['acao']=='inalterada'
    assert Oferta.query.count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==1
    assert o.esgotado is None and o.url_afiliado=='https://exemplo.test/afiliado'
    assert (p.preco,p.esgotado,p.preco_atualizado_em)==antes
    executar(p,ofertas=[anuncio(preco=90)],simular=False)
    assert HistoricoOferta.query.count()==2 and Oferta.query.one().preco==Decimal('90')


def test_cinco_menores_novas_de_vendedores_distintos(banco):
    _,p=banco
    ofertas=[anuncio('MLB1',1,1,'used'),anuncio('MLB2',1,40),anuncio('MLB3',1,30)]
    ofertas += [anuncio(f'MLB{10+i}',i,50+i) for i in range(2,10)]
    executar(p,ofertas=ofertas,simular=False)
    registros=Oferta.query.order_by(Oferta.preco).all()
    assert len(registros)==5 and registros[0].produto_id_loja=='MLB3'
    assert len({o.vendedor_id for o in registros})==5


@pytest.mark.parametrize('mudanca',[{'name':'Kit Upgrade AMD Ryzen 5500'},{'name':'AMD Ryzen 5500 OEM'},
    {'name':'Notebook Ryzen 5500'},{'domain_id':'MLB-NOTEBOOKS'},
    {'attributes':[{'id':'BRAND','value_name':'AMD'},{'id':'MPN','value_name':'100-100000457BOX-XT'}]},
    {'attributes':[{'id':'BRAND','value_name':'Intel'},{'id':'MPN','value_name':'100-100000457BOX'}]}])
def test_nao_associa_variantes_ou_kits(banco,mudanca):
    _,p=banco
    r=executar(p,prod=produto(**mudanca),simular=False)
    assert r['revisao']==1 and Oferta.query.count()==0


def test_sem_mpn_exige_revisao(banco):
    _,p=banco;p.part_number=None;db.session.commit()
    r=executar(p,simular=False)
    assert r['revisao']==1 and VinculoMercadoLivre.query.count()==0


def test_ficha_remota_ou_identidade_local_alterada_preserva_dados(banco):
    _,p=banco;executar(p,simular=False)
    r=executar(p,prod=produto(name='AMD Ryzen 5500 outra edição'),simular=False)
    assert r['falhas']==1 and HistoricoOferta.query.count()==1
    p.modelo='Ryzen 5500X';db.session.commit()
    assert executar(p,simular=False)['revisao']==1


def test_busca_incompleta_ou_ambigua_nao_vincula(banco):
    _,p=banco
    with patch.object(BuscarOfertasMercadoLivreService,'_consultar',return_value={'paging':{'total':30},'results':[produto()]}):
        r=AssociarCatalogoService().executar(p,BuscarOfertasMercadoLivreService(),'t')
    assert r['status']=='revisao'
    with patch.object(BuscarOfertasMercadoLivreService,'_consultar',return_value={'paging':{'total':2},'results':[produto(),produto(id='MLB2')]}):
        assert AssociarCatalogoService().executar(p,BuscarOfertasMercadoLivreService(),'t')['status']=='revisao'


def test_orcamento_nao_persiste_resultado_parcial(banco):
    _,p=banco
    r=executar(p,max_requisicoes=2,simular=False)
    assert r['interrompido'] is True and r['requisicoes']==2
    assert Oferta.query.count()==VinculoMercadoLivre.query.count()==0


def test_sem_ofertas_nao_marca_esgotado_nem_apaga(banco):
    _,p=banco;executar(p,simular=False)
    assert executar(p,ofertas=[],simular=False)['sem_ofertas']==1
    assert Oferta.query.one().ativa and Oferta.query.one().esgotado is None


def test_falha_na_gravacao_reverte_vinculo_ofertas_e_historico(banco):
    _,p=banco
    with patch.object(db.session,'commit',side_effect=RuntimeError('falha')):
        with pytest.raises(RuntimeError): executar(p,simular=False)
    assert Oferta.query.count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==0


def test_limite_reduzido_desativa_sem_esgotar(banco):
    _,p=banco
    executar(p,ofertas=[anuncio('MLB1',1,10),anuncio('MLB2',2,20)],simular=False)
    executar(p,ofertas=[anuncio('MLB1',1,10),anuncio('MLB2',2,20)],limite_ofertas=1,simular=False)
    o=Oferta.query.filter_by(produto_id_loja='MLB2').one()
    assert o.ativa is False and o.esgotado is None and HistoricoOferta.query.count()==2


def test_codigo_interno_seed_nao_e_mpn_do_fabricante(banco):
    _,p=banco;p.part_number='SEED-CPU-12';db.session.commit()
    prod=produto(attributes=[{'id':'BRAND','value_name':'AMD'},{'id':'MPN','value_name':'SEED-CPU-12'}])
    with patch.object(BuscarOfertasMercadoLivreService,'_consultar',return_value={'paging':{'total':1},'results':[prod]}) as consultar:
        r=AssociarCatalogoService().executar(p,BuscarOfertasMercadoLivreService(),'t')
    assert r['status']=='revisao'
    assert consultar.call_args.kwargs['params']['q']=='AMD Ryzen 5 5500'
