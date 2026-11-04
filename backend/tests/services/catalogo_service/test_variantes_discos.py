from types import SimpleNamespace
from dataclasses import replace
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from services.catalogo_service.comparar_codigo_modelo_service import CompararCodigoModeloService


def par():
    p=SimpleNamespace(__tablename__='hd',id=1,fabricante='Seagate',modelo='Constellation ES.3 ST4000NM0053 4TB',
        part_number=None,codigo_modelo_fabricante='ST4000NM0053',fontes_especificacoes={},
        capacidade_gb=4000,interface='SATA III',velocidade_rpm=7200,memoria_cache_mb=None)
    d=ProdutoNormalizado(loja='loja',id_externo='1',categoria='hd',categoria_confirmada=True,
        marca='Seagate',modelo='ST4000NM0033',modelos_alternativos=('Constellation ES.3',),
        titulo='HD Seagate Constellation ES.3 ST4000NM0033 4TB SATA III 7200RPM',ativo=True,
        especificacoes={'capacidade_gb':4000,'interface':'SATA III','velocidade_rpm':7200})
    return p,d


def test_modelos_completos_diferentes_na_mesma_linha_sao_bloqueados():
    p,d=par();r=AssociacaoInteligenteService().avaliar(p,d)
    assert r['classificacao']=='rejeitada' and 'codigo_armazenamento_divergente' in r['conflitos']


def test_codigo_exato_e_multiplos_codigos_nao_sao_equivalentes():
    p,d=par();d=replace(d,modelo='ST4000NM0053',titulo='HD Seagate ST4000NM0053 4TB')
    assert not CompararCodigoModeloService.variantes_armazenamento(p,d)['conflitos']
    d=replace(d,modelos_alternativos=('ST4000NM0033',))
    assert 'codigos_armazenamento_multiplos' in CompararCodigoModeloService.variantes_armazenamento(p,d)['pendencias']


def test_sas_no_modelo_nao_passa_com_sata_no_cadastro():
    p,d=par();p.modelo='Constellation ST3000NM0023 SAS 3';p.codigo_modelo_fabricante=None
    r=CompararCodigoModeloService.variantes_armazenamento(p,d)
    assert 'interface_local_inconsistente' in r['conflitos']


def test_revisoes_explicitas_de_codigo_nao_sao_apagadas():
    p,d=par();p.modelo='WD Red Plus WD40EFZZ-00BFB0';p.codigo_modelo_fabricante=None
    d=replace(d,modelo='WD40EFZZ-68GBG0',titulo='HD WD40EFZZ-68GBG0',modelos_alternativos=())
    assert 'codigo_armazenamento_divergente' in CompararCodigoModeloService.variantes_armazenamento(p,d)['conflitos']


def test_interface_e_versao_de_linha_nao_sao_codigos_comerciais():
    extrair=CompararCodigoModeloService.extrair
    assert not extrair('PCIe4.0 NVMe1.3 SATA3 Gen4 ES.3','ssd')
    assert extrair('ST4000NM0053','hd')=={'st4000nm0053'}
    p=SimpleNamespace(__tablename__='ssd',id=1,fabricante='Kingston',modelo='NV3 PCIe4.0',part_number=None,
        capacidade_gb=500,tipo='NVMe',interface='PCIe 4.0')
    d=ProdutoNormalizado(loja='loja',id_externo='1',categoria='ssd',categoria_confirmada=True,
        marca='Kingston',modelo='NV2 PCIe4.0',titulo='SSD Kingston NV2 500GB PCIe4.0',ativo=True,
        especificacoes={'capacidade_gb':500,'tipo':'NVMe','interface':'PCIe 4.0'})
    assert AssociacaoInteligenteService().avaliar(p,d)['classificacao']!='confirmada'
