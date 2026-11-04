from types import SimpleNamespace
from dataclasses import replace
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from services.mercadolivre_service.normalizar_produto_service import NormalizarProdutoService
from services.mercadolivre_service.especificacoes_complementares import tipo_refrigeracao
from utils.identidade_peca import assinatura_peca


def test_codigo_comercial_precisa_origem_valida_e_nao_apaga_contradicao():
    p=SimpleNamespace(__tablename__='fan',id=1,fabricante='Marca',modelo='F120',part_number=None,
        codigo_modelo_fabricante='F120-3P',fontes_especificacoes={},tamanho_mm=120,quantidade=3,
        iluminacao=None,kabum_external='https://www.kabum.com.br/produto/123/fan')
    d=ProdutoNormalizado(loja='loja',id_externo='1',categoria='fan',categoria_confirmada=True,
        titulo='Kit 3 fans Marca F120',marca='Marca',modelo='F120-3P',ativo=True,
        especificacoes={'tamanho_mm':120,'quantidade':3})
    s=AssociacaoInteligenteService()
    assert s.avaliar(p,d)['classificacao']=='ambigua'
    p.fontes_especificacoes={'codigo_modelo_fabricante':dict(valor='F120-3P',criterio='anuncio_original_e_especificacoes_compativeis',
        assinatura_peca=assinatura_peca(p),url='https://www.kabum.com.br/produto/123',sha256_especificacoes='a'*64,titulo_origem='Marca F120 kit 3 fans')}
    r=s.avaliar(p,d)
    assert r['classificacao']=='confirmada' and r['criterio']=='codigo_fabricante'
    assert s.avaliar(p,replace(d,especificacoes={'tamanho_mm':120,'quantidade':1}))['classificacao']=='rejeitada'
    p.modelo='F120 V2'
    assert s.avaliar(p,d)['classificacao']!='confirmada'


def test_led_azul_nao_significa_rgb_e_sem_rgb_nao_significa_sem_luz():
    n=NormalizarProdutoService()
    dados={'id':'MLB123','name':'Fan azul','status':'active','domain_id':'MLB-DESKTOP_COMPUTER_COOLERS_AND_FANS',
        'attributes':[{'id':'PRODUCT_TYPE','value_name':'Ventoinha'},{'id':'WITH_RGB_LIGHTING','value_name':'Não'},
                      {'id':'LED_COLOR','value_name':'Azul'}]}
    d=n.executar(dados,'fan')
    assert d.especificacoes['iluminacao']==['sim'] and d.especificacoes['rgb']==['nao']
    dados['attributes']=dados['attributes'][:2]
    assert 'iluminacao' not in n.executar(dados,'fan').especificacoes


def test_refrigeracao_considera_sockets_de_cpu_e_bloqueia_contradicoes():
    assert tipo_refrigeracao({'PRODUCT_TYPE':{'ventoinha'},'REFRIGERATION_TYPE':{'air cooling'},'CPU_SOCKETS':{'amd am4, intel lga1700'}})=='air_cooler'
    assert tipo_refrigeracao({'PRODUCT_TYPE':{'ventoinha'},'REFRIGERATION_TYPE':{'ar'}})=='fan'
    assert tipo_refrigeracao({'PRODUCT_TYPE':{'cooler liquido aio'},'REFRIGERATION_TYPE':{'ar'}}) is None


def test_conexao_desconhecida_nao_vira_contradicao_e_analogicos_preservam_tipo():
    from services.catalogo_service.normalizar_especificacoes import comparar_conexoes
    from services.catalogo_service.conferir_especificacoes_service import converter
    assert comparar_conexoes('usb','wired') is None
    assert comparar_conexoes('usb','usb2.0') is True
    assert comparar_conexoes('hdmi|displayport','hdmi') is None
    assert comparar_conexoes('p2','p3') is False
    assert converter('conexao','3.5 mm') == 'jack3.5mm'
    assert converter('conexao','jack3.5mm') == 'jack3.5mm'
    assert comparar_conexoes('p3','jack3.5mm') is None


def test_codigo_no_titulo_preserva_sufixo_e_rejeita_acessorio():
    p=SimpleNamespace(__tablename__='memoria_ram',id=1,fabricante='Crucial',modelo='Value',part_number=None,
        codigo_modelo_fabricante='CT8G4DFRA32A',fontes_especificacoes={},capacidade_gb=8,ddr='DDR4',
        frequencia_mhz=3200,quantidade_pentes=1,latencia='CL22',formato=None,
        kabum_external='https://www.kabum.com.br/produto/123')
    p.fontes_especificacoes={'codigo_modelo_fabricante':dict(valor=p.codigo_modelo_fabricante,
        criterio='anuncio_original_e_especificacoes_compativeis',assinatura_peca=assinatura_peca(p),
        url=p.kabum_external,sha256_especificacoes='b'*64,titulo_origem='Crucial CT8G4DFRA32A')}
    d=ProdutoNormalizado(loja='loja',id_externo='1',categoria='memoria_ram',categoria_confirmada=True,
        titulo='Crucial CT8G4DFRA32A 8GB DDR4',marca='Crucial',modelo='Value',ativo=True,
        especificacoes={'capacidade_gb':8,'ddr':'DDR4','quantidade_pentes':1})
    s=AssociacaoInteligenteService()
    assert s.avaliar(p,d)['classificacao']=='confirmada'
    assert s.avaliar(p,replace(d,titulo='Crucial CT8G4DFRA32A-US 8GB DDR4'))['classificacao']!='confirmada'
    assert s.avaliar(p,replace(d,titulo='Suporte para Crucial CT8G4DFRA32A'))['classificacao']=='rejeitada'
