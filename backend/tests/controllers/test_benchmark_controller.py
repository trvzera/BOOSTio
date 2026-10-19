import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin

from controllers.benchmark_controller import benchmark_bp
from services.benchmark_service.fpshq_service import ErroBenchmark


@pytest.fixture
def cliente_benchmark():
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="somente-testes")
    login = LoginManager(app)

    class UsuarioTeste(UserMixin):
        id = 42

    login.user_loader(lambda _id: UsuarioTeste())
    app.register_blueprint(benchmark_bp)
    return app.test_client()


def autenticar(cliente):
    with cliente.session_transaction() as sessao:
        sessao["_user_id"] = "42"
        sessao["_fresh"] = True


@pytest.mark.parametrize("rota", ["/benchmark/fps", "/benchmark/jogos?q=Valorant"])
def test_exige_sessao_e_responde_json(cliente_benchmark, rota):
    resposta = cliente_benchmark.get(rota)
    assert resposta.status_code == 401
    assert resposta.json["codigo"] == "nao-autenticado"


def test_rota_delega_ao_service_com_usuario_da_sessao(cliente_benchmark, mocker):
    executar = mocker.patch("controllers.benchmark_controller.ConsultarBenchmarkService.executar", return_value={"fps": 288})
    autenticar(cliente_benchmark)
    resposta = cliente_benchmark.get("/benchmark/fps?game=valorant&cpu=ryzen-5-5600&gpu=rtx-3060")
    assert resposta.status_code == 200
    assert resposta.json == {"resultado": {"fps": 288}}
    assert executar.call_args.args[1] == 42
    assert resposta.headers["Cache-Control"] == "no-store"


@pytest.mark.parametrize("query", ["?game=valorant&game=cs2", "?url=https://externo.test", "?usuario_id=10"])
def test_rejeita_parametros_duplicados_e_nao_permitidos(cliente_benchmark, query, mocker):
    executar = mocker.patch("controllers.benchmark_controller.ConsultarBenchmarkService.executar")
    autenticar(cliente_benchmark)
    assert cliente_benchmark.get("/benchmark/fps" + query).status_code == 400
    executar.assert_not_called()


def test_erro_validacao_e_limite_tem_contrato_json(cliente_benchmark, mocker):
    autenticar(cliente_benchmark)
    executar = mocker.patch("controllers.benchmark_controller.ConsultarBenchmarkService.executar", side_effect=ValueError("Entrada inválida"))
    assert cliente_benchmark.get("/benchmark/fps").status_code == 400
    executar.side_effect = ErroBenchmark("Aguarde", "limite", 429, 90)
    resposta = cliente_benchmark.get("/benchmark/fps")
    assert resposta.status_code == 429
    assert resposta.headers["Retry-After"] == "90"
    assert resposta.json["espera"] == 90
