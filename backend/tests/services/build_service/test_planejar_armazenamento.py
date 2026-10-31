from services.build_service.planejar_armazenamento_service import PlanejarArmazenamentoService as Planner


def test_combinacao_ssd_hd_pode_ser_mais_barata_que_repetir_um_tipo():
    pools = {'ssd': [{'id': 1, 'preco': 300, 'capacidade_gb': 500}],
             'hd': [{'id': 1, 'preco': 200, 'capacidade_gb': 400}]}
    r = Planner().executar(pools, 900)
    assert r['custo'] == 500 and r['capacidade_total_gb'] == 900
    assert [(i['tipo'], i['quantidade']) for i in r['itens']] == [('ssd', 1), ('hd', 1)]


def test_limite_de_unidades_e_capacidade_desconhecida():
    assert Planner().executar({'ssd': [{'id': 1, 'preco': 1, 'capacidade_gb': None}]}, 500) is None
    assert Planner().executar({'ssd': [{'id': 1, 'preco': 1, 'capacidade_gb': 1}]}, 65) is None
    assert Planner().executar({'ssd': [{'id': 1, 'preco': 1, 'capacidade_gb': 1}]}, 64)['custo'] == 64


def test_fronteira_de_reserva_nao_muta_dados_nem_perde_alternativa_barata():
    pools = {'ssd': [{'id': 1, 'preco': 100, 'capacidade_gb': 100},
                     {'id': 2, 'preco': 101, 'capacidade_gb': 90},
                     {'id': 3, 'preco': 400, 'capacidade_gb': 1000}]}
    assert Planner().executar(pools, 500)['custo'] == 400
    assert len(pools['ssd']) == 3
