from services.especificacoes_service.aplicar_revisao_identidade_service import AplicarRevisaoIdentidadeService
from dataclasses import replace
import pytest
from flask import Flask
from models import db, PlacaVideo, Oferta, RevisaoIdentidadePeca
from services.especificacoes_service.converter_referencias_gpu_service import ConverterReferenciasGpuService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado


@pytest.fixture
def banco():
    a=Flask(__name__);a.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(a)
    with a.app_context():
        db.create_all();yield;db.session.remove();db.engine.dispose()


def par():
    p=PlacaVideo(fabricante='NVIDIA',modelo='GeForce RTX 4060',memoria_gb=8,tipo_memoria='GDDR6',
        preco=1500,consumo_energia=115,kabum_external='https://www.kabum.com.br/produto/123')
    db.session.add(p);db.session.commit()
    d=ProdutoNormalizado(loja='kabum',id_externo='123',categoria='placa_video',categoria_confirmada=True,
        titulo='Placa de Vídeo Marca GeForce RTX 4060 8GB GDDR6 - GV-N4060-8GD',marca='Marca',modelo='GV-N4060-8GD',
        modelos_alternativos=('GV-N4060-8GD',),ativo=True,fonte=p.kabum_external,
        especificacoes={'memoria_gb':8,'tipo_memoria':'GDDR6'},
        contexto={'finalidade':'especificacoes','origem_peca':f'placa_video:{p.id}'})
    return p,d


def test_conversao_preserva_id_preco_benchmark_e_registra_antes_depois(banco):
    p,d=par();p.benchmark_g3d=20000;db.session.commit();ident=p.id
    s=ConverterReferenciasGpuService();proposta=s.preparar(p,d)
    assert proposta['status']=='proposta'
    assert AplicarRevisaoIdentidadeService().executar(p,proposta)['status']=='proposta'
    assert p.fabricante=='NVIDIA' and RevisaoIdentidadePeca.query.count()==0
    AplicarRevisaoIdentidadeService().executar(p,proposta,simular=False)
    assert p.id==ident and p.fabricante=='Marca' and p.fabricante_chip=='NVIDIA'
    assert p.modelo_referencia=='GeForce RTX 4060' and p.preco==1500 and p.benchmark_g3d==20000
    assert RevisaoIdentidadePeca.query.one().campos_antes['fabricante']=='NVIDIA'
    assert s.preparar(p,d)['status']=='inalterada'


@pytest.mark.parametrize('titulo,memoria',[
 ('Placa Marca RTX 4060 Ti - GV-N4060-8GD',8),
 ('Placa Marca RTX 4060 - GV-N4060-8GD',16),
 ('Placa Marca RTX 4060 para Notebook - GV-N4060-8GD',8),
])
def test_nao_troca_chip_memoria_ou_notebook(banco,titulo,memoria):
    p,d=par();d=replace(d,titulo=titulo,especificacoes={'memoria_gb':memoria,'tipo_memoria':'GDDR6'})
    assert ConverterReferenciasGpuService().preparar(p,d)['status']=='revisao'
    assert p.fabricante=='NVIDIA'


def test_nao_converte_com_oferta_ml_preexistente(banco):
    p,d=par();proposta=ConverterReferenciasGpuService().preparar(p,d)
    db.session.add(Oferta(tabela_peca='placa_video',peca_id=p.id,loja='mercado_livre',produto_id_loja='MLB123',url='https://produto.mercadolivre.com.br/MLB-123-_JM'))
    db.session.commit()
    with pytest.raises(ValueError,match='oferta externa'):
        AplicarRevisaoIdentidadeService().executar(p,proposta,simular=False)
    assert p.fabricante=='NVIDIA' and RevisaoIdentidadePeca.query.count()==0


def test_revalida_ficha_alterada_antes_da_conversao(banco):
    p,d=par();proposta=ConverterReferenciasGpuService().preparar(p,d)
    p.memoria_gb=16;db.session.commit()
    with pytest.raises(ValueError,match='Peça mudou'):
        AplicarRevisaoIdentidadeService().executar(p,proposta,simular=False)
    assert p.fabricante=='NVIDIA' and RevisaoIdentidadePeca.query.count()==0
