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


def test_mysql_comandos_para_colunas_antigas_obrigatorias_e_aspas_de_tabela():
    from sqlalchemy import Boolean, Float, Text
    from sqlalchemy.dialects import mysql
    colunas = [{'name': 'preco', 'type': Float(), 'nullable': False},
               {'name': 'esgotado', 'type': Boolean(), 'nullable': False},
               {'name': 'kabum_external', 'type': Text(), 'nullable': True},
               {'name': 'modelo', 'type': Text(), 'nullable': False}]
    comandos = MigrarOfertasKabumService.comandos_colunas_opcionais(mysql.dialect(), 'placa_video', colunas)
    assert comandos == ['ALTER TABLE placa_video MODIFY preco FLOAT NULL',
                        'ALTER TABLE placa_video MODIFY esgotado BOOL NULL']
    assert mysql.dialect().identifier_preparer.quote('order') == '`order`'


def test_shopee_conta_como_disponivel_mesmo_sem_informar_estoque(banco):
    p = nova_placa()
    banco.session.add(Oferta(tabela_peca='placa_video', peca_id=p.id, loja='shopee', produto_id_loja='10:2',
                             vendedor_id='10', url='https://shopee.com.br/product/10/2', preco=Decimal('700'), esgotado=None))
    banco.session.commit()
    banco.session.refresh(p)
    assert p.preco == 700 and p.esgotado is False
    assert PlacaVideo.listar_candidatos_disponiveis(800) == [p]
    # Mercado Livre sem estoque conhecido continua não entrando nas builds.
    banco.session.add(Oferta(tabela_peca='placa_video', peca_id=p.id, loja='mercado_livre', produto_id_loja='MLB9',
                             vendedor_id='1', url='https://produto.mercadolivre.com.br/MLB-9-x', preco=Decimal('500'), esgotado=None))
    banco.session.commit()
    banco.session.refresh(p)
    assert p.preco == 700


def test_peca_sem_oferta_com_preco_nao_existe_para_o_usuario(banco):
    from models import Processador
    from services.build_service.listar_catalogo_build_service import ListarCatalogoBuildService
    sem_oferta, sem_preco, inativa, com_preco = nova_placa(), nova_placa(), nova_placa(), nova_placa()
    definir_link(sem_preco, 'https://www.kabum.com.br/produto/201/sem-preco')
    gravar_cotacao_inicial(inativa, 'https://www.kabum.com.br/produto/202/inativa', 800, False, DATA)
    gravar_cotacao_inicial(com_preco, 'https://www.kabum.com.br/produto/203/ok', 700, False, DATA)
    banco.session.commit()
    definir_link(inativa, None)
    banco.session.commit()
    esperado = [com_preco.id]
    assert [p.id for p in PlacaVideo.listar_publicadas()] == esperado
    assert [p.id for p in PlacaVideo.consulta_para_montagem().all()] == esperado
    assert [p.id for p in PlacaVideo.listar_candidatos_disponiveis(5000)] == esperado
    for peca in (sem_oferta, sem_preco, inativa):
        assert PlacaVideo.buscar_publicada_por_id(peca.id) is None
    assert PlacaVideo.buscar_publicada_por_id(com_preco.id) is not None
    catalogo = ListarCatalogoBuildService().executar()
    assert [p['id'] for p in catalogo] == [f'placa_video:{com_preco.id}']
    # A marca continua conhecida para reconhecer anúncios, mesmo sem preço.
    assert PlacaVideo.fabricantes_para_descoberta() == ['Marca']


def test_montagem_manual_recusa_peca_sem_preco_e_aceita_a_com_preco(banco):
    from services.validacoes_service.validar_estado_build_service import validar_estado
    sem_preco, com_preco = nova_placa(), nova_placa()
    gravar_cotacao_inicial(com_preco, 'https://www.kabum.com.br/produto/301/ok', 700, False, DATA)
    banco.session.commit()
    with pytest.raises(ValueError, match='Peça não encontrada no catálogo'):
        validar_estado({'titulo': 'Teste', 'componentes': {'placa_video': {'id': sem_preco.id, 'quantidade': 1}}})
    estado = validar_estado({'titulo': 'Teste', 'componentes': {'placa_video': {'id': com_preco.id, 'quantidade': 1}}})
    assert estado['componentes']['placa_video']['id'] == com_preco.id
