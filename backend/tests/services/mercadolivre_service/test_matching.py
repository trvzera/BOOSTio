import json
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from services.mercadolivre_service.comparar_produtos_service import CompararProdutosService
from services.catalogo_service.normalizar_produto import nome, gtin


def peca(categoria='processador', **extras):
    return SimpleNamespace(**{**dict(__tablename__=categoria, id=1, fabricante='AMD', modelo='Ryzen 5 5500',
                          part_number='100-100000457BOX', soquete='AM4', nucleo=6, thread=12), **extras})


def produto(**extras):
    return {**dict(id='MLB1', name='AMD Ryzen 5 5500 BOX', status='active', domain_id='MLB-COMPUTER_PROCESSORS',
                  attributes=[dict(id='BRAND',value_name='AMD'),dict(id='MPN',value_name='100-100000457BOX')]), **extras}


def avaliar(p=None, r=None):
    return CompararProdutosService().avaliar(p or peca(), r or produto())


def test_normaliza_equivalencias_sem_remover_sufixos():
    assert nome('AMD®  Ryzen™ 5  5500') == nome('amd ryzen 5 5500')
    assert nome('RTX4060 Ti SUPER') == nome('RTX 4060 Ti SUPER')
    assert nome('Ryzen 7 5700 X') == nome('Ryzen 7 5700X')
    assert nome('RX 7900 XT') != nome('RX 7900 XTX')
    assert nome('Ryzen 5600G') != nome('Ryzen 5600')


@pytest.mark.parametrize('titulo', ['Ryzen 5 5500X','Kit AMD Ryzen 5 5500 + A520',
    'AMD Ryzen 5 5500 para notebook','AMD Ryzen 5 5500 OEM','Somente caixa Ryzen 5 5500'])
def test_identificador_igual_nao_sobrepoe_conflito(titulo):
    assert avaliar(r=produto(name=titulo))['classificacao'] == 'rejeitada'


@pytest.mark.parametrize('local,remoto', [('RTX 4070','RTX 4070 Ti'),('RTX 4070 Ti','RTX 4070 Ti SUPER'),
    ('RX 7900 XT','RX 7900 XTX'),('GTX 1660','GTX 1660 SUPER')])
def test_variantes_gpu(local, remoto):
    p = peca('placa_video', modelo=local, fabricante='MSI', part_number='SKU', memoria_gb=8)
    r = produto(name=remoto, domain_id='MLB-GRAPHICS_CARDS', attributes=[dict(id='BRAND',value_name='MSI'),dict(id='MPN',value_name='SKU')])
    assert avaliar(p,r)['classificacao'] == 'rejeitada'


def test_gtin_valida_checksum_e_nao_mascara_mpn_divergente():
    assert gtin('7894900011517') == '07894900011517'
    assert gtin('7894900011518') is None
    r = produto(attributes=[dict(id='BRAND',value_name='AMD'),dict(id='GTIN',value_name='7894900011517')])
    s = CompararProdutosService()
    assert s.avaliar(peca(part_number=None), r, identidade={'gtin':'7894900011517'})['classificacao'] == 'confirmada'
    r['attributes'].append(dict(id='MPN',value_name='OUTRO'))
    assert s.avaliar(peca(), r, identidade={'gtin':'7894900011517'})['classificacao'] == 'rejeitada'


def test_nome_sozinho_e_multiplos_identificadores_nao_confirmam():
    r=produto(attributes=[dict(id='BRAND',value_name='AMD')])
    assert avaliar(r=r)['classificacao'] == 'ambigua'
    r['attributes'] += [dict(id='MPN',value_name='100-100000457BOX'),dict(id='MPN',value_name='OUTRO')]
    assert avaliar(r=r)['classificacao'] == 'ambigua'
    assert CompararProdutosService().selecionar([peca(),peca(id=2)],produto())['classificacao']=='ambigua'
    assert CompararProdutosService().selecionar([peca()],produto(),completo=False)['classificacao']=='ambigua'


@pytest.mark.parametrize('titulo,atributo,valor', [('RAM 16GB DDR4','RAM_MEMORY_MODULE_TOTAL_CAPACITY','16 GB'),
    ('RAM 8GB DDR5','RAM_MEMORY_MODULE_TYPE','DDR5'),('Kit RAM 2x4GB DDR4','RAM_MEMORY_MODULES','2'),
    ('RAM 8GB DDR4 notebook','RAM_MEMORY_FORMAT','SO-DIMM')])
def test_ram_capacidade_ddr_modulos_formato(titulo, atributo, valor):
    p=peca('memoria_ram',modelo='Fury Beast 8GB',fabricante='Kingston',part_number='KF432C16BB/8', capacidade_gb=8,ddr='DDR4',quantidade_pentes=1)
    r=produto(name=titulo,domain_id='MLB-RAM_MEMORY_MODULES',attributes=[dict(id='BRAND',value_name='Kingston'),dict(id='MPN',value_name='KF432C16BB/8'),dict(id=atributo,value_name=valor)])
    assert avaliar(p,r)['classificacao']!='confirmada'


def test_specs_contradizem_mpn_e_categoria_nao_e_sugestao():
    r=produto(attributes=produto()['attributes']+[dict(id='CPU_CORES_NUMBER',value_name='8')])
    assert avaliar(r=r)['classificacao']=='rejeitada'
    assert avaliar(r=produto(domain_id='MLB-COMPUTER_MOTHERBOARDS'))['classificacao']=='rejeitada'
    assert avaliar(r=produto(domain_id=None))['classificacao']=='ambigua'


def test_snapshots_reais_e_pares_negativos_sem_inventar_respostas():
    dados=json.loads((Path(__file__).parents[2]/'fixtures/matching_catalogos_reais.json').read_text())
    s=CompararProdutosService();confirmados=0;negativos=0;falsos=0
    for i,a in enumerate(dados):
        p=SimpleNamespace(__tablename__=a['categoria'],id=i+1,fabricante=a['fabricante'],modelo=a['modelo'],part_number=a['mpn'],**a['especificacoes'])
        resultado=s.avaliar(p,a['produto'])
        assert resultado['classificacao']!='rejeitada', resultado
        confirmados += resultado['classificacao']=='confirmada'
        for b in dados:
            if b['categoria']!=a['categoria'] or b['mpn']==a['mpn']:continue
            negativos+=1
            falsos+=s.avaliar(p,b['produto'])['classificacao']=='confirmada'
    assert confirmados>0 and negativos>0 and falsos==0


def test_classifica_fila_sem_publicar_e_detecta_codigo_local_duplicado(tmp_path):
    from flask import Flask
    from models import db, Processador, ProdutoPendente, Oferta
    from datetime import datetime
    from services.mercadolivre_service.classificar_pendencias_service import ClassificarPendenciasService
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all()
        dados=dict(fabricante='AMD',modelo='Ryzen 5 5500',part_number='100-100000457BOX',soquete='AM4',nucleo=6,thread=12,clockbase=3,clockmax=4,consumo_energia=65,preco=100)
        db.session.add(Processador(**dados))
        p=ProdutoPendente(loja='mercado_livre',produto_id_loja='MLB10',titulo='AMD',url='https://example.test',categoria_sugerida='processador',dados_originais={'catalogo':produto(),'anuncio':{}},coletado_em=datetime(2026,11,3))
        db.session.add(p);db.session.commit()
        s=ClassificarPendenciasService()
        assert s.executar()['confirmadas']==1 and p.evidencias is None
        assert s.executar(simular=False)['confirmadas']==1
        assert p.evidencias['matching']['classificacao']=='confirmada' and Oferta.query.count()==0
        db.session.add(Processador(**dados));db.session.commit()
        assert s.executar()['ambiguas']==1
        db.session.remove();db.engine.dispose()


def test_migracao_gtin_preserva_identidade_antiga():
    from flask import Flask
    from models import db, IdentidadeFabricante
    from sqlalchemy import text
    from migrations.identidades_fabricante import preparar_identidades_fabricante
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all()
        db.session.add(IdentidadeFabricante(tabela_peca='processador',peca_id=1,assinatura_peca='a'*64,mpn='SKU',fonte='https://example.test',especificacoes={}))
        db.session.commit();db.session.remove()
        with db.engine.begin() as c:c.execute(text('ALTER TABLE identidade_fabricante DROP COLUMN gtin'))
        assert preparar_identidades_fabricante()['alteracoes']==['gtin']
        assert preparar_identidades_fabricante()=={'criadas':[]}
        assert IdentidadeFabricante.query.one().mpn=='SKU' and IdentidadeFabricante.query.one().gtin is None
        db.session.remove();db.engine.dispose()
