import json
from unittest.mock import patch
import pytest
from models import BuildSalva
from services.build_service.criar_build_service import CriarBuildService
from utils.aparencia import validar_aparencia


@pytest.mark.parametrize("valor", [[], "branco", {"cor":"azul"}, {"estilo":"<script>"}, {"porte":"ATX"}, {"porte":[]}, {"gabinete_id":True}, {"gabinete_id":0}, {"gabinete_id":1.5}, {"outro":1}])
def test_rejeita_preferencias_invalidas(valor):
    with pytest.raises(ValueError):
        validar_aparencia(valor)


def test_preferencia_opcional_persistida_sem_exigir_peca():
    preferencia={"estilo":"vidro","cor":"branco","gabinete_id":999}
    assert validar_aparencia() == {"estilo":"sem-preferencia","porte":"sem-preferencia","cor":"sem-preferencia","gabinete_id":None}
    assert BuildSalva.validar_estado({"titulo":"PC","aparencia":preferencia})["aparencia"] == validar_aparencia(preferencia)
    dados={"nome":"PC","descricao":"Teste","utilidade":"Estudos","aparencia":preferencia}
    prompt=CriarBuildService._criar_prompt(dados,5000,800,{})
    pedido=json.loads(prompt.split("# PEDIDO\n")[1].split("\n")[0])
    assert pedido["aparencia"] == validar_aparencia(preferencia)
    assert "referência visual, não uma obrigação" in prompt
    assert "não são uma recomendação de qualidade" in prompt
    assert "DPI alto" in prompt


def test_preferencia_invalida_nao_chega_a_llm():
    with patch("services.build_service.criar_build_service.LLMService.executar") as llm:
        with pytest.raises(ValueError):
            CriarBuildService().executar(1,{"nome":"PC","descricao":"Teste","utilidade":"Estudos","orcamento":5000,"aparencia":{"cor":"azul"}})
        llm.assert_not_called()


@pytest.mark.parametrize("porte", ["mini-tower", "mid-tower", "full-tower"])
@pytest.mark.parametrize("estilo", ["discreto", "vidro", "panoramico", "panoramico-3-faces"])
def test_estilo_e_tamanho_independentes_persistidos_e_enviados_no_prompt(porte, estilo):
    preferencia = {"estilo": estilo, "porte": porte, "cor": "preto", "gabinete_id": None}
    assert validar_aparencia(preferencia) == preferencia
    assert BuildSalva.validar_estado({"titulo": "PC", "aparencia": preferencia})["aparencia"] == preferencia
    prompt = CriarBuildService._criar_prompt({"nome": "PC", "descricao": "Teste", "utilidade": "Jogos", "aparencia": preferencia}, 5000, 800, {})
    pedido = json.loads(prompt.split("# PEDIDO\n")[1].split("\n")[0])
    assert pedido["aparencia"] == preferencia
    assert "panoramico-3-faces indica vidro na frente, lateral e teto" in prompt
    assert "painel_vidro=True sozinho não confirma" in prompt
    assert "não conte radiador ou ventoinhas no teto sem suporte confirmado" in prompt
    assert "não são limites universais do porte" in prompt


def test_compacto_legado_continua_valido_sem_virar_tamanho():
    assert validar_aparencia({"estilo": "compacto"})["estilo"] == "compacto"
    assert validar_aparencia({"estilo": "compacto"})["porte"] == "sem-preferencia"
