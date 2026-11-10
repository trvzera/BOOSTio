"""Fixtures sintéticas do contrato XML documentado, sem chamadas de rede."""
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock
import pytest
from flask import Flask
from models import db, HD, Oferta, HistoricoOferta, ProdutoPendente, ControleColeta
from services.icecat_service.indice_icecat_service import IndiceIcecatService
from services.icecat_service.completar_ficha_icecat_service import CompletarFichaIcecatService
from services.icecat_service.normalizar_ficha_icecat_service import NormalizarFichaIcecatService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.mercadolivre_service.importar_produto_service import ImportarProdutoService
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService


def indice_xml(arquivo, registros=''):
    arquivo.write_text('<ICECAT-interface><files.index Generated="20261104000000">'+registros+'</files.index></ICECAT-interface>')


def registro(identificador='123',mpn='ST8000NM017B'):
    return f'<file Product_ID="{identificador}" Prod_ID="{mpn}" Model_Name="Exos 8TB" Catid="175" Updated="20261104000000"/>'


def xml_ficha(identificador='123',capacidade='8 TB'):
    atributos = {'HDD capacity':capacidade,'Interface':'SATA III','HDD speed':'7200 RPM'}
    features = ''.join(f'<ProductFeature Presentation_Value="{v}"><Feature><Name Value="{k}"/></Feature></ProductFeature>' for k,v in atributos.items())
    return (f'<ICECAT-interface><Product ID="{identificador}" Name="Exos 8TB" Prod_id="ST8000NM017B">'
            '<Supplier Name="Seagate"/><Category ID="175"><Name Value="Internal Hard Drives"/></Category>'
            +features+'</Product></ICECAT-interface>').encode()


@pytest.fixture
def base(tmp_path):
    arquivo=tmp_path/'indice.xml';indice_xml(arquivo,registro())
    indice=IndiceIcecatService(tmp_path/'indice.db');indice.preparar(arquivo)
    fichas=Mock();fichas.executar.return_value=xml_ficha()
    return CompletarFichaIcecatService(indice,fichas)


def test_indice_ambiguidades_e_reconstrucao_atomica(tmp_path):
    arquivo=tmp_path/'indice.xml';indice_xml(arquivo,registro()+registro('124'))
    indice=IndiceIcecatService(tmp_path/'indice.db')
    assert indice.preparar(arquivo)['produtos']==2
    produto=ProdutoNormalizado(loja='teste',id_externo='1',categoria='hd',titulo='Exos',identificadores={'mpn':'ST8000NM017B'})
    assert len(indice.buscar(produto))==2
    arquivo.write_text('<invalido>')
    with pytest.raises(Exception):indice.preparar(arquivo)
    assert len(indice.buscar(produto))==2


def test_ficha_id_categoria_e_entidades_sao_validados():
    ref=dict(id='123',categoria='175',atualizado='20261104000000')
    normalizar=NormalizarFichaIcecatService()
    with pytest.raises(ValueError):normalizar.executar(xml_ficha('999'),ref,'hd')
    with pytest.raises(ValueError):normalizar.executar(xml_ficha(),ref,'ssd')
    with pytest.raises(ValueError):normalizar.executar(b'<!DOCTYPE x [<!ENTITY a "ataque">]><ICECAT-interface>&a;</ICECAT-interface>',ref,'hd')


@pytest.fixture
def banco():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        p=ProdutoPendente(loja='mercado_livre',produto_id_loja='MLB10',vendedor_id='7',titulo='Seagate Exos 8TB',
            url='https://produto.mercadolivre.com.br/MLB-10-_JM',categoria_sugerida='hd',coletado_em=datetime(2026,11,4),
            dados_originais={'catalogo':{'id':'MLB99'},'anuncio':{'title':'Seagate Exos 8TB'}})
        db.session.add(p);db.session.commit()
        yield p
        db.session.remove();db.engine.dispose()


def importar(base):
    cliente=BuscarOfertasMercadoLivreService()
    produto=dict(id='MLB99',name='Seagate Exos 8TB',status='active',domain_id='MLB-HARD_DRIVES_AND_SSDS',attributes=[
        dict(id=k,value_name=v) for k,v in [('BRAND','Seagate'),('MODEL','Exos 8TB'),('MPN','ST8000NM017B'),
        ('CAPACITY','8 TB'),('DRIVE_STORAGE_TYPE','HDD')]])
    cliente._consultar=Mock(return_value=produto)
    anuncio=cliente._normalizar(dict(item_id='MLB10',seller_id=7,site_id='MLB',currency_id='BRL',price=999.9,condition='new'),'MLB99')
    cliente.executar=Mock(return_value={'ofertas':[anuncio]})
    token=Mock();token.executar.return_value='token-de-teste'
    return ImportarProdutoService(cliente=cliente,tokens=token,base_icecat=base)


def test_descoberta_completa_com_icecat_cria_peca_oferta_historico_e_repete(banco,base):
    service=importar(base)
    assert service.executar(banco.id,permitir_novos=True)['acao']=='proposta'
    assert HD.query.count()==Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==0
    r=service.executar(banco.id,simular=False,permitir_novos=True)
    assert r['acao']=='importada' and r['novo_componente'],r
    p=HD.query.one()
    assert p.capacidade_gb==8000 and p.interface=='SATA III' and p.velocidade_rpm==7200
    assert p.consumo_energia is None and p.ficha_montagem_validada is True
    assert Oferta.query.filter(Oferta.loja!='kabum').one().preco==Decimal('999.90') and Oferta.query.filter(Oferta.loja!='kabum').one().esgotado is None
    assert HistoricoOferta.query.count()==1
    assert p.fontes_especificacoes['interface']['base']=='Icecat'
    assert service.executar(banco.id,simular=False,permitir_novos=True)['acao']=='inalterada'
    assert HD.query.count()==Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==1


def test_divergencia_na_ficha_nao_cadastra(banco,base):
    base.fichas.executar.return_value=xml_ficha(capacidade='4 TB')
    assert importar(base).executar(banco.id,simular=False,permitir_novos=True)['acao']=='revisao'
    assert HD.query.count()==Oferta.query.filter(Oferta.loja!='kabum').count()==0


def test_sem_permissao_nao_consulta_icecat(banco,base):
    assert importar(base).executar(banco.id,simular=False)['acao']=='revisao'
    base.fichas.executar.assert_not_called()


def test_falha_historico_reverte_peca_e_oferta(banco,base,monkeypatch):
    from services.catalogo_service.gravar_importacao_catalogo_service import GravarImportacaoCatalogoService
    def falhar(*a,**k):raise ValueError('Falha de persistência')
    monkeypatch.setattr(GravarImportacaoCatalogoService,'concluir',falhar)
    with pytest.raises(ValueError):importar(base).executar(banco.id,simular=False,permitir_novos=True)
    assert HD.query.count()==Oferta.query.filter(Oferta.loja!='kabum').count()==HistoricoOferta.query.count()==0


def test_peca_conflitante_com_mesmo_mpn_nao_vira_duplicata(banco,base):
    db.session.add(HD(fabricante='Seagate',modelo='Exos 4TB',part_number='ST8000NM017B',
        capacidade_gb=4000,interface='SATA III',preco=500,consumo_energia=7,status_validacao='aprovado'))
    db.session.commit()
    r=importar(base).executar(banco.id,simular=False,permitir_novos=True)
    assert r['acao']=='revisao'
    assert HD.query.count()==1 and Oferta.query.filter(Oferta.loja!='kabum').count()==0


def test_indice_gtin_contraditorio_nao_recua_para_modelo(tmp_path):
    arquivo=tmp_path/'indice.xml'
    indice_xml(arquivo,registro())
    indice=IndiceIcecatService(tmp_path/'indice.db');indice.preparar(arquivo)
    p=ProdutoNormalizado(loja='teste',id_externo='1',categoria='hd',titulo='Exos 8TB',marca='Seagate',modelo='Exos 8TB',
        identificadores={'mpn':'ST8000NM017B','gtin':'0740617206937'})
    assert indice.buscar(p)==[]


def test_indice_bloqueia_entidades_externas(tmp_path):
    arquivo=tmp_path/'indice.xml'
    arquivo.write_text('<!DOCTYPE x [<!ENTITY e SYSTEM "file:///etc/passwd">]><ICECAT-interface>&e;</ICECAT-interface>')
    with pytest.raises(Exception):IndiceIcecatService(tmp_path/'indice.db').preparar(arquivo)
    assert not (tmp_path/'indice.db').exists()


def test_ram_representacoes_gb_mb_observadas_na_ficha_real():
    corpo=b'''<ICECAT-interface><Product ID="14532212" Name="ValueRAM" Prod_id="KVR16N11/8">
    <Supplier Name="Kingston Technology"/><Category ID="911"><Name Value="Memory Modules"/></Category>
    <ProductFeature Presentation_Value="8 GB"><Feature><Name Value="Internal memory"/></Feature></ProductFeature>
    <ProductFeature Presentation_Value="8192 MB"><Feature><Name Value="Internal memory"/></Feature></ProductFeature>
    <ProductFeature Presentation_Value="1 x 8 GB"><Feature><Name Value="Memory layout (modules x size)"/></Feature></ProductFeature>
    <ProductFeature Presentation_Value="1600 MHz"><Feature><Name Value="Bus clock rate"/></Feature></ProductFeature>
    </Product></ICECAT-interface>'''
    r=NormalizarFichaIcecatService().executar(corpo,dict(id='14532212',categoria='911',atualizado='20261104000000'),'memoria_ram')
    assert r['dados']['capacidade_gb']==8 and r['dados']['quantidade_pentes']==1
    assert r['dados']['frequencia_mhz']==1600 and r['conflitos']==[]


def test_serial_ata_iii_da_ficha_real_preserva_geracao():
    ref = dict(id='123',categoria='175',atualizado='20261104000000')
    xml = xml_ficha().replace(b'SATA III', b'Serial ATA III')
    ficha = NormalizarFichaIcecatService().executar(xml,ref,'hd')
    assert ficha['dados']['interface'] == 'SATA III'
    from services.catalogo_service.conferir_especificacoes_service import converter
    assert converter('interface', ficha['dados']['interface']) == converter('interface','SATA rev. 3.0 (6Gb/s)')


def test_embalagem_de_20_discos_nao_vira_componente_unitario(banco,base):
    xml = xml_ficha().replace(b'</Product>', b'<ProductFeature Presentation_Value="20 pc(s)"><Feature>'
        b'<Name Value="Quantity per pack"/></Feature></ProductFeature></Product>')
    base.fichas.executar.return_value = xml
    resultado = importar(base).executar(banco.id,simular=False,permitir_novos=True)
    assert resultado['acao']=='revisao'
    assert 'icecat_embalagem_com_varias_unidades' in resultado['icecat']['candidatos'][0]['conflitos']
    assert HD.query.count()==Oferta.query.filter(Oferta.loja!='kabum').count()==0


def test_codigo_regional_e_somente_sugestao_para_revisao(tmp_path):
    arquivo=tmp_path/'indice.xml'
    indice_xml(arquivo,registro(mpn='CT500BX500SSD1-IN'))
    indice=IndiceIcecatService(tmp_path/'indice.db');indice.preparar(arquivo)
    p=ProdutoNormalizado(loja='loja',id_externo='1',categoria='ssd',titulo='Crucial CT500BX500SSD1',
        marca='Crucial',modelo='CT500BX500SSD1',identificadores={'mpn':'CT500BX500SSD1'})
    assert indice.buscar(p)==[]
    diagnostico=indice.diagnosticar_ausencia(p)
    assert diagnostico['motivo']=='candidatos_alternativos_exigem_revisao'
    assert diagnostico['candidatos_para_revisao'][0]['mpn']=='ct500bx500ssd1-in'


def test_codigo_parecido_de_outro_fabricante_fica_rejeitado(banco,base,tmp_path):
    arquivo=tmp_path/'outro-indice.xml'
    indice_xml(arquivo,registro(mpn='ST8000NM017B-IN'))
    base.indice.preparar(arquivo)
    base.fichas.executar.return_value=xml_ficha().replace(b'ST8000NM017B',b'ST8000NM017B-IN').replace(b'Seagate',b'Outro fabricante')
    produto=ProdutoNormalizado(loja='mercado_livre',id_externo='MLB99',categoria='hd',categoria_confirmada=True,
        ativo=True,marca='Seagate',modelo='Exos 8TB',titulo='Seagate Exos 8TB',identificadores={'mpn':'ST8000NM017B'})
    _,ficha=base.executar(produto,dict(dados={},conflitos=[],fontes={}))
    d=ficha['icecat']['avaliacoes_alternativas'][0]
    assert d['classificacao']=='rejeitada' and 'marca_divergente' in d['conflitos']
    assert HD.query.count()==0
