from inspect import unwrap

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from controllers.usuario_controller import UsuarioController


def test_falha_ao_atualizar_usuario_faz_rollback_e_retorna_500(mocker):
    mocker.patch("controllers.usuario_controller.AtualizarUsuarioService.executar",
                 side_effect=SQLAlchemyError("falha no banco"))
    rollback = mocker.patch("controllers.usuario_controller.db.session.rollback")
    app = Flask(__name__)

    with app.test_request_context(json={"nome": "Gustavo"}):
        resposta, status = unwrap(UsuarioController.atualizar_usuario)(1)

    assert status == 500
    assert resposta.json == {"erro": "Erro ao atualizar o usuario no banco de dados"}
    rollback.assert_called_once_with()
