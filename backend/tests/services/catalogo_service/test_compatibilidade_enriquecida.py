from dataclasses import replace
import pytest
from flask import Flask
from models import db, PlacaMae, Gabinete
from services.catalogo_service.conferir_especificacoes_service import converter
from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService
from services.catalogo_service.extrair_dados_tecnicos_service import ExtrairDadosTecnicosService
from services.especificacoes_service.normalizar_ficha_kabum_service import NormalizarFichaKabumService


def ficha(categoria='placa_mae', texto=None):
    placa = categoria == 'placa_mae'
    return NormalizarFichaKabumService().executar(dict(
        id=123, title='Placa Mãe MSI PRO B660M-A DDR4' if placa else 'Gabinete MSI MAG FORGE 100R',
        manufacturer={'name': 'MSI'}, category='Placa Mae' if placa else 'Gabinete',
        technicalInformation={'text': texto if texto is not None else (
            'Modelo: PRO B660M-A DDR4<br>Socket: LGA1700<br>Tipo de memória: DDR4<br>'
            'Formato: Micro-ATX<br>Slots de memória: 4 DIMM<br>Memória máxima: 128 GB<br>Slots M.2: 2'
        )}), categoria, codigo_esperado='123')


def test_slots_persistidos_com_fonte_e_divergencias_encaminhadas_para_revisao():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        try:
            peca = PlacaMae(fabricante='MSI', modelo='PRO B660M-A DDR4', socket='LGA1700',
                           tipo_memoria='DDR4', formato='Micro-ATX', quantidade_slots_m2=1)
            db.session.add(peca)
            db.session.commit()
            produto = replace(ficha(), identificadores={'mpn': ['PRO B660M-A DDR4']})
            novos = ExtrairDadosTecnicosService().executar(PlacaMae, produto)
            assert novos['dados']['quantidade_slots_ram'] == 4
            assert novos['dados']['memoria_maxima_gb'] == 128
            motor = EnriquecerPecaExistenteService()
            assert motor.executar(peca, produto, simular=False)['status'] == 'revisao'
            assert peca.quantidade_slots_ram is None
            peca.quantidade_slots_m2 = None
            db.session.commit()
            resultado = motor.executar(peca, produto, simular=False)
            assert resultado['status'] == 'atualizada'
            assert (peca.quantidade_slots_ram, peca.memoria_maxima_gb, peca.quantidade_slots_m2) == (4, 128, 2)
            assert peca.fontes_especificacoes['quantidade_slots_ram']['url'] == produto.fonte
            assert motor.executar(peca, produto, simular=False)['status'] == 'inalterada'
        finally:
            db.session.remove()
            db.engine.dispose()


def test_gabinete_usa_limites_explicitos_e_nao_dimensoes_externas():
    dto = ficha('gabinete', 'Comprimento máximo da placa de vídeo: 33 cm<br>'
                'Altura máxima do cooler: 160 mm<br>Slots de expansão: 7<br>Ventoinhas inclusas: 3')
    dados = ExtrairDadosTecnicosService().executar(Gabinete, dto)['dados']
    assert dados == dict(tamanho_max_gpu_mm=330, tamanho_max_cooler_mm=160, slots_expansao=7, fans_inclusos=3)
    externo = ficha('gabinete', 'Dimensões: 400 x 210 x 450 mm<br>Suporte para placa de vídeo: até 330 mm com radiador removido')
    assert ExtrairDadosTecnicosService().executar(Gabinete, externo)['dados'] == {}


@pytest.mark.parametrize('valor', ['2 ou 4', 'até 4', '-1', '2.5', True, '4 slots com adaptador'])
def test_slots_ambiguos_nao_sao_confirmados(valor):
    assert converter('quantidade_slots_ram', valor) is None


def test_icecat_le_limites_internos_sem_usar_altura_externa():
    from services.icecat_service.normalizar_ficha_icecat_service import NormalizarFichaIcecatService
    atributos = {'Maximum graphics card length': '330 mm', 'Maximum CPU cooler height': '160 mm',
                 'Number of expansion slots': '7', 'Height': '450 mm'}
    features = ''.join(f'<ProductFeature Presentation_Value="{v}"><Feature><Name Value="{k}"/></Feature></ProductFeature>'
                       for k, v in atributos.items())
    xml = ('<ICECAT-interface><Product ID="123" Name="MAG FORGE 100R" Prod_id="306-7G03R11-809">'
           '<Supplier Name="MSI"/><Category ID="1"><Name Value="Computer cases"/></Category>'
           + features + '</Product></ICECAT-interface>').encode()
    resultado = NormalizarFichaIcecatService().executar(xml, dict(id='123', categoria='1', atualizado='20261112000000'), 'gabinete')
    assert resultado['dados']['tamanho_max_gpu_mm'] == 330
    assert resultado['dados']['tamanho_max_cooler_mm'] == 160
    assert resultado['dados']['slots_expansao'] == 7
    assert resultado['fontes']['tamanho_max_gpu_mm']['atributo'] == 'Maximum graphics card length'
    assert 'altura_mm' not in resultado['dados']
