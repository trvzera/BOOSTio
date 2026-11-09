from dataclasses import replace
from types import SimpleNamespace

import pytest
from services.catalogo_service.associacao_inteligente_service import AssociacaoInteligenteService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado


def peca(**mudancas):
    return SimpleNamespace(**{**dict(__tablename__='processador',id=1,fabricante='AMD',modelo='Ryzen 5 5500',part_number='SEED-1',soquete='AM4',nucleo=6,thread=12),**mudancas})


def produto(**mudancas):
    return replace(ProdutoNormalizado(loja='outra_loja',id_externo='cpu-5500',categoria='processador',
        categoria_confirmada=True,titulo='Processador AMD Ryzen 5 5500',marca='AMD',modelo='Ryzen 5 5500',
        especificacoes={'soquete':'AM4','nucleo':6,'thread':12},ativo=True),**mudancas)


def test_sem_mpn_confirma_modelo_marca_e_especificacoes():
    r=AssociacaoInteligenteService().avaliar(peca(),produto())
    assert r['percentual']==100 and r['criterio']=='modelo_especificacoes' and r['classificacao']=='confirmada'
    assert r['parcelas']==dict(marca=10,modelo=35,titulo=15,especificacoes=40,identificador_conclusivo=False)
    assert AssociacaoInteligenteService().avaliar(peca(),produto(loja='terceira_loja',id_externo='123'))['percentual']==100


@pytest.mark.parametrize('pct,status',[(0,'rejeitada'),(59.99,'rejeitada'),(60,'ambigua'),(79.99,'ambigua'),(80,'ambigua'),(80.01,'confirmada'),(100,'confirmada')])
def test_fronteiras_exatas(pct,status):
    assert AssociacaoInteligenteService.classificar_percentual(pct)==status


@pytest.mark.parametrize('mudancas',[
 dict(marca='Intel'),dict(titulo='Processador AMD Ryzen 5 5500X',modelo='Ryzen 5 5500X'),
 dict(especificacoes={'soquete':'AM5','nucleo':6,'thread':12}),dict(titulo='Kit AMD Ryzen 5 5500 + A520'),
 dict(titulo='Ryzen 5 5500 para notebook'),dict(identificadores={'mpn':['OUTRO']})])
def test_conflito_nao_e_diluido_por_media(mudancas):
    local=peca(part_number='100-100000457BOX')
    r=AssociacaoInteligenteService().avaliar(local,produto(**mudancas))
    assert r['percentual']==0 and r['classificacao']=='rejeitada'


def test_faltas_essenciais_e_categoria_sugerida_nao_autorizam():
    s=AssociacaoInteligenteService()
    assert 60<=s.avaliar(peca(),produto(especificacoes={'soquete':'AM4'}))['percentual']<=80
    assert s.avaliar(peca(),produto(categoria_confirmada=False))['classificacao']=='ambigua'
    assert s.avaliar(peca(),produto(marca=None,titulo='CPU Ryzen 5 5500'))['classificacao']=='ambigua'


def test_titulo_sozinho_com_as_especificacoes_pode_confirmar():
    p=peca(__tablename__='memoria_ram',fabricante='Kingston',modelo='Fury Beast 8GB',formato='DIMM',capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1,latencia='CL16')
    r=produto(categoria='memoria_ram',marca='Kingston',modelo=None,titulo='Memória RAM Kingston Fury Beast 8GB DDR4 3200MHz CL16 DIMM',
        especificacoes={'quantidade_pentes':1})
    assert AssociacaoInteligenteService().avaliar(p,r)['classificacao']=='confirmada'
    assert AssociacaoInteligenteService().avaliar(p,replace(r,titulo=r.titulo.replace('DDR4','DDR5')))['percentual']==0


def test_duplicatas_e_busca_truncada_nao_escolhem_arbitrariamente():
    s=AssociacaoInteligenteService()
    assert s.selecionar([peca(),peca(id=2)],produto())['classificacao']=='ambigua'
    assert s.selecionar([peca()],produto(),completo=False)['classificacao']=='ambigua'
    assert s.selecionar([peca()],produto())['criterio']=='modelo_especificacoes'


def test_chips_gpu_nao_substituem_versoes_comerciais():
    p=peca(__tablename__='placa_video',fabricante='MSI',modelo='RTX 4070',memoria_gb=12,tipo_memoria='GDDR6X')
    d=produto(categoria='placa_video',marca='MSI',modelo='RTX 4070',titulo='MSI RTX 4070 12GB',especificacoes={'memoria_gb':'12 GB','tipo_memoria':'GDDR6X'})
    assert AssociacaoInteligenteService().avaliar(p,d)['percentual']<=80


def test_wifi_e_rgb_nao_somem_quando_modelo_estruturado_e_generico():
    p=peca(__tablename__='placa_mae',fabricante='MSI',modelo='B550M PRO-VDH',socket='AM4',tipo_memoria='DDR4',formato='mATX')
    d=produto(categoria='placa_mae',marca='MSI',modelo='B550M PRO-VDH',titulo='MSI B550M PRO-VDH WiFi',
              especificacoes={'socket':'AM4','tipo_memoria':'DDR4','formato':'Micro ATX'})
    r=AssociacaoInteligenteService().avaliar(p,d)
    assert r['percentual']==80 and 'variante_nao_comprovada:wifi' in r['pendencias']


def test_ram_sem_formato_local_nao_confunde_dimm_e_sodimm():
    p=peca(__tablename__='memoria_ram',fabricante='Kingston',modelo='Fury Beast 8GB',capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1,latencia='CL16')
    d=produto(categoria='memoria_ram',marca='Kingston',modelo='Fury Beast',titulo='Kingston Fury Beast 8GB DDR4 3200MHz CL16',
        especificacoes={'capacidade_gb':'8 GB','ddr':'DDR4','frequencia_mhz':'3200 MHz','quantidade_pentes':1,'latencia':'16','formato_ram':'DIMM'})
    assert AssociacaoInteligenteService().avaliar(p,d)['percentual']==80
    assert AssociacaoInteligenteService().avaliar(p,replace(d,especificacoes={**d.especificacoes,'formato_ram':'SO-DIMM'}))['percentual']<=80


def test_identificador_existente_com_ficha_divergente_impede_criar_duplicata():
    p=peca(part_number='SKU-1',soquete='AM5')
    r=AssociacaoInteligenteService().selecionar([p],produto(identificadores={'mpn':['SKU-1']}))
    assert r['classificacao']=='ambigua' and 60<=r['percentual']<=80


def test_pares_reais_sem_mpn_tambem_sao_avaliados_sem_falsos_positivos():
    import json
    from pathlib import Path
    from services.mercadolivre_service.normalizar_produto_service import NormalizarProdutoService
    rows=json.loads((Path(__file__).parents[2]/'fixtures/matching_catalogos_reais.json').read_text())
    motor=AssociacaoInteligenteService();confirmados=negativos=falsos=0
    for i,row in enumerate(rows):
        p=SimpleNamespace(__tablename__=row['categoria'],id=i+1,fabricante=row['fabricante'],modelo=row['modelo'],part_number='SEED-TESTE',**row['especificacoes'])
        normal=NormalizarProdutoService().executar(row['produto'],row['categoria'])
        normal=replace(normal,identificadores={})
        confirmados+=motor.avaliar(p,normal)['classificacao']=='confirmada'
        for other in rows:
            if other['categoria']!=row['categoria'] or other['modelo']==row['modelo']:continue
            d=replace(NormalizarProdutoService().executar(other['produto'],row['categoria']),identificadores={})
            negativos+=1;falsos+=motor.avaliar(p,d)['classificacao']=='confirmada'
    assert confirmados>=7 and negativos==42 and falsos==0


def test_titulo_de_outro_modelo_nao_e_mascarado_por_modelo_estruturado():
    p=peca(__tablename__='fonte',fabricante='Corsair',modelo='CV650',potencia_w=650,formato='ATX')
    d=produto(categoria='fonte',marca='Corsair',modelo='CV650',titulo='Fonte Corsair CX650M 650W',especificacoes={'potencia_w':650,'formato':'ATX'})
    assert AssociacaoInteligenteService().avaliar(p,d)['percentual']==0


def test_sufixo_alfanumerico_completo_nao_e_truncado():
    p=peca(modelo='Ryzen 9 9950X3D',soquete='AM5',nucleo=16,thread=32,part_number='SKU')
    d=produto(modelo='Ryzen 9 9950X3D2',titulo='AMD Ryzen 9 9950X3D2',especificacoes={'soquete':'AM5','nucleo':16,'thread':32},identificadores={'mpn':['SKU']})
    assert AssociacaoInteligenteService().avaliar(p,d)['percentual']==0
