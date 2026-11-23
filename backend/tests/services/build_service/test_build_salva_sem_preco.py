from datetime import datetime

import pytest
from flask import Flask

from models import db, Oferta, PlacaVideo, Usuario, BuildSalva

AGORA = datetime(2026, 11, 17, 12, 0)


@pytest.fixture
def banco(tmp_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path / 'sem_preco.db'}"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.engine.dispose()


def placa(codigo, com_oferta):
    peca = PlacaVideo(status_validacao='aprovado', fabricante='NVIDIA', modelo=f'GeForce GTX 1050 Ti {codigo}',
                      memoria_gb=4, consumo_energia=75)
    db.session.add(peca)
    db.session.commit()
    if com_oferta:
        db.session.add(Oferta(tabela_peca='placa_video', peca_id=peca.id, loja='kabum', produto_id_loja=str(codigo),
                              vendedor_id='', url=f'https://www.kabum.com.br/produto/{codigo}/placa',
                              preco=1000, esgotado=False, ativa=True, preco_atualizado_em=AGORA, consultado_em=AGORA))
        db.session.commit()
    return peca


def test_peca_sem_oferta_nao_derruba_a_build_e_fica_fora_do_total(banco):
    usuario = Usuario(nome='Teste', email='teste@example.com')
    db.session.add(usuario)
    db.session.commit()
    com_preco, sem_preco = placa(1062024, True), placa(1062025, False)
    build = BuildSalva(usuario_id=usuario.id, estado={
        'titulo': 'Build', 'componentes': {'placa_video': {'id': com_preco.id, 'quantidade': 1}}})
    outra = BuildSalva(usuario_id=usuario.id, estado={
        'titulo': 'Build 2', 'componentes': {'placa_video': {'id': sem_preco.id, 'quantidade': 1}}})
    db.session.add_all([build, outra])
    db.session.commit()
    assert build.to_dict()['preco_total'] == 1000
    dados = outra.to_dict()
    assert dados['preco_total'] == 0
    assert dados['componentes'][0]['preco'] is None
