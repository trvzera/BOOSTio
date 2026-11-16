from copy import deepcopy

import pytest

from services.build_service.gerar_candidata_service import gerar_candidata
from services.build_service.prompt_build_service import criar_prompt
from services.validacoes_service.conferir_placa_video_service import ConferirPlacaVideoService
from services.validacoes_service.validar_build_gerada_service import validar_build_gerada
from tests.services.build_service.test_trabalho_pesado_gpu import cenario


@pytest.mark.parametrize('uso', ['Jogos', 'PC gamer', 'Jogos competitivos', 'Trabalho pesado'])
def test_a_partir_de_4000_jogos_e_trabalho_pesado_exigem_placa_de_video(uso):
    build, catalogo = cenario()
    with pytest.raises(ValueError, match='placa_video dedicada'):
        validar_build_gerada(build, catalogo, 4000, utilidade=uso)


def test_ryzen_g_nao_dispensa_placa_de_video_a_partir_de_4000():
    build, catalogo = cenario()
    catalogo['processador'][0].update(fabricante='AMD', modelo='Ryzen 7 8700G', videointegrado=True)
    with pytest.raises(ValueError, match='placa_video dedicada'):
        validar_build_gerada(build, catalogo, 8000, utilidade='Jogos')


def test_abaixo_de_4000_jogos_ainda_aceita_video_integrado():
    build, catalogo = cenario()
    assert validar_build_gerada(build, catalogo, 3999.99, utilidade='Jogos')['preco_total'] == 600


@pytest.mark.parametrize('uso', ['Estudos', 'Trabalho e estudo', 'Escritório', 'Um pouco de tudo'])
def test_outros_usos_nao_sao_obrigados_mesmo_com_orcamento_alto(uso):
    build, catalogo = cenario()
    assert validar_build_gerada(build, catalogo, 8000, utilidade=uso)['preco_total'] == 600


def test_placa_de_video_comprada_ou_propria_satisfaz():
    build, catalogo = cenario(com_gpu=True)
    assert validar_build_gerada(build, catalogo, 8000, utilidade='Jogos')['preco_total'] == 700
    build, catalogo = cenario()
    assert validar_build_gerada(build, catalogo, 8000, proprias={'placa_video': 'RTX 4060'},
                               detalhes_proprias={'placa_video': {'especificacoes_confirmadas': {'consumo_energia': 115}}},
                               utilidade='Jogos')['preco_total'] == 600


def test_ia_que_omite_a_placa_de_video_em_jogos_recebe_correcao(mocker):
    completa, catalogo = cenario(com_gpu=True)
    incompleta = deepcopy(completa)
    incompleta['componentes'] = [p for p in incompleta['componentes'] if p['tipo'] != 'placa_video']
    llm = mocker.patch('services.build_service.gerar_candidata_service.LLMService.executar',
                       side_effect=[incompleta, completa])
    mocker.patch('services.build_service.gerar_candidata_service.BuildSalva.verificar_espaco')
    resultado = gerar_candidata(1, 'Pedido: Jogos', 'teste', catalogo, 8000, 0, {}, {}, {}, utilidade='Jogos')
    assert any(p['tipo'] == 'placa_video' for p in resultado['componentes'])
    assert llm.call_count == 2 and 'placa_video dedicada' in llm.call_args.args[0]


def test_prompt_avisa_a_ia_antes_da_primeira_tentativa():
    _, catalogo = cenario(com_gpu=True)
    pedido = dict(nome='PC', descricao='Jogar', utilidade='Jogos')
    assert '"comprar_gpu_dedicada_pelo_orcamento": true' in criar_prompt(pedido, 8000, 800, catalogo)
    assert '"comprar_gpu_dedicada_pelo_orcamento": false' in criar_prompt(pedido, 3000, 800, catalogo)
    assert '"comprar_gpu_dedicada_pelo_orcamento": false' in criar_prompt(
        pedido, 8000, 800, catalogo, proprias={'placa_video': {}})


@pytest.mark.parametrize('orcamento', [None, 'abc', float('nan')])
def test_orcamento_invalido_nao_quebra_a_conferencia(orcamento):
    assert not ConferirPlacaVideoService.exige('Jogos', orcamento)


def test_falta_de_placa_de_video_nao_e_confundida_com_estouro_de_orcamento():
    from services.build_service.prompt_build_service import codigo_falha
    with pytest.raises(ValueError) as erro:
        ConferirPlacaVideoService.validar('Jogos', 8000, {'processador'})
    assert codigo_falha(erro.value) == 'pecas-obrigatorias'
