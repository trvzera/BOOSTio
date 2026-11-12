"""Cobertura do catálogo completo e regressões de identidade, sem chamadas externas."""
from dataclasses import replace
from types import SimpleNamespace

import pytest
from flask import Flask
from models import db, ControleColeta, Processador
from services.catalogo_service.indice_candidatos_service import IndiceCandidatosService
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.conferir_especificacoes_service import extrair_titulo


def local(**dados):
    return SimpleNamespace(**{**dict(__tablename__='processador', id=1, fabricante='AMD',
        modelo='Ryzen 5 5500', part_number='100-100000457BOX', soquete='AM4', nucleo=6, thread=12), **dados})


def remoto(**dados):
    return replace(ProdutoNormalizado(loja='loja_independente', id_externo='123', categoria='processador',
        titulo='Processador AMD Ryzen 5 5500', marca='AMD', modelo='Ryzen 5 5500',
        especificacoes={'soquete':'AM4', 'nucleo':6, 'thread':12},
        ativo=True, categoria_confirmada=True), **dados)


def test_encontra_depois_do_id_2000_sem_truncar_ou_favorecer_primeiros_ids():
    pecas = [local(id=i, fabricante='Intel', modelo=f'Core i5-{10000+i}') for i in range(1, 2501)]
    alvo = local(id=2501)
    indice = IndiceCandidatosService([*pecas, alvo])
    decisao = indice.avaliar(remoto())
    assert decisao['peca'] == 'processador:2501' and decisao['busca_completa']
    assert decisao['total_catalogo'] == 2501
    assert decisao['total_candidatos_avaliados'] == 1
    assert decisao['descartados_por_marca'] == 2500
    assert IndiceCandidatosService([alvo, *reversed(pecas)]).avaliar(remoto())['peca'] == decisao['peca']


def test_duplicata_apos_limite_antigo_permanece_ambigua():
    decisao = IndiceCandidatosService([local(), local(id=3000)]).avaliar(remoto())
    assert decisao['classificacao'] == 'ambigua' and decisao['peca'] is None


@pytest.mark.parametrize('marca', ['AMD', 'Intel', None])
@pytest.mark.parametrize('identificadores', [{}, {'mpn':['100-100000457BOX']}, {'mpn':['DIVERGENTE']}])
def test_indice_preserva_decisao_da_busca_exaustiva(marca, identificadores):
    pecas = [local(), local(id=2, fabricante='Intel', modelo='Core i5-11400', part_number='BX8070811400'),
             local(id=3, modelo='Ryzen 5 5600', part_number='100-100000927BOX')]
    produto = remoto(marca=marca, identificadores=identificadores)
    exaustiva = AssociacaoInteligenteService().selecionar(pecas, produto)
    indexada = IndiceCandidatosService(pecas).avaliar(produto)
    for campo in ('classificacao', 'percentual', 'peca', 'criterio'):
        assert indexada[campo] == exaustiva[campo]


def test_identificador_igual_em_outra_marca_nao_e_ocultado():
    pecas = [local(), local(id=2, fabricante='Intel')]
    decisao = IndiceCandidatosService(pecas).avaliar(remoto(identificadores={'mpn':['100-100000457BOX']}))
    assert decisao['total_candidatos_avaliados'] == 2
    assert decisao['classificacao'] == 'ambigua'


def test_indice_nao_converte_amostra_incompleta_em_busca_completa():
    assert IndiceCandidatosService([local()], completo=False).avaliar(remoto())['classificacao'] == 'ambigua'


def test_titulo_contraditorio_bloqueia_mpn_ate_quando_ficha_local_tem_lacuna():
    produto = remoto(titulo='AMD Ryzen 5 5500 AM5', identificadores={'mpn':['100-100000457BOX']})
    r = AssociacaoInteligenteService().avaliar(local(soquete=None), produto)
    assert r['classificacao'] == 'rejeitada' and 'titulo_divergente:soquete' in r['conflitos']


@pytest.mark.parametrize('velocidade', ['12Gb/s', '12 Gb/s', '6 Gbps', '6 GB/s'])
def test_velocidade_nao_vira_capacidade_de_armazenamento(velocidade):
    assert extrair_titulo('hd', f'HD HPE 1TB SAS {velocidade} 7200RPM')['capacidade_gb'] == ['1tb']


def test_ram_sodimm_com_formato_cadastrado_nao_exige_palavra_no_modelo():
    p = local(__tablename__='memoria_ram', fabricante='Crucial', modelo='CT8G4SFRA32A',
              part_number='CT8G4SFRA32A', formato='SO-DIMM', capacidade_gb=8, ddr='DDR4',
              frequencia_mhz=3200, quantidade_pentes=1, latencia='CL22')
    d = remoto(categoria='memoria_ram', marca='Crucial', modelo='CT8G4SFRA32A',
        titulo='Crucial CT8G4SFRA32A 8GB DDR4 3200MHz CL22 SO-DIMM',
        especificacoes={'formato_ram':'SO-DIMM', 'capacidade_gb':'8GB', 'ddr':'DDR4',
                        'frequencia_mhz':'3200 MHz', 'quantidade_pentes':1, 'latencia':'CL22'})
    assert AssociacaoInteligenteService().avaliar(p,d)['classificacao'] == 'confirmada'


def test_codigo_comercial_completo_no_titulo_sem_mpn_compara_gpu():
    p = local(__tablename__='placa_video', fabricante='ASUS', modelo='DUAL-RTX4060-O8G-EVO',
              part_number=None, memoria_gb=8, tipo_memoria='GDDR6')
    d = remoto(categoria='placa_video', marca='ASUS', modelo='RTX 4060',
        titulo='Placa ASUS DUAL-RTX4060-O8G-EVO 8GB GDDR6',
        especificacoes={'memoria_gb':'8GB', 'tipo_memoria':'GDDR6'})
    assert AssociacaoInteligenteService().avaliar(p,d)['classificacao'] == 'confirmada'
    assert AssociacaoInteligenteService().avaliar(p,replace(d,titulo=d.titulo.replace('4060','4060 Ti')))['classificacao'] != 'confirmada'


@pytest.mark.parametrize('titulo', ['Cooler para processador AMD Ryzen 5 5500',
                                    'Dissipador para AMD Ryzen 5 5500'])
def test_acessorio_nao_vira_cpu_com_mpn_copiado(titulo):
    d = remoto(titulo=titulo, identificadores={'mpn':['100-100000457BOX']})
    assert AssociacaoInteligenteService().avaliar(local(),d)['classificacao'] == 'rejeitada'


def test_carregamento_real_em_lotes_encontra_peca_apos_2000():
    app = Flask('matching-amplo')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        try:
            db.create_all()
            db.session.add_all([Processador(fabricante='Intel', modelo=f'Core i5-{10000+i}',
                               nucleo=4, clockbase=3.0) for i in range(2100)])
            alvo = Processador(fabricante='AMD', modelo='Ryzen 5 5500', part_number='100-100000457BOX',
                               nucleo=6, thread=12, soquete='AM4', clockbase=3.6)
            db.session.add(alvo)
            db.session.commit()
            indice = IndiceCandidatosService.carregar(Processador)
            assert indice.avaliar(remoto())['peca'] == f'processador:{alvo.id}'
            assert Processador.query.count() == 2101
            alvo_id = alvo.id
            db.session.commit()
            from sqlalchemy import event
            consultas = []
            def contar(*args):
                consultas.append(args[2])
            event.listen(db.engine, 'before_cursor_execute', contar)
            try:
                for _ in range(2):
                    assert indice.avaliar(remoto())['peca'] == f'processador:{alvo_id}'
                assert consultas == []
            finally:
                event.remove(db.engine, 'before_cursor_execute', contar)
        finally:
            db.session.remove()
            db.engine.dispose()


@pytest.mark.parametrize('titulo,esperado', [
    ('Memória Kingston 32GB (2x16GB) DDR4', 'confirmada'),
    ('Memória Kingston 64GB (2x16GB) DDR4', 'rejeitada'),
    ('Memória Kingston 32GB (4x8GB) DDR4', 'rejeitada'),
])
def test_quantidade_e_capacidade_total_do_kit_nao_sao_intercambiaveis(titulo, esperado):
    p = local(__tablename__='memoria_ram', fabricante='Kingston', modelo='Fury Beast', part_number='KIT-32GB',
              formato='DIMM', capacidade_gb=32, ddr='DDR4', frequencia_mhz=3200, quantidade_pentes=2, latencia='CL16')
    d = remoto(categoria='memoria_ram', marca='Kingston', modelo='Fury Beast', titulo=titulo,
        identificadores={'mpn':['KIT-32GB']}, especificacoes={'capacidade_gb':'32GB', 'quantidade_pentes':2,
            'ddr':'DDR4', 'frequencia_mhz':'3200MHz', 'latencia':'CL16', 'formato_ram':'DIMM'})
    assert AssociacaoInteligenteService().avaliar(p,d)['classificacao'] == esperado


def test_cpu_de_mesmo_modelo_com_ficha_errada_vai_para_revisao_sem_novo_cadastro():
    produto = remoto(especificacoes={'soquete':'AM4', 'nucleo':3, 'thread':2})
    decisao = IndiceCandidatosService([local(part_number=None)]).avaliar(produto)
    assert decisao['classificacao'] == 'ambigua' and decisao['peca'] is None
    assert 'identidade_existente_com_dados_contraditorios' in decisao['impedimentos']


def test_ram_da_mesma_linha_com_outra_capacidade_nao_e_duplicata_comprovada():
    p = local(__tablename__='memoria_ram', fabricante='Kingston', modelo='Fury Beast', part_number=None,
              formato='DIMM', capacidade_gb=8, ddr='DDR4', frequencia_mhz=3200, quantidade_pentes=1, latencia='CL16')
    d = remoto(categoria='memoria_ram', marca='Kingston', modelo='Fury Beast', titulo='Kingston Fury Beast 16GB DDR4',
        especificacoes={'capacidade_gb':'16GB', 'quantidade_pentes':1, 'ddr':'DDR4',
                        'frequencia_mhz':'3200MHz', 'latencia':'CL16', 'formato_ram':'DIMM'})
    decisao = IndiceCandidatosService([p]).avaliar(d)
    assert decisao['classificacao'] == 'rejeitada' and not decisao['impedimentos']


def test_codigo_de_linha_de_ssd_nao_e_identificador_de_capacidade():
    p = local(__tablename__='ssd', fabricante='Kingston', modelo='A400 SATA', part_number=None,
              capacidade_gb=480, tipo='SATA', interface='SATA III', formato='2.5')
    outro = SimpleNamespace(**{**vars(p), 'id':2, 'capacidade_gb':240})
    d = remoto(categoria='ssd', marca='Kingston', modelo='A400', titulo='SSD Kingston A400 480GB',
               especificacoes={'capacidade_gb':'480GB', 'tipo':'SATA', 'interface':'SATA III'})
    decisao = IndiceCandidatosService([p,outro]).avaliar(d)
    assert decisao['classificacao'] == 'confirmada' and decisao['peca'] == 'ssd:1'


@pytest.mark.parametrize('descricao,esperado', [('SATA 6.0 Gb/s','sata3'),('SATA 6 Gbps','sata3'),
    ('SATA III','sata3'),('SATA 3 Gb/s','sata2'),('SATA 1,5 Gbit/s','sata1')])
def test_taxa_sata_equivale_somente_a_geracao_correspondente(descricao, esperado):
    from services.catalogo_service.conferir_especificacoes_service import converter
    assert converter('interface', descricao) == esperado
    assert converter('interface', 'SATA II 6 Gbps') != 'sata3'


@pytest.mark.parametrize('titulo', ['SSD 240GB + Adaptador Caddy', 'SSD 240GB com caddy', 'SSD 240GB + Case USB'])
def test_bundle_armazenamento_nao_e_oferta_de_peca_avulsa(titulo):
    p = local(__tablename__='ssd', modelo='A400', fabricante='Kingston')
    resultado = AssociacaoInteligenteService().comparar_titulo(p, remoto(categoria='ssd', titulo=titulo))
    assert 'produto_composto_ou_inadequado' in resultado['conflitos']
