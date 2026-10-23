import pytest
from flask import Flask

from services.build_service.criar_build_service import CriarBuildService
from services.usuario_service.criar_usuario_service import CriarUsuarioService
from services.usuario_service.entrar_usuario_service import EntrarUsuarioService
from utils.validacoes import validacao_campos


@pytest.mark.parametrize("dados", [None, [], "texto"])
def test_campos_obrigatorios_exigem_objeto(dados):
    with pytest.raises(ValueError, match="objeto JSON"):
        validacao_campos(dados, ["nome"])


@pytest.mark.parametrize("campo,valor", [
    ("nome", "x" * 101), ("descricao", "x" * 301),
    ("utilidade", "x" * 121), ("utilidade", ["jogos"]),
])
def test_pedido_grande_rejeitado_antes_de_consultar_banco(campo, valor):
    dados = {"nome": "PC", "descricao": "Teste", "utilidade": "Jogos"}
    dados[campo] = valor
    with pytest.raises(ValueError, match=campo):
        CriarBuildService()._validar_textos_pedido(dados)


def test_cadastro_e_login_rejeitam_tamanho_excessivo():
    with pytest.raises(ValueError, match="nome"):
        CriarUsuarioService().executar({"nome": "x" * 31, "email": "a@example.com", "senha": "Senha123!"})
    with pytest.raises(ValueError, match="inválidos"):
        EntrarUsuarioService().executar({"email": "a" * 151, "senha": "Senha123!"})


def test_limite_http_responde_json():
    from app import requisicao_grande
    from configs import Desenvolvimento
    from werkzeug.exceptions import RequestEntityTooLarge
    app = Flask(__name__)
    app.config.from_object(Desenvolvimento)
    app.config["MAX_CONTENT_LENGTH"] = 8
    app.register_error_handler(RequestEntityTooLarge, requisicao_grande)

    @app.post("/teste")
    def teste():
        from flask import request
        request.get_data()
        return "ok"

    resposta = app.test_client().post("/teste", data="x" * 9)
    assert resposta.status_code == 413
    assert resposta.json["codigo"] == "requisicao-grande"
