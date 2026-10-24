import importlib
import inspect

import pytest
from flask import Flask


CONTROLLERS = [
    ("auth_controller", "AuthController", "auth_bp"),
    ("usuario_controller", "UsuarioController", "usuario_bp"),
    ("build_controller", "BuildController", "build_bp"),
    ("email_controller", "EmailController", "email_bp"),
    ("benchmark_controller", "BenchmarkController", "benchmark_bp"),
    ("saude_controller", "SaudeController", "saude_bp"),
    ("peca_controller", "PecaController", "peca_bp"),
]


@pytest.mark.parametrize("modulo,nome,blueprint", CONTROLLERS)
def test_rotas_sao_metodos_de_classes_sem_estado_compartilhado(modulo, nome, blueprint):
    arquivo = importlib.import_module("controllers." + modulo)
    classe = getattr(arquivo, nome)
    app = Flask(__name__)
    app.register_blueprint(getattr(arquivo, blueprint))
    views = [f for endpoint, f in app.view_functions.items() if endpoint != "static"]
    assert views
    for view in views:
        original = inspect.unwrap(view)
        assert original.__qualname__.startswith(nome + ".")
        assert isinstance(inspect.getattr_static(classe, original.__name__), staticmethod)


def test_contrato_de_urls_metodos_e_endpoints_preservado():
    app = Flask(__name__)
    for modulo, _, blueprint in CONTROLLERS:
        app.register_blueprint(getattr(importlib.import_module("controllers." + modulo), blueprint))
    esperadas = {
        ("/auth/csrf", "GET", "auth.obter_csrf"),
        ("/auth/entrar", "POST", "auth.entrar_usuario"),
        ("/auth/sair", "POST", "auth.sair_usuario"),
        ("/auth/me", "GET", "auth.teste_logado"),
        ("/auth/google/redirecionar", "GET", "auth.redirecionar_google"),
        ("/auth/google/confirmar", "POST", "auth.confirmar_google"),
        ("/auth/google/entrar", "GET", "auth.callback_google"),
        ("/usuarios/<int:usuario_id>/budget", "PUT", "usuario.atualizar_budget"),
        ("/usuarios/", "POST", "usuario.criar_usuario"),
        ("/usuarios/<int:usuario_id>", "DELETE", "usuario.excluir_usuario"),
        ("/usuarios/<int:usuario_id>", "GET", "usuario.listar_usuario_id"),
        ("/usuarios/<int:usuario_id>", "PUT", "usuario.atualizar_usuario"),
        ("/usuarios/esqueci-senha", "POST", "usuario.esqueci_senha"),
        ("/usuarios/redefinir-senha", "POST", "usuario.redefinir_senha"),
        ("/build/", "GET", "build.mostrar_builds"),
        ("/build/", "POST", "build.criar_build"),
        ("/build/catalogo", "GET", "build.catalogo_build"),
        ("/build/manual", "POST", "build.criar_build_manual"),
        ("/build/<build_id>", "GET", "build.buscar_build"),
        ("/build/<build_id>", "PUT", "build.atualizar_build"),
        ("/build/<build_id>/duplicar", "POST", "build.duplicar_build"),
        ("/build/<build_id>/setup-atual", "POST", "build.definir_setup_atual"),
        ("/build/<build_id>", "DELETE", "build.excluir_build"),
        ("/build/<build_id>/publica", "GET", "build.buscar_build_publica"),
        ("/build/<build_id>/copiar-publica", "POST", "build.copiar_build_publica"),
        ("/email/verificar/enviar/<int:usuario_id>", "POST", "email.enviar_email"),
        ("/email/verificar/conferir/<int:usuario_id>", "POST", "email.conferir_email"),
        ("/benchmark/fps", "GET", "benchmark.consultar_benchmark"),
        ("/benchmark/jogos", "GET", "benchmark.buscar_jogos"),
        ("/benchmark/blender", "GET", "benchmark.consultar_blender"),
        ("/benchmark/requisitos", "GET", "benchmark.consultar_requisitos"),
        ("/benchmark/requisitos-build", "GET", "benchmark.consultar_requisitos_build"),
        ("/health", "GET", "saude.verificar_saude"),
        ("/pecas/", "GET", "peca.mostrar_pecas"),
    }
    atuais = {(regra.rule, metodo, regra.endpoint) for regra in app.url_map.iter_rules()
              if regra.endpoint != "static" for metodo in regra.methods - {"OPTIONS", "HEAD"}}
    assert atuais == esperadas
