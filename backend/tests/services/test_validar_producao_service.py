import pytest
from flask import Flask

from services.configuracao_service.validar_producao_service import ValidarProducaoService


def test_configuracao_de_producao_exige_segredos(monkeypatch):
    app = Flask(__name__)
    app.config.update(SECRET_KEY="x" * 32, SQLALCHEMY_DATABASE_URI="sqlite:////tmp/teste.db")
    valores = {
        "GOOGLE_CLIENT_ID": "cliente", "GOOGLE_CLIENT_SECRET": "segredo",
        "GEMINI_API_KEY": "gemini", "MAIL_USERNAME": "teste@example.com",
        "MAIL_PASSWORD": "senha",
    }
    for nome, valor in valores.items():
        monkeypatch.setenv(nome, valor)

    servico = ValidarProducaoService()
    servico.executar(app)

    app.config["SECRET_KEY"] = "curta"
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        servico.executar(app)
    app.config["SECRET_KEY"] = "x" * 32

    app.config["SQLALCHEMY_DATABASE_URI"] = None
    with pytest.raises(RuntimeError, match="URL_DATABASE"):
        servico.executar(app)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/teste.db"

    monkeypatch.delenv("GOOGLE_CLIENT_SECRET")
    with pytest.raises(RuntimeError, match="GOOGLE_CLIENT_SECRET"):
        servico.executar(app)
