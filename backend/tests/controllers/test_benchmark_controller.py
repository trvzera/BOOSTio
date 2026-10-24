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


@pytest.mark.parametrize("rota", ["/benchmark/fps", "/benchmark/jogos?q=Valorant", "/benchmark/blender", "/benchmark/requisitos?game=valorant", "/benchmark/requisitos-build?game=valorant&build_id=s-1"])
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


def test_rota_blender_autenticada_e_parametros_restritos(cliente_benchmark, mocker):
    executar = mocker.patch("controllers.benchmark_controller.cliente_blender.executar", return_value={"score": 150})
    autenticar(cliente_benchmark)
    resposta = cliente_benchmark.get("/benchmark/blender?dispositivo=CPU&tipo=cpu")
    assert resposta.status_code == 200 and resposta.json == {"resultado": {"score": 150}}
    assert executar.call_args.args[1] == 42
    assert resposta.headers["Cache-Control"] == "no-store"
    assert cliente_benchmark.get("/benchmark/blender?url=https://interno").status_code == 400
    assert cliente_benchmark.get("/benchmark/blender?tipo=cpu&tipo=gpu").status_code == 400


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


def test_diagnostico_tem_apenas_metadados_publicos_permitidos(cliente_benchmark, mocker):
    autenticar(cliente_benchmark)
    diagnostico = {"httpProvedor": 302, "tipoResposta": "html", "redirecionamento": True,
                   "pausa": True, "headers": {"Set-Cookie": "segredo"},
                   "url": "https://externo.invalid/?token=segredo", "corpo": "nao-expor"}
    mocker.patch("controllers.benchmark_controller.ConsultarBenchmarkService.executar",
                 side_effect=ErroBenchmark("Serviço indisponível", "redirecionamento", 503, 60, diagnostico))
    resposta = cliente_benchmark.get("/benchmark/fps")
    assert resposta.status_code == 503
    assert resposta.json["diagnostico"] == {
        "httpProvedor": 302, "tipoResposta": "html", "redirecionamento": True, "pausa": True,
    }
    assert "segredo" not in resposta.get_data(as_text=True)


def test_diagnostico_nao_inventa_status_nem_formato():
    erro = ErroBenchmark("Falha", diagnostico={"httpProvedor": True, "tipoResposta": "texto livre", "pausa": "sim"})
    assert erro.diagnostico == {}


@pytest.mark.parametrize("codigo,status,espera", [("timeout", 504, 30), ("rede", 503, 30),
                                                ("tls", 503, 60), ("provedor", 503, 60),
                                                ("resposta", 502, 0), ("sem-dados", 422, 0)])
def test_falhas_do_provedor_preservam_codigo_http_e_espera(cliente_benchmark, mocker, codigo, status, espera):
    autenticar(cliente_benchmark)
    executar = mocker.patch("controllers.benchmark_controller.ConsultarBenchmarkService.executar",
                           side_effect=ErroBenchmark("Consulta indisponível", codigo, status, espera))
    resposta = cliente_benchmark.get("/benchmark/fps?game=valorant&cpu=ryzen-5-5600&gpu=rtx-3060")
    assert resposta.status_code == status
    assert resposta.json == {"erro": "Consulta indisponível", "codigo": codigo, "espera": espera}
    assert resposta.headers.get("Retry-After") == (str(espera) if espera else None)
    assert resposta.headers["Cache-Control"] == "no-store"
    executar.assert_called_once()


def test_requisitos_autenticados_nao_dependem_de_fpshq(cliente_benchmark, mocker):
    fps = mocker.patch("services.benchmark_service.fpshq_service.FpshqService.executar", side_effect=AssertionError("Não deve consultar FPSHQ"))
    autenticar(cliente_benchmark)
    resposta = cliente_benchmark.get("/benchmark/requisitos?game=fortnite&ram_gb=8")
    assert resposta.status_code == 200
    assert resposta.headers["Cache-Control"] == "no-store"
    assert resposta.json["resultado"]["ram"]["atendeMinimo"] is True
    assert resposta.json["resultado"]["ram"]["atendeRecomendado"] is False
    assert resposta.json["resultado"]["requisitosVerificados"] is False
    assert cliente_benchmark.get("/benchmark/requisitos?game=sem-ficha").status_code == 404
    assert cliente_benchmark.get("/benchmark/requisitos?game=valorant&ram_gb=8&ram_gb=16").status_code == 400
    assert cliente_benchmark.get("/benchmark/requisitos?game=valorant&cpu=cpu").status_code == 400
    fps.assert_not_called()
