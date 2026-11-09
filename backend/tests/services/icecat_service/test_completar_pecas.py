"""Completar peças já cadastradas com a ficha do Icecat, sem rede (o Icecat é simulado)."""
import pytest
from flask import Flask

from models import db, Fone, Monitor
from services.icecat_service.completar_pecas_icecat_service import CompletarPecasIcecatService
from services.icecat_service.normalizar_ficha_icecat_service import NormalizarFichaIcecatService
from services.icecat_service.obter_ficha_icecat_service import ErroConsultaIcecat

URL = 'https://data.icecat.biz/export/freexml/EN/26030190.xml'


class IcecatSimulado:
    """Devolve sempre a ficha pronta; guarda quais part numbers foram consultados."""
    def __init__(self, dados, mpn='KHX-HSCP-RD', erro=None):
        self.dados, self.mpn, self.erro, self.consultados = dados, mpn, erro, []

    def executar(self, produto, ficha):
        self.consultados.append(produto.identificadores['mpn'])
        if self.erro:
            raise self.erro
        return produto, {'icecat': {'status': 'encontrada'}, 'dados': self.dados, 'fonte_identidade': URL,
                         'identidade': {'mpn': self.mpn, 'gtin': None}}


FICHA_FONE = {'fabricante': 'HyperX', 'modelo': 'Cloud II', 'tipo': 'Headset', 'microfone': True, 'conexao': 'Wired'}


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.engine.dispose()


def fone_em_revisao(**campos):
    dados = dict(fabricante='HyperX', modelo='Cloud II', part_number='KHX-HSCP-RD', status_validacao='em_revisao')
    fone = Fone(**{**dados, **campos})
    db.session.add(fone)
    db.session.commit()
    fone.microfone = fone.tipo = None  # na produção a ficha chega vazia; o padrão da coluna não se aplica
    db.session.commit()
    return fone


def completar(icecat, simular=True, categoria='fone'):
    return CompletarPecasIcecatService(icecat=icecat).executar(categoria=categoria, simular=simular)


def test_simulacao_mostra_a_proposta_e_nao_grava(banco):
    fone = fone_em_revisao()
    resumo = completar(IcecatSimulado(FICHA_FONE))
    assert resumo['proposta'] == 1 and resumo['simulacao'] is True
    db.session.refresh(fone)
    assert fone.microfone is None and fone.conexao is None


def test_aplicar_preenche_so_campos_vazios_com_a_origem_e_nao_aprova(banco):
    fone = fone_em_revisao(conexao='bluetooth')
    resumo = completar(IcecatSimulado({**FICHA_FONE, 'conexao': 'Bluetooth'}), simular=False)
    assert resumo['atualizada'] == 1
    db.session.refresh(fone)
    assert (fone.tipo, fone.microfone, fone.conexao) == ('headset', True, 'bluetooth')
    assert fone.fontes_especificacoes['microfone']['url'] == URL
    assert fone.status_validacao == 'em_revisao'  # aprovar é outro passo


def test_ficha_que_contradiz_a_peca_vai_para_revisao_sem_gravar(banco):
    fone = fone_em_revisao()
    fone.microfone = False  # a peça diz que não tem microfone; a ficha diz que tem
    db.session.commit()
    resumo = completar(IcecatSimulado(FICHA_FONE), simular=False)
    assert resumo['revisao'] == 1 and resumo['atualizada'] == 0
    db.session.refresh(fone)
    assert fone.conexao is None and fone.microfone is False


def test_ignora_sem_part_number_aprovada_e_ja_completa(banco):
    fone_em_revisao(part_number=None, modelo='Sem código')
    aprovada = fone_em_revisao(modelo='Aprovada', part_number='AAA-111')
    aprovada.status_validacao = 'aprovado'
    db.session.commit()
    icecat = IcecatSimulado(FICHA_FONE)
    resumo = completar(icecat)
    assert (resumo['sem_part_number'], resumo['ignoradas'], resumo['analisadas']) == (1, 1, 0)
    assert icecat.consultados == []  # nem consulta o Icecat


def test_limite_do_icecat_interrompe_e_informa_de_onde_retomar(banco):
    fone = fone_em_revisao()
    resumo = completar(IcecatSimulado(FICHA_FONE, erro=ErroConsultaIcecat('Limite de consultas Icecat atingido')))
    assert resumo['interrompido'] is True and resumo['ultima_peca_id'] == fone.id
    assert 'Limite' in resumo['motivo_interrupcao']


def test_categoria_invalida_e_sem_indice_configurado(banco, monkeypatch):
    with pytest.raises(ValueError):
        CompletarPecasIcecatService(icecat=IcecatSimulado({})).executar(categoria='nada')
    monkeypatch.delenv('ICECAT_INDICE', raising=False)
    with pytest.raises(ValueError, match='ICECAT_INDICE'):
        CompletarPecasIcecatService()


def test_monitor_ganha_conexao_pelas_portas_de_video(banco):
    monitor = Monitor(fabricante='LG', modelo='27GP850-B', part_number='27GP850-B', tamanho_polegadas=27,
                      resolucao='2560x1440', taxa_atualizacao_hz=165, tipo_painel='IPS', status_validacao='em_revisao')
    db.session.add(monitor)
    db.session.commit()
    ficha = {'fabricante': 'LG', 'modelo': '27GP850-B', 'conexao': 'displayport, hdmi'}
    resumo = completar(IcecatSimulado(ficha, mpn='27GP850-B'), simular=False, categoria='monitor')
    assert resumo['atualizada'] == 1
    db.session.refresh(monitor)
    assert monitor.conexao == 'displayport, hdmi'


def xml_monitor(portas):
    features = ''.join(f'<ProductFeature Presentation_Value="{v}"><Feature><Name Value="{k}"/></Feature></ProductFeature>'
                       for k, v in portas.items())
    return ('<ICECAT-interface><Product ID="9" Name="M" Prod_id="M-1"><Supplier Name="LG"/>'
            '<Category ID="222"><Name Value="Computer Monitors"/></Category>' + features + '</Product></ICECAT-interface>').encode()


def xml_fone(conexao):
    return ('<ICECAT-interface><Product ID="9" Name="F" Prod_id="F-1"><Supplier Name="HyperX"/>'
            '<Category ID="1637"><Name Value="Headphones &amp; Headsets"/></Category>'
            f'<ProductFeature Presentation_Value="{conexao}"><Feature><Name Value="Connectivity technology"/></Feature>'
            '</ProductFeature></Product></ICECAT-interface>').encode()


def normalizar(corpo, categoria, categoria_id):
    referencia = {'id': '9', 'categoria': categoria_id, 'atualizado': '20261104000000'}
    return NormalizarFichaIcecatService().executar(corpo, referencia, categoria)['dados']


def test_normalizador_le_conexao_do_fone_e_portas_do_monitor():
    assert normalizar(xml_fone('Wired'), 'fone', '1637')['conexao'] == 'Wired'
    portas = {'HDMI ports quantity': '2', 'DisplayPorts quantity': '1', 'VGA (D-Sub) ports quantity': '0'}
    assert normalizar(xml_monitor(portas), 'monitor', '222')['conexao'] == 'displayport, hdmi'
    assert 'conexao' not in normalizar(xml_monitor({'HDMI ports quantity': '0'}), 'monitor', '222')
