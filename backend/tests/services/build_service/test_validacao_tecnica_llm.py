from copy import deepcopy

import pytest

from services.build_service.criar_build_service import CriarBuildService


@pytest.fixture
def sugestao():
    especificacoes = {
        "processador": {"soquete": "AM4", "videointegrado": True, "cooler": True, "consumo_energia": 65},
        "placa_mae": {"socket": "AM4", "tipo_memoria": "DDR4", "quantidade_slots_ram": 2,
                      "memoria_maxima_gb": 64, "quantidade_slots_m2": 1, "formato": "mATX"},
        "memoria_ram": {"ddr": "DDR4", "capacidade_gb": 8, "quantidade_pentes": 1},
        "ssd": {"interface": "NVMe", "formato": "M.2"},
        "fonte": {"potencia_w": 500},
        "gabinete": {"formatos_placa_mae": "mATX, ITX", "tamanho_max_gpu_mm": 300,
                     "tamanho_max_cooler_mm": 160, "suporte_water_cooler": False},
    }
    catalogo = {tipo: [{"id": 1, "fabricante": "Teste", "modelo": tipo, "preco": 100,
                        "consumo_energia": 5, **campos}] for tipo, campos in especificacoes.items()}
    build = {"nome": "Sugestão", "descricao": "PC de teste", "utilidade": "Estudos",
             "componentes": [{"tipo": tipo, "id": 1, "quantidade": 1} for tipo in catalogo]}
    return build, catalogo


def validar(sugestao, **opcoes):
    build, catalogo = deepcopy(sugestao)
    return CriarBuildService._validar_build(build, catalogo, 5000, **opcoes)


def adicionar(sugestao, tipo, **campos):
    build, catalogo = sugestao
    catalogo[tipo] = [{"id": 1, "fabricante": "Teste", "modelo": tipo, "preco": 100,
                       "consumo_energia": 5, **campos}]
    build["componentes"].append({"tipo": tipo, "id": 1, "quantidade": 1})


@pytest.mark.parametrize("tipo,campo,valor", [
    ("processador", "soquete", "AM5"),
    ("memoria_ram", "ddr", "DDR5"),
    ("memoria_ram", "capacidade_gb", 128),
    ("placa_mae", "formato", "ATX"),
    ("fonte", "potencia_w", 50),
])
def test_rejeita_conflito_confirmado_no_catalogo(sugestao, tipo, campo, valor):
    sugestao[1][tipo][0][campo] = valor
    with pytest.raises(ValueError, match="incompatibilidades"):
        validar(sugestao)


@pytest.mark.parametrize("tipo", ["memoria_ram", "ssd"])
def test_revalida_quantidades_slots_e_kits(sugestao, tipo):
    item = next(item for item in sugestao[0]["componentes"] if item["tipo"] == tipo)
    item["quantidade"] = 3 if tipo == "memoria_ram" else 2
    with pytest.raises(ValueError, match="incompatibilidades"):
        validar(sugestao)
    if tipo == "memoria_ram":
        item["quantidade"] = 2
        sugestao[1][tipo][0]["quantidade_pentes"] = 2
        with pytest.raises(ValueError, match="incompatibilidades"):
            validar(sugestao)


@pytest.mark.parametrize("tipo,campos", [
    ("placa_video", {"comprimento_mm": 301}),
    ("air_cooler", {"altura_mm": 161, "compatibilidade": "AM4"}),
    ("air_cooler", {"altura_mm": 150, "compatibilidade": "AM5"}),
    ("water_cooler", {"tamanho_radiador_mm": 360, "compatibilidade": "AM4"}),
])
def test_revalida_encaixe_e_cooler(sugestao, tipo, campos):
    adicionar(sugestao, tipo, **campos)
    with pytest.raises(ValueError, match="incompatibilidades"):
        validar(sugestao)


@pytest.mark.parametrize("campo,pendente", [("videointegrado", "placa_video"), ("cooler", "cooler")])
def test_exige_gpu_ou_cooler_quando_cpu_precisa(sugestao, campo, pendente):
    sugestao[1]["processador"][0][campo] = False
    with pytest.raises(ValueError, match=pendente):
        validar(sugestao)


def test_nao_bloqueia_sugestao_so_por_especificacoes_ausentes(sugestao):
    for itens in sugestao[1].values():
        itens[0] = {k: v for k, v in itens[0].items() if k in ("id", "fabricante", "modelo", "preco")}
    assert validar(sugestao)["preco_total"] == 600


def test_valida_peca_propria_identificada_sem_inventar_dados(sugestao):
    build, catalogo = sugestao
    build["componentes"] = [item for item in build["componentes"] if item["tipo"] != "processador"]
    del catalogo["processador"]
    proprias = {"processador": "Minha CPU"}
    assert validar(sugestao, proprias=proprias)["preco_total"] == 500
    detalhes = {"processador": {"especificacoes_confirmadas": {"soquete": "AM5"}}}
    with pytest.raises(ValueError, match="incompatibilidades"):
        validar(sugestao, proprias=proprias, detalhes_proprias=detalhes)


@pytest.mark.parametrize("preco", [None, True, "100", 0, -1, float("nan"), float("inf")])
def test_rejeita_precos_desconhecidos_ou_invalidos(sugestao, preco):
    sugestao[1]["ssd"][0]["preco"] = preco
    with pytest.raises(ValueError, match="preço válido"):
        validar(sugestao)


def test_nao_aceita_peca_esgotada_ou_especificacoes_inventadas_pela_ia(sugestao):
    sugestao[1]["ssd"][0]["esgotado"] = True
    with pytest.raises(ValueError, match="indisponível"):
        validar(sugestao)
    sugestao[1]["ssd"][0]["esgotado"] = False
    sugestao[1]["processador"][0]["soquete"] = "AM5"
    sugestao[0]["componentes"][0]["soquete"] = "AM4"
    with pytest.raises(ValueError, match="incompatibilidades"):
        validar(sugestao)


def test_prompt_recebe_os_dados_tecnicos_que_a_validacao_usa():
    from models import PlacaMae, AirCooler, Gabinete

    dados = CriarBuildService._campos_pecas(PlacaMae(id=1, quantidade_slots_ram=4, quantidade_slots_m2=2))
    assert dados["quantidade_slots_ram"] == 4
    assert dados["quantidade_slots_m2"] == 2
    dados = CriarBuildService._campos_pecas(AirCooler(id=2, compatibilidade="AM4, AM5"))
    assert dados["compatibilidade"] == "AM4, AM5"
    dados = CriarBuildService._campos_pecas(Gabinete(id=3, tamanho_max_gpu_mm=320, tamanho_max_cooler_mm=160))
    assert dados["tamanho_max_gpu_mm"] == 320
    assert dados["tamanho_max_cooler_mm"] == 160


def test_geracao_completa_sete_posicoes_descontando_duas_fans_do_water(sugestao):
    build, catalogo = sugestao
    catalogo["gabinete"][0].update(fans_inclusos=0, quantidade_max_fans=7,
                                 tamanhos_fan_suportados_mm=[120], suporte_water_cooler=True,
                                 radiadores_suportados_mm=[240])
    adicionar(sugestao, "water_cooler", tamanho_radiador_mm=240, quantidade_fans=2, tamanho_fan_mm=120)
    adicionar(sugestao, "fan", tamanho_mm=120, quantidade=1)
    fan = build["componentes"][-1]
    fan["quantidade"] = 4
    with pytest.raises(ValueError, match="faltam 1 fans"):
        validar(sugestao)
    fan["quantidade"] = 5
    assert validar(sugestao)["preco_total"] == 1200
    fan["quantidade"] = 7
    with pytest.raises(ValueError, match="incompatibilidades"):
        validar(sugestao)


def test_geracao_nao_omite_fans_quando_so_gabinete_foi_selecionado(sugestao):
    sugestao[1]["gabinete"][0].update(fans_inclusos=0, quantidade_max_fans=2)
    with pytest.raises(ValueError, match="faltam 2 fans"):
        validar(sugestao)
    sugestao[1]["gabinete"][0]["fans_inclusos"] = 2
    assert validar(sugestao)["preco_total"] == 600


def test_prompt_descreve_ventilacao_sem_inferir_tamanho_do_gabinete_ou_folga():
    prompt = CriarBuildService._criar_prompt({"nome": "QA", "descricao": "QA", "utilidade": "Jogos"}, 5000, 800, {})
    assert "sete posições" in prompt and "cinco fans" in prompt
    assert "Não planeje substituir fans originais" in prompt
    assert "Não some uma folga genérica" in prompt
    assert "fonte_fluxo_ar nome_comercial" in prompt
