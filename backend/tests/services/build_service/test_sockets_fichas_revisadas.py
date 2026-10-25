import json
from copy import deepcopy
from pathlib import Path

import pytest

from models.medidas_fisicas import completar_medidas
from services.build_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService
from utils.sockets import normalizar_socket, listar_sockets, suporte_socket_cooler

FIXTURES = Path(__file__).resolve().parents[4] / 'frontend/tests/fixtures'
SOCKETS = json.loads((FIXTURES / 'sockets.json').read_text())
ORIGINAIS = json.loads((FIXTURES / 'revisao-compatibilidade.json').read_text())
CATALOGO = [completar_medidas(p) for p in ORIGINAIS]


@pytest.mark.parametrize('valor,esperado', SOCKETS['normalizar'])
def test_normalizar_socket_sem_aproximar_familias(valor, esperado):
    assert normalizar_socket(valor) == esperado


@pytest.mark.parametrize('valor,esperado', SOCKETS['listar'])
def test_listas_explicitas_sem_tratar_marca_como_socket(valor, esperado):
    assert listar_sockets(valor) == esperado


@pytest.mark.parametrize('socket,cooler,esperado', SOCKETS['cooler'])
def test_kit_ou_revisao_pendente_nao_vira_aprovacao(socket, cooler, esperado):
    assert suporte_socket_cooler(socket, cooler) is esperado


def estado():
    return {'componentes': {
        'processador': {'id': 'processador:6'}, 'placa_mae': {'id': 'placa_mae:91'},
        'placa_video': {'id': 'placa_video:99'}, 'air_cooler': {'id': 'air_cooler:19'},
        'fonte': {'id': 'fonte:4'}, 'gabinete': {'id': 'gabinete:54'},
        'memoria_ram': [{'id': 'memoria_ram:56', 'quantidade': 2}],
        'ssd': [{'id': 'ssd:31', 'quantidade': 1}], 'fan': [{'id': 'fan:60', 'quantidade': 2}],
    }}


def avaliar(build=None, catalogo=None):
    r = AvaliarCompatibilidadeService().executar(build or estado(), catalogo=catalogo or CATALOGO)
    return {i['codigo']: i['status'] for i in r['verificacoes']}


def test_hpm610_resolve_ram_m2_fans_e_nao_inventa_folgas_bios_ou_kit():
    r = avaliar()
    for codigo in ('socket', 'ram-slots', 'ram-capacidade', 'discos-m2', 'fans-quantidade', 'gpu-slots', 'fonte-formato'):
        assert r[codigo] == 'sem_conflitos', codigo
    for codigo in ('suporte-cpu-bios', 'ram-perfis', 'air_cooler-socket', 'placa_video-medida', 'fans-posicoes'):
        assert r[codigo] == 'nao_verificado', codigo
    assert 'incompativel' not in r.values()
    for categoria, quantidade, codigo in [('memoria_ram', 3, 'ram-slots'), ('ssd', 2, 'discos-m2'), ('fan', 4, 'fans-quantidade')]:
        b = estado()
        b['componentes'][categoria][0]['quantidade'] = quantidade
        assert avaliar(b)[codigo] == 'incompativel'


def test_socket_normalizado_confirma_encaixe_e_nunca_a_bios():
    cat = deepcopy(CATALOGO)
    placa = next(p for p in cat if p['id'] == 'placa_mae:91')
    placa['socket'] = 'Intel Socket LGA 1700'
    assert avaliar(catalogo=cat)['socket'] == 'sem_conflitos'
    assert avaliar(catalogo=cat)['suporte-cpu-bios'] == 'nao_verificado'
    placa['socket'] = 'AM5'
    assert avaliar(catalogo=cat)['socket'] == 'incompativel'
    placa['socket'] = None
    assert avaliar(catalogo=cat)['socket'] == 'nao_verificado'


@pytest.mark.parametrize('p', [p for p in ORIGINAIS if p['categoria'] == 'placa_mae'], ids=lambda p:p['part_number'])
def test_anuncio_e_variante_exatos_sem_mudar_preco_ou_estoque(p):
    for mudanca in ({'link': 'https://www.kabum.com.br/produto/999999'}, {'modelo': p['modelo'] + ' V3'}):
        assert 'fonte_medidas' not in completar_medidas({**p, **mudanca})
    revisada = completar_medidas({**p, 'preco': 123, 'esgotado': True})
    assert revisada['preco'] == 123 and revisada['esgotado'] is True
    if p['id'] in ('placa_mae:10', 'placa_mae:14', 'placa_mae:85'):
        assert revisada['quantidade_slots_ram'] == 2 and revisada['memoria_maxima_gb'] == 64
    if p['id'] == 'placa_mae:88':
        assert revisada['tipo_memoria'] == 'DDR5' and revisada['memoria_maxima_gb'] is None
