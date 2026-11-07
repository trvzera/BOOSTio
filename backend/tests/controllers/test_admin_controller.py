import time
from datetime import datetime
from decimal import Decimal

import pytest
from flask import Flask
from flask_login import LoginManager

from controllers.admin_controller import admin_bp
from models import db, Usuario, Processador, ProdutoPendente, Oferta, ControleColeta
from services.shopee_service.normalizar_produto_service import NormalizarProdutoShopeeService
from dataclasses import asdict

AGORA = int(time.time())


def anuncio(item, shop, titulo, preco='900.00'):
    return dict(itemId=str(item), shopId=str(shop), productName=titulo, priceMin=preco, priceMax=preco,
                productLink=f'https://shopee.com.br/product/{shop}/{item}', offerLink=None, productCatIds=[101950],
                periodStartTime=AGORA - 3600, periodEndTime=AGORA + 3600)


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config.update(SECRET_KEY='teste', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:')
    db.init_app(app)
    login = LoginManager(app)
    login.user_loader(lambda ident: Usuario.buscar_por_sessao(ident))
    app.register_blueprint(admin_bp)
    with app.app_context():
        db.create_all()
        ControleColeta.inicializar()
        admin = Usuario(nome='Admin', email='admin@teste.com', senha='x', verificado=True, administrador=True)
        comum = Usuario(nome='Comum', email='comum@teste.com', senha='x', verificado=True)
        p5500 = Processador(fabricante='AMD', modelo='Ryzen 5 5500', soquete='AM4', nucleo=6, thread=12, clockbase=3.6,
                            clockmax=4.2, consumo_energia=65, status_validacao='aprovado')
        p5600 = Processador(fabricante='AMD', modelo='Ryzen 5 5600', soquete='AM4', nucleo=6, thread=12, clockbase=3.5,
                            clockmax=4.4, consumo_energia=65, status_validacao='aprovado')
        db.session.add_all([admin, comum, p5500, p5600])
        db.session.commit()
        yield app, admin, comum, p5500, p5600
        db.session.remove()
        db.engine.dispose()


def entrar(app, usuario):
    cliente = app.test_client()
    with cliente.session_transaction() as sessao:
        sessao['_user_id'] = usuario.get_id()
        sessao['_fresh'] = True
    return cliente


def pendencia(p5500, p5600, loja='shopee', item=1, conflito_5600=False, **extras):
    bruto = anuncio(item, 10, 'Processador AMD Ryzen 5 AM4 6 Núcleos 12 Threads')
    produto, _ = NormalizarProdutoShopeeService().executar(bruto, 'processador')
    candidatos = [dict(peca=f'processador:{p5500.id}', percentual=75, conflitos=[], pendencias=['modelo_exato_nao_comprovado']),
                  dict(peca=f'processador:{p5600.id}', percentual=70, conflitos=['modelo_ou_sufixo_divergente'] if conflito_5600 else [],
                       pendencias=[])]
    p = ProdutoPendente(loja=loja, produto_id_loja=f'10:{item}', vendedor_id='10', titulo=produto.titulo, url=produto.fonte,
                        categoria_sugerida='processador', dados_originais={'normalizado': asdict(produto), 'anuncio': bruto},
                        candidatos=candidatos, status='em_revisao', motivo='Matching ambigua',
                        coletado_em=datetime(2026, 11, 7), **extras)
    db.session.add(p)
    db.session.commit()
    return p


def test_exige_login(banco):
    app, *_ = banco
    assert app.test_client().get('/admin/pendencias').status_code == 401
    assert app.test_client().post('/admin/pendencias/1/rejeitar').status_code == 401


def test_conta_comum_recebe_403_e_administrador_acessa(banco):
    app, admin, comum, *_ = banco
    comum_logado = entrar(app, comum)
    r = comum_logado.get('/admin/pendencias')
    assert r.status_code == 403 and r.get_json()['codigo'] == 'sem-permissao'
    assert comum_logado.get('/admin/pendencias/1').status_code == 403
    assert comum_logado.post('/admin/pendencias/1/rejeitar').status_code == 403
    assert comum_logado.post('/admin/pendencias/1/aceitar', json={'peca': 'processador:1'}).status_code == 403


def test_administrador_acessa(banco):
    app, admin, *_ = banco
    assert entrar(app, admin).get('/admin/pendencias').status_code == 200


def test_lista_filtra_e_pagina(banco):
    app, admin, _, p5500, p5600 = banco
    for i in range(1, 4):
        pendencia(p5500, p5600, item=i)
    pendencia(p5500, p5600, loja='mercado_livre', item=9)
    cliente = entrar(app, admin)
    d = cliente.get('/admin/pendencias?limite=2').get_json()
    assert d['total'] == 4 and len(d['pendencias']) == 2 and d['proximo'] == d['pendencias'][-1]['id']
    assert d['por_status'] == {'em_revisao': 4} and 'shopee' in d['lojas']
    assert [p['loja'] for p in cliente.get('/admin/pendencias?loja=mercado_livre').get_json()['pendencias']] == ['mercado_livre']
    assert cliente.get('/admin/pendencias?status=importado').get_json()['total'] == 0
    primeiro = d['pendencias'][0]
    assert primeiro['preco'] == {'minimo': 900.0, 'maximo': 900.0} and primeiro['total_candidatos'] == 2
    for ruim in ('status=x', 'loja=x', 'categoria=x', 'limite=0', 'limite=101', 'depois_id=-1', 'limite=abc'):
        assert cliente.get('/admin/pendencias?' + ruim).status_code == 400


def test_detalhe_mostra_candidatos_com_nome_da_peca(banco):
    app, admin, _, p5500, p5600 = banco
    p = pendencia(p5500, p5600)
    cliente = entrar(app, admin)
    d = cliente.get(f'/admin/pendencias/{p.id}').get_json()
    assert [(c['modelo'], c['percentual']) for c in d['candidatos']] == [('Ryzen 5 5500', 75), ('Ryzen 5 5600', 70)]
    assert cliente.get('/admin/pendencias/999').status_code == 404


def test_aceitar_grava_oferta_pelo_caminho_seguro_e_fecha_a_pendencia(banco):
    app, admin, _, p5500, p5600 = banco
    p = pendencia(p5500, p5600)
    cliente = entrar(app, admin)
    r = cliente.post(f'/admin/pendencias/{p.id}/aceitar', json={'peca': f'processador:{p5500.id}'})
    assert r.status_code == 200, r.get_json()
    oferta = Oferta.query.filter_by(loja='shopee').one()
    assert (oferta.tabela_peca, oferta.peca_id, oferta.produto_id_loja) == ('processador', p5500.id, '10:1')
    assert oferta.preco == Decimal('900.00') and oferta.para_exibicao() is not None
    db.session.refresh(p)
    assert p.status == 'importado' and p.oferta_id == oferta.id
    assert p.evidencias['revisao_manual']['administrador_id'] == admin.id and p.evidencias['revisao_manual']['acao'] == 'aceitar'
    assert cliente.post(f'/admin/pendencias/{p.id}/aceitar', json={'peca': f'processador:{p5500.id}'}).status_code == 409


def test_aceitar_recusa_peca_fora_dos_candidatos_com_conflito_ou_loja_sem_suporte(banco):
    app, admin, _, p5500, p5600 = banco
    p = pendencia(p5500, p5600, conflito_5600=True)
    cliente = entrar(app, admin)
    for corpo in ({}, {'peca': 'processador:999'}, {'peca': f'processador:{p5600.id}'}, {'peca': 5}):
        assert cliente.post(f'/admin/pendencias/{p.id}/aceitar', json=corpo).status_code == 400
    ml = pendencia(p5500, p5600, loja='mercado_livre', item=2)
    r = cliente.post(f'/admin/pendencias/{ml.id}/aceitar', json={'peca': f'processador:{p5500.id}'})
    assert r.status_code == 409 and 'mercadolivre-vincular' in r.get_json()['erro']
    assert Oferta.query.count() == 0 and ProdutoPendente.query.filter_by(status='em_revisao').count() == 2


def test_aceitar_nao_rouba_anuncio_de_outra_peca(banco):
    app, admin, _, p5500, p5600 = banco
    p = pendencia(p5500, p5600)
    db.session.add(Oferta(tabela_peca='processador', peca_id=p5600.id, loja='shopee', produto_id_loja='10:1',
                          vendedor_id='10', url='https://shopee.com.br/product/10/1', preco=Decimal('500')))
    db.session.commit()
    r = entrar(app, admin).post(f'/admin/pendencias/{p.id}/aceitar', json={'peca': f'processador:{p5500.id}'})
    assert r.status_code == 400 and Oferta.query.filter_by(peca_id=p5500.id).count() == 0
    db.session.refresh(p)
    assert p.status == 'em_revisao'


def test_rejeitar_registra_quem_decidiu_e_nao_reabre(banco):
    app, admin, _, p5500, p5600 = banco
    p = pendencia(p5500, p5600)
    cliente = entrar(app, admin)
    r = cliente.post(f'/admin/pendencias/{p.id}/rejeitar', json={'motivo': 'Outro produto'})
    assert r.status_code == 200 and r.get_json()['status'] == 'rejeitado' and r.get_json()['motivo'] == 'Outro produto'
    db.session.refresh(p)
    assert p.evidencias['revisao_manual']['administrador_id'] == admin.id and p.revisado_em is not None
    assert cliente.post(f'/admin/pendencias/{p.id}/rejeitar').status_code == 400
    assert cliente.post('/admin/pendencias/999/rejeitar').status_code == 404
    outra = pendencia(p5500, p5600, item=2)
    assert cliente.post(f'/admin/pendencias/{outra.id}/rejeitar', json={'motivo': 'x' * 201}).status_code == 400
    assert cliente.post(f'/admin/pendencias/{outra.id}/rejeitar').get_json()['motivo'] == 'Rejeitada por um administrador'
