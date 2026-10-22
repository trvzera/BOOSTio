import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

from flask import Flask
from sqlalchemy import inspect, text

from models import db, Usuario
from commands.banco import registrar_comandos_banco
from commands.precos import registrar_comandos_precos


def test_importar_app_e_wsgi_nao_cria_banco_nem_coleta(tmp_path):
    backend = Path(__file__).resolve().parents[1]
    for ambiente, modulo in [("desenvolvimento", "app"), ("producao", "wsgi")]:
        banco = tmp_path / f"{ambiente}.db"
        env = dict(os.environ, PYTHON_DOTENV_DISABLED="1", APP_ENV=ambiente,
                   URL_DATABASE=f"sqlite:///{banco.as_posix()}", SECRET_KEY="apenas-testes",
                   FRONTEND_URL="https://www.example.com", API_PUBLIC_URL="https://api.example.com",
                   RATELIMIT_STORAGE_URI="redis://127.0.0.1:6379/0", TRUSTED_PROXY_HOPS="0",
                   TRUSTED_PROXY_PROTO_HOPS="0", SESSION_COOKIE_SAMESITE="Lax")
        codigo = f'''
from unittest.mock import patch
# Redis é externo a este teste de importação; não inicializar seu cliente.
with patch("utils.limite_requisicoes.limiter.init_app"), patch("flask_sqlalchemy.SQLAlchemy.create_all", side_effect=AssertionError("criou tabelas")), patch("services.peca_service.popular_pecas_service.PopularPecasService.executar", side_effect=AssertionError("executou seed")):
    import {modulo} as entrada
    assert not entrada.app.debug
    assert "banco-preparar" in entrada.app.cli.commands
'''
        resultado = subprocess.run([sys.executable, "-c", codigo], cwd=backend, env=env,
                                   capture_output=True, text=True, timeout=30)
        assert resultado.returncode == 0, resultado.stderr
        assert not banco.exists()


def test_preparar_banco_novo_e_migrar_preservando_usuario(tmp_path):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path / 'teste.db'}"
    db.init_app(app)
    registrar_comandos_banco(app)
    runner = app.test_cli_runner()
    assert runner.invoke(args=["banco-preparar"]).exit_code == 0
    with app.app_context():
        Usuario(nome="Preservado", email="teste@example.com").salvar()
        db.session.remove()
        with db.engine.begin() as conexao:
            conexao.execute(text("ALTER TABLE usuario DROP COLUMN versao_sessao"))
    resultado = runner.invoke(args=["banco-preparar"])
    assert resultado.exit_code == 0, resultado.output
    assert list(tmp_path.glob("*.antes-migracao-*.db"))
    with app.app_context():
        assert Usuario.buscar_por_id(1).nome == "Preservado"
        assert Usuario.buscar_por_id(1).versao_sessao == 1
        assert "email_destino" in {c["name"] for c in inspect(db.engine).get_columns("token_recuperacao")}
        db.session.remove()
    assert runner.invoke(args=["banco-preparar"]).exit_code == 0
    with app.app_context():
        db.engine.dispose()


def test_cadastro_nao_atualiza_precos_sem_opcao_explicita():
    app = Flask(__name__)
    registrar_comandos_precos(app)
    with patch("commands.precos.PopularPecasService.executar", return_value={}) as executar:
        assert app.test_cli_runner().invoke(args=["pecas-popular"]).exit_code == 0
        assert executar.call_args.kwargs["atualizar_precos"] is False
        assert app.test_cli_runner().invoke(args=["pecas-popular", "--atualizar-precos"]).exit_code == 0
        assert executar.call_args.kwargs["atualizar_precos"] is True
