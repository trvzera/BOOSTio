import pytest
from flask import Flask

from commands.catalogo import registrar_comandos_catalogo
from models import db, Oferta, Processador
from services.catalogo_service.aprovar_em_lote_service import AprovarEmLoteService, MOTIVO


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    registrar_comandos_catalogo(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def cpu(modelo='Ryzen 5 5500', fabricante='AMD', **extras):
    base = dict(fabricante=fabricante, modelo=modelo, soquete='AM4', nucleo=6, thread=12, clockbase=3.6,
                clockmax=4.2, consumo_energia=65, status_validacao='em_revisao')
    p = Processador(**{**base, **extras})
    db.session.add(p)
    db.session.commit()
    return p


def test_aprova_so_quem_passa_nas_regras_e_explica_as_recusas(banco):
    ok = cpu()
    generico = cpu(modelo='Processador Gamer')
    incompleta = cpu(modelo='Ryzen 7 5700', soquete=None)
    reprovada = cpu(modelo='Ryzen 9 5900', ficha_montagem_validada=False)
    sem_marca = cpu(modelo='Core i5 12400', fabricante='')
    dup_a, dup_b = cpu(modelo='Ryzen 5 5600'), cpu(modelo='ryzen 5 5600')
    r = AprovarEmLoteService().executar(categoria='processador', simular=True)
    c = r['categorias']['processador']
    assert c['em_revisao'] == 7 and c['aprovaveis'] == 1 and c['aprovadas'] == 0
    assert c['recusadas'] == {'modelo_generico': 1, 'ficha_incompleta': 1, 'ficha_reprovada': 1,
                              'identidade_incompleta': 1, 'possivel_duplicata': 2}
    db.session.refresh(ok)
    assert ok.status_validacao == 'em_revisao'  # simulação não grava
    r = AprovarEmLoteService().executar(categoria='processador', simular=False)
    assert r['total_aprovadas'] == 1
    for p in (ok, generico, incompleta, reprovada, sem_marca, dup_a, dup_b):
        db.session.refresh(p)
    assert ok.status_validacao == 'aprovado' and ok.validacao_motivo == MOTIVO and ok.validado_em is not None
    assert all(p.status_validacao == 'em_revisao' for p in (generico, incompleta, reprovada, sem_marca, dup_a, dup_b))


def test_part_number_repetido_e_duplicata_e_exigir_identificador(banco):
    a = cpu(modelo='Ryzen 5 5500', part_number='100-000000457')
    b = cpu(modelo='Ryzen 5 5500X', part_number='100-000000457')
    c = cpu(modelo='Ryzen 5 5600')
    r = AprovarEmLoteService().executar(categoria='processador')
    assert r['categorias']['processador']['recusadas'] == {'possivel_duplicata': 2}
    assert r['categorias']['processador']['aprovaveis'] == 1 and r['categorias']['processador']['sem_identificador'] == 1
    r = AprovarEmLoteService().executar(categoria='processador', exigir_identificador=True)
    assert r['categorias']['processador']['recusadas']['sem_part_number'] == 1


def test_limite_sorteia_amostra_reproduzivel_e_nao_mexe_em_peca_ja_decidida(banco):
    pecas = [cpu(modelo=f'Ryzen 5 {5000 + i}') for i in range(10)]
    ja = cpu(modelo='Ryzen 7 9999', status_validacao='rejeitado')
    r1 = AprovarEmLoteService().executar(categoria='processador', limite=3, semente=7, simular=False)
    assert r1['total_aprovadas'] == 3 and r1['total_aprovaveis'] == 10
    aprovadas = {p.id for p in pecas if db.session.get(Processador, p.id).status_validacao == 'aprovado'}
    assert len(aprovadas) == 3
    db.session.refresh(ja)
    assert ja.status_validacao == 'rejeitado'


def test_reverter_so_o_que_a_regra_aprovou_e_ainda_nao_tem_oferta(banco):
    a, b = cpu(modelo='Ryzen 5 5500'), cpu(modelo='Ryzen 5 5600')
    AprovarEmLoteService().executar(categoria='processador', simular=False)
    db.session.add(Oferta(tabela_peca='processador', peca_id=b.id, loja='shopee', produto_id_loja='1:1', vendedor_id='1',
                          url='https://shopee.com.br/product/1/1', preco=500, esgotado=None))
    humana = cpu(modelo='Ryzen 7 5800', status_validacao='aprovado')
    db.session.commit()
    simulado = AprovarEmLoteService().reverter(categoria='processador')
    assert simulado['categorias']['processador'] == 1
    AprovarEmLoteService().reverter(categoria='processador', simular=False)
    for p in (a, b, humana):
        db.session.refresh(p)
    assert (a.status_validacao, b.status_validacao, humana.status_validacao) == ('em_revisao', 'aprovado', 'aprovado')


def test_comando_simula_por_padrao(banco):
    cpu()
    r = banco.test_cli_runner().invoke(args=['catalogo-aprovar-lote', '--categoria', 'processador'])
    assert r.exit_code == 0 and '"simulacao": true' in r.output and '"aprovaveis": 1' in r.output
    r = banco.test_cli_runner().invoke(args=['catalogo-aprovar-lote', '--categoria', 'inexistente'])
    assert r.exit_code != 0
