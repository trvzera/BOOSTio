import pytest
from flask import Flask

from models import db, Build, BuildSalva, SSD, Usuario


@pytest.fixture
def banco(tmp_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path / 'legadas.db'}"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.engine.dispose()


def test_copia_builds_antigas_uma_vez(banco):
    usuario = Usuario(nome='Teste', email='teste@example.com')
    ssd = SSD(status_validacao='aprovado', fabricante='Kingston', modelo='NV2 1TB', capacidade_gb=1000, interface='NVMe')
    db.session.add_all([usuario, ssd])
    db.session.commit()
    antiga = Build(usuario_id=usuario.id, nome='Antiga', placa_mae_id=99, processador_id=99, memoria_ram_id=99,
                   fonte_id=99, gabinete_id=99, ssd_id=ssd.id, quantidade_ssd=2)
    db.session.add(antiga)
    db.session.commit()

    assert BuildSalva.migrar_legadas() == 1
    assert BuildSalva.migrar_legadas() == 0
    copia = BuildSalva.query.one()
    assert copia.usuario_id == usuario.id and copia.build_original_id == antiga.id
    assert copia.estado['titulo'] == 'Antiga'
    assert copia.estado['componentes'] == {'ssd': [{'id': ssd.id, 'quantidade': 2}]}
