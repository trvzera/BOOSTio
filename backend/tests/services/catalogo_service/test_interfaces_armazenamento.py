from types import SimpleNamespace
from services.catalogo_service.conferir_especificacoes_service import converter, ConferirEspecificacoesService
from services.mercadolivre_service.normalizar_produto_service import NormalizarProdutoService


def produto(interfaces,conectividade=None):
    attrs=[{'id':'MODEL','value_name':'NV2'},{'id':'BRAND','value_name':'Kingston'},
           {'id':'CAPACITY','value_name':'500 GB'}]
    if interfaces:attrs.append({'id':'INTERFACES','value_name':interfaces})
    if conectividade:attrs.append({'id':'CONNECTIVITY','value_name':conectividade})
    return NormalizarProdutoService().executar({'id':'MLB123','name':'SSD Kingston NV2 500GB',
        'status':'active','domain_id':'MLB-HARD_DRIVES_AND_SSDS','attributes':attrs},'ssd')


def test_revisoes_equivalentes_preservam_geracao_e_lanes():
    assert converter('interface','SATA Rev. 3.0 (6Gb/s)')==converter('interface','SATA III')
    assert converter('interface','PCI Express 4.0 x4')==converter('interface','PCIe Gen4 x4')
    assert converter('interface','PCIe 3.0 x4')!=converter('interface','PCIe 4.0 x4')
    assert converter('interface','PCIe 4.0 x2')!=converter('interface','PCIe 4.0 x4')
    assert converter('interface','SATA II')!=converter('interface','SATA III')
    assert converter('interface','NVMe')!=converter('interface','PCIe 4.0')


def test_nvme_nao_e_segunda_interface_conflitante_com_pcie():
    d=produto('PCIe 4.0 x4, NVMe')
    assert d.especificacoes['interface']==['pcie 4.0 x4']
    assert d.especificacoes['tipo']==['nvme']
    p=SimpleNamespace(__tablename__='ssd',capacidade_gb=500,tipo='NVMe',interface='PCIe 4.0')
    r=ConferirEspecificacoesService().executar(p,d)
    assert r['completa'] and not r['conflitos']


def test_connectivity_explicita_sata_sem_inferir_pcie_por_nvme():
    d=produto(None,'SATA Rev. 3.0 (6Gb/s)')
    assert d.especificacoes['tipo']==['sata rev. 3.0 (6gb/s)']
    p=SimpleNamespace(__tablename__='ssd',capacidade_gb=500,tipo='SATA',interface='SATA III')
    assert ConferirEspecificacoesService().executar(p,d)['completa']
    d=produto('NVMe')
    assert d.especificacoes['tipo']==['nvme'] and d.especificacoes['interface']==[]
    assert 'interface' in ConferirEspecificacoesService().executar(p,d)['ausentes']


def test_geracao_divergente_ou_duas_interfaces_continuam_bloqueadas():
    p=SimpleNamespace(__tablename__='ssd',capacidade_gb=500,tipo='NVMe',interface='PCIe 4.0')
    assert 'especificacao_divergente:interface' in ConferirEspecificacoesService().executar(p,produto('PCIe 3.0 x4, NVMe'))['conflitos']
    assert 'especificacao_divergente:interface' in ConferirEspecificacoesService().executar(p,produto('PCIe 3.0, PCIe 4.0, NVMe'))['conflitos']


def test_reprocessa_normalizacao_antiga_e_cache_com_fonte_alterada():
    from dataclasses import asdict
    from unittest.mock import patch
    from services.mercadolivre_service.classificar_pendencias_service import ClassificarPendenciasService
    from services.catalogo_service.consultar_base_hardware_service import ConsultarBaseHardwareService
    from utils.identidade_peca import assinatura_catalogo
    bruto={'id':'MLB123','name':'SSD Kingston NV2 500GB','domain_id':'MLB-HARD_DRIVES_AND_SSDS',
           'status':'active','attributes':[{'id':'INTERFACES','value_name':'PCIe 4.0 x4, NVMe'}]}
    velho=asdict(NormalizarProdutoService().executar(bruto,'ssd'));velho['especificacoes']['interface']=['nvme']
    ficha=dict(produto=bruto,normalizado=velho,normalizacao_versao='antiga',assinatura_catalogo=assinatura_catalogo(bruto))
    pendente=SimpleNamespace(loja='mercado_livre',categoria_sugerida='ssd',dados_originais={'catalogo':bruto},evidencias={'enriquecimento':ficha})
    with patch.object(ConsultarBaseHardwareService,'executar',side_effect=lambda p:{'produto':p}) as base:
        normalizado=ClassificarPendenciasService.normalizar(pendente)[0]
        assert normalizado.especificacoes['interface']==['pcie 4.0 x4'] and base.call_count==1
        ficha['normalizacao_versao']=NormalizarProdutoService.VERSAO
        ficha['assinatura_catalogo']='0'*64
        assert ClassificarPendenciasService.normalizar(pendente)[0].especificacoes['interface']==['pcie 4.0 x4']
