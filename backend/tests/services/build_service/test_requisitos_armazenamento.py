from services.build_service.prompt_build_service import criar_prompt
import json

import pytest

from models import Usuario
from services.build_service.criar_build_service import CriarBuildService
from services.build_service.requisitos_armazenamento_service import RequisitosArmazenamentoService as Requisitos
from services.build_service.seletor_inteligente_service import SeletorInteligenteService


@pytest.mark.parametrize('valor', [True, False, '500', 0, -1, 500.5, 500.0, [], {}, float('nan'), float('inf'), 1000001])
def test_parametro_invalido_rejeitado_antes_de_acessar_banco(valor, mocker):
    buscar = mocker.patch.object(Usuario, 'buscar_por_id')
    with pytest.raises(ValueError, match='armazenamento mínimo'):
        CriarBuildService().executar(1, dict(nome='PC', descricao='Teste', utilidade='Jogos', orcamento=8000,
                                           armazenamento_minimo_gb=valor))
    with pytest.raises(ValueError, match='armazenamento mínimo'):
        SeletorInteligenteService().executar(dict(orcamento=8000, prioridade_montagem='desempenho',
                                                armazenamento_minimo_gb=valor))
    buscar.assert_not_called()


@pytest.mark.parametrize('valor', [None, 1, 500, 1000, 1000000])
def test_parametro_opcional_em_gb(valor):
    assert Requisitos.validar_parametro(valor) == valor


def test_prompt_inclui_requisito_sem_inventar_minimo_padrao():
    dados = dict(nome='PC', descricao='Teste', utilidade='Jogos')
    for valor in (None, 1000):
        prompt = criar_prompt({**dados, 'armazenamento_minimo_gb': valor}, 8000, 2000, {})
        pedido = json.loads(prompt.split('# PEDIDO\n')[1].split('\n')[0])
        if valor is None:
            assert 'armazenamento_minimo_gb' not in pedido
        else:
            assert pedido['armazenamento_minimo_gb'] == 1000


def test_soma_capacidades_e_quantidades_do_catalogo_nao_da_ia():
    build = {'componentes': [{'tipo': 'ssd', 'id': 1, 'quantidade': 2, 'capacidade_gb': 999999},
                             {'tipo': 'hd', 'id': 1, 'quantidade': 1}]}
    catalogo = {'ssd': [{'id': 1, 'capacidade_gb': 256}], 'hd': [{'id': 1, 'capacidade_gb': 1000}]}
    Requisitos.validar_build(build, catalogo, 1512)
    with pytest.raises(ValueError, match='selecionado 1512 GB'):
        Requisitos.validar_build(build, catalogo, 1513)


def test_capacidade_de_peca_propria_reconhecida_conta_uma_vez():
    detalhes = {'ssd': {'especificacoes_confirmadas': {'capacidade_gb': 1000}}}
    Requisitos.validar_build({'componentes': []}, {}, 1000, {'ssd': 'Meu SSD'}, detalhes)
    with pytest.raises(ValueError, match='selecionado 1000 GB'):
        Requisitos.validar_build({'componentes': []}, {}, 1001, {'ssd': 'Meu SSD'}, detalhes)


@pytest.mark.parametrize('valor', [None, 0, -1, True, '1000', float('nan'), float('inf')])
def test_capacidade_desconhecida_nao_e_inventada(valor):
    with pytest.raises(ValueError, match='não permite confirmar'):
        Requisitos.validar_build({'componentes': [{'tipo': 'ssd', 'id': 1}]},
                                 {'ssd': [{'id': 1, 'capacidade_gb': valor}]}, 500)


def test_sem_parametro_preserva_comportamento_e_proprio_desconhecido_nao_apaga_total_confirmado():
    Requisitos.validar_build({'componentes': []}, {}, None)
    build = {'componentes': [{'tipo': 'hd', 'id': 1}]}
    catalogo = {'hd': [{'id': 1, 'capacidade_gb': 1000}]}
    Requisitos.validar_build(build, catalogo, 500, {'ssd': 'Desconhecido'})
    with pytest.raises(ValueError, match='não permite confirmar'):
        Requisitos.validar_build(build, catalogo, 2000, {'ssd': 'Desconhecido'})
