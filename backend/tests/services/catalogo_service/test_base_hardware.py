from dataclasses import replace
import json
from pathlib import Path

from services.catalogo_service.consultar_base_hardware_service import ConsultarBaseHardwareService,BASE
from services.catalogo_service.produto_normalizado import ProdutoNormalizado


def test_base_real_completa_so_campos_com_fonte_e_licenca():
    row=next(r for r in json.loads(BASE.read_text())['motherboard'] if r['id']=='mb-asrock-a620am-x')
    p=ProdutoNormalizado(loja='loja_teste',id_externo='x',categoria='placa_mae',categoria_confirmada=True,ativo=True,
        marca='ASRock',modelo='A620AM-X',titulo='Placa mãe ASRock A620AM-X',especificacoes={'socket':'AM5'})
    r=ConsultarBaseHardwareService().executar(p)
    assert r['status']=='encontrada' and r['dados']['tipo_memoria']=='DDR5'
    assert r['dados']['formato']=='Micro-ATX'
    assert all(f['licenca']=='CC BY 4.0' and f['url']==row['source'] and len(f['sha256'])==64 for f in r['fontes'].values())
    assert not {'preco','esgotado','consumo_energia','benchmark_multi_core'} & set(r['dados'])
    conflito=ConsultarBaseHardwareService().executar(replace(p,especificacoes={'socket':'AM4'}))
    assert conflito['status']=='nao_encontrada'


def test_chip_generico_da_base_nao_vira_placa_custom():
    p=ProdutoNormalizado(loja='loja_teste',id_externo='x',categoria='placa_video',categoria_confirmada=True,ativo=True,
        marca='ASUS',modelo='RTX 5060 Ti 16GB',titulo='ASUS RTX 5060 Ti 16GB',especificacoes={'memoria_gb':16})
    assert ConsultarBaseHardwareService().executar(p)['status']=='nao_encontrada'


def test_cache_de_ficha_preserva_identidade_e_estado_do_segundo_anuncio():
    base = ConsultarBaseHardwareService()
    primeiro = ProdutoNormalizado(loja='loja', id_externo='1', categoria='ssd',
        titulo='SSD teste', marca='Marca', modelo='Modelo', ativo=True)
    segundo = replace(primeiro, id_externo='2', ativo=False, identificadores={'mpn':'outra-variante'})
    base.executar(primeiro)
    assert base.executar(segundo)['produto'] == segundo
