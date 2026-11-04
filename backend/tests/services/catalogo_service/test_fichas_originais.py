from dataclasses import replace
import pytest
from flask import Flask
from models import db, MemoriaRAM, Oferta
from services.especificacoes_service.normalizar_ficha_kabum_service import NormalizarFichaKabumService
from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService


@pytest.fixture
def banco():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();yield app;db.session.remove();db.engine.dispose()


def ficha(**mudancas):
    return {**dict(id=123,title='Memória RAM Crucial Value 8GB DDR4 3200MHz CL22',
        manufacturer={'name':'Crucial'},category='Hardware/Memória RAM/DDR 4',
        technicalInformation={'text':'<b>Modelo:</b> CT8G4DFRA32A<br>Capacidade: 8GB<br>Tipo: DDR4<br>Velocidade: 3200 MHz<br>Latência: CL22<br>288-Pin UDIMM<br><b>Altura Real</b><p>99</p><script>formato: SODIMM</script>'}),**mudancas}


def memoria():
    p=MemoriaRAM(fabricante='Crucial',modelo='Value',consumo_energia=5,preco=123,
        capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1,latencia='CL22',
        formato=None,kabum_external='https://www.kabum.com.br/produto/123/teste')
    db.session.add(p);db.session.commit();return p


def dto(p):
    d=NormalizarFichaKabumService().executar(ficha(), 'memoria_ram', codigo_esperado='123')
    return replace(d,contexto={**d.contexto,'origem_peca':f'memoria_ram:{p.id}'})


def test_origem_comprovada_preenche_lacuna_sem_inventar_dimensoes(banco):
    p=memoria();d=dto(p)
    assert EnriquecerPecaExistenteService().preparar(p,d)['status']=='sem_correspondencia'
    db.session.add(Oferta(tabela_peca='memoria_ram',peca_id=p.id,loja='kabum',produto_id_loja='123',url=d.fonte));db.session.commit()
    s=EnriquecerPecaExistenteService();r=s.executar(p,d,simular=False)
    assert r['status']=='atualizada' and p.formato=='DIMM' and p.part_number=='CT8G4DFRA32A'
    assert p.preco==123 and p.fontes_especificacoes['formato']['criterio']=='anuncio_original_e_especificacoes_compativeis'
    assert s.executar(p,d,simular=False)['status']=='inalterada'


def test_id_ou_categoria_errada_nao_autoriza():
    s=NormalizarFichaKabumService()
    with pytest.raises(ValueError):s.executar(ficha(), 'memoria_ram',codigo_esperado=456)
    assert not s.executar(ficha(category='Hardware/SSD'), 'memoria_ram',codigo_esperado=123).categoria_confirmada


def test_formato_contraditorio_e_preservado(banco):
    p=memoria();p.formato='SO-DIMM';db.session.commit()
    db.session.add(Oferta(tabela_peca='memoria_ram',peca_id=p.id,loja='kabum',produto_id_loja='123',url='https://www.kabum.com.br/produto/123'));db.session.commit()
    assert EnriquecerPecaExistenteService().executar(p,dto(p),simular=False)['status']=='revisao'
    assert p.formato=='SO-DIMM' and p.part_number is None


def test_modelo_e_titulo_com_sufixos_distintos_ficam_em_revisao(banco):
    p=memoria();p.fabricante='Kingston';p.modelo='KVR26N19S8/8';p.frequencia_mhz=2666;p.latencia='CL19';db.session.commit()
    db.session.add(Oferta(tabela_peca='memoria_ram',peca_id=p.id,loja='kabum',produto_id_loja='123',url='https://www.kabum.com.br/produto/123'));db.session.commit()
    dados=ficha(title='Kingston KVR26N19S8/8 8GB DDR4 2666MHz CL19',manufacturer={'name':'Kingston'},
        technicalInformation={'text':'Modelo: KVR26N19S8/8-US<br>8GB DDR4 2666MHz CL19<br>288-Pin DIMM'})
    d=NormalizarFichaKabumService().executar(dados,'memoria_ram',codigo_esperado='123')
    d=replace(d,contexto={**d.contexto,'origem_peca':f'memoria_ram:{p.id}'})
    assert EnriquecerPecaExistenteService().executar(p,d,simular=False)['status']=='revisao'
    assert p.part_number is None and p.formato is None


def test_revalida_oferta_original_antes_de_persistir(banco):
    from models.especificacoes_peca import preencher_especificacoes
    from utils.identidade_peca import assinatura_peca
    p=memoria();d=dto(p)
    oferta=Oferta(tabela_peca='memoria_ram',peca_id=p.id,loja='kabum',produto_id_loja='123',url=d.fonte)
    db.session.add(oferta);db.session.commit()
    proposta=EnriquecerPecaExistenteService().preparar(p,d);assinatura=assinatura_peca(p)
    oferta.produto_id_loja='456';db.session.commit()
    with pytest.raises(ValueError,match='Oferta original mudou'):
        preencher_especificacoes(p,proposta,assinatura,simular=False)
    assert p.formato is None and p.part_number is None
