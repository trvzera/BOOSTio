from decimal import Decimal
from copy import deepcopy
import json
import pytest
from services.build_service.planejamento_geracao import validar_minimos, validar_percentual, ErroPlanejamentoBuild, RecusaModeloBuild
from services.build_service.preferencias_processador_service import PreferenciasProcessadorService
from services.build_service.prompt_build_service import criar_prompt, criar_prompt_correcao
from services.validacoes_service.requisitos_uso_service import RequisitosUsoService

@pytest.mark.parametrize("uso,minimo",[("Jogos",3500),("Planilhas",2500),("Reuniões",2500),("Edição de vídeos e imagens",3500),("Modelagem 3D",3500),("Programação",3500),("Estudos",2500),("Um pouco de tudo",2500)])
def test_minimo_depende_do_uso_e_e_aplicado_depois_dos_perifericos(uso,minimo):
    with pytest.raises(ErroPlanejamentoBuild) as erro:
        validar_minimos(Decimal(minimo)-Decimal(".01"),Decimal("1000"),20,uso)
    assert erro.value.geracao["etapa"]=="orcamento"
    validar_minimos(Decimal(minimo),Decimal("1000"),20,uso)

@pytest.mark.parametrize("p",[1,9,41,99,100,True,10.0,"20",None])
def test_percentual_invalido_e_barrado(p):
    with pytest.raises(ErroPlanejamentoBuild): validar_percentual(p)

@pytest.mark.parametrize("p",[0,10,20,40])
def test_percentual_valido_inclui_limites(p):
    assert validar_percentual(p)==p

def test_edicao_e_3d_recebem_gpu_obrigatoria_e_prioridade_de_ram():
    for uso in ["Edição de vídeos e imagens","Modelagem 3D"]:
        with pytest.raises(ValueError,match="placa_video dedicada"):
            RequisitosUsoService.validar_gpu(uso,{"processador"})
        RequisitosUsoService.validar_gpu(uso,{"placa_video"})
    assert not RequisitosUsoService.exige_gpu_dedicada("Programação")
    prompt=criar_prompt({"nome":"PC","descricao":"Teste","utilidade":"Edição de vídeos e imagens"},8000,2000,{})
    pedido=json.loads(prompt.split("# PEDIDO\n")[1].split("\n")[0])
    assert pedido["criterios_uso"]["memoria_alvo_gb"]==32

def test_marca_escolhida_nao_vira_fallback_nem_troca_peca_propria():
    catalogo={"processador":[{"id":1,"fabricante":"Intel"},{"id":2,"fabricante":"AMD"}],"placa_video":[{"id":3,"fabricante":"NVIDIA"}]}
    original=deepcopy(catalogo)
    PreferenciasProcessadorService.exigir_catalogo(catalogo,"amd")
    assert [p["id"] for p in catalogo["processador"]]==[2]
    assert catalogo["placa_video"]==original["placa_video"]
    with pytest.raises(ErroPlanejamentoBuild): PreferenciasProcessadorService.exigir_catalogo(catalogo,"intel")
    with pytest.raises(ErroPlanejamentoBuild):
        PreferenciasProcessadorService.exigir_catalogo(original,"amd",{"processador":"Intel"},{"processador":{"especificacoes_confirmadas":{"fabricante":"Intel"}}})

def test_recusa_visual_recebe_revisao_flexivel_sem_mudar_limites():
    prompt=criar_prompt_correcao("Pedido original",RecusaModeloBuild("aparencia"),{},None,{},8000,20)
    assert "cor, tamanho e estilo do gabinete são flexíveis" in prompt
    assert '"teto_pc": 6400.0' in prompt
    assert '"teto_perifericos": 1600.0' in prompt
    assert "marca obrigatória" in prompt

from tests.services.build_service.test_criacao_build import app_build, cadastrar_pecas, autenticar
from models import BuildSalva


@pytest.mark.parametrize("uso", ["Jogos", "Planilhas", "Reuniões", "Edição de vídeos e imagens", "Modelagem 3D", "Programação", "Estudos", "Um pouco de tudo"])
def test_api_gera_e_salva_os_novos_usos_com_llm_simulada(app_build, mocker, uso):
    tipos = ["processador", "placa_mae", "memoria_ram", "fonte", "gabinete", "ssd"]
    if uso in ("Jogos", "Edição de vídeos e imagens", "Modelagem 3D"):
        tipos.append("placa_video")
    with app_build.app_context():
        cadastrar_pecas(tipos)
    llm = mocker.patch("services.build_service.gerar_candidata_service.LLMService.executar", return_value={
        "nome": "PC", "descricao": "Teste", "utilidade": uso,
        "componentes": [{"tipo": t, "id": 1, "quantidade": 1} for t in tipos]})
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json={"nome": "PC", "descricao": "Teste", "utilidade": uso, "orcamento": 5000})
    assert resposta.status_code == 201, resposta.json
    llm.assert_called_once()
    with app_build.app_context():
        assert BuildSalva.query.count() == 1


@pytest.mark.parametrize("pct", [9, 41])
def test_api_rejeita_percentual_fora_da_faixa_sem_consumir_ia(app_build, mocker, pct):
    llm = mocker.patch("services.build_service.gerar_candidata_service.LLMService.executar")
    cliente = app_build.test_client()
    autenticar(cliente)
    resposta = cliente.post("/build/", json={"nome": "PC", "descricao": "Teste", "utilidade": "Estudos", "orcamento": 10000, "percentual_perifericos": pct})
    assert resposta.status_code == 400
    assert resposta.json["geracao"]["etapa"] == "perifericos"
    llm.assert_not_called()
    with app_build.app_context():
        assert BuildSalva.query.count() == 0
