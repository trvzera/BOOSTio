"""Fichas compartilhadas com JS; sem rede, escrita ou migração do banco real."""
import json
from pathlib import Path

import pytest

from models import Gabinete
from models.medidas_fisicas import completar_medidas
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.encaixe_fisico import avaliar_fans, encaixe_radiador
from services.build_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService

CASOS = json.loads((Path(__file__).resolve().parents[4] / "frontend/tests/fixtures/gabinetes-ventilacao.json").read_text())


def base(caso):
    return {**{k: caso[k] for k in ("fabricante", "modelo", "part_number")}, "categoria": "gabinete",
            "link": "https://www.kabum.com.br/produto/" + caso["produto_kabum"]}


def gabinete(codigo):
    return completar_medidas(base(next(c for c in CASOS if c["part_number"] == codigo)))


def fans(quantidade, tamanho=120, kit=1):
    return [({"quantidade": quantidade}, {"quantidade": kit, "tamanho_mm": tamanho})] if quantidade else []


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["part_number"])
def test_identidade_medidas_e_preservacao_catalogo(caso):
    original = {**base(caso), "fans_inclusos": None, "preco": 123, "imagem": "foto.webp", "esgotado": True,
                "ofertas": [{"loja": "kabum", "preco": 123}]}
    p = completar_medidas(original)
    for k, v in caso["esperado"].items():
        assert p[k] == v, k
    for k in ("preco", "imagem", "esgotado", "ofertas", "modelo", "part_number", "link"):
        assert p[k] == original[k]
    assert original["fans_inclusos"] is None
    assert p["ficha_tecnica_verificada_em"] == caso['esperado'].get('ficha_tecnica_verificada_em', "2026-10-23") and p["fonte_medidas"].startswith("https://")
    for alteracao in ({"part_number": "outro"}, {"modelo": caso["modelo"] + " RGB"}, {"fabricante": "outro"},
                      {"link": "https://www.kabum.com.br/produto/999999"}, {"link": None}):
        assert "fonte_medidas" not in completar_medidas({**base(caso), **alteracao})


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["part_number"])
def test_fabrica_vagas_e_excesso(caso):
    p = completar_medidas(base(caso))
    vazio = avaliar_fans(p, [])
    assert vazio["total"] == caso["esperado"]["fans_inclusos"]
    assert vazio["livres"] == caso["extras"]
    assert vazio["distribuicao"] is caso["distribuicao_sem_extras"]
    cheio = avaliar_fans(p, fans(caso["extras"], caso["diametro_extras"]))
    assert cheio["total"] == caso["esperado"]["quantidade_max_fans"]
    assert cheio["quantidade"] is True and cheio["livres"] == 0
    excesso = avaliar_fans(p, fans(caso["extras"] + 1, caso["diametro_extras"]))
    assert excesso["quantidade"] is False and excesso["distribuicao"] is False
    assert avaliar_fans(p, fans(1, 360))["tamanhos"] is False


@pytest.mark.parametrize("caso", CASOS, ids=lambda c: c["part_number"])
def test_api_e_prompt_recebem_contagens_sem_alterar_modelo(caso):
    obj = Gabinete(id=1, fabricante=caso["fabricante"], modelo=caso["modelo"], part_number=caso["part_number"],
                   kabum_external=base(caso)["link"], fans_inclusos=None)
    for dados in (obj.to_catalogo(), CriarBuildService._campos_pecas(obj)):
        for k in ("fans_inclusos", "quantidade_max_fans", "tamanhos_fan_suportados_mm"):
            assert dados[k] == caso["esperado"][k]
        assert dados["fonte_medidas"].startswith("https://")
    assert obj.fans_inclusos is None


def test_kits_e_aio_ocupam_mesmas_posicoes():
    p = gabinete("SEED-CASE-40")
    assert avaliar_fans(p, fans(2, 120, 2))["total"] == 8
    assert avaliar_fans(p, fans(3, 120, 2))["quantidade"] is False
    water = {"quantidade_fans": 2, "tamanho_fan_mm": 120, "tamanho_radiador_mm": 240}
    info = avaliar_fans(p, fans(2), water)
    assert info["total"] == 8 and info["distribuicao"] is True
    assert avaliar_fans(p, fans(3), water)["quantidade"] is False
    assert avaliar_fans(p, fans(3, 140))["distribuicao"] is False
    assert encaixe_radiador(p, water) is None


def test_msi_rejeita_120_mm_e_hayom_nao_inventa_posicoes_e_eixos():
    info = avaliar_fans(gabinete("KABUM-1017873"), fans(1))
    assert info["tamanhos"] is False and info["quantidade"] is False
    for codigo in ("KABUM-938469", "KABUM-933255"):
        p = gabinete(codigo)
        for k in ("comprimento_mm", "largura_mm", "altura_mm", "tamanho_max_cooler_mm", "tamanho_max_fonte_mm"):
            assert p.get(k) is None
        assert p["suporte_water_cooler"] is None
        assert encaixe_radiador(p, {"tamanho_radiador_mm": 240}) is None
    assert "posicoes_fans" not in gabinete("KABUM-933255")


def test_h5_nao_confunde_tamanho_nominal_com_folgas_confirmadas():
    p = gabinete("SEED-CASE-43")
    assert 280 in next(g for g in p["posicoes_fans"] if g["nome"] == "Frente")["radiadores_mm"]
    assert 280 not in next(g for g in p["posicoes_fans"] if g["nome"] == "Topo")["radiadores_mm"]
    assert "perfil baixo" in p["observacoes_medidas"]
    assert p["tamanho_max_gpu_mm"] is None and p["tamanho_max_cooler_mm"] is None
    catalogo = [{**p, "id": "gabinete"}, {"categoria": "placa_video", "id": "gpu", "comprimento_mm": 415}]
    estado = {"componentes": {"gabinete": {"id": "gabinete"}, "placa_video": {"id": "gpu"}}}
    resultado = AvaliarCompatibilidadeService().executar(estado, catalogo=catalogo)
    assert next(v for v in resultado["verificacoes"] if v["codigo"] == "placa_video-medida")["status"] == "nao_verificado"
    assert encaixe_radiador(p, {"tamanho_radiador_mm": 280}) is None
