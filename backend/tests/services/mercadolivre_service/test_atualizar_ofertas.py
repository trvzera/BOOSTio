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
            nucleo=6,thread=12,clockbase=3.6,clockmax=4.2,consumo_energia=65,preco=600,esgotado=False,status_validacao='aprovado')
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
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==0


def test_importacao_idempotente_preserva_peca_e_afiliado(banco):
    _,p=banco
    antes=(p.preco,p.esgotado,p.preco_atualizado_em)
    r=executar(p,simular=False)
    assert r['associadas']==1
    o=Oferta.query.filter(Oferta.loja!='kabum').one();o.url_afiliado='https://exemplo.test/afiliado';db.session.commit()
    r=executar(p,simular=False)
    assert r['requisicoes']==2 and r['detalhes'][0]['ofertas'][0]['acao']=='inalterada'
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==1
    assert o.esgotado is None and o.url_afiliado=='https://exemplo.test/afiliado'
    assert (p.preco,p.esgotado,p.preco_atualizado_em)==antes
    executar(p,ofertas=[anuncio(preco=90)],simular=False)
    assert HistoricoOferta.query.count()==2 and Oferta.query.filter(Oferta.loja!='kabum').one().preco==Decimal('90')


def test_cinco_menores_novas_de_vendedores_distintos(banco):
    _,p=banco
    ofertas=[anuncio('MLB1',1,1,'used'),anuncio('MLB2',1,40),anuncio('MLB3',1,30)]
    ofertas += [anuncio(f'MLB{10+i}',i,50+i) for i in range(2,10)]
    executar(p,ofertas=ofertas,limite_ofertas=5,simular=False)
    registros=Oferta.query.filter(Oferta.loja!='kabum').order_by(Oferta.preco).all()
    assert len(registros)==5 and registros[0].produto_id_loja=='MLB3'
    assert len({o.vendedor_id for o in registros})==5


@pytest.mark.parametrize('mudanca',[{'name':'Kit Upgrade AMD Ryzen 5500'},{'name':'AMD Ryzen 5500 OEM'},
    {'name':'Notebook Ryzen 5500'},{'domain_id':'MLB-NOTEBOOKS'},
    {'attributes':[{'id':'BRAND','value_name':'AMD'},{'id':'MPN','value_name':'100-100000457BOX-XT'}]},
    {'attributes':[{'id':'BRAND','value_name':'Intel'},{'id':'MPN','value_name':'100-100000457BOX'}]}])
def test_nao_associa_variantes_ou_kits(banco,mudanca):
    _,p=banco
    r=executar(p,prod=produto(**mudanca),simular=False)
    assert r['revisao']==1 and Oferta.query.filter(Oferta.loja!='kabum').count()==0


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
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==VinculoMercadoLivre.query.count()==0


def test_sem_ofertas_nao_marca_esgotado_nem_apaga(banco):
    _,p=banco;executar(p,simular=False)
    assert executar(p,ofertas=[],simular=False)['sem_ofertas']==1
    assert Oferta.query.filter(Oferta.loja!='kabum').one().ativa and Oferta.query.filter(Oferta.loja!='kabum').one().esgotado is None


def test_falha_na_gravacao_reverte_vinculo_ofertas_e_historico(banco):
    _,p=banco
    with patch.object(db.session,'commit',side_effect=RuntimeError('falha')):
        with pytest.raises(RuntimeError): executar(p,simular=False)
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==0


def test_limite_reduzido_desativa_sem_esgotar(banco):
    _,p=banco
    executar(p,ofertas=[anuncio('MLB1',1,10),anuncio('MLB2',2,20)],limite_ofertas=2,simular=False)
    executar(p,ofertas=[anuncio('MLB1',1,10),anuncio('MLB2',2,20)],simular=False)
    o=Oferta.query.filter_by(produto_id_loja='MLB2').one()
    assert o.ativa is False and o.esgotado is None and HistoricoOferta.query.count()==2


def test_codigo_interno_seed_nao_e_mpn_do_fabricante(banco):
    _,p=banco;p.part_number='SEED-CPU-12';db.session.commit()
    prod=produto(attributes=[{'id':'BRAND','value_name':'AMD'},{'id':'MPN','value_name':'SEED-CPU-12'}])
    with patch.object(BuscarOfertasMercadoLivreService,'_consultar',return_value={'paging':{'total':1},'results':[prod]}) as consultar:
        r=AssociarCatalogoService().executar(p,BuscarOfertasMercadoLivreService(),'t')
    assert r['status']=='revisao'
    assert consultar.call_args.kwargs['params']['q']=='AMD Ryzen 5 5500'


def test_fluxo_novo_aceita_resultado_comprovado_em_busca_ampla(banco):
    _,p=banco
    def api(self,path,token,params=None):
        if path=='/products/search':return {'paging':{'total':900},'results':[produto()]}
        if path==f'/products/{CAT}':return produto()
        return {'paging':{'total':1,'offset':0},'results':[anuncio()]}
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch('services.mercadolivre_service.atualizar_ofertas_service.TokenMercadoLivreService') as tokens:
        tokens.return_value.executar.return_value='token'
        r=Service().executar(categoria='processador',somente_com_minimos=True)
    assert r['associadas']==1 and r['detalhes'][0]['busca_remota_completa'] is False
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==0


def test_nao_consulta_api_para_peca_sem_minimos(banco):
    _,p=banco;p.thread=None;db.session.commit()
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar') as api:
        r=Service().executar(categoria='processador',somente_com_minimos=True,limite_pecas=None)
    assert r['pecas']==0 and r['ignoradas_sem_minimos']==1 and r['cursores']=={'processador':p.id}
    api.assert_not_called()


def test_nao_grava_oferta_para_ficha_ainda_em_revisao(banco):
    _,p=banco;p.status_validacao='em_revisao';db.session.commit()
    r=executar(p,simular=False)
    assert r['revisao']==1 and Oferta.query.filter(Oferta.loja!='kabum').count()==0
    assert p.status_validacao=='em_revisao'


def test_duplicata_criada_durante_http_e_detectada_antes_da_gravacao(banco):
    _,p=banco
    def api(self,path,token,params=None):
        if path=='/products/search':return {'paging':{'total':1},'results':[produto()]}
        if path==f'/products/{CAT}':return produto()
        duplicata=Processador(fabricante=p.fabricante,modelo=p.modelo,part_number=p.part_number,
            soquete=p.soquete,nucleo=p.nucleo,thread=p.thread,clockbase=p.clockbase)
        db.session.add(duplicata);db.session.commit()
        return {'paging':{'total':1,'offset':0},'results':[anuncio()]}
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch('services.mercadolivre_service.atualizar_ofertas_service.TokenMercadoLivreService') as tokens:
        tokens.return_value.executar.return_value='token'
        r=Service().executar(categoria='processador',peca_id=p.id,simular=False)
    assert r['falhas']==1 and r['interrompido']
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==0


def test_cli_relatorio_retoma_sem_repetir_peca_concluida(banco,tmp_path):
    import json
    from commands.mercadolivre import registrar_comandos_mercadolivre
    app,p=banco;registrar_comandos_mercadolivre(app)
    path=tmp_path/'teste.json'
    def api(self,caminho,token,params=None):
        if caminho=='/products/search':return {'paging':{'total':1},'results':[produto()]}
        if caminho==f'/products/{CAT}':return produto()
        return {'paging':{'total':1,'offset':0},'results':[anuncio()]}
    args=['mercadolivre-ofertas-atualizar','--categoria','processador','--todas','--resumo',str(path)]
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch('services.mercadolivre_service.atualizar_ofertas_service.TokenMercadoLivreService') as tokens:
        tokens.return_value.executar.return_value='token'
        r=app.test_cli_runner().invoke(args=args)
        assert r.exit_code==0,r.output
        r=app.test_cli_runner().invoke(args=[*args,'--retomar'])
        assert r.exit_code==0,r.output
        assert tokens.return_value.executar.call_count==1
    dados=json.loads(path.read_text())
    assert dados['pecas']==dados['associadas']==1
    assert dados['requisicoes']==3 and len(path.with_suffix('.detalhes.jsonl').read_text().splitlines())==1
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==0


def test_carrega_catalogo_uma_vez_por_categoria_na_simulacao(banco):
    from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
    _,p=banco
    outro=Processador(fabricante='AMD',modelo='Ryzen 5 5600',part_number='100-100000927BOX',
        soquete='AM4',nucleo=6,thread=12,clockbase=3.5,consumo_energia=65,status_validacao='aprovado')
    db.session.add(outro);db.session.commit()
    produtos={}
    por_mpn={}
    for comp in (p,outro):
        raw=produto(id=f'MLB{100+comp.id}',name=f'AMD {comp.modelo} BOX',attributes=[
            {'id':'BRAND','value_name':'AMD'},{'id':'MPN','value_name':comp.part_number}])
        produtos[raw['id']]=raw;por_mpn[comp.part_number]=raw
    def api(self,caminho,token,params=None):
        if caminho=='/products/search':return {'paging':{'total':1},'results':[por_mpn[params['q']]]}
        if caminho.endswith('/items'):return {'paging':{'total':1,'offset':0},'results':[anuncio()]}
        return produtos[caminho.split('/')[-1]]
    carregar=IndiceCandidatosService.carregar
    with patch.object(IndiceCandidatosService,'carregar',wraps=carregar) as indice,patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch('services.mercadolivre_service.atualizar_ofertas_service.TokenMercadoLivreService') as tokens:
        tokens.return_value.executar.return_value='token'
        r=Service().executar(categoria='processador',somente_com_minimos=True,limite_pecas=None)
    assert r['associadas']==2 and indice.call_count==1


def test_busca_alternativa_por_nome_quando_mpn_nao_encontra(banco):
    _, p = banco
    def api(path, token, params=None):
        resultados = [] if params['q'] == p.part_number else [produto()]
        return {'paging': {'total': len(resultados)}, 'results': resultados}
    cliente = BuscarOfertasMercadoLivreService()
    with patch.object(cliente, '_consultar', side_effect=api) as consulta:
        resultado = AssociarCatalogoService().localizar_candidatos(p, cliente, 't')
    assert resultado['status'] == 'encontrada'
    assert consulta.call_count == 2
    assert [b['consulta'] for b in resultado['buscas']] == [p.part_number, 'AMD Ryzen 5 5500']


def test_busca_pagina_seguinte_sem_relaxar_matching(banco):
    _, p = banco
    incorretos = [produto(id=f'MLB{1000+i}', name='Intel Core i5', attributes=[{'id':'BRAND','value_name':'Intel'}]) for i in range(20)]
    cliente = BuscarOfertasMercadoLivreService()
    with patch.object(cliente, '_consultar', side_effect=[
        {'paging':{'total':21}, 'results':incorretos},
        {'paging':{'total':21}, 'results':[produto()]},
    ]) as consulta:
        resultado = AssociarCatalogoService().localizar_candidatos(p, cliente, 't')
    assert resultado['status'] == 'encontrada' and consulta.call_count == 2
    assert consulta.call_args.kwargs['params']['offset'] == 20


def test_buscas_limitadas_e_sem_reavaliar_catalogos_repetidos(banco):
    _, p = banco
    incorretos = [produto(id=f'MLB{1000+i}', name='Intel Core i5', attributes=[{'id':'BRAND','value_name':'Intel'}]) for i in range(20)]
    cliente = BuscarOfertasMercadoLivreService()
    with patch.object(cliente, '_consultar', return_value={'paging':{'total':10000},'results':incorretos}) as consulta:
        resultado = AssociarCatalogoService().localizar_candidatos(p, cliente, 't')
    assert resultado['status'] == 'revisao'
    assert consulta.call_count <= 4 and resultado['candidatos_unicos'] == 20


def test_busca_nao_tenta_fallback_apos_429(banco):
    _, p = banco
    cliente = BuscarOfertasMercadoLivreService()
    with patch.object(cliente, '_consultar', side_effect=ErroMercadoLivre(429)) as consulta:
        with pytest.raises(ErroMercadoLivre):
            AssociarCatalogoService().localizar_candidatos(p, cliente, 't')
    assert consulta.call_count == 1


def test_consulta_limpa_descricao_preserva_capacidade_e_variante():
    from types import SimpleNamespace
    p = SimpleNamespace(__tablename__='ssd', modelo='860 EVO [500 GB M.2 SATA]', fabricante='Samsung',
                        capacidade_gb=500, part_number=None)
    consultas = AssociarCatalogoService().consultas(p)
    assert consultas == ['Samsung 860 EVO 500GB', 'Samsung 860 EVO [500 GB M.2 SATA]']
    p.__tablename__='placa_video';p.modelo='RTX 4070 Ti SUPER';p.fabricante='ASUS'
    assert AssociarCatalogoService().consultas(p) == ['ASUS RTX 4070 Ti SUPER']


def test_catalogo_ambiguo_vira_pendencia_como_na_shopee(banco):
    from models import ProdutoPendente
    _,p=banco
    sem_mpn=produto(attributes=[{'id':'BRAND','value_name':'AMD'}])
    simulado=executar(p,prod=sem_mpn,ofertas=[anuncio('MLB77',5,300),anuncio('MLB78',6,250,'used')])
    assert ProdutoPendente.query.count()==0  # simulação não grava
    r=executar(p,prod=sem_mpn,ofertas=[anuncio('MLB77',5,300),anuncio('MLB78',6,250,'used')],simular=False)
    assert r['revisao']==1 and r['detalhes'][0]['ambiguas']==1 and r['detalhes'][0]['ambiguas_registradas']==1
    pendencia=ProdutoPendente.query.one()
    assert (pendencia.loja,pendencia.produto_id_loja,pendencia.status)==('mercado_livre','MLB77','em_revisao')
    assert pendencia.dados_originais['catalogo']['id']==CAT and pendencia.dados_originais['anuncio']['price']=='300.00'
    assert [c['peca'] for c in pendencia.candidatos]==[f'processador:{p.id}']
    assert Oferta.query.filter(Oferta.loja!='kabum').count()==0
    # repetir não duplica
    executar(p,prod=sem_mpn,ofertas=[anuncio('MLB77',5,300)],simular=False)
    assert ProdutoPendente.query.count()==1


def test_catalogo_ambiguo_cujo_anuncio_ja_e_oferta_nao_quebra(banco):
    from models import ProdutoPendente
    _,p=banco
    sem_mpn=produto(attributes=[{'id':'BRAND','value_name':'AMD'}])
    db.session.add(Oferta(loja='mercado_livre',produto_id_loja='MLB77',vendedor_id='5',url='https://x/MLB77',
                          preco=Decimal('300.00'),tabela_peca='processador',peca_id=p.id,ativa=True))
    db.session.commit()
    r=executar(p,prod=sem_mpn,ofertas=[anuncio('MLB77',5,300)],simular=False)
    assert r['detalhes'][0]['ambiguas_registradas']==0
    assert ProdutoPendente.query.count()==0


def test_catalogo_sem_ofertas_404_na_fila_nao_derruba_a_tarefa(banco):
    from services.marketplace_service.erros import FalhaMarketplace
    _,p=banco
    prod=produto()
    def api(self,path,token,params=None):
        if path=='/products/search': return {'paging':{'total':1},'results':[prod]}
        if path==f'/products/{CAT}': return prod
        raise FalhaMarketplace(206)  # /items: na fila o 404 chega como FalhaMarketplace
    with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',api),patch('services.mercadolivre_service.atualizar_ofertas_service.TokenMercadoLivreService') as tokens:
        tokens.return_value.executar.return_value='token'
        r=Service().executar(categoria='processador',peca_id=p.id,simular=False)
    assert r['falhas']==0 and r['revisao']==1 and not r['interrompido']
