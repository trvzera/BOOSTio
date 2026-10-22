import json
from pathlib import Path

import pytest

from models import Gabinete, AirCooler
from models.medidas_fisicas import completar_medidas
from services.build_service.encaixe_fisico import avaliar_fans, encaixe_radiador
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService


def avaliar(pecas, componentes=None):
    if componentes is None:
        componentes = {p["categoria"]: {"id": p["id"], "quantidade": 1} for p in pecas}
    return AvaliarCompatibilidadeService().executar({"componentes": componentes}, catalogo=pecas)


def regra(resultado, codigo):
    return next(r for r in resultado["verificacoes"] if r["codigo"] == codigo)


FIXTURE = json.loads((Path(__file__).resolve().parents[4] / "frontend/tests/fixtures/encaixe-fans.json").read_text())
RADIADORES = json.loads((Path(__file__).resolve().parents[4] / "frontend/tests/fixtures/radiadores-dimensoes.json").read_text())


@pytest.mark.parametrize("caso", RADIADORES["casos"], ids=lambda c: c["nome"])
def test_dimensoes_reais_do_radiador(caso):
    assert encaixe_radiador({**RADIADORES["gabinete"], **caso.get("gabinete", {})},
                           {**RADIADORES["water"], **caso.get("water", {})}) == caso["esperado"]


@pytest.mark.parametrize("caso", FIXTURE["casos"], ids=lambda c: c["nome"])
def test_mesmas_regras_do_frontend(caso):
    resultado = avaliar_fans({**FIXTURE["gabinete"], **caso.get("gabinete", {})},
                             [(f["item"], f["peca"]) for f in caso["fans"]], caso.get("water"), caso.get("substituir") is True)
    for campo, valor in caso["esperado"].items():
        assert resultado[campo] == valor, campo


def test_catalogo_real_expoe_complemento_sem_migracao_e_sem_mutar_db():
    gabinete = Gabinete(id=1, fabricante="Cooler Master", modelo="MasterBox Q300L", part_number="SEED-CASE-01", tamanho_max_cooler_mm=160)
    dados = gabinete.to_catalogo()
    assert dados["quantidade_max_fans"] == 6 and dados["tamanho_max_cooler_mm"] == 159
    assert len(dados["posicoes_fans"]) == 4 and dados["fonte_medidas"].startswith("https://www.coolermaster.com/")
    enviado = CriarBuildService._campos_pecas(gabinete)
    assert enviado["id"] == 1 and enviado["quantidade_max_fans"] == 6
    assert len(enviado["posicoes_fans"]) == 4
    assert gabinete.tamanho_max_cooler_mm == 160
    air = AirCooler(id=2, fabricante="Deepcool", modelo="AK400", part_number="SEED-ACOOL-02", dimensoes=129)
    assert air.to_catalogo()["altura_mm"] == 155
    dados["posicoes_fans"].clear()
    assert len(gabinete.to_catalogo()["posicoes_fans"]) == 4
    for campo, valor in (("part_number", "outro"), ("modelo", "MasterBox Q300L V2"), ("fabricante", "Outra")):
        original = {"categoria": "gabinete", "fabricante": "Cooler Master", "modelo": "MasterBox Q300L", "part_number": "SEED-CASE-01"}
        assert "posicoes_fans" not in completar_medidas({**original, campo: valor})


def test_limites_fisicos_aparecem_no_diagnostico_python_e_catalogo_llm():
    case = {"id": 1, "categoria": "gabinete", **FIXTURE["gabinete"], "tamanho_max_gpu_mm": 300,
            "tamanho_max_cooler_mm": 160, "tamanho_max_fonte_mm": 160, "formatos_fonte": ["ATX"], "baias_25": 1}
    pecas = [case, {"id": 2, "categoria": "placa_video", "comprimento_mm": 301},
             {"id": 3, "categoria": "air_cooler", "altura_mm": 161},
             {"id": 4, "categoria": "fonte", "comprimento_mm": 161, "formato": "SFX"},
             {"id": 5, "categoria": "ssd", "formato": "2.5"},
             {"id": 6, "categoria": "fan", "tamanho_mm": 140, "quantidade": 3}]
    resultado = avaliar(pecas)
    for codigo in ("placa_video-medida", "air_cooler-medida", "fonte-medida", "fonte-formato", "fans-posicoes"):
        assert regra(resultado, codigo)["status"] == "incompativel"
    assert resultado["fans"]["selecionadas"] == 3
    assert set(("comprimento_mm", "altura_mm", "posicoes_fans", "quantidade", "tamanho_mm", "quantidade_fans", "tamanho_fan_mm", "baias_25")) <= set(CriarBuildService.CAMPOS_PECAS)
    componentes = {p["categoria"]: {"id": p["id"], "quantidade": 1} for p in pecas}
    componentes["ssd"]["quantidade"] = 2
    assert regra(avaliar(pecas, componentes), "baias-baias_25")["status"] == "incompativel"


def test_geracao_nao_salva_configuracao_com_fans_que_nao_cabem():
    tipos = ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd", "fan")
    catalogo = {tipo: [{"id": i, "fabricante": "QA", "modelo": tipo, "preco": 100}]
                for i, tipo in enumerate(tipos, 1)}
    catalogo["processador"][0].update(videointegrado=True, cooler=True)
    catalogo["gabinete"][0].update(FIXTURE["gabinete"])
    catalogo["fan"][0].update(tamanho_mm=140, quantidade=3)
    build = {"nome": "Teste", "descricao": "Montagem", "utilidade": "Estudos",
             "componentes": [{"tipo": tipo, "id": i} for i, tipo in enumerate(tipos, 1)]}
    with pytest.raises(ValueError, match="Posições das fans"):
        CriarBuildService._validar_build(build, catalogo, 5000)


def test_diagnostico_resolve_medidas_do_catalogo_persistido_em_banco_isolado():
    from flask import Flask
    from models import db, Fan
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI="sqlite://", SQLALCHEMY_TRACK_MODIFICATIONS=False)
    db.init_app(app)
    with app.app_context():
        db.create_all()
        case = Gabinete(fabricante="Cooler Master", modelo="MasterBox Q300L", part_number="SEED-CASE-01", consumo_energia=0, preco=200,
                        formato="mATX", formatos_placa_mae="ATX", fans_inclusos=2, suporte_water_cooler=True)
        fan = Fan(fabricante="QA", modelo="Kit", consumo_energia=3, preco=50, tamanho_mm=140, quantidade=3, iluminacao=False)
        db.session.add_all([case, fan]); db.session.commit()
        resultado = AvaliarCompatibilidadeService().executar({"componentes": {"gabinete": {"id": f"gabinete:{case.id}"}, "fan": [{"id": f"fan:{fan.id}", "quantidade": 1}]}})
        assert regra(resultado, "fans-posicoes")["status"] == "incompativel"
        assert resultado["fans"]["inclusas"] == 1
        assert case.fans_inclusos == 2  # complemento não faz update silencioso na base
        db.session.remove(); db.drop_all()


@pytest.mark.parametrize("valor", ["true", 1, None, [], {}])
def test_flag_substituicao_exige_booleano(valor):
    from models import BuildSalva
    with pytest.raises(ValueError, match="substituição das fans"):
        BuildSalva.validar_estado({"titulo": "QA", "substituirFansWaterCooler": valor})


def test_estado_preserva_substituicao_e_normaliza_default():
    from models import BuildSalva, Fan
    assert BuildSalva.validar_estado({"titulo": "QA", "substituirFansWaterCooler": True})["substituirFansWaterCooler"] is True
    assert BuildSalva.validar_estado({"titulo": "QA"})["substituirFansWaterCooler"] is False
    dados = Fan(id=1, modelo="TR120 Reverse").to_catalogo()
    assert dados["fluxo_ar"] == "reverso" and dados["fonte_fluxo_ar"] == "nome_comercial"
    assert "fluxo_ar" not in Fan(id=2, modelo="Sem informação").to_catalogo()


def test_estado_aceita_fans_de_modelos_diferentes_e_preserva_quantidade(monkeypatch):
    from models import BuildSalva, Fan
    monkeypatch.setattr(Fan, "buscar_por_id", lambda identificador: Fan(id=identificador, modelo="Fan"))
    estado = BuildSalva.validar_estado({"titulo": "QA", "substituirFansWaterCooler": True,
                                      "componentes": {"fan": [{"id": 1, "quantidade": 3}, {"id": 2, "quantidade": 2}]}})
    assert estado["componentes"]["fan"] == [{"id": 1, "quantidade": 3}, {"id": 2, "quantidade": 2}]
    assert estado["substituirFansWaterCooler"] is True
