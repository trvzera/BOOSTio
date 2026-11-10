from inspect import unwrap

from flask import Flask
from sqlalchemy.exc import SQLAlchemyError

from controllers.usuario_controller import atualizar_usuario


def test_falha_ao_atualizar_usuario_retorna_500(mocker):
    mocker.patch("controllers.usuario_controller.AtualizarUsuarioService.executar",
                 side_effect=SQLAlchemyError("falha no banco"))
    app = Flask(__name__)

    with app.test_request_context(json={"nome": "Gustavo"}):
        resposta, status = unwrap(atualizar_usuario)(1)

    assert status == 500
    assert resposta.json == {"erro": "Erro ao atualizar o usuario no banco de dados"}


def test_fim_da_requisicao_desfaz_transacao_quebrada(mocker):
    from utils.transacao import desfazer_transacao_quebrada
    sessao = mocker.patch("utils.transacao.db.session", is_active=False)

    desfazer_transacao_quebrada(None)

    sessao.rollback.assert_called_once_with()


def test_fim_da_requisicao_nao_mexe_em_transacao_saudavel(mocker):
    from utils.transacao import desfazer_transacao_quebrada
    sessao = mocker.patch("utils.transacao.db.session", is_active=True)

    desfazer_transacao_quebrada(None)

    sessao.rollback.assert_not_called()
