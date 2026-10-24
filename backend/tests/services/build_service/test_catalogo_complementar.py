import json
from pathlib import Path

from flask import Flask
import pytest

from models import db, Fan
from models.medidas_fisicas import completar_medidas
from commands.precos import registrar_comandos_precos
from services.peca_service.pecas_complementares import pecas_complementares
from services.peca_service.cadastrar_complementares_service import CadastrarComplementaresService
from services.build_service.encaixe_fisico import avaliar_fans, encaixe_radiador


CASOS = json.loads((Path(__file__).resolve().parents[4] /
                    "frontend/tests/fixtures/catalogo-complementar.json").read_text())


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["part_number"])
def test_complemento_so_corrige_variante_revisada_e_nao_precos(caso):
    original = {k: v for k, v in caso.items() if k != "esperado"}
    original.update(preco=99, esgotado=False, preco_atualizado_em="2026-10-24", quantidade=3)
    dados = completar_medidas(original)
    assert dados.items() >= caso["esperado"].items()
    for campo in ("preco", "esgotado", "preco_atualizado_em", "part_number", "modelo"):
        assert dados[campo] == original[campo]
    assert original["quantidade"] == 3
    assert dados["ficha_tecnica_verificada_em"] == "2026-10-24"
    for mudanca in ({"link": None}, {"link": "https://www.kabum.com.br/produto/1"},
                    {"modelo": caso["modelo"] + " V2"}, {"part_number": "outra-variante"}):
        assert "fonte_medidas" not in completar_medidas({**original, **mudanca})


def test_lote_tem_fichas_exatas_sem_ofertas_e_consumo_do_kit_nao_e_de_uma_fan():
    registros = [(classe, item) for classe, itens in pecas_complementares().items() for item in itens]
    assert len(registros) == 7
    for classe, item in registros:
        obj = classe(id=1, **item)
        dados = obj.to_catalogo()
        assert dados["fonte_medidas"].startswith("https://")
        assert dados["ficha_tecnica_verificada_em"] == "2026-10-24"
        assert dados["preco"] == 0 and dados["esgotado"] and not dados["ofertas"]
        if classe.__tablename__ in ("mouse", "teclado", "fone"):
            assert dados["consumo_energia"] is None
    fans = {i["part_number"]: i for i in pecas_complementares()[Fan]}
    assert fans["ACFAN00120A"]["quantidade"] == 1
    assert fans["ACFAN00137A"]["quantidade"] == 5
    assert fans["ACFAN00137A"]["consumo_energia"] == 5 * fans["ACFAN00120A"]["consumo_energia"]
    assert fans["ACFAN00137A"]["kabum_external"] is None


def test_fans_ocupam_posicoes_reais_e_condicoes_desconhecidas_nao_sao_aprovadas():
    lian = completar_medidas({k: v for k, v in CASOS[2].items() if k != "esperado"})
    fan = {"quantidade": 1, "tamanho_mm": 120}
    assert avaliar_fans(lian, [({"quantidade": 10}, fan)])["quantidade"] is True
    assert avaliar_fans(lian, [({"quantidade": 11}, fan)])["quantidade"] is False
    assert 420 not in lian["radiadores_suportados_mm"]
    assert encaixe_radiador(lian, {"tamanho_radiador_mm": 420}) is not True
    corsair = completar_medidas({k: v for k, v in CASOS[3].items() if k != "esperado"})
    assert avaliar_fans(corsair, [({"quantidade": 8}, fan)])["quantidade"] is None
    assert avaliar_fans(corsair, [({"quantidade": 8}, fan)])["distribuicao"] is None


def test_cli_idempotente_simula_sem_gravar_e_preserva_anuncio_existente(tmp_path):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{tmp_path / 'lote.db'}"
    db.init_app(app)
    registrar_comandos_precos(app)
    with app.app_context():
        db.create_all()
        # Mesmo anúncio já cadastrado com ID interno: não duplicar por mudar PN.
        antiga = Fan(fabricante="ARCTIC", modelo="Nome interno", part_number="KABUM-464964",
                     tamanho_mm=120, quantidade=1, consumo_energia=2, preco=123, esgotado=False,
                     kabum_external="https://www.kabum.com.br/produto/464964/outro-slug")
        antiga.salvar()
        runner = app.test_cli_runner()
        resultado = runner.invoke(args=["pecas-complementares", "--simular"])
        assert resultado.exit_code == 0, resultado.output
        assert json.loads(resultado.output)["inseridas"] == 0
        assert Fan.query.count() == 1
        resumo = CadastrarComplementaresService().executar()
        assert resumo["inseridas"] == 6 and resumo["existentes"] == 1
        assert CadastrarComplementaresService().executar()["inseridas"] == 0
        assert antiga.preco == 123 and antiga.esgotado is False
        assert antiga.part_number == "KABUM-464964" and antiga.modelo == "Nome interno"
        db.session.remove()
        db.engine.dispose()
