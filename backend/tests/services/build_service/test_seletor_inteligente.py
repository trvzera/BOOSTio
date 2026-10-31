from decimal import Decimal

from flask import Flask
import pytest

from models import db, Processador, PlacaVideo
from services.build_service.seletor_inteligente_service import SeletorInteligenteService


@pytest.fixture
def banco(tmp_path):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{tmp_path / 'seletor.db'}"
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.engine.dispose()


def inserir(preco, score, gpu=False, **extras):
    classe = PlacaVideo if gpu else Processador
    dados = dict(fabricante='Teste', modelo='Modelo', preco=preco, consumo_energia=65,
                 benchmark_teste='PassMark G2D / G3D' if gpu else 'PassMark CPU Mark / Single Thread')
    dados.update(dict(memoria_gb=8, benchmark_g3d=score) if gpu else dict(
        soquete='AM4', nucleo=6, thread=12, clockbase=3, clockmax=4, benchmark_multi_core=score))
    peca = classe(**{**dados, **extras})
    db.session.add(peca)
    db.session.commit()
    return f'{classe.__tablename__}:{peca.id}'


def ids(dados):
    return [p['id'] for p in SeletorInteligenteService().executar(dados)['componentes_selecionados']]


@pytest.mark.parametrize('gpu', [False, True])
def test_desempenho_e_custo_beneficio_ordenam_por_metricas_distintas(banco, gpu):
    barato = inserir(500, 10000, gpu)
    rapido = inserir(1000, 15000, gpu)
    dados = dict(orcamento=2000, prioridade_montagem='desempenho')
    assert ids(dados) == [rapido, barato]
    assert ids({**dados, 'prioridade_montagem': 'custo_beneficio'}) == [barato, rapido]
    assert ids(dict(orcamento=2000, preferencias='custo-beneficio')) == [barato, rapido]


@pytest.mark.parametrize('gpu', [False, True])
def test_filtros_excluem_preco_invalido_esgotado_sem_benchmark_e_outro_teste(banco, gpu):
    valido = inserir(1000, 15000, gpu)
    for preco, score, extras in [(1201, 50000, {}), (0, 20000, {}), (-1, 20000, {}),
                                  (500, None, {}), (500, 0, {}), (500, -10, {}),
                                  (500, 20000, {'esgotado': True}),
                                  (500, 20000, {'benchmark_teste': 'Outro teste'}),
                                  (500, 20000, {'benchmark_versao': '10'}),
                                  (500, 20000, {'benchmark_teste': None})]:
        inserir(preco, score, gpu, **extras)
    assert ids(dict(orcamento=2000, preferencias='desempenho')) == [valido]


def test_categoria_limite_e_desempate_deterministico(banco):
    a = inserir(500, 10000)
    b = inserir(500, 10000)
    menor = inserir(250, 5000)
    inserir(100, 50000, gpu=True)
    dados = dict(orcamento=Decimal('2000'), preferencias='desempenho', categoria='processador',
                 limite=1)
    assert ids(dados) == [a]
    assert ids({**dados, 'limite': 2}) == [a, b]
    assert ids({**dados, 'limite': 3}) == [a, b, menor]


@pytest.mark.parametrize('dados', [None, [], {}, {'orcamento': 1000},
    *({'orcamento': v, 'preferencias': 'desempenho'} for v in [None, True, 0, -1, 2000.001, float('nan'), float('inf')]),
    {'orcamento': 1000, 'preferencias': []},
    {'orcamento': 1000, 'preferencias': 'desempenho', 'limite': True},
    {'orcamento': 1000, 'preferencias': 'desempenho', 'categoria': 'fonte'},
])
def test_validacao_antes_de_acessar_banco(dados):
    with pytest.raises(ValueError):
        SeletorInteligenteService().executar(dados)


def test_lista_cpu_gpu_sem_pontuacao_minima_e_nao_altera_banco(banco):
    cpu = inserir(500, 12000)
    gpu = inserir(500, 30000, gpu=True)
    assert ids(dict(orcamento=2000, preferencias='desempenho')) == [cpu, gpu]
    assert Processador.query.count() == PlacaVideo.query.count() == 1
    assert Processador.query.one().preco == 500
    assert PlacaVideo.query.one().benchmark_g3d == 30000


def test_teto_usa_margem_da_montagem_em_vez_do_orcamento_total(banco):
    dentro = inserir(3000, 10000)
    inserir(3000.01, 50000)
    inserir(4000, 60000)
    assert ids(dict(orcamento=4000, preferencias='desempenho')) == [dentro]


def test_reserva_perifericos_limita_pc_sem_transferir_sobra(banco):
    dentro = inserir(2000, 10000)
    inserir(2000.01, 50000)
    # 60% de 5000 ficam reservados aos periféricos; PC tem teto de 2000.
    assert ids(dict(orcamento=5000, percentual_perifericos=60, preferencias='desempenho')) == [dentro]


@pytest.mark.parametrize('dados', [
    dict(orcamento=1999, preferencias='desempenho'),
    dict(orcamento=2500, percentual_perifericos=30, preferencias='desempenho'),
    dict(orcamento=3000, percentual_perifericos=10, preferencias='desempenho'),
    *(dict(orcamento=5000, percentual_perifericos=p, preferencias='desempenho')
      for p in [True, '20', -1, 100, 20.5]),
])
def test_mesmas_validacoes_de_orcamento_da_montagem_antes_da_consulta(dados):
    with pytest.raises(ValueError):
        SeletorInteligenteService().executar(dados)


@pytest.mark.parametrize('gpu', [False, True])
def test_custo_beneficio_ordena_pontos_por_real_antes_de_aplicar_limite(banco, gpu):
    inserir(1000, 15000, gpu)  # 15 pontos por real
    melhor = inserir(800, 20000, gpu)  # 25 pontos por real
    intermediario = inserir(500, 10000, gpu)  # 20 pontos por real
    inserir(1201, 100000, gpu)  # Acima do teto de 1200, mesmo com ótima relação.
    resultado = ids(dict(orcamento=2000, prioridade_montagem='custo_beneficio', limite=2))
    assert resultado == [melhor, intermediario]


@pytest.mark.parametrize('gpu', [False, True])
def test_empate_custo_beneficio_prioriza_menor_preco_depois_id(banco, gpu):
    inserir(1000, 20000, gpu)
    primeiro = inserir(500, 10000, gpu)
    segundo = inserir(500, 10000, gpu)
    resultado = ids(dict(orcamento=2000, prioridade_montagem='custo_beneficio', limite=2))
    assert resultado == [primeiro, segundo]


def salvar_modelo(classe, preco, **campos):
    obj = classe(**{'fabricante': 'Teste', 'modelo': 'Modelo', 'preco': preco,
                    'consumo_energia': 10, **campos})
    db.session.add(obj)
    db.session.commit()
    return f'{classe.__tablename__}:{obj.id}'


def test_demais_categorias_reutilizam_amostragem_sem_substituir_benchmarks(banco):
    from models import MemoriaRAM, Fonte, PlacaMae
    cpu = inserir(500, 12000)
    salvar_modelo(PlacaMae, 300, socket="AM4", tipo_memoria="DDR4")
    inserir(500, None)  # CPU sem benchmark não pode voltar pelo catálogo geral.
    for n in range(20):
        salvar_modelo(MemoriaRAM, 100 + n, capacidade_gb=16, ddr='DDR4', frequencia_mhz=3200,
                      quantidade_pentes=1)
    fonte = salvar_modelo(Fonte, 500, potencia_w=650)
    salvar_modelo(Fonte, 4000, potencia_w=1000)
    resultado = ids(dict(orcamento=4000, prioridade_montagem='desempenho'))
    assert resultado[0] == cpu
    assert sum(i.startswith('memoria_ram:') for i in resultado) == 20
    assert [i for i in resultado if i.startswith('fonte:')] == [fonte]
    assert sum(i.startswith('processador:') for i in resultado) == 1


def test_perifericos_seguem_reserva_e_painel_da_montagem(banco):
    from models import Monitor
    campos = dict(conexao='HDMI', tamanho_polegadas=24, resolucao='1920x1080', taxa_atualizacao_hz=60)
    permitido = salvar_modelo(Monitor, 900, tipo_painel='IPS', **campos)
    salvar_modelo(Monitor, 950, tipo_painel='TN', **campos)
    salvar_modelo(Monitor, 1001, tipo_painel='VA', **campos)
    dados = dict(orcamento=5000, prioridade_montagem='desempenho')
    assert ids(dados) == []
    assert ids({**dados, 'percentual_perifericos': 20}) == [permitido]


def test_reaproveitamento_exclui_cpu_e_ambos_os_armazenamentos(banco, mocker):
    from models import SSD, HD, Fonte
    inserir(500, 10000)
    salvar_modelo(SSD, 200, capacidade_gb=500, tipo='NVMe', interface='PCIe')
    salvar_modelo(HD, 200, capacidade_gb=1000)
    fonte = salvar_modelo(Fonte, 300, potencia_w=500)
    consulta_cpu = mocker.spy(Processador, 'listar_por_benchmark')
    resultado = ids(dict(orcamento=4000, prioridade_montagem='desempenho',
                         pecas_proprias={'processador': 'Minha CPU', 'ssd': 'Meu SSD'}))
    assert resultado == [fonte]
    consulta_cpu.assert_not_called()


def test_rede_respeita_tipo_compra_e_comprimento_da_montagem(banco):
    from models import CaboRede
    salvar_modelo(CaboRede, 30, categoria='Cat6', comprimento_m=2)
    longo = salvar_modelo(CaboRede, 50, categoria='Cat6', comprimento_m=10)
    dados = dict(orcamento=4000, prioridade_montagem='desempenho',
                 rede={'tipo': 'cabo', 'possuiAcessorio': False, 'comprimentoCaboM': 5})
    assert ids(dados) == [longo]
    assert ids({**dados, 'rede': {'tipo': 'cabo', 'possuiAcessorio': True}}) == []


def test_categoria_especifica_nao_retorna_outras_pecas(banco):
    from models import Fonte
    inserir(500, 10000)
    fonte = salvar_modelo(Fonte, 300, potencia_w=500)
    assert ids(dict(orcamento=4000, prioridade_montagem='desempenho', categoria='fonte')) == [fonte]


@pytest.mark.parametrize('quantidades,esperadas', [((20, 20), (12, 12)), ((2, 30), (2, 22)),
                                                 ((30, 0), (24, 0)), ((10, 10), (10, 10))])
def test_placas_distribuem_24_vagas_por_socket_e_reaproveitam_sobras(banco, quantidades, esperadas):
    from collections import Counter
    from models import PlacaMae
    from utils.sockets import normalizar_socket
    inserir(500, 10000, soquete='AM4')
    inserir(500, 9000, soquete='AM4')  # Duas CPUs AM4 não dão peso duplo ao grupo.
    inserir(500, 8000, soquete='AM5')
    for socket, quantidade in zip(('AMD AM4', 'Socket AM5'), quantidades):
        for n in range(quantidade):
            salvar_modelo(PlacaMae, 300 + n, socket=socket, tipo_memoria='DDR4' if '4' in socket else 'DDR5')
    salvar_modelo(PlacaMae, 100, socket='LGA1700')
    salvar_modelo(PlacaMae, 4000, socket='AM4')
    salvar_modelo(PlacaMae, 100, socket='AM5', esgotado=True)
    selecionadas = SeletorInteligenteService().executar(
        dict(orcamento=4000, prioridade_montagem='desempenho'))['componentes_selecionados']
    placas = [p for p in selecionadas if p['categoria'] == 'placa_mae']
    contagens = Counter(normalizar_socket(p['socket']) for p in placas)
    assert (contagens['AM4'], contagens['AM5']) == esperadas
    assert len({p['id'] for p in placas}) == sum(esperadas)
    assert ids(dict(orcamento=4000, prioridade_montagem='desempenho')) == [p['id'] for p in selecionadas]


def test_sem_cpu_elegivel_nao_reintroduz_placas_de_socket_aleatorio(banco):
    from models import PlacaMae
    inserir(500, None, soquete='AM4')
    salvar_modelo(PlacaMae, 300, socket='AM4')
    assert ids(dict(orcamento=4000, prioridade_montagem='desempenho')) == []


def test_placas_consideram_cpu_propria_e_categoria_especifica(banco):
    from models import PlacaMae
    inserir(500, 10000, soquete='AM5')
    inserir(500, None, soquete='AM4', modelo='CPU propria')
    am4 = salvar_modelo(PlacaMae, 300, socket='AM4')
    am5 = salvar_modelo(PlacaMae, 400, socket='AM5')
    dados = dict(orcamento=4000, prioridade_montagem='desempenho', categoria='placa_mae')
    assert ids(dados) == [am5]
    assert ids({**dados, 'pecas_proprias': {'processador': 'CPU propria'}}) == [am4]
    assert ids({**dados, 'pecas_proprias': {'processador': 'CPU desconhecida'}}) == []


def test_placa_mae_propria_nao_gera_novas_recomendacoes_de_placa(banco, mocker):
    from models import PlacaMae
    inserir(500, 10000, soquete='AM4')
    salvar_modelo(PlacaMae, 300, socket='AM4')
    consulta = mocker.spy(PlacaMae, 'listar_disponiveis_por_sockets')
    resultado = ids(dict(orcamento=4000, prioridade_montagem='desempenho',
                         pecas_proprias={'placa_mae': 'Minha placa'}))
    assert all(not p.startswith('placa_mae:') for p in resultado)
    consulta.assert_not_called()


@pytest.mark.parametrize('quantidades,esperadas', [((20, 20), (12, 12)), ((2, 30), (2, 22)),
                                                 ((30, 0), (24, 0)), ((4, 5), (4, 5))])
def test_ram_distribui_vagas_por_ddr_das_placas_e_reaproveita_sobras(banco, quantidades, esperadas):
    from collections import Counter
    from models import PlacaMae, MemoriaRAM
    from utils.memorias import normalizar_ddr
    inserir(500, 10000, soquete='LGA1700')
    # Mesmo socket com placas DDR diferentes: o padrão vem da placa, não da CPU.
    for ddr in ('DDR4', 'DDR 5'):
        salvar_modelo(PlacaMae, 300, socket='LGA1700', tipo_memoria=ddr)
    for ddr, quantidade in zip(('ddr-4', 'DDR5'), quantidades):
        for n in range(quantidade):
            salvar_modelo(MemoriaRAM, 100 + n, ddr=ddr, capacidade_gb=16,
                          frequencia_mhz=3200, quantidade_pentes=1)
    for preco, ddr, extras in [(50, 'DDR3', {}), (4000, 'DDR4', {}),
                               (50, 'DDR5', {'esgotado': True}), (0, 'DDR4', {})]:
        salvar_modelo(MemoriaRAM, preco, ddr=ddr, capacidade_gb=16, frequencia_mhz=3200,
                      quantidade_pentes=1, **extras)
    dados = dict(orcamento=4000, prioridade_montagem='desempenho')
    pecas = SeletorInteligenteService().executar(dados)['componentes_selecionados']
    memorias = [p for p in pecas if p['categoria'] == 'memoria_ram']
    contagens = Counter(normalizar_ddr(p['ddr']) for p in memorias)
    assert (contagens['DDR4'], contagens['DDR5']) == esperadas
    assert len(memorias) == len({m['id'] for m in memorias}) == sum(esperadas)
    assert ids(dados) == [p['id'] for p in pecas]


def test_ram_segue_apenas_placas_selecionadas_e_categoria_especifica(banco):
    from models import PlacaMae, MemoriaRAM
    inserir(500, 10000, soquete='AM4')
    salvar_modelo(PlacaMae, 300, socket='AM4', tipo_memoria='DDR4')
    salvar_modelo(PlacaMae, 300, socket='AM5', tipo_memoria='DDR5')
    ram = salvar_modelo(MemoriaRAM, 100, ddr='DDR4', capacidade_gb=16,
                       frequencia_mhz=3200, quantidade_pentes=1)
    salvar_modelo(MemoriaRAM, 100, ddr='DDR5', capacidade_gb=16,
                  frequencia_mhz=5200, quantidade_pentes=1)
    dados = dict(orcamento=4000, prioridade_montagem='desempenho', categoria='memoria_ram')
    assert ids(dados) == [ram]


@pytest.mark.parametrize('tipo_memoria', [None, '', 'desconhecido', 'DDR4/DDR5'])
def test_ddr_ausente_ou_ambiguo_nao_e_inferido_pelo_socket(banco, tipo_memoria):
    from models import PlacaMae, MemoriaRAM
    inserir(500, 10000, soquete='AM4')
    salvar_modelo(PlacaMae, 300, socket='AM4', tipo_memoria=tipo_memoria)
    salvar_modelo(MemoriaRAM, 100, ddr='DDR4', capacidade_gb=16,
                  frequencia_mhz=3200, quantidade_pentes=1)
    resultado = ids(dict(orcamento=4000, prioridade_montagem='desempenho'))
    assert not any(p.startswith('memoria_ram:') for p in resultado)


def test_ram_propria_nao_consulta_novas_memorias_e_placa_propria_define_ddr(banco, mocker):
    from models import PlacaMae, MemoriaRAM
    salvar_modelo(PlacaMae, 300, socket='AM4', tipo_memoria='DDR4', modelo='Placa propria')
    ram = salvar_modelo(MemoriaRAM, 100, ddr='DDR4', capacidade_gb=16,
                       frequencia_mhz=3200, quantidade_pentes=1)
    dados = dict(orcamento=4000, prioridade_montagem='desempenho', categoria='memoria_ram')
    assert ids({**dados, 'pecas_proprias': {'placa_mae': 'Placa propria'}}) == [ram]
    assert ids({**dados, 'pecas_proprias': {'placa_mae': 'Placa desconhecida'}}) == []
    consulta = mocker.spy(MemoriaRAM, 'listar_disponiveis_por_ddrs')
    assert ids({**dados, 'pecas_proprias': {'memoria_ram': 'Minha RAM'}}) == []
    consulta.assert_not_called()
