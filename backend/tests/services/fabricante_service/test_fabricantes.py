from unittest.mock import Mock
import json
import pytest
from services.fabricante_service.normalizar_ficha_service import NormalizarFichaFabricanteService
from services.fabricante_service.consultar_paginas_service import ConsultarPaginasFabricanteService
from services.fabricante_service.descobrir_ficha_service import DescobrirFichaFabricanteService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado


def produto():
    return ProdutoNormalizado(loja='loja',id_externo='1',titulo='Corsair CMW16GX4M2C3200C16',
        categoria='memoria_ram',marca='Corsair',modelo='CMW16GX4M2C3200C16',ativo=True,categoria_confirmada=True)


def html(sku='CMW16GX4M2C3200C16'):
    p={'@type':'Product','sku':sku,'name':'Vengeance RGB Pro','brand':{'name':'Corsair'}}
    return '<script type="application/ld+json">'+json.dumps(p)+'</script><table><tr><th>Memory Size</th><td>16GB (2 x 8GB)</td></tr><tr><th>Tested Speed</th><td>3200 MT/s</td></tr><tr><th>Memory Type</th><td>DDR4</td></tr></table>'


def test_ram_kit_e_unidade_preservados():
    r=NormalizarFichaFabricanteService().executar(html(),'https://www.corsair.com/p','corsair',produto())
    assert r['dados']['capacidade_gb']==16 and r['dados']['quantidade_pentes']==2
    assert 'frequencia_mhz' not in r['dados']
    assert r['especificacoes_originais']['Tested Speed']=='3200 MT/s'
    assert r['fontes']['capacidade_gb']['sha256']


def test_variante_diferente_recusada():
    with pytest.raises(ValueError):NormalizarFichaFabricanteService().executar(html('OUTRO-SKU'),'https://www.corsair.com/p','corsair',produto())


@pytest.mark.parametrize('url',['http://www.corsair.com/a','https://www.corsair.com.evil.test/a','https://user:senha@www.corsair.com/a','https://127.0.0.1/a'])
def test_url_oficial_exigida(url):
    with pytest.raises(ValueError):ConsultarPaginasFabricanteService.validar(url,'corsair')


def test_sitemap_localiza_codigo_exato_sem_confundir_sufixo():
    paginas=Mock();paginas.regras.return_value.site_maps.return_value=['https://www.corsair.com/us-sitemap.xml']
    paginas.executar.return_value='<urlset><url><loc>https://www.corsair.com/us/en/p/CMW16GX4M2C3200C16</loc></url><url><loc>https://www.corsair.com/us/en/p/CMW16GX4M2C3200C16W</loc></url></urlset>'
    urls=DescobrirFichaFabricanteService(paginas).executar('corsair',produto())
    assert len(urls)==1 and urls[0].endswith('CMW16GX4M2C3200C16')


def test_amd_sem_evidencia_da_embalagem_nao_escolhe_mpn():
    p=ProdutoNormalizado(loja='loja',id_externo='1',categoria='processador',marca='AMD',modelo='5700X',titulo='AMD Ryzen 7 5700X')
    h='<dl><dt>Name</dt><dd>AMD Ryzen 7 5700X</dd><dt>Product ID Boxed</dt><dd>100-100000926WOF</dd></dl>'
    with pytest.raises(ValueError):NormalizarFichaFabricanteService().executar(h,'https://www.amd.com/a','amd',p)


def test_robots_bloqueia_antes_de_buscar_pagina(tmp_path,monkeypatch):
    from urllib.robotparser import RobotFileParser
    regras=RobotFileParser();regras.parse(['User-agent: *','Disallow: /'])
    s=ConsultarPaginasFabricanteService(tmp_path);s.robos['corsair']=regras
    get=Mock();monkeypatch.setattr('requests.get',get)
    with pytest.raises(ValueError,match='recusada'):s.executar('https://www.corsair.com/p','corsair')
    get.assert_not_called()


def test_dois_skus_confirmados_da_mesma_familia_exigem_revisao():
    h=html()+html('CMW16GX4M2C3200C16W')
    r=NormalizarFichaFabricanteService().executar(h,'https://www.corsair.com/p','corsair',produto())
    assert r['identidade']['mpn']=='CMW16GX4M2C3200C16'
