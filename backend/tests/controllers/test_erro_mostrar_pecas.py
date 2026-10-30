from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from controllers.peca_controller import peca_bp


def test_falha_na_listagem_de_pecas_retorna_500_sem_detalhes_internos(mocker):
    mocker.patch("services.peca_service.mostrar_pecas_service.Processador.mostrar_pecas",
                 side_effect=SQLAlchemyError("credencial-interna"))
    app = Flask(__name__)
    app.register_blueprint(peca_bp)

    resposta = app.test_client().get("/pecas/")

    assert resposta.status_code == 500
    assert resposta.json == {"erro": "Ocorreu um erro ao buscar as peças."}
