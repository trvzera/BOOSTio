from copy import deepcopy

import pytest

from services.build_service.gerar_candidata_service import gerar_candidata
from services.build_service.prompt_build_service import criar_prompt
from services.validacoes_service.requisitos_uso_service import RequisitosUsoService
from services.validacoes_service.validar_build_gerada_service import validar_build_gerada


def cenario(com_gpu=False):
    tipos = ['processador', 'placa_mae', 'memoria_ram', 'ssd', 'fonte', 'gabinete']
    if com_gpu:
        tipos.append('placa_video')
    catalogo = {tipo: [dict(id=1, fabricante='Teste', modelo=tipo, preco=100, esgotado=False)] for tipo in tipos}
    catalogo['processador'][0].update(videointegrado=True, cooler=True, consumo_energia=65)
    catalogo['fonte'][0]['potencia_w'] = 500
    catalogo['gabinete'][0]['fans_inclusos'] = 1
    catalogo['memoria_ram'][0]['quantidade_pentes'] = 1
    if com_gpu:
        catalogo['placa_video'][0]['consumo_energia'] = 115
    build = dict(nome='PC', descricao='Teste', utilidade='Estudos',
                 componentes=[dict(tipo=tipo, id=1, quantidade=1) for tipo in tipos])
    return build, catalogo


@pytest.mark.parametrize('uso', ['Trabalho pesado', 'trabalho-pesado', 'TRABALHO_PESADO', 'Trabalho pesado para edição'])
def test_video_integrado_nao_substitui_gpu_no_pedido_original(uso):
    build, catalogo = cenario()
    with pytest.raises(ValueError, match='placa_video dedicada'):
        validar_build_gerada(build, catalogo, 3000, utilidade=uso)


def test_gpu_dedicada_nova_ou_propria_satisfaz_requisito():
    build, catalogo = cenario(com_gpu=True)
    assert validar_build_gerada(build, catalogo, 3000, utilidade='Trabalho pesado')['preco_total'] == 700
    build, catalogo = cenario()
    assert validar_build_gerada(build, catalogo, 3000, proprias={'placa_video': 'RTX 4060'},
                               detalhes_proprias={'placa_video': {'especificacoes_confirmadas': {'consumo_energia': 115}}},
                               utilidade='Trabalho pesado')['preco_total'] == 600


@pytest.mark.parametrize('uso', ['Estudos', 'Trabalho casual', 'Servidor NAS'])
def test_outros_usos_preservam_opcao_de_video_integrado(uso):
    build, catalogo = cenario()
    assert validar_build_gerada(build, catalogo, 3000, utilidade=uso)['preco_total'] == 600
    assert not RequisitosUsoService.exige_gpu_dedicada(uso)


def test_ia_corrige_gpu_ausente_sem_mudar_utilidade_para_burlar_regra(mocker):
    completa, catalogo = cenario(com_gpu=True)
    incompleta = deepcopy(completa)
    incompleta['componentes'] = [p for p in incompleta['componentes'] if p['tipo'] != 'placa_video']
    llm = mocker.patch('services.build_service.gerar_candidata_service.LLMService.executar',
                       side_effect=[incompleta, completa])
    mocker.patch('services.build_service.gerar_candidata_service.BuildSalva.verificar_espaco')
    resultado = gerar_candidata(1, 'Pedido: Trabalho pesado', 'teste', catalogo, 3000, 0, {}, {}, {},
                                utilidade='Trabalho pesado')
    assert any(p['tipo'] == 'placa_video' for p in resultado['componentes'])
    assert llm.call_count == 2
    assert 'placa_video dedicada' in llm.call_args.args[0]


def test_prompt_exige_gpu_sem_recomprar_placa_propria():
    _, catalogo = cenario(com_gpu=True)
    pedido = dict(nome='PC', descricao='Edição', utilidade='Trabalho pesado')
    prompt = criar_prompt(pedido, 3000, 800, catalogo)
    assert '"gpu_dedicada_exigida_pelo_uso": true' in prompt
    assert '"comprar_gpu_para_trabalho_pesado": true' in prompt
    prompt = criar_prompt(pedido, 3000, 800, catalogo, proprias={'placa_video': {}})
    assert '"comprar_gpu_para_trabalho_pesado": false' in prompt
