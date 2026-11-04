from datetime import datetime

import pytest
from flask import Flask
from sqlalchemy import MetaData, Table, UniqueConstraint, inspect, text
from sqlalchemy.exc import IntegrityError
from models import db, SSD, Oferta, ProdutoPendente, HistoricoOferta, Usuario
from migrations.catalogo_automatizado import preparar_catalogo_automatizado


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        yield app
        db.session.remove()
        db.engine.dispose()


def legado(modelo):
    campos = {'status_validacao', 'validacao_motivo', 'validado_em'}
    t = Table(modelo.__tablename__, MetaData(), *[c._copy() for c in modelo.__table__.columns if c.name not in campos])
    if modelo is Oferta:
        t.append_constraint(UniqueConstraint('loja', 'produto_id_loja', 'vendedor_id', name='uq_oferta_loja_produto_vendedor'))
    t.create(db.engine)
    return t


def dados_ssd(**extras):
    return dict(fabricante='Teste', modelo='SSD 500', consumo_energia=4, preco=100,
                capacidade_gb=500, tipo='NVMe', interface='PCIe 4.0', esgotado=False, **extras)


def test_migracao_preserva_usuarios_pecas_ofertas_historico_e_nao_publica_novas(banco):
    ssd, ofertas = legado(SSD), legado(Oferta)
    Usuario.__table__.create(db.engine)
    HistoricoOferta.__table__.create(db.engine)
    with db.engine.begin() as conn:
        conn.execute(ssd.insert().values(id=42, **dados_ssd()))
        conn.execute(ofertas.insert().values(id=9, tabela_peca='ssd', peca_id=42, loja='mercado_livre', produto_id_loja='MLB1', vendedor_id='7', url='https://example.test', preco=100))
    db.session.add_all([Usuario(nome='Preservado', email='teste@example.test', senha='hash'), HistoricoOferta(oferta_id=9, preco=100, coletado_em=datetime(2026,11,3))])
    db.session.commit()
    assert preparar_catalogo_automatizado()['alteracoes']
    assert 'status_validacao' not in {c['name'] for c in inspect(db.engine).get_columns('ssd')}
    assert not inspect(db.engine).has_table('produto_pendente')
    preparar_catalogo_automatizado(simular=False)
    assert preparar_catalogo_automatizado()['alteracoes'] == []
    assert db.session.get(SSD,42).status_validacao is None
    assert SSD.listar_publicadas()[0].id == 42
    assert Oferta.query.one().id == 9 and HistoricoOferta.query.one().oferta_id == 9
    assert Usuario.query.one().nome == 'Preservado'
    assert ProdutoPendente.query.count() == 0
    with db.engine.begin() as conn:
        conn.execute(ssd.insert().values(id=43, **dados_ssd()))
    assert db.session.get(SSD,43).status_validacao == 'pendente'
    assert [p.id for p in SSD.listar_publicadas()] == [42]
    assert {'ix_ssd_nome','ix_ssd_part_number','ix_ssd_publicacao'} <= {i['name'] for i in inspect(db.engine).get_indexes('ssd')}


def test_duplicatas_bloqueiam_todo_plano_sem_excluir(banco):
    legado(SSD)
    t = legado(Oferta)
    with db.engine.begin() as conn:
        for vendedor in ['1','2']:
            conn.execute(t.insert().values(tabela_peca='ssd', peca_id=1, loja='mercado_livre', produto_id_loja='MLB1', vendedor_id=vendedor, url='https://example.test'))
    with pytest.raises(ValueError, match='duplicadas'):
        preparar_catalogo_automatizado(simular=False)
    assert not inspect(db.engine).has_table('produto_pendente')
    assert 'status_validacao' not in {c['name'] for c in inspect(db.engine).get_columns('ssd')}
    with db.engine.connect() as conn:
        assert conn.execute(text('SELECT COUNT(*) FROM oferta')).scalar_one() == 2


def test_novas_pecas_fora_da_publicacao_e_selecao_ate_aprovacao(banco):
    SSD.__table__.create(db.engine)
    p = SSD(**dados_ssd())
    db.session.add(p);db.session.commit()
    assert p.status_validacao == 'pendente' and not p.publicavel
    assert SSD.listar_publicadas() == SSD.listar_candidatos_disponiveis(200) == []
    p.status_validacao = 'aprovado';db.session.commit()
    assert SSD.listar_publicadas() == SSD.listar_candidatos_disponiveis(200) == [p]
    p.status_validacao = 'rejeitado';db.session.commit()
    assert SSD.listar_publicadas() == []
    with pytest.raises(ValueError):p.status_validacao = 'inventado'


def test_pendencia_idempotente_por_identidade_independe_do_vendedor(banco):
    preparar_catalogo_automatizado(simular=False)
    dados = dict(loja='mercado_livre', produto_id_loja='MLB2', titulo='Não identificado', url='https://example.test', dados_originais={'id':'MLB2'}, coletado_em=datetime(2026,11,3))
    p = ProdutoPendente(**dados)
    db.session.add(p);db.session.commit()
    assert p.status == 'pendente'
    assert ProdutoPendente.buscar_por_anuncio('mercado_livre','MLB2') == p
    assert ProdutoPendente.listar_para_revisao() == [p]
    db.session.add(ProdutoPendente(**dados, vendedor_id='outro'))
    with pytest.raises(IntegrityError):db.session.commit()
    db.session.rollback()
    assert ProdutoPendente.query.count() == 1 and Oferta.query.count() == 0


def test_comando_simula_por_padrao_e_aplica_explicitamente(banco):
    from commands.banco import registrar_comandos_banco
    registrar_comandos_banco(banco)
    legado(SSD)
    runner = banco.test_cli_runner()
    resultado = runner.invoke(args=['catalogo-preparar'])
    assert resultado.exit_code == 0 and '"simulacao": true' in resultado.output
    assert not inspect(db.engine).has_table('produto_pendente')
    resultado = runner.invoke(args=['catalogo-preparar', '--aplicar'])
    assert resultado.exit_code == 0
    resultado = runner.invoke(args=['catalogo-preparar'])
    assert resultado.exit_code == 0 and '"alteracoes": []' in resultado.output


def test_status_e_identidade_invalidos_rejeitados_no_banco(banco):
    preparar_catalogo_automatizado(simular=False)
    for extras in ({'status': 'aprovado'}, {'loja': ''}):
        dados = dict(loja='mercado_livre', produto_id_loja='MLB2', titulo='Produto',
                     url='https://example.test', dados_originais={}, coletado_em=datetime(2026,11,3))
        db.session.add(ProdutoPendente(**{**dados, **extras}))
        with pytest.raises(IntegrityError):
            db.session.commit()
        db.session.rollback()
    for limite in (0, 201, True):
        with pytest.raises(ValueError):
            ProdutoPendente.listar_para_revisao(limite=limite)


def test_migracao_formato_ram_preserva_dados_e_nao_inventa_dimm(banco):
    from models import MemoriaRAM
    MemoriaRAM.__table__.create(db.engine)
    db.session.add(MemoriaRAM(fabricante='Teste',modelo='Memória',capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1,consumo_energia=5,preco=100))
    db.session.commit();db.session.remove()
    with db.engine.begin() as c:c.execute(text('ALTER TABLE memoria_ram DROP COLUMN formato'))
    assert any('`formato`' in p.get('sql','') for p in preparar_catalogo_automatizado()['alteracoes'])
    preparar_catalogo_automatizado(simular=False)
    assert MemoriaRAM.query.one().formato is None and MemoriaRAM.query.count()==1
    assert preparar_catalogo_automatizado()['alteracoes']==[]
