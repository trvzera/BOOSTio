from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from sqlalchemy import String

from models import db
from migrations import vinculos_criterio
from migrations.vinculos_criterio import preparar_vinculos_criterio


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def test_sqlite_nao_altera_nada(app):
    assert preparar_vinculos_criterio()['alteracoes'] == []


def _mysql(tamanho):
    inspetor = MagicMock()
    inspetor.has_table.return_value = True
    inspetor.get_columns.return_value = [{'name': 'criterio', 'type': String(tamanho)}]
    motor = MagicMock()
    motor.dialect.name = 'mysql'
    return inspetor, motor


def test_mysql_simula_e_aplica_o_alargamento(app):
    inspetor, motor = _mysql(20)
    with patch.object(vinculos_criterio, 'inspect', return_value=inspetor), \
            patch.object(vinculos_criterio, 'db', MagicMock(engine=motor)):
        simulado = preparar_vinculos_criterio(simular=True)
        assert 'VARCHAR(100) NOT NULL' in simulado['alteracoes'][0]
        motor.begin.assert_not_called()
        aplicado = preparar_vinculos_criterio()
        assert aplicado['alteracoes'] == simulado['alteracoes']
        motor.begin.assert_called_once()


def test_mysql_ja_alargado_e_repetivel(app):
    inspetor, motor = _mysql(100)
    with patch.object(vinculos_criterio, 'inspect', return_value=inspetor), \
            patch.object(vinculos_criterio, 'db', MagicMock(engine=motor)):
        assert preparar_vinculos_criterio()['alteracoes'] == []
        motor.begin.assert_not_called()
