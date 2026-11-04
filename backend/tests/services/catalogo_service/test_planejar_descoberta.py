from types import SimpleNamespace
import json
import pytest
from services.catalogo_service.planejar_descoberta_service import PlanejarDescobertaService
from services.mercadolivre_service.processar_catalogo_service import ProcessarCatalogoService


def test_plano_reserva_100_por_categoria_marca_e_preserva_familia(tmp_path):
    modelos = [SimpleNamespace(__tablename__='processador', fabricantes_para_descoberta=lambda: ['Intel', 'AMD', ' intel ']),
               SimpleNamespace(__tablename__='ssd', fabricantes_para_descoberta=lambda: ['Kingston'])]
    plano = PlanejarDescobertaService().executar(modelos=modelos)
    assert [t['consulta'] for t in plano['trabalhos']] == ['processador Intel', 'processador AMD Ryzen', 'SSD Kingston']
    assert len({t['nome'] for t in plano['trabalhos']}) == 3
    assert all(t['max_produtos'] == t['max_anuncios'] == 100 and t['max_ofertas_por_produto'] == 1 for t in plano['trabalhos'])
    caminho = tmp_path / 'plano.json'
    caminho.write_text(json.dumps(plano))
    assert len(ProcessarCatalogoService.ler_plano(caminho)) == 3


@pytest.mark.parametrize('limite', [True, 0, 101])
def test_limite_invalido(limite):
    with pytest.raises(ValueError):
        PlanejarDescobertaService().executar(limite=limite)


def test_prioriza_limita_e_ignora_rotulos_sem_marca():
    modelos = [SimpleNamespace(__tablename__='ssd', fabricantes_para_descoberta=lambda: ['Outros', 'Kingston', ' kingston ', 'WD', 'Importado', 'Crucial'])]
    p = PlanejarDescobertaService().executar(modelos=modelos, marcas_por_categoria=2)
    assert [t['marca'] for t in p['trabalhos']] == ['Kingston', 'WD']
    p = PlanejarDescobertaService().executar(modelos=modelos, marcas_por_categoria=None)
    assert [t['marca'] for t in p['trabalhos']] == ['Kingston', 'WD', 'Crucial']


def test_fabricantes_ordenados_por_quantidade_apenas_de_pecas_publicaveis():
    from flask import Flask
    from models import db, Processador
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        for fabricante, status in [('AMD', 'legado'), ('Intel', 'aprovado'), ('Intel', 'legado'), ('Z', 'pendente'), ('Z', 'pendente'), ('Z', 'pendente')]:
            db.session.add(Processador(fabricante=fabricante, modelo='teste', consumo_energia=65, preco=100,
                soquete='AM4', nucleo=6, thread=12, clockbase=3, clockmax=4, status_validacao=status))
        db.session.commit()
        assert Processador.fabricantes_para_descoberta() == ['Intel', 'AMD']
        db.session.remove()
        db.engine.dispose()


def test_busca_por_peca_preserva_codigo_e_nao_pesquisa_id_interno(tmp_path):
    pecas = [SimpleNamespace(id=1, fabricante='Kingston', modelo='Fury Beast 8GB', part_number='KF432C16BB/8'),
             SimpleNamespace(id=2, fabricante='Kingston', modelo='Fury Beast 16GB', part_number='KABUM-123')]
    modelo = SimpleNamespace(__tablename__='memoria_ram', lote_para_identificadores=lambda cursor, limite:pecas)
    plano = PlanejarDescobertaService().por_peca(categoria='memoria_ram', modelos=[modelo])
    assert [t['consulta'] for t in plano['trabalhos']] == ['memoria RAM Kingston KF432C16BB/8', 'memoria RAM Kingston Fury Beast 16GB']
    assert all(t['max_produtos'] == 10 for t in plano['trabalhos'])
    arquivo = tmp_path / 'plano.json'
    arquivo.write_text(json.dumps(plano))
    assert len(ProcessarCatalogoService.ler_plano(arquivo)) == 2


def test_alternativas_preservam_sufixo_e_nao_usam_codigo_interno():
    p=SimpleNamespace(__tablename__='memoria_ram',id=8,fabricante='Kingston',modelo='Fury Beast RGB, 8GB, DDR4',
        part_number='KABUM-123',codigo_modelo_fabricante='KF432C16BBA/8')
    grupos=PlanejarDescobertaService().alternativas(p)
    assert [g['consulta'] for g in grupos]==['Kingston KF432C16BBA/8','Kingston Fury Beast RGB']
    assert all(g['max_produtos']==30 for g in grupos)


def test_pesquisa_corrige_grafia_comprovada_sem_alterar_modelo():
    p=SimpleNamespace(__tablename__='fonte',id=1,fabricante='C3Techtech',modelo='PS-600BK',part_number=None,codigo_modelo_fabricante=None)
    plano=PlanejarDescobertaService().alternativas(p)
    assert plano[0]['consulta']=='c3tech ps-600bk'
    assert plano[0]['marca']=='C3Techtech'
    assert p.fabricante=='C3Techtech'


def test_alternativa_pesquisa_edicao_do_titulo_original_sem_autorizar_match():
    p=SimpleNamespace(__tablename__='placa_video',id=1,fabricante='MSI',modelo='RTX 4060 912-V516-001',part_number=None,codigo_modelo_fabricante='912-V516-001',fontes_especificacoes={'codigo_modelo_fabricante':{'criterio':'anuncio_original_e_especificacoes_compativeis','titulo_origem':'Placa de Vídeo MSI RTX 4060 Ventus 2X OC, 8GB GDDR6'}})
    trabalhos=PlanejarDescobertaService().alternativas(p)
    assert trabalhos[-1]['consulta']=='Placa de Vídeo MSI RTX 4060 Ventus 2X OC'
    assert all('peca' not in t for t in trabalhos)
    assert p.modelo=='RTX 4060 912-V516-001'
