from copy import deepcopy

import pytest
from flask import Flask

from controllers.auth_controller import auth_bp
from controllers.benchmark_controller import benchmark_bp
from controllers.build_controller import build_bp
from models import db, lm, Usuario, BuildSalva, Processador, MemoriaRAM
from utils.csrf import configurar_csrf


@pytest.fixture
def app_publica(tmp_path):
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="somente-testes", SQLALCHEMY_DATABASE_URI=f"sqlite:///{tmp_path / 'publica.db'}")
    db.init_app(app)
    lm.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(build_bp)
    app.register_blueprint(benchmark_bp)
    configurar_csrf(app)
    with app.app_context():
        db.create_all()
        db.session.add_all([
            Usuario(nome="Dono", email="dono@example.test", verificado=True),
            Usuario(nome="Visitante", email="visitante@example.test", verificado=True, budget=3500, usar_budget=True),
            Usuario(nome="Não verificado", email="pendente@example.test", verificado=False),
            Processador(id=1, fabricante="Teste", modelo="CPU", preco=500, consumo_energia=65, soquete="AM4", nucleo=4, thread=8, clockbase=3, clockmax=4, videointegrado=True, cooler=True),
            MemoriaRAM(id=1, fabricante="Teste", modelo="Kit 16 GB", preco=200, consumo_energia=6, capacidade_gb=16, ddr="DDR4", frequencia_mhz=3200, quantidade_pentes=2),
        ])
        db.session.flush()
        estado = {
            "titulo": "Pública", "descricao": "Somente leitura", "visibilidade": "publico", "travada": True,
            "orcamento": 99999, "percentualPerifericos": 25, "setupAtual": True,
            "rede": {"anotacao": "informação privada"}, "pecasExtras": {"webcam": "Minha webcam privada"},
            "componentes": {"processador": {"id": 1, "quantidade": 1}, "memoria_ram": [{"id": 1, "quantidade": 2}]},
        }
        db.session.add_all([
            BuildSalva(usuario_id=1, estado=estado),
            BuildSalva(usuario_id=1, estado={**deepcopy(estado), "visibilidade": "privado"}),
        ])
        db.session.commit()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


def cliente(app, usuario=None):
    navegador = app.test_client()
    if usuario:
        with navegador.session_transaction() as sessao:
            sessao["_user_id"] = f"{usuario}:1"
            sessao["_fresh"] = True
    token = navegador.get("/auth/csrf").json["csrf_token"]
    return navegador, {"X-CSRF-Token": token}


def test_visualizacao_anonima_nao_expoe_perfil_nem_muda_estado(app_publica):
    navegador, _ = cliente(app_publica)
    with app_publica.app_context():
        antes = deepcopy(db.session.get(BuildSalva, 1).estado)
    resposta = navegador.get("/build/s-1/publica")
    assert resposta.status_code == 200
    assert resposta.headers["Cache-Control"] == "no-store"
    dados = resposta.json["build"]
    assert "usuario_id" not in dados
    assert {p["id"] for p in dados["pecas"]} == {"processador:1", "memoria_ram:1"}
    assert dados["estado"]["travada"] is True
    for campo in ("orcamento", "rede", "pecasExtras", "percentualPerifericos", "setupAtual"):
        assert campo not in dados["estado"]
    privada = navegador.get("/build/s-2/publica")
    ausente = navegador.get("/build/s-999/publica")
    assert privada.status_code == ausente.status_code == 404
    assert privada.json == ausente.json
    for identificador in ("s-0", "s-01", "s-9999999999999999999999999999", "s-١"):
        assert navegador.get(f"/build/{identificador}/publica").status_code == 404
    with app_publica.app_context():
        assert db.session.get(BuildSalva, 1).estado == antes
        assert BuildSalva.query.count() == 2


def test_copia_exige_login_csrf_email_e_vaga_sem_alterar_original(app_publica):
    visitante, csrf = cliente(app_publica)
    assert visitante.post("/build/s-1/copiar-publica", headers=csrf).status_code == 401
    pendente, csrf = cliente(app_publica, 3)
    assert pendente.post("/build/s-1/copiar-publica", headers=csrf).status_code == 403
    navegador, csrf = cliente(app_publica, 2)
    assert navegador.post("/build/s-1/copiar-publica").json["codigo"] == "csrf-invalido"
    with app_publica.app_context():
        antes = deepcopy(db.session.get(BuildSalva, 1).estado)
    for _ in range(3):
        resposta = navegador.post("/build/s-1/copiar-publica", headers=csrf)
        assert resposta.status_code == 201
        estado = resposta.json["build"]["estado"]
        assert estado["visibilidade"] == "privado" and estado["travada"] is False
        assert estado["orcamento"] == 3500
        assert estado["componentes"]["memoria_ram"][0]["quantidade"] == 2
        assert not estado.get("setupAtual") and not estado["pecasExtras"] and not estado["rede"]
    assert navegador.post("/build/s-1/copiar-publica", headers=csrf).status_code == 409
    # As rotas privadas existentes usam 400 para falhas de alteração/exclusão.
    assert navegador.put("/build/s-1", json={"travada": False}, headers=csrf).status_code == 400
    assert navegador.delete("/build/s-1", headers=csrf).status_code == 400
    with app_publica.app_context():
        assert db.session.get(BuildSalva, 1).estado == antes
        assert BuildSalva.query.filter_by(usuario_id=2).count() == 3


def test_visibilidade_revalidada_na_copia_e_nos_requisitos_autenticados(app_publica):
    navegador, csrf = cliente(app_publica, 2)
    assert navegador.post("/build/s-2/copiar-publica", headers=csrf).status_code == 404
    rota = "/benchmark/requisitos-build?game=fortnite&build_id=s-1"
    assert navegador.get(rota).status_code == 404
    publica = rota + "&origem_publica=1"
    resposta = navegador.get(publica)
    assert resposta.status_code == 200
    assert resposta.json["resultado"]["ram"]["fonte"] == "build_publica"
    assert resposta.json["resultado"]["ram"]["informadaGb"] == 32
    assert navegador.get(rota + "&origem_publica=false").status_code == 400
    assert navegador.get(publica + "&origem_publica=1").status_code == 400
    assert app_publica.test_client().get(publica).status_code == 401
    with app_publica.app_context():
        build = db.session.get(BuildSalva, 1)
        build.estado = {**build.estado, "visibilidade": "privado"}
        db.session.commit()
    assert navegador.get("/build/s-1/publica").status_code == 404
    assert navegador.post("/build/s-1/copiar-publica", headers=csrf).status_code == 404
    assert navegador.get(publica).status_code == 404
