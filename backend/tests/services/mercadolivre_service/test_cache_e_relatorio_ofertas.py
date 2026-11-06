import json
from unittest.mock import patch
import pytest
from services.mercadolivre_service.cliente_catalogo_cache_service import ClienteCatalogoCacheService
from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.mercadolivre_service.controle_requisicoes_service import ControleRequisicoesService
from services.catalogo_service.relatorio_ofertas_service import RelatorioOfertasService


def cliente(**opcoes):
    controle=ControleRequisicoesService(50,.1,dormir=lambda _:None,relogio=lambda:0)
    return ClienteCatalogoCacheService(controle,**opcoes)


def test_cache_limitado_expira_e_nao_compartilha_mutacoes():
    tempo=[0];c=cliente(capacidade=2,validade=60,relogio=lambda:tempo[0])
    try:
        with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',return_value={'results':[{'id':'MLB1'}]}) as api:
            primeiro=c._consultar('/products/search','token',{'q':'a'})
            primeiro['results'].clear()
            assert c._consultar('/products/search','token',{'q':'a'})['results']==[{'id':'MLB1'}]
            assert c.controle.total==1 and c.reaproveitadas==1
            tempo[0]=61;c._consultar('/products/search','token',{'q':'a'})
            assert api.call_count==2
            c._consultar('/products/search','token',{'q':'b'})
            c._consultar('/products/search','token',{'q':'c'})
            c._consultar('/products/search','token',{'q':'a'})
            assert api.call_count==5 and len(c.cache)==2
    finally:c.fechar()


def test_gravacao_nunca_reaproveita_detalhe_ou_preco():
    c=cliente(simular=False)
    try:
        with patch.object(BuscarOfertasMercadoLivreService,'_requisitar',return_value={'results':[]}) as api:
            for caminho in ('/products/MLB1','/products/MLB1/items'):
                c._consultar(caminho,'token');c._consultar(caminho,'token')
            assert api.call_count==4
            c._consultar('/products/search','token');c._consultar('/products/search','token')
            assert api.call_count==5
    finally:c.fechar()


def estado(**opcoes):
    return dict(simulacao=True,pecas=1,associadas=1,falhas=0,requisicoes=3,
        cursores={'processador':1},detalhes=[{'peca':'processador:1','status':'proposta'}],
        ultima_peca_concluida='processador:1',**opcoes)


def test_relatorio_incremental_retomada_nao_duplica_contagens(tmp_path):
    path=tmp_path/'resumo.json';opcoes={'simular':True,'banco':'hash'}
    r=estado();r.update(pecas=2,falhas=1,interrompido=True)
    r['detalhes'].append({'peca':'processador:2','status':'falha'})
    with RelatorioOfertasService(path,opcoes) as relatorio:relatorio.atualizar(r)
    with RelatorioOfertasService(path,opcoes,retomar=True) as relatorio:
        assert relatorio.cursores=={'processador':1}
        r=estado();r['cursores']={'processador':2};r['detalhes']=[{'peca':'processador:2','status':'proposta'}]
        r['ultima_peca_concluida']='processador:2'
        relatorio.atualizar(r)
    resultado=json.loads(path.read_text())
    assert resultado['pecas']==resultado['associadas']==2 and resultado['falhas']==0
    assert resultado['falhas_anteriores']==1 and resultado['requisicoes']==6
    assert len(path.with_suffix('.detalhes.jsonl').read_text().splitlines())==3


def test_relatorio_bloqueia_outro_banco_filtro_ou_processo(tmp_path):
    path=tmp_path/'resumo.json';opcoes={'simular':True,'banco':'hash'}
    with RelatorioOfertasService(path,opcoes) as relatorio:
        relatorio.atualizar(estado())
        with pytest.raises(ValueError,match='outra execução'):
            with RelatorioOfertasService(path,opcoes,retomar=True):pass
    for alteracao in ({'simular':False,'banco':'hash'},{'simular':True,'banco':'outra-base'}):
        with pytest.raises(ValueError,match='Banco ou filtros'):
            with RelatorioOfertasService(path,alteracao,retomar=True):pass
    with pytest.raises(ValueError,match='já existe'):
        with RelatorioOfertasService(path,opcoes):pass
