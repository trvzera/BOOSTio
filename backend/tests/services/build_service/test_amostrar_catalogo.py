from services.build_service.amostrar_catalogo_service import AmostrarCatalogoService


def test_memorias_preservam_entrada_ddr4_e_ddr5_sem_densidade_de_marcas_excluir_padrao():
    pecas = [{"id": i, "preco": 200+i, "ddr": "DDR4", "capacidade_gb": 8, "quantidade_pentes": 1} for i in range(1, 91)]
    pecas += [{"id": 91, "preco": 55, "ddr": "DDR3", "capacidade_gb": 4, "quantidade_pentes": 1},
              {"id": 92, "preco": 1187, "ddr": "DDR5", "capacidade_gb": 16, "quantidade_pentes": 1},
              {"id": 93, "preco": 8833, "ddr": "DDR5", "capacidade_gb": 32, "quantidade_pentes": 2}]
    amostra = AmostrarCatalogoService().executar("memoria_ram", pecas)
    assert len(amostra) == 12
    assert {1, 91, 92} <= {p["id"] for p in amostra}
    assert {p["ddr"] for p in amostra} == {"DDR3", "DDR4", "DDR5"}
    assert len(pecas) == 93


def test_preco_por_faixas_oferece_alternativas_intermediarias_sem_afirmar_desempenho():
    pecas = [{"id": i, "preco": 100+i} for i in range(1, 91)]
    pecas += [{"id": 91+i, "preco": preco} for i, preco in enumerate([1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 8900])]
    amostra = AmostrarCatalogoService().executar("placa_video", pecas)
    assert len(amostra) == 12
    assert min(p["preco"] for p in amostra) == 101
    assert max(p["preco"] for p in amostra) == 8900
    assert len([p for p in amostra if p["preco"] >= 1000]) >= 8


def test_placas_preservam_sockets_e_ddr_e_nao_duplicam_ids():
    pecas = [{"id": i, "preco": i * 10, "socket": "AM4", "tipo_memoria": "DDR4"} for i in range(1, 30)]
    pecas += [{"id": 31, "preco": 300, "socket": "AM5", "tipo_memoria": "DDR5"},
              {"id": 32, "preco": 310, "socket": "LGA1700", "tipo_memoria": "DDR4"},
              {"id": 33, "preco": 320, "socket": "LGA1700", "tipo_memoria": "DDR5"}]
    amostra = AmostrarCatalogoService().executar("placa_mae", pecas)
    assert {31, 32, 33} <= {p["id"] for p in amostra}
    assert len({p["id"] for p in amostra}) == len(amostra) == 12


def test_catalogo_pequeno_so_e_ordenado_sem_mudar_os_objetos():
    dados = [{"id": 2, "preco": 20}, {"id": 1, "preco": 10}]
    assert AmostrarCatalogoService().executar("fan", dados) == [dados[1], dados[0]]
    assert dados[0]["id"] == 2


def test_preservar_sockets_nao_remove_as_opcoes_de_maior_investimento():
    pecas = [{"id": i, "preco": 200+i*30, "soquete": "AM4" if i<30 else "LGA1700" if i<50 else "AM5"} for i in range(1,100)]
    amostra = AmostrarCatalogoService().executar("processador",pecas)
    assert {1,99} <= {p["id"] for p in amostra}
    assert {p["soquete"] for p in amostra} == {"AM4","AM5","LGA1700"}
