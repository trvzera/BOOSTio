import pytest
from flask import Flask
from sqlalchemy import update
from models import db, MemoriaRAM, Oferta, IdentidadeFabricante, VinculoMercadoLivre
from utils.identidade_peca import assinatura_peca


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def memoria(**extras):
    p = MemoriaRAM(**{**dict(fabricante='Kingston', modelo='KVR26N19S8/8', consumo_energia=5,
        preco=100, capacidade_gb=8, ddr='DDR4', frequencia_mhz=2666, quantidade_pentes=1,
        kabum_external='https://www.kabum.com.br/produto/175110/teste', status_validacao='legado'), **extras})
    db.session.add(p)
    db.session.commit()
    return p


def legada(p, codigo):
    db.session.execute(update(MemoriaRAM).where(MemoriaRAM.id == p.id).values(part_number=codigo, referencia_interna=None))
    db.session.commit()
    db.session.refresh(p)


def test_novo_cadastro_separa_codigo_sem_inventar_mpn(banco):
    p = memoria(part_number='SEED-RAM-1')
    assert p.part_number is None and p.referencia_interna == 'SEED-RAM-1'
    p.part_number = 'KVR26N19S8/8'
    assert p.referencia_interna == 'SEED-RAM-1'


def test_simulacao_preserva_banco_e_aplicar_e_idempotente(banco):
    p = memoria()
    legada(p, 'KABUM-175110')
    antes = p.id, p.preco, p.esgotado, p.kabum_external
    r = p.separar_identificadores()
    assert r['alterada'] and r['oferta'] == 'criada'
    assert Oferta.query.count() == 0
    assert p.part_number == 'KABUM-175110' and p.referencia_interna is None
    p.separar_identificadores(simular=False)
    assert p.part_number is None and p.referencia_interna == 'KABUM-175110'
    o = Oferta.query.one()
    assert o.loja == 'kabum' and o.produto_id_loja == '175110'
    assert o.preco is None and o.esgotado is None and o.url_afiliado is None
    assert (p.id, p.preco, p.esgotado, p.kabum_external) == antes
    r = p.separar_identificadores(simular=False)
    assert not r['alterada'] and r['oferta'] == 'inalterada' and Oferta.query.count() == 1


def test_mpn_revisado_e_vinculo_existente_sao_preservados(banco):
    p = memoria()
    legada(p, 'KABUM-175110')
    assinatura = assinatura_peca(p)
    db.session.add(IdentidadeFabricante(tabela_peca='memoria_ram', peca_id=p.id, assinatura_peca=assinatura,
        mpn='KVR26N19S8/8', fonte='https://www.kingston.com/teste', especificacoes={'capacidade_gb': 8}))
    db.session.add(VinculoMercadoLivre(tabela_peca='memoria_ram', peca_id=p.id, assinatura_peca=assinatura,
        assinatura_catalogo='a'*64, catalogo_id='MLB123', criterio='revisado'))
    db.session.commit()
    p.separar_identificadores(simular=False)
    assert p.part_number == 'KVR26N19S8/8'
    assert IdentidadeFabricante.buscar(p).mpn == p.part_number
    assert VinculoMercadoLivre.query.one().assinatura_peca == assinatura_peca(p)
    assert VinculoMercadoLivre.query.one().catalogo_id == 'MLB123'


def test_id_de_loja_contraditorio_fica_em_revisao(banco):
    p = memoria()
    legada(p, 'KABUM-999')
    r = p.separar_identificadores(simular=False)
    assert r['oferta'] == 'revisao' and Oferta.query.count() == 0
    assert p.part_number is None and p.referencia_interna == 'KABUM-999'


def test_seed_sem_anuncio_nao_cria_oferta_ficticia(banco):
    p = memoria(part_number='REDE-INTERNO', kabum_external=None)
    r = p.separar_identificadores(simular=False)
    assert r['oferta'] == 'sem_anuncio' and Oferta.query.count() == 0
