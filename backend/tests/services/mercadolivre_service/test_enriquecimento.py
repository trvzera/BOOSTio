import csv
from unittest.mock import Mock
from copy import deepcopy

from services.mercadolivre_service.enriquecer_produto_service import EnriquecerProdutoService
from services.catalogo_service.consultar_benchmark_catalogo_service import ConsultarBenchmarkCatalogoService
from services.benchmark_service.importar_referencias_passmark_service import COLUNAS


def produto_hd():
    return dict(id='MLB99',name='Seagate Exos 8TB',status='active',domain_id='MLB-HARD_DRIVES_AND_SSDS',attributes=[
        dict(id=k,value_name=v) for k,v in [('BRAND','Seagate'),('MODEL','ST8000NM017B'),('MPN','ST8000NM017B'),
        ('CAPACITY','8 TB'),('DRIVE_STORAGE_TYPE','HDD'),('HARD_DRIVE_AND_SSD_POWER_CONSUMPTION','7 W')]])


def test_ficha_completa_so_com_valores_evidenciados():
    r=EnriquecerProdutoService().executar('hd',produto_hd(),{'price':'999.90','available_quantity':3})
    assert r['pronto'] and r['dados']['capacidade_gb']==8000 and r['dados']['consumo_energia']==7
    assert r['dados']['esgotado'] is False
    assert r['dados']['fabricante']=='seagate'
    assert r['fontes']['capacidade_gb']['atributo']=='CAPACITY'
    assert 'velocidade_rpm' not in r['dados']


def test_ausencia_preco_estoque_potencia_nao_vira_zero_ou_disponivel():
    p=produto_hd();p['attributes']=[a for a in p['attributes'] if a['id']!='HARD_DRIVE_AND_SSD_POWER_CONSUMPTION']
    r=EnriquecerProdutoService().executar('hd',p,{})
    assert not r['pronto']
    assert {'consumo_energia','preco','esgotado'}<=set(r['campos_pendentes'])
    assert not {'consumo_energia','preco','esgotado'}&set(r['dados'])


def test_ficha_com_codigo_mas_tipo_ou_titulo_divergente_requer_revisao():
    p=produto_hd();p['attributes'].append(dict(id='DRIVE_STORAGE_TYPE',value_name='SSD'))
    assert not EnriquecerProdutoService().executar('hd',p,{'price':100,'available_quantity':1})['pronto']
    p=produto_hd()
    r=EnriquecerProdutoService().executar('hd',p,{'price':100,'available_quantity':1,'title':'Seagate Exos 16TB'})
    assert not r['pronto'] and 'Título individual requer revisão' in r['avisos']


def test_cpu_nao_inventa_cooler_ou_video():
    p=dict(id='MLB1',name='AMD Ryzen 5 5500',status='active',domain_id='MLB-COMPUTER_PROCESSORS',attributes=[
        dict(id=k,value_name=v) for k,v in [('BRAND','AMD'),('MODEL','Ryzen 5 5500'),('MPN','100-100000457BOX'),
        ('TDP','65 W'),('CPU_CORES_NUMBER','6'),('CPU_THREADS_NUMBER','12'),('MIN_CLOCK_FREQUENCY','3.6 GHz'),('MAX_CLOCK_FREQUENCY','4.2 GHz'),('COMPATIBLE_SOCKETS','AM4')]])
    r=EnriquecerProdutoService().executar('processador',p,{'price':500,'available_quantity':1})
    assert not r['pronto'] and {'cooler','videointegrado'}<=set(r['campos_pendentes'])
    assert r['dados']['clockbase']==3.6


def test_benchmark_reutiliza_parser_sem_pontuacao_inferida(tmp_path):
    caminho=tmp_path/'cpus.csv'
    with caminho.open('w',newline='') as arq:
        w=csv.DictWriter(arq,fieldnames=COLUNAS['cpu']);w.writeheader()
        w.writerow({**{k:'' for k in COLUNAS['cpu']},'id':'1','name':'AMD Ryzen 5 5500','multi_thread_rating':'19000','single_thread_rating':'3000'})
    s=ConsultarBenchmarkCatalogoService(cpu=caminho)
    r=s.executar('processador','AMD','Ryzen 5 5500')
    assert r['status']=='encontrado' and r['dados']['benchmark_multi_core']=='19000'
    assert s.executar('processador','AMD','Ryzen 5 5500X')['status']=='nao_encontrado'
    assert ConsultarBenchmarkCatalogoService().executar('processador','AMD','Ryzen')['dados']=={}


def test_consulta_ficha_oficial_e_registra_pendencias_sem_publicar():
    from flask import Flask
    from models import db, ProdutoPendente, Oferta
    from datetime import datetime
    from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
    from services.mercadolivre_service.enriquecer_pendencias_service import EnriquecerPendenciasService
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all()
        p=ProdutoPendente(loja='mercado_livre',produto_id_loja='MLB10',titulo='Seagate',url='https://example.test',categoria_sugerida='hd',
            dados_originais={'catalogo':{'id':'MLB99'},'anuncio':{'price':100,'available_quantity':1}},coletado_em=datetime(2026,11,3))
        db.session.add(p);db.session.commit()
        cliente=BuscarOfertasMercadoLivreService();cliente._consultar=Mock(return_value=produto_hd())
        tokens=Mock();tokens.executar.return_value='teste'
        s=EnriquecerPendenciasService(cliente=cliente,tokens=tokens)
        assert s.executar()['completas']==1 and p.evidencias is None
        assert s.executar(simular=False)['completas']==1
        assert p.evidencias['enriquecimento']['pronto'] and Oferta.query.count()==0
        cliente._consultar.assert_called_with('/products/MLB99','teste')
        db.session.remove();db.engine.dispose()
