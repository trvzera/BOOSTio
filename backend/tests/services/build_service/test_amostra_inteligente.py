from copy import deepcopy

import pytest

from services.build_service.amostra_inteligente_service import AmostraInteligenteService as Amostra


def cpu(ident, preco, multi, single=100, **extras):
    return dict(id=ident, categoria='processador', preco=preco, benchmark_multi_core=multi,
                benchmark_single_thread=single, benchmark_teste='PassMark CPU Mark / Single Thread',
                benchmark_versao=None, consumo_energia=65, soquete='AM4', videointegrado=False,
                cooler=False, nucleo=6, thread=12, **extras)


def test_pareto_remove_apenas_dominada_e_preserva_igual_e_troca_entre_metricas():
    a = cpu(1, 100, 200)
    b = cpu(2, 150, 150, 90)
    c = cpu(3, 150, 250, 80)
    d = cpu(4, 100, 200)
    mantidas, removidas = Amostra().pareto([a, b, c, d], 'processador')
    assert {p['id'] for p in mantidas} == {1, 3, 4}
    assert removidas == [2]


@pytest.mark.parametrize('alteracao', [dict(soquete='AM5'), dict(videointegrado=True, modelo_videointegrado='GPU'),
                                     dict(consumo_energia=35), dict(cooler=True, modelo_cooler='Box'),
                                     dict(nucleo=8), dict(benchmark_versao='outra'),
                                     dict(benchmark_teste='Outro teste'), dict(benchmark_single_thread=None),
                                     dict(consumo_energia=None), dict(consumo_energia=0)])
def test_pareto_preserva_recursos_diferentes_e_informacao_desconhecida(alteracao):
    forte = cpu(1, 100, 200)
    candidato = {**cpu(2, 150, 150, 90), **alteracao}
    mantidas, removidas = Amostra().pareto([forte, candidato], 'processador')
    assert len(mantidas) == 2 and not removidas


def test_cor_pedida_impede_eliminar_variante_equivalente_da_cor():
    preto = {**cpu(1, 100, 200), 'cor': 'preto'}
    branco = {**cpu(2, 150, 150, 90), 'cor': 'branco'}
    assert Amostra().pareto([preto, branco], 'processador', 'branco')[1] == []


def test_amostra_combina_faixas_plataformas_rankings_e_preserva_entrada():
    pecas = [{**cpu(i, 50 + i*10, i*100), 'soquete': 'AM4' if i < 10 else 'AM5' if i < 20 else 'LGA1700',
              'benchmark_single_thread': None} for i in range(1, 31)]
    antes = deepcopy(pecas)
    amostra, diagnostico = Amostra().executar(pecas, 'processador', 'desempenho', 400, limite=9)
    assert len(amostra) == len({p['id'] for p in amostra}) == 9
    assert {p['soquete'] for p in amostra} == {'AM4', 'AM5', 'LGA1700'}
    assert all(diagnostico['faixas'][f] > 0 for f in ('entrada', 'intermediaria', 'superior'))
    assert pecas == antes
    assert [p['benchmark_multi_core'] for p in amostra] == sorted([p['benchmark_multi_core'] for p in amostra], reverse=True)


def test_limite_um_mantem_melhor_e_catalogo_pequeno_nao_inventa_candidatos():
    pecas = [cpu(1, 100, 100), cpu(2, 200, 300)]
    assert Amostra().executar(pecas, 'processador', 'desempenho', 300, 1)[0][0]['id'] == 2
    assert len(Amostra().executar(pecas, 'processador', 'desempenho', 300, 12)[0]) == 2
    assert Amostra().executar([], 'processador', 'desempenho', 300)[0] == []


def test_gpu_memoria_e_chip_diferentes_nao_sao_dominados_por_benchmark_maior():
    comum = dict(categoria='placa_video', gpu_chip='RTX A', memoria_gb=8, tipo_memoria='GDDR6',
                 interface_memoria='128', consumo_energia=100, benchmark_teste='PassMark G2D / G3D', benchmark_versao=None)
    a = dict(comum, id=1, preco=100, benchmark_g3d=1000, benchmark_g2d=100)
    b = {**a, 'id': 2, 'preco': 200, 'benchmark_g3d': 900, 'memoria_gb': 16}
    c = {**a, 'id': 3, 'gpu_chip': None, 'preco': 200, 'benchmark_g3d': 900}
    assert Amostra().pareto([a, b, c], 'placa_video')[1] == []
