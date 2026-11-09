from services.validacoes_service.validar_pedido_build_service import validar_prioridade_montagem
from services.build_service.prompt_build_service import criar_prompt
import json
from contextlib import nullcontext

import pytest
from requests.exceptions import Timeout

from models import Usuario
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.gerar_build_service import GerarBuildService


@pytest.mark.parametrize('prioridade', ['custo_beneficio', 'desempenho'])
def test_escolha_do_frontend_chega_ao_pedido_do_modelo(prioridade):
    dados = dict(nome='PC', descricao='Teste', utilidade='Jogos', prioridade_montagem=prioridade)
    prompt = criar_prompt(dados, 8000, 2000, {})
    pedido = json.loads(prompt.split('# PEDIDO\n')[1].split('\n')[0])
    assert pedido['prioridade_montagem'] == prioridade
    assert '# PRIORIDADE DA MONTAGEM' in prompt
    assert 'não invente benchmarks ou ganhos percentuais' in prompt


def test_cliente_antigo_mantem_compatibilidade():
    assert validar_prioridade_montagem({}) == 'custo_beneficio'


@pytest.mark.parametrize('valor', [None, '', 'custo-beneficio', 'outro', [], {}, 1, True])
def test_prioridade_invalida_rejeitada_antes_de_acessar_banco(valor, mocker):
    buscar = mocker.patch.object(Usuario, 'buscar_por_id')
    with pytest.raises(ValueError, match='prioridade da montagem'):
        CriarBuildService().executar(1, dict(nome='PC', descricao='Teste', utilidade='Jogos',
                                           orcamento=8000, prioridade_montagem=valor))
    buscar.assert_not_called()


@pytest.mark.parametrize('prioridade', ['custo_beneficio', 'desempenho'])
def test_fallback_preserva_prioridade_selecionada(prioridade, mocker):
    mocker.patch('services.build_service.gerar_build_service.BloquearGeracaoService.executar',
                 return_value=nullcontext())
    criar = mocker.patch.object(CriarBuildService, 'executar', side_effect=[Timeout(), {'id': 1}])
    dados = dict(prioridade_montagem=prioridade)
    assert GerarBuildService().executar(7, dados) == {'id': 1}
    assert criar.call_args_list[0].args[1]['prioridade_montagem'] == prioridade
    assert criar.call_args_list[1].args[1]['prioridade_montagem'] == prioridade
