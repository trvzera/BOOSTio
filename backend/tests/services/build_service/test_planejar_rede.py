from copy import deepcopy
from unittest.mock import patch

import pytest

from services.build_service.planejar_rede_service import PlanejarRedeService as Rede
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService


PEDIDO = {"tipo": "cabo", "possuiAcessorio": False, "comprimentoCaboM": 20, "velocidadeMbps": 500}
CATALOGO = {"cabo_rede": [
    {"id": 1, "preco": 30, "comprimento_m": 1},
    {"id": 2, "preco": 60, "comprimento_m": 10},
    {"id": 3, "preco": 120, "comprimento_m": 20, "esgotado": True},
]}


def test_vinte_metros_sem_cabo_adequado_vira_pendencia_sem_alterar_pedido():
    antes = deepcopy(PEDIDO)
    assert Rede.executar(CATALOGO, PEDIDO) == {"tipo": "cabo_rede", "ids_permitidos": [], "pendente": True}
    assert PEDIDO == antes
    prompt = CriarBuildService._criar_prompt({"nome": "PC", "descricao": "Jogos", "utilidade": "Jogos", "rede": PEDIDO}, 8000, 2000, CATALOGO, 10)
    assert '"acessorio_rede_obrigatorio": null' in prompt
    assert '"categorias_rede_proibidas": ["adaptador_wifi", "cabo_rede"]' in prompt
    assert "Isso não inviabiliza" in prompt


@pytest.mark.parametrize("comprimento", [None, 0, -1, True, 10, float("nan"), float("inf")])
def test_comprimento_desconhecido_ou_curto_nao_aprova_cabo(comprimento):
    assert not Rede.opcoes({"cabo_rede": [{"id": 1, "preco": 50, "comprimento_m": comprimento}]}, PEDIDO)


def test_cabo_longo_sem_taxa_cadastrada_nao_inventa_velocidade():
    cabo = {"id": 4, "preco": 80, "comprimento_m": 25, "fabricante": "Teste", "modelo": "CAT6 25m"}
    assert Rede.opcoes({"cabo_rede": [cabo]}, PEDIDO) == [cabo]
    assert "velocidade_mbps" not in cabo
    assert not Rede.opcoes({"cabo_rede": [{**cabo, "velocidade_mbps": 100}]}, PEDIDO)


def test_nao_compra_rede_ja_possuida_ou_nao_solicitada():
    for rede, proprias in [({**PEDIDO, "possuiAcessorio": True}, {}), ({}, {}), (PEDIDO, {"cabo_rede": "Meu cabo"})]:
        assert Rede.executar(CATALOGO, rede, proprias)["tipo"] is None


def test_complemento_remove_somente_cabo_impossivel_sem_inventar_produto():
    build = {"componentes": [{"tipo": "processador", "id": 9}, {"tipo": "cabo_rede", "id": 1}]}
    antes = deepcopy(build)
    assert Rede.completar(build, CATALOGO, PEDIDO) == {"componentes": [{"tipo": "processador", "id": 9}]}
    assert build == antes


def test_complemento_inclui_opcao_adequada_mas_total_ainda_e_validado():
    cabo = {"id": 4, "preco": 80, "comprimento_m": 25, "fabricante": "Teste", "modelo": "CAT6 25m"}
    catalogo = {"cabo_rede": [*CATALOGO["cabo_rede"], cabo]}
    build = {"componentes": [{"tipo": "cabo_rede", "id": 1}]}
    assert Rede.completar(build, catalogo, PEDIDO)["componentes"] == [{"tipo": "cabo_rede", "id": 4, "quantidade": 1}]
    assert Rede.completar({"componentes": []}, catalogo, PEDIDO)["componentes"][0]["id"] == 4
    with pytest.raises(ValueError, match="orçamento"):
        CriarBuildService._validar_build({"nome": "PC", "descricao": "Teste", "utilidade": "Jogos",
            **Rede.completar({"componentes": []}, catalogo, PEDIDO)}, catalogo, 50, rede=PEDIDO)


def test_diagnostico_preserva_pendencia_no_editor_sem_bloquear_pc():
    dados = AvaliarCompatibilidadeService().executar({"componentes": {}, "rede": PEDIDO}, catalogo=[])
    texto = next(o["mensagem"] for o in dados["orientacoes"] if o["codigo"] == "rede-pendente")
    assert "20 m" in texto and "nem no total" in texto
    assert "cabo_rede" not in dados["pecasPendentes"]


def test_recuperacao_rede_usa_mesma_chamada_e_nao_modifica_flag_de_posse():
    resposta = {"componentes": [{"tipo": "cabo_rede", "id": 1}]}
    with patch("services.build_service.criar_build_service.LLMService.executar", return_value=resposta) as llm, \
         patch("services.build_service.criar_build_service.CompletarVentilacaoService.executar", side_effect=lambda b,*a,**k:b), \
         patch.object(CriarBuildService, "_validar_build", side_effect=lambda b,*a,**k:b):
        resultado = CriarBuildService()._gerar_validada(1, "Prompt", "teste", CATALOGO, 8000, 10, {}, {}, PEDIDO, tentativas_correcao=0)
    assert resultado["componentes"] == [] and PEDIDO["possuiAcessorio"] is False
    llm.assert_called_once()
