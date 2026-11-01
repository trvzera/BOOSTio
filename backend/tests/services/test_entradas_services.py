import importlib

import pytest


@pytest.mark.parametrize("modulo,classe,argumentos", [
    ("benchmark_service.blender_service", "BlenderService", (None, 1)),
    ("benchmark_service.buscar_jogos_benchmark_service", "BuscarJogosBenchmarkService", (None, 1)),
    ("benchmark_service.consultar_benchmark_service", "ConsultarBenchmarkService", (None, 1)),
    ("benchmark_service.consultar_requisitos_build_service", "ConsultarRequisitosBuildService", (None, 1)),
    ("benchmark_service.consultar_requisitos_service", "ConsultarRequisitosService", (None, 1)),
    ("benchmark_service.fpshq_service", "FpshqService", ("fps", None, 1)),
    ("build_service.avaliar_compatibilidade_service", "AvaliarCompatibilidadeService", (None,)),
    ("build_service.planejar_perifericos_service", "PlanejarPerifericosService", (None, 100)),
    ("build_service.planejar_rede_service", "PlanejarRedeService", (None,)),
    ("build_service.criar_build_manual_service", "CriarBuildManualService", (1, None)),
    ("peca_service.salvar_peca_service", "SalvarPecaService", (None, None)),
    ("peca_service.atualizar_imagem_peca_service", "AtualizarImagemPecaService", (None,)),
    ("configuracao_service.gerar_configuracao_frontend_service", "GerarConfiguracaoFrontendService", (None, "nao-criar.js")),
    ("llm_service.llm_service", "LLMService", (None,)),
    ("llm_service.llm_service", "LLMService", ("prompt", None)),
])
def test_rejeita_parametro_ausente_antes_de_acessar_dependencias(modulo, classe, argumentos, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    service = getattr(importlib.import_module("services." + modulo), classe)()
    with pytest.raises(ValueError):
        service.executar(*argumentos)
