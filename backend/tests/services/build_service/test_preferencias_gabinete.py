from copy import deepcopy

import pytest

from services.build_service.preferencias_gabinete_service import PreferenciasGabineteService as Gabinete
from services.build_service.preferencias_cores_service import PreferenciasCoresService as Cores
from services.build_service.criar_build_service import CriarBuildService


@pytest.mark.parametrize("modelo,esperado", [
    ("ATX", {"porte": None, "estilo": None}),
    ("Mini Tower Lateral em Vidro", {"porte": "mini-tower", "estilo": "vidro"}),
    ("Mid Tower Lateral e Frontal em Vidro", {"porte": "mid-tower", "estilo": "panoramico"}),
    ("Full Tower Aquário", {"porte": "full-tower", "estilo": "panoramico"}),
    ("Vidro na frente, lateral e teto", {"porte": None, "estilo": "panoramico-3-faces"}),
    ("Gabinete sem vidro", {"porte": None, "estilo": "discreto"}),
])
def test_estilo_e_porte_nao_sao_inferidos_de_atx_ou_foto(modelo, esperado):
    assert Gabinete.identificar({"modelo": modelo}) == esperado


def test_falta_full_tower_nao_descarta_estilo_panorama_preto():
    preferencia = {"porte": "full-tower", "estilo": "panoramico", "cor": "preto"}
    pecas = [{"id": 1, "modelo": "Mid Tower Lateral de Vidro Branco", "preco": 100},
             {"id": 2, "modelo": "Mid Tower Aquário Preto", "preco": 180}]
    assert Gabinete.destaques(pecas, preferencia)[0]["id"] == 2
    assert not any(Gabinete.identificar(p)["porte"] == "full-tower" for p in pecas)


def test_cor_so_troca_variantes_da_mesma_familia_e_ficha():
    branca = {"id": 1, "fabricante": "Marca", "modelo": "GM1 White", "preco": 99,
              "mecanico": True, "switch": "Brown", "layout": "ABNT2"}
    preta = {**branca, "id": 2, "modelo": "GM1 Black", "preco": 119}
    pior = {**preta, "id": 3, "mecanico": False}
    outra = {**preta, "id": 4, "modelo": "Outro Black"}
    assert Cores.alternativas_equivalentes(branca, [branca, preta, pior, outra], "preto") == [preta]
    assert Cores.alternativas_equivalentes(branca, [preta], "sem-preferencia") == []


def test_gpu_troca_cor_so_com_chip_e_memoria_confirmados():
    branca = {"id": 1, "categoria": "placa_video", "modelo": "AERO", "fabricante": "Gigabyte",
              "preco": 3000, "cor": "branco", "gpu_chip": "NVIDIA GeForce RTX 5060",
              "memoria_gb": 8, "tipo_memoria": "GDDR7", "interface_memoria": "128-bit"}
    preta = {**branca, "id": 2, "modelo": "SHADOW", "fabricante": "MSI", "preco": 3300, "cor": "preto"}
    outra_gpu = {**preta, "id": 3, "gpu_chip": "NVIDIA GeForce RTX 5050"}
    outra_memoria = {**preta, "id": 4, "memoria_gb": 4}
    desconhecida = {**preta, "id": 5, "interface_memoria": None}
    assert Cores.alternativas_equivalentes(branca, [preta, outra_gpu, outra_memoria, desconhecida], "preto") == [preta]
    assert Cores.alternativas_equivalentes({**branca, "gpu_chip": None}, [preta], "preto") == []


def test_ficha_de_cor_da_gpu_exige_anuncio_e_variante_exatos():
    from models.medidas_fisicas import completar_medidas
    dados = {"categoria": "placa_video", "fabricante": "Gigabyte", "modelo": "RTX 5060 AERO OC 8G GeForce",
             "part_number": "SEED-GPU-14", "link": "https://www.kabum.com.br/produto/777072/placa"}
    assert completar_medidas(dados)["cor"] == "branco"
    assert "cor" not in completar_medidas({**dados, "link": "https://www.kabum.com.br/produto/999999/placa"})


def test_ajuste_estetico_revalida_orcamento_antes_de_trocar(mocker):
    branca = {"id": 1, "fabricante": "Marca", "modelo": "GM1 White", "preco": 99}
    preta = {**branca, "id": 2, "modelo": "GM1 Black", "preco": 119}
    build = {"componentes": [{"tipo": "teclado", "id": 1, "quantidade": 1}]}
    antes = deepcopy(build)
    mocker.patch("services.build_service.criar_build_service.CompletarVentilacaoService.executar", side_effect=lambda b,*a,**k:b)
    validar = mocker.patch.object(CriarBuildService, "_validar_build", side_effect=ValueError("Teto de periféricos"))
    assert CriarBuildService()._ajustar_aparencia(build, {"teclado": [branca, preta]}, 8000, 10, {}, {}, {}, {"cor": "preto"}) == antes
    validar.assert_called_once()
    validar.side_effect = lambda b,*a,**k:b
    assert CriarBuildService()._ajustar_aparencia(build, {"teclado": [branca, preta]}, 8000, 10, {}, {}, {}, {"cor": "preto"})["componentes"][0]["id"] == 2
    assert build == antes


def test_avisa_preferencias_nao_confirmadas_sem_tratar_atx_como_full_tower():
    itens = [("gabinete", {"id": 1}, {"categoria": "gabinete", "modelo": "ATX Branco"})]
    orientacoes = Gabinete.orientacoes({"aparencia": {"porte": "full-tower", "estilo": "panoramico", "cor": "preto"}}, itens)
    assert {o["codigo"] for o in orientacoes} == {"aparencia-gabinete", "aparencia-cor"}
    assert "Full Tower" in orientacoes[0]["mensagem"] and "aquário" in orientacoes[0]["mensagem"]
    assert "outra cor" in orientacoes[1]["mensagem"]
