"""Mesma identidade/medidas do demo JS, sem tocar o banco real ou fazer rede."""
import json
from pathlib import Path

import pytest

from models import Gabinete, PlacaMae, WaterCooler
from models.medidas_fisicas import completar_medidas, manifesto
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService
from services.build_service.encaixe_fisico import avaliar_fans, encaixe_radiador, encaixe_cooler_placa


FIXTURE = json.loads((Path(__file__).resolve().parents[4] / "frontend/tests/fixtures/fichas-tecnicas.json").read_text())


def peca(categoria):
    return completar_medidas({k: v for k, v in next(p for p in FIXTURE["aliases"] if p["categoria"] == categoria).items() if k != "esperado"})


@pytest.mark.parametrize("caso", FIXTURE["aliases"], ids=lambda c: c["modelo"])
def test_alias_exige_identidade_e_produto_revisados(caso):
    original = {k: v for k, v in caso.items() if k != "esperado"}
    original.update(preco=123.45, imagem="foto-local.webp", preco_atualizado_em="2026-10-21", esgotado=True)
    dados = completar_medidas(original)
    for chave, valor in caso["esperado"].items():
        assert dados[chave] == valor
    for chave in original:
        assert dados[chave] == original[chave]
    assert dados["ficha_tecnica_verificada_em"] == "2026-10-23"
    assert dados["modelo_ficha_tecnica"] and dados["fonte_medidas"].startswith("https://")
    assert "fonte_medidas" not in original
    for alteracao in ({"part_number": "outra-revisao"}, {"modelo": original["modelo"] + " V3"},
                      {"categoria": "processador"}, {"fabricante": "outro"}, {"link": None}):
        assert "fonte_medidas" not in completar_medidas({**original, **alteracao})


@pytest.mark.parametrize("link", FIXTURE["links_aceitos_gabinete"])
def test_url_revisado_independe_de_slug_e_tracking(link):
    base = {k: v for k, v in FIXTURE["aliases"][1].items() if k != "esperado"}
    assert "fonte_medidas" in completar_medidas({**base, "link": link})


@pytest.mark.parametrize("link", FIXTURE["links_rejeitados_gabinete"])
def test_nao_herda_medidas_por_slug_parecido_ou_link_nao_revisado(link):
    base = {k: v for k, v in FIXTURE["aliases"][1].items() if k != "esperado"}
    assert "fonte_medidas" not in completar_medidas({**base, "link": link})


def test_part_number_oficial_sem_anuncio_e_dados_nao_compartilhados():
    for ficha in (f for f in manifesto() if f.get("verificado_em") and f["part_numbers"]):
        dados = {"categoria": ficha["categoria"], "fabricante": ficha["fabricante"].upper(),
                 "modelo": ficha["modelo"].lower(), "part_number": ficha["part_numbers"][0]}
        assert completar_medidas(dados)["fonte_medidas"] == ficha["fonte"]
        assert "fonte_medidas" not in completar_medidas({**dados, "part_number": "outra"})
    case = peca("gabinete")
    case["posicoes_fans"][0]["opcoes"][0]["quantidade"] = 99
    assert peca("gabinete")["posicoes_fans"][0]["opcoes"][0]["quantidade"] == 3
    ambigua = {"categoria": "placa_mae", "fabricante": "ASRock", "modelo": "H610M-HDV/M.2",
               "part_number": "SEED-MB-22", "tipo_memoria": "DDR4",
               "link": "https://www.kabum.com.br/produto/587807/placa-mae-d5"}
    assert completar_medidas(ambigua) is ambigua


def test_todas_as_variantes_novas_preservam_preco_estoque_e_identidade():
    revisadas = [f for f in manifesto() if f.get("verificado_em")]
    for ficha in revisadas:
        assert ficha["part_numbers"] or ficha.get("aliases_catalogo")
        for alias in ficha.get("aliases_catalogo", []):
            original = {"categoria": ficha["categoria"], "fabricante": alias["fabricante"], "modelo": alias["modelo"],
                        "part_number": alias["part_number"], "link": "https://www.kabum.com.br/produto/" + alias["produto_kabum"],
                        "preco": 123.45, "esgotado": True, "imagem": "foto-local.webp"}
            dados = completar_medidas(original)
            for campo, valor in ficha["medidas"].items():
                assert dados[campo] == valor, alias["part_number"] + " " + campo
            for campo in ("preco", "esgotado", "imagem", "modelo", "part_number"):
                assert dados[campo] == original[campo]
            assert "fonte_medidas" not in completar_medidas({**original, "link": None})


def test_cpu_fan_e_ssd_usam_especificacao_da_capacidade_variante_certa():
    def ficha(codigo):
        origem = next(f for f in manifesto() if any(a["part_number"] == codigo for a in f.get("aliases_catalogo", [])))
        alias = next(a for a in origem["aliases_catalogo"] if a["part_number"] == codigo)
        return completar_medidas({**alias, "categoria": origem["categoria"], "link": "https://www.kabum.com.br/produto/" + alias["produto_kabum"]})
    cpu = ficha("SEED-CPU-01")
    assert cpu["videointegrado"] is True and cpu["cooler"] is False and cpu["tdp_w"] == 120
    fan = ficha("SEED-FAN-02")
    assert fan["quantidade"] == 1 and fan["tensao_rgb_v"] == 12 and fan["espessura_mm"] == 25
    assert ficha("SEED-SSD-01")["velocidade_gravacao_mbps"] == 2100
    assert ficha("SEED-SSD-02")["velocidade_gravacao_mbps"] == 2100
    assert ficha("SEED-SSD-03")["capacidade_gb"] == 500
    assert ficha("SEED-SSD-04")["velocidade_gravacao_mbps"] == 4000
    assert ficha("SEED-SSD-06")["comprimento_mm"] == 80
    assert ficha("SEED-RAM-01")["altura_mm"] == 34


def test_to_catalogo_e_prompt_recebem_novas_medidas_sem_update_no_modelo():
    case = Gabinete(id=2, fabricante="Cooler Master", modelo="MasterBox TD500", part_number="SEED-CASE-02",
                    kabum_external="https://www.kabum.com.br/produto/509115/gabinete", slots_expansao=4)
    assert case.to_catalogo()["slots_expansao"] == 7
    assert case.slots_expansao == 4
    dados = CriarBuildService._campos_pecas(case)
    assert dados["quantidade_max_fans"] == 7
    assert dados["modelo_ficha_tecnica"] == "MasterBox TD500 Mesh V2 White"
    assert dados["fonte_medidas"].startswith("https://www.coolermaster.com/")
    assert dados["ficha_tecnica_verificada_em"] == "2026-10-23"
    case.kabum_external = None
    assert "quantidade_max_fans" not in case.to_catalogo()
    placa = PlacaMae(id=17, fabricante="ASRock", modelo="A620AM Pro RS", part_number="SEED-MB-17",
                     kabum_external="https://www.kabum.com.br/produto/938417/placa-mae", quantidade_slots_m2=1)
    assert CriarBuildService._campos_pecas(placa)["quantidade_slots_m2"] == 3
    assert CriarBuildService._campos_pecas(placa)["quantidade_slots_m2_sata"] == 0
    assert placa.quantidade_slots_m2 == 1
    water = WaterCooler(id=11, fabricante="MSI", modelo="MAG Coreliquid A13", part_number="SEED-WCOOL-11",
                       kabum_external="https://www.kabum.com.br/produto/679305/water-cooler")
    assert CriarBuildService._campos_pecas(water)["comprimento_radiador_mm"] == 277


def test_novos_limites_sao_usados_na_compatibilidade_sem_aprovar_folgas_desconhecidas():
    case, gpu, air, fonte, water = (peca(c) for c in ("gabinete", "placa_video", "air_cooler", "fonte", "water_cooler"))
    componentes = {p["categoria"]: {"id": p["categoria"], "quantidade": 1} for p in (case, gpu, air, fonte)}
    pecas = [{**p, "id": p["categoria"]} for p in (case, gpu, air, fonte)]
    resultado = AvaliarCompatibilidadeService().executar({"componentes": componentes}, catalogo=pecas)
    assert not any(r["status"] == "incompativel" for r in resultado["verificacoes"])
    for limite, codigo in (("tamanho_max_gpu_mm", "placa_video-medida"), ("tamanho_max_cooler_mm", "air_cooler-medida"),
                            ("tamanho_max_fonte_mm", "fonte-medida")):
        reduzida = [{**p, limite: 1} if p["categoria"] == "gabinete" else p for p in pecas]
        resultado = AvaliarCompatibilidadeService().executar({"componentes": componentes}, catalogo=reduzida)
        assert next(r for r in resultado["verificacoes"] if r["codigo"] == codigo)["status"] == "incompativel"
    fan = lambda quantidade: [({"quantidade": quantidade}, {"quantidade": 1, "tamanho_mm": 120})]
    assert avaliar_fans(case, fan(2), water)["quantidade"] is True
    assert avaliar_fans(case, fan(3), water)["quantidade"] is False
    assert encaixe_radiador(case, water) is None
    pequeno = {**case, "limites_radiador_mm": [{"nome": "Topo", "tamanhos_mm": [240], "comprimento_mm": 276,
                                             "largura_mm": 120, "espessura_conjunto_mm": 53}]}
    assert encaixe_radiador(pequeno, water) is False


def test_m2_wifi_nao_conta_como_armazenamento_e_qvl_nao_e_inventada():
    placa = peca("placa_mae")
    assert placa["quantidade_slots_m2"] == 3 and placa["quantidade_slots_m2_sata"] == 0
    assert "frequencia_maxima_mhz" not in placa
    assert "Key E" in placa["observacoes_medidas"] and "não conta" in placa["observacoes_medidas"]


def test_excecoes_oficiais_cooler_placa_nao_exigem_gabinete_e_nao_certificam_outros_modelos():
    air = next(f["medidas"] for f in manifesto() if f["modelo"] == "ASSASSIN IV")
    placa = {"fabricante": "ASUS", "modelo": "TUF GAMING B760M-PLUS WIFI"}
    assert encaixe_cooler_placa(air, placa) is False
    assert encaixe_cooler_placa(air, {**placa, "modelo": placa["modelo"] + " D4"}) is None
    assert encaixe_cooler_placa(air, {"fabricante": "MSI", "modelo": "b650m ape wifi"}) is False
    assert encaixe_cooler_placa(air, {"fabricante": "MSI", "modelo": "MAG B650 TOMAHAWK WIFI"}) is None
    assert encaixe_cooler_placa({}, placa) is None
    catalogo = [{**air, "id": "1", "categoria": "air_cooler"}, {**placa, "id": "2", "categoria": "placa_mae"}]
    estado = {"componentes": {"air_cooler": {"id": "1"}, "placa_mae": {"id": "2"}}}
    resultado = AvaliarCompatibilidadeService().executar(estado, catalogo=catalogo)
    regra = next(r for r in resultado["verificacoes"] if r["codigo"] == "air_cooler-placa-excecao")
    assert regra["status"] == "incompativel"
