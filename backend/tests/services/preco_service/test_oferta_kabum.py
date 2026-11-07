from datetime import datetime
from decimal import Decimal

import pytest
from flask import Flask
from sqlalchemy import text

from models import db, Oferta, HistoricoOferta, PlacaVideo
from repositories.ofertas_kabum_repository import definir_link, gravar_cotacao_inicial
from services.peca_service.migrar_ofertas_kabum_service import MigrarOfertasKabumService

URL = 'https://www.kabum.com.br/produto/123/placa'
DATA = datetime(2026, 11, 1, 10)


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.engine.dispose()


def nova_placa():
    p = PlacaVideo(fabricante='Marca', modelo='GPU', memoria_gb=8, consumo_energia=100, status_validacao='aprovado')
    db.session.add(p)
    db.session.flush()
    return p


def test_peca_nao_guarda_preco_nem_link():
    colunas = set(PlacaVideo.__table__.columns.keys())
    assert not colunas & {'preco', 'esgotado', 'preco_atualizado_em', 'kabum_external'}


def test_preco_da_peca_vem_da_menor_oferta_disponivel(banco):
    p = nova_placa()
    gravar_cotacao_inicial(p, URL, 900, False, DATA)
    banco.session.add_all([
        Oferta(tabela_peca='placa_video', peca_id=p.id, loja='mercado_livre', produto_id_loja='MLB1',
               vendedor_id='1', url='https://produto.mercadolivre.com.br/MLB-1-x', preco=Decimal('800'), esgotado=False),
        Oferta(tabela_peca='placa_video', peca_id=p.id, loja='mercado_livre', produto_id_loja='MLB2',
               vendedor_id='2', url='https://produto.mercadolivre.com.br/MLB-2-x', preco=Decimal('500'), esgotado=True),
        Oferta(tabela_peca='placa_video', peca_id=p.id, loja='mercado_livre', produto_id_loja='MLB3',
               vendedor_id='3', url='https://produto.mercadolivre.com.br/MLB-3-x', preco=Decimal('300'), ativa=False)])
    banco.session.commit()
    banco.session.refresh(p)
    assert p.preco == 800 and p.esgotado is False
    assert p.kabum_external == URL
    assert PlacaVideo.listar_candidatos_disponiveis(850) == [p]
    assert PlacaVideo.listar_candidatos_disponiveis(700) == []


def test_troca_de_link_desativa_oferta_antiga_sem_apagar_historico(banco):
    p = nova_placa()
    antiga = gravar_cotacao_inicial(p, URL, 900, False, DATA)
    banco.session.add(HistoricoOferta(oferta_id=antiga.id, preco=Decimal('900'), esgotado=False, coletado_em=DATA))
    banco.session.commit()
    nova = definir_link(p, 'https://www.kabum.com.br/produto/456/outra')
    banco.session.commit()
    banco.session.refresh(p)
    assert antiga.ativa is False and nova.ativa and nova.preco is None
    assert p.kabum_external.endswith('/456/outra') and p.preco is None
    assert HistoricoOferta.query.filter_by(oferta_id=antiga.id).count() == 1
    definir_link(p, None)
    banco.session.commit()
    banco.session.refresh(p)
    assert p.kabum_external is None


def test_anuncio_de_outra_peca_nao_e_reaproveitado(banco):
    a, b = nova_placa(), nova_placa()
    gravar_cotacao_inicial(a, URL, 900, False, DATA)
    with pytest.raises(ValueError, match='outra peça'):
        definir_link(b, URL)


def test_migracao_copia_colunas_antigas_e_e_repetivel(banco):
    p, sem_link = nova_placa(), nova_placa()
    for coluna, tipo in (('kabum_external', 'TEXT'), ('preco', 'FLOAT'), ('esgotado', 'BOOLEAN'), ('preco_atualizado_em', 'DATETIME')):
        banco.session.execute(text(f'ALTER TABLE placa_video ADD COLUMN {coluna} {tipo}'))
    banco.session.execute(text("UPDATE placa_video SET kabum_external=:u, preco=1234.5, esgotado=0, preco_atualizado_em='2026-11-01 10:00:00' WHERE id=:i"),
                          {'u': URL, 'i': p.id})
    banco.session.execute(text('DROP TABLE historico_preco'))
    banco.session.execute(text('CREATE TABLE historico_preco (id INTEGER PRIMARY KEY, tabela_peca TEXT, peca_id INT, loja TEXT, produto_id_loja TEXT, preco FLOAT, esgotado BOOLEAN, coletado_em DATETIME)'))
    banco.session.execute(text("INSERT INTO historico_preco VALUES (1,'placa_video',:i,'kabum','123',1300,0,'2026-10-30 09:00:00'), (2,'placa_video',:i,'kabum','123',NULL,1,'2026-10-31 09:00:00')"), {'i': p.id})
    banco.session.commit()
    simulado = MigrarOfertasKabumService().executar(simular=True)
    assert simulado['criadas'] == 1 and simulado['sem_link'] == 1 and Oferta.query.count() == 0
    r = MigrarOfertasKabumService().executar(simular=False)
    assert (r['criadas'], r['historicos']) == (1, 1)
    banco.session.refresh(p)
    assert p.preco == 1234.5 and p.esgotado is False and p.kabum_external == URL
    assert p.preco_atualizado_em == DATA
    assert HistoricoOferta.query.one().preco == Decimal('1300.00')
    r = MigrarOfertasKabumService().executar(simular=False)
    assert (r['criadas'], r['inalteradas'], r['historicos']) == (0, 1, 0)
    assert Oferta.query.count() == 1 and sem_link.preco is None
