from copy import deepcopy

from services.build_service.planejar_orcamento_componentes_service import PlanejarOrcamentoComponentesService as Planner


def contexto(**extras):
    return {**dict(teto_pc=8000, teto_peca=6000, utilidade='Jogos', prioridade='desempenho',
                   proprias={}, detalhes_proprias={}, armazenamento_minimo_gb=500, rede={}), **extras}


def pools():
    return {'processador': [dict(id='processador:1', preco=1000, soquete='AM4', cooler=True),
                             dict(id='processador:2', preco=7000, soquete='AM4', cooler=True)],
            'placa_mae': [dict(preco=500, socket='AM4', tipo_memoria='DDR4')],
            'memoria_ram': [dict(preco=300, ddr='DDR4')], 'placa_video': [dict(preco=2000)],
            'ssd': [dict(id=1, preco=200, capacidade_gb=500), dict(id=2, preco=900, capacidade_gb=2000)],
            'fonte': [dict(preco=300)], 'gabinete': [dict(preco=200)]}


def test_reserva_real_e_viabilidade_do_conjunto():
    dados = pools()
    antes = deepcopy(dados)
    plano = Planner().executar(contexto(), dados)
    assert plano['reserva_basica_estimada'] == 700
    assert plano['estimativas_cpu']['processador:1']['plataforma_minima'] == 1800
    assert plano['estimativas_cpu']['processador:1']['disponivel_gpu'] == 5500
    assert plano['estimativas_cpu']['processador:2']['viavel'] is False
    assert dados == antes


def test_orcamento_uso_prioridade_e_reaproveitamento_alteram_metas():
    base = Planner().executar(contexto(), pools())
    baixo = Planner().executar(contexto(teto_pc=3000, teto_peca=2200), pools())
    pesado = Planner().executar(contexto(utilidade='Trabalho pesado'), pools())
    custo = Planner().executar(contexto(prioridade='custo_beneficio'), pools())
    propria = Planner().executar(contexto(proprias={'processador': 'Minha CPU'}), pools())
    assert baixo['tetos_sugeridos']['processador'] != base['tetos_sugeridos']['processador'] * 3000 / 8000
    assert pesado['tetos_sugeridos']['processador'] > base['tetos_sugeridos']['processador']
    assert custo['tetos_sugeridos']['processador'] < base['tetos_sugeridos']['processador']
    assert propria['tetos_sugeridos']['placa_video'] > base['tetos_sugeridos']['placa_video']


def test_armazenamento_cliente_aumenta_reserva_e_reduz_verba_para_gpu():
    pequeno = Planner().executar(contexto(), pools())
    grande = Planner().executar(contexto(armazenamento_minimo_gb=2000), pools())
    assert grande['reserva_basica_estimada'] > pequeno['reserva_basica_estimada']
    assert grande['estimativas_cpu']['processador:1']['disponivel_gpu'] < pequeno['estimativas_cpu']['processador:1']['disponivel_gpu']


def test_dados_incompletos_geram_pendencia_sem_inventar_preco_ou_compatibilidade():
    plano = Planner().executar(contexto(), {'processador': [dict(id=1, preco=1000, soquete='AM4')]})
    assert plano['estimativas_cpu'][1] is None
    assert plano['avisos']
    assert plano['reserva_basica_estimada'] == 0


def test_placa_propria_restringe_estimativa_ao_socket_confirmado():
    c = contexto(proprias={'placa_mae': 'Minha placa'}, detalhes_proprias={
        'placa_mae': {'especificacoes_confirmadas': {'socket': 'AM5', 'tipo_memoria': 'DDR5'}}})
    assert Planner().executar(c, pools())['estimativas_cpu']['processador:1'] is None


def test_cpu_sem_cooler_exige_opcao_para_confirmar_estimativa():
    dados = pools()
    dados['processador'][0]['cooler'] = False
    assert Planner().executar(contexto(), dados)['estimativas_cpu']['processador:1'] is None
    dados['air_cooler'] = [dict(preco=100, compatibilidade='AM4')]
    assert Planner().executar(contexto(), dados)['estimativas_cpu']['processador:1']['plataforma_minima'] == 1900
