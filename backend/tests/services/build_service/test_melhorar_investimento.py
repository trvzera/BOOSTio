from copy import deepcopy

from services.build_service.melhorar_investimento_build_service import MelhorarInvestimentoBuildService
from services.build_service.gerar_candidata_service import gerar_candidata


def catalogo():
    return {
        'placa_video': [{'id': 1, 'preco': 500, 'benchmark_g3d': 5000}, {'id': 2, 'preco': 2000, 'benchmark_g3d': 12000},
                        {'id': 3, 'preco': 2800, 'benchmark_g3d': 20000}, {'id': 4, 'preco': 5000, 'benchmark_g3d': 30000},
                        {'id': 5, 'preco': 3000, 'benchmark_g3d': 4000}, {'id': 6, 'preco': 2900}],
        'processador': [{'id': 1, 'preco': 400, 'benchmark_multi_core': 10000},
                        {'id': 2, 'preco': 1500, 'benchmark_multi_core': 15000},
                        {'id': 3, 'preco': 2500, 'benchmark_multi_core': 18000}],
        'memoria_ram': [{'id': 1, 'preco': 100, 'capacidade_gb': 16, 'frequencia_mhz': 3200},
                        {'id': 2, 'preco': 400, 'capacidade_gb': 32, 'frequencia_mhz': 3200},
                        {'id': 3, 'preco': 150, 'capacidade_gb': 16, 'frequencia_mhz': 3600},
                        {'id': 4, 'preco': 90, 'capacidade_gb': 8, 'frequencia_mhz': 4000}],
        'fonte': [{'id': 1, 'preco': 300}],
    }


def build():
    return {'nome': 'Teste', 'descricao': 'Teste', 'utilidade': 'trabalho pesado', 'componentes': [
        {'tipo': tipo, 'id': 1, 'quantidade': 1} for tipo in ('placa_video', 'processador', 'memoria_ram', 'fonte')]}


def ids(resultado):
    return {i['tipo']: i['id'] for i in resultado[0]['componentes']}


def aceita(candidata):
    return candidata


def test_sobe_gpu_cpu_e_ram_respeitando_teto_e_participacao_maxima():
    resultado = MelhorarInvestimentoBuildService().executar(build(), catalogo(), 8000, {}, aceita)
    assert ids(resultado) == {'placa_video': 3, 'processador': 3, 'memoria_ram': 2, 'fonte': 1}
    assert len(resultado[1]) == 3


def test_nao_mexe_quando_a_build_ja_usa_75_por_cento_do_teto():
    assert MelhorarInvestimentoBuildService().executar(build(), catalogo(), 1200, {}, aceita) is None


def test_peca_mais_cara_sem_benchmark_melhor_nao_conta_como_melhoria():
    pecas = catalogo()
    pecas['placa_video'] = [pecas['placa_video'][0], pecas['placa_video'][4], pecas['placa_video'][5]]
    resultado = MelhorarInvestimentoBuildService().executar(build(), pecas, 8000, {}, aceita)
    assert ids(resultado)['placa_video'] == 1


def test_ram_so_sobe_com_mais_capacidade_ou_mais_frequencia_na_mesma_capacidade():
    pecas = catalogo()
    pecas['memoria_ram'] = [pecas['memoria_ram'][0], pecas['memoria_ram'][2], pecas['memoria_ram'][3]]
    resultado = MelhorarInvestimentoBuildService().executar(build(), pecas, 8000, {}, aceita)
    assert ids(resultado)['memoria_ram'] == 3


def test_troca_recusada_pelo_validador_cai_para_a_proxima_candidata():
    def recusa_gpu_3(candidata):
        if next(i for i in candidata['componentes'] if i['tipo'] == 'placa_video')['id'] == 3:
            raise ValueError('fonte insuficiente')
        return candidata
    resultado = MelhorarInvestimentoBuildService().executar(build(), catalogo(), 8000, {}, recusa_gpu_3)
    assert ids(resultado)['placa_video'] == 2


def test_peca_propria_e_preservada():
    resultado = MelhorarInvestimentoBuildService().executar(build(), catalogo(), 8000, {'placa_video': 'minha'}, aceita)
    assert ids(resultado)['placa_video'] == 1 and ids(resultado)['processador'] == 3


def test_sem_nenhuma_melhoria_valida_devolve_none_e_limita_validacoes():
    chamadas = []
    def recusa_tudo(candidata):
        chamadas.append(1)
        raise ValueError('incompatível')
    assert MelhorarInvestimentoBuildService().executar(build(), catalogo(), 8000, {}, recusa_tudo) is None
    assert len(chamadas) <= MelhorarInvestimentoBuildService.MAX_VALIDACOES


def test_catalogo_sem_a_peca_atual_nao_tenta_melhorar():
    pecas = catalogo()
    pecas['placa_video'] = [p for p in pecas['placa_video'] if p['id'] != 1]
    assert MelhorarInvestimentoBuildService().executar(build(), pecas, 8000, {}, aceita) is None


def test_gerar_candidata_melhora_a_build_barata_sem_nova_chamada_a_ia(mocker):
    pecas = {tipo: [{'id': 1, 'fabricante': 'T', 'modelo': tipo, 'preco': 20}] for tipo in
             ('processador', 'placa_mae', 'memoria_ram', 'fonte', 'gabinete', 'ssd', 'placa_video')}
    pecas['placa_video'][0].update(benchmark_g3d=1000, consumo_energia=100)
    pecas['placa_video'].append({**pecas['placa_video'][0], 'id': 2, 'preco': 1500, 'benchmark_g3d': 9000})
    pecas['gabinete'][0]['fans_inclusos'] = 1
    pecas['fonte'][0]['potencia_w'] = 500
    pecas['memoria_ram'][0]['quantidade_pentes'] = 1
    pecas['processador'][0].update(videointegrado=True, cooler=True, consumo_energia=65, benchmark_multi_core=1000, preco=800)
    pecas['processador'].append({**pecas['processador'][0], 'id': 2, 'preco': 2000, 'benchmark_multi_core': 5000})
    resposta = {'nome': 'T', 'descricao': 'T', 'utilidade': 'trabalho pesado',
                'componentes': [{'tipo': t, 'id': 1, 'quantidade': 1} for t in pecas]}
    mocker.patch('services.build_service.gerar_candidata_service.BuildSalva.verificar_espaco')
    llm = mocker.patch('services.build_service.gerar_candidata_service.LLMService.executar', return_value=deepcopy(resposta))
    resultado = gerar_candidata(1, 'Pedido', 'teste', pecas, 8000, 0, {}, {}, {}, revisar_investimento=True)
    assert next(i for i in resultado['componentes'] if i['tipo'] == 'placa_video')['id'] == 2
    assert resultado['melhoria_investimento']['trocas'][0]['tipo'] == 'placa_video'
    llm.assert_called_once()
