import pytest
from flask import Flask
from sqlalchemy import text

from commands.usuarios import registrar_comandos_usuarios
from migrations.administrador_usuario import preparar_administrador_usuario
from models import db, Usuario


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    registrar_comandos_usuarios(app)
    with app.app_context():
        db.create_all()
        db.session.add_all([Usuario(nome='Ana', email='ana@teste.com', senha='x', verificado=True),
                            Usuario(nome='Beto', email='beto@teste.com', senha='x', verificado=False)])
        db.session.commit()
        yield app
        db.session.remove()
        db.engine.dispose()


def rodar(app, *args):
    return app.test_cli_runner().invoke(args=list(args))


def test_promover_encerra_sessoes_e_remover_retira_o_papel(app):
    ana = Usuario.buscar_por_email('ana@teste.com')
    antes = ana.get_id()
    r = rodar(app, 'usuario-promover-admin', '--email', 'ana@teste.com')
    assert r.exit_code == 0 and '"alterada": true' in r.output
    db.session.refresh(ana)
    assert ana.administrador and ana.get_id() != antes and Usuario.buscar_por_sessao(antes) is None
    assert ana.to_dict()['administrador'] is True
    assert '"alterada": false' in rodar(app, 'usuario-promover-admin', '--email', 'ana@teste.com').output
    assert 'ana@teste.com' in rodar(app, 'usuario-listar-admins').output
    assert rodar(app, 'usuario-remover-admin', '--email', 'ana@teste.com').exit_code == 0
    db.session.refresh(ana)
    assert not ana.administrador and 'ana@teste.com' not in rodar(app, 'usuario-listar-admins').output


def test_recusa_conta_inexistente_ou_nao_verificada(app):
    assert rodar(app, 'usuario-promover-admin', '--email', 'nao@teste.com').exit_code != 0
    r = rodar(app, 'usuario-promover-admin', '--email', 'beto@teste.com')
    assert r.exit_code != 0 and 'verificado' in r.output
    assert not Usuario.buscar_por_email('beto@teste.com').administrador


def test_migracao_adiciona_a_coluna_sem_mexer_nas_contas_e_e_repetivel(app):
    db.session.execute(text('ALTER TABLE usuario DROP COLUMN administrador'))
    db.session.commit()
    simulada = preparar_administrador_usuario()
    assert len(simulada['alteracoes']) == 1
    assert 'administrador' not in {c['name'] for c in db.inspect(db.engine).get_columns('usuario')}
    preparar_administrador_usuario(simular=False)
    assert preparar_administrador_usuario()['alteracoes'] == []
    assert Usuario.query.count() == 2 and not any(u.administrador for u in Usuario.query)
