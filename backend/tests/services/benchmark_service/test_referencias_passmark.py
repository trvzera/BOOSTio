import csv
import json
from decimal import Decimal

import pytest
from flask import Flask
from models import db, Processador, PlacaVideo
from commands.benchmarks import registrar_comandos_benchmarks
from services.benchmark_service.importar_benchmarks_service import ImportarBenchmarksService
from services.benchmark_service.importar_referencias_passmark_service import (
    ImportarReferenciasPassmarkService, COLUNAS, FONTE,
)


@pytest.fixture
def banco(tmp_path):
    app=Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{tmp_path / "referencias.db"}'
    db.init_app(app)
    registrar_comandos_benchmarks(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.engine.dispose()


def inserir(nome='Intel Core i5-13500T',gpu=False):
    comum=dict(fabricante='ASUS' if gpu else 'Intel',modelo=nome,preco=999,consumo_energia=65)
    p=PlacaVideo(**comum,memoria_gb=8) if gpu else Processador(**comum,soquete='LGA1700',nucleo=6,thread=12,clockbase=3,clockmax=4)
    db.session.add(p);db.session.commit()
    return p


def arquivo(tmp_path,tipo,linhas):
    path=tmp_path/(tipo+'.csv')
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=COLUNAS[tipo]);w.writeheader()
        w.writerows([{k:r.get(k,'') for k in COLUNAS[tipo]} for r in linhas])
    return path


def fonte(tipo='cpu',**extras):
    return dict(id='123',name='Intel Core i5-13500T',multi_thread_rating='20000',single_thread_rating='3000',**extras) if tipo=='cpu' else dict(id='456',name='GeForce RTX 5060 Ti 8GB',g2d_mark='1000',g3d_mark='20000',**extras)


def associacoes(tmp_path,pecas,nomes=None):
    entradas=[]
    for p in pecas:
        gpu=isinstance(p,PlacaVideo)
        a=dict(tipo='gpu' if gpu else 'cpu',fabricante=p.fabricante,modelo=p.modelo,
               fonte_id=456 if gpu else 123,fonte_nome=(nomes or {}).get(p.id,'GeForce RTX 5060 Ti 8GB' if gpu else 'Intel Core i5-13500T'),
               escopo='referencia_chip_gpu' if gpu else 'modelo_cpu')
        if gpu:a['memoria_gb']=p.memoria_gb
        entradas.append(a)
    path=tmp_path/'associacoes.json';path.write_text(json.dumps(dict(versao=1,fonte=FONTE,associacoes=entradas)))
    return path


def test_formato_novo_automatico_cli_e_idempotencia(banco,tmp_path):
    p=inserir()
    antes=p.atualizado_em
    path=arquivo(tmp_path,'cpu',[fonte()])
    runner=banco.test_cli_runner()
    r=runner.invoke(args=['benchmarks-importar','--cpu',str(path),'--simular'])
    assert r.exit_code==0,r.output
    resumo=json.loads(r.output)
    assert resumo['propostas']==1 and p.benchmark_multi_core is None
    r=ImportarBenchmarksService().executar(cpu=path)
    assert r['por_tipo']['cpu']['atualizadas']==1 and r['atualizadas']==1
    assert p.benchmark_multi_core==Decimal('20000') and p.benchmark_single_thread==Decimal('3000')
    assert p.benchmark_fonte==FONTE+'/blob/main/data/raw/cpu/cpus.csv'
    assert p.benchmark_referencia_em is None and p.benchmark_versao is None
    assert p.preco==999 and p.atualizado_em==antes
    data=p.benchmark_atualizado_em
    assert ImportarBenchmarksService().executar(cpu=path)['inalteradas']==1
    assert p.benchmark_atualizado_em==data


def test_referencias_explicitas_compartilham_modelo_sem_duplicar_pecas(banco,tmp_path):
    a=inserir('Core i5-13500T 3GHz, OEM A')
    b=inserir('Core i5-13500T 3GHz, OEM B')
    path=arquivo(tmp_path,'cpu',[fonte()])
    s=ImportarReferenciasPassmarkService(associacoes(tmp_path,[a,b]))
    r=s.executar(cpu=path)
    assert r['atualizadas']==2 and Processador.query.count()==2
    assert a.benchmark_multi_core==b.benchmark_multi_core==20000
    assert {d['fonte_id'] for d in r['detalhes']}=={123}


@pytest.mark.parametrize('mudanca',['id','nome','vram'])
def test_alias_obsoleto_ou_variante_diferente_nao_sobrescreve(banco,tmp_path,mudanca):
    p=inserir('RTX 5060 Ti OC 8GB',gpu=True)
    p.benchmark_g3d=10000;db.session.commit()
    aliases=associacoes(tmp_path,[p])
    row=fonte('gpu')
    if mudanca=='id':row['id']='999'
    if mudanca=='nome':row['name']='GeForce RTX 5060 Ti 16GB Laptop GPU'
    if mudanca=='vram':p.memoria_gb=16;db.session.commit()
    path=arquivo(tmp_path,'gpu',[row])
    r=ImportarReferenciasPassmarkService(aliases).executar(gpu=path)
    assert r['atualizadas']==0 and p.benchmark_g3d==10000
    assert r['nao_encontradas']+r['ambiguas']+r['invalidas']==1


def test_dois_cadastros_com_mesmo_nome_comercial_sao_ambiguos(banco,tmp_path):
    a=inserir();inserir()
    path=arquivo(tmp_path,'cpu',[fonte()])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[a])).executar(cpu=path)
    assert r['ambiguas']==2 and r['atualizadas']==0


@pytest.mark.parametrize('valor',['-1','0','NaN','Infinity','abc'])
def test_entrada_invalida_preserva_benchmark(banco,tmp_path,valor):
    p=inserir();p.benchmark_multi_core=100;db.session.commit()
    row=fonte();row['multi_thread_rating']=valor
    path=arquivo(tmp_path,'cpu',[row])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[p])).executar(cpu=path)
    assert r['invalidas']==1 and p.benchmark_multi_core==100


def test_sem_score_nao_apaga_e_metrica_parcial_de_outro_teste_e_rejeitada(banco,tmp_path):
    p=inserir();p.benchmark_multi_core=100;p.benchmark_teste='Outro teste';db.session.commit()
    row=fonte();row['multi_thread_rating']='NA'
    path=arquivo(tmp_path,'cpu',[row])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[p])).executar(cpu=path)
    assert r['invalidas']==1 and p.benchmark_multi_core==100


def test_id_duplicado_conflitante_nao_escolhe_ultima_linha(banco,tmp_path):
    p=inserir();a=fonte();b={**a,'multi_thread_rating':'999'}
    path=arquivo(tmp_path,'cpu',[a,b])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[p])).executar(cpu=path)
    assert r['ambiguas']==1 and r['atualizadas']==0


def test_nome_repetido_em_ids_diferentes_bloqueia_alias(banco,tmp_path):
    p=inserir();path=arquivo(tmp_path,'cpu',[fonte(),{**fonte(),'id':'999'}])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[p])).executar(cpu=path)
    assert r['ambiguas']==1 and r['atualizadas']==0


def test_gpu_sem_alias_nao_extrae_chip_da_descricao(banco,tmp_path):
    p=inserir('Marca RTX 5060 Ti 16GB OC',gpu=True)
    path=arquivo(tmp_path,'gpu',[fonte('gpu')])
    r=ImportarBenchmarksService().executar(gpu=path)
    assert r['nao_encontradas']==1 and p.benchmark_g3d is None


def test_formato_invalido_segundo_arquivo_impede_todas_as_gravacoes(banco,tmp_path):
    p=inserir();cpu=arquivo(tmp_path,'cpu',[fonte()]);gpu=tmp_path/'gpu.csv';gpu.write_text('id,name\n1,errado\n')
    with pytest.raises(ValueError,match='Cabeçalho'):
        ImportarBenchmarksService().executar(cpu=cpu,gpu=gpu)
    assert p.benchmark_multi_core is None


def test_alias_nao_pode_ignorar_sufixo_ti_super_ou_mobile(banco,tmp_path):
    p=inserir('RTX 5060 Ti OC 8GB',gpu=True)
    aliases=associacoes(tmp_path,[p]);a=json.loads(aliases.read_text())
    a['associacoes'][0]['fonte_nome']='GeForce RTX 5060 8GB'
    aliases.write_text(json.dumps(a))
    row=fonte('gpu');row['name']='GeForce RTX 5060 8GB'
    path=arquivo(tmp_path,'gpu',[row])
    r=ImportarReferenciasPassmarkService(aliases).executar(gpu=path)
    assert r['invalidas']==1 and p.benchmark_g3d is None


def test_alias_nao_pode_ignorar_vram_explicita_na_fonte(banco,tmp_path):
    p=inserir('RTX 5060 Ti OC 8GB',gpu=True)
    aliases=associacoes(tmp_path,[p]);a=json.loads(aliases.read_text())
    a['associacoes'][0]['fonte_nome']='GeForce RTX 5060 Ti 16GB'
    aliases.write_text(json.dumps(a))
    row=fonte('gpu');row['name']='GeForce RTX 5060 Ti 16GB'
    path=arquivo(tmp_path,'gpu',[row])
    assert ImportarReferenciasPassmarkService(aliases).executar(gpu=path)['invalidas']==1


def test_duplicatas_equivalentes_sao_estaveis(banco,tmp_path):
    p=inserir();path=arquivo(tmp_path,'cpu',[fonte(),fonte()])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[p])).executar(cpu=path)
    assert r['duplicadas']==1 and r['atualizadas']==1


def test_fontes_misturadas_nao_gravam(banco,tmp_path):
    p=inserir();cpu=arquivo(tmp_path,'cpu',[fonte()]);gpu=tmp_path/'legado.csv'
    gpu.write_text('name,g2d,g3d\nGeForce RTX 4060,500,20000\n')
    with pytest.raises(ValueError,match='Não misture'):
        ImportarBenchmarksService().executar(cpu=cpu,gpu=gpu)
    assert p.benchmark_multi_core is None


def test_falha_no_lote_reverte_e_reexecucao_retoma(banco,tmp_path,monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    a=inserir('Core i5-13500T OEM A');b=inserir('Core i5-13500T OEM B')
    path=arquivo(tmp_path,'cpu',[fonte()])
    s=ImportarReferenciasPassmarkService(associacoes(tmp_path,[a,b]))
    original=db.session.commit
    chamadas=[]
    def commit():
        chamadas.append(1)
        if len(chamadas)==2:raise SQLAlchemyError('falha simulada')
        return original()
    with monkeypatch.context() as m:
        m.setattr(db.session,'commit',commit)
        with pytest.raises(RuntimeError,match='1 peças já confirmadas'):
            s.executar(cpu=path,lote=1)
    db.session.expire_all()
    assert a.benchmark_multi_core==20000 and b.benchmark_multi_core is None
    r=s.executar(cpu=path,lote=1)
    assert r['atualizadas']==1 and r['inalteradas']==1


@pytest.mark.parametrize('modelo',['Core i5-13500TF OEM', 'Core i5-13500T PRO', 'Core i5-13500T ES', 'Core i5-13500T Mobile'])
def test_alias_cpu_nao_remove_sufixos_ou_qualificadores(banco,tmp_path,modelo):
    p=inserir(modelo);path=arquivo(tmp_path,'cpu',[fonte()])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[p])).executar(cpu=path)
    assert r['invalidas']==1 and p.benchmark_multi_core is None


def test_pro_em_marca_comercial_gpu_nao_vira_variante_cpu(banco,tmp_path):
    p=inserir('Vx Pro RTX 5060 Ti OC 8GB',gpu=True)
    path=arquivo(tmp_path,'gpu',[fonte('gpu')])
    r=ImportarReferenciasPassmarkService(associacoes(tmp_path,[p])).executar(gpu=path)
    assert r['atualizadas']==1


def inserir_gpu(modelo, referencia, memoria=8):
    p = PlacaVideo(fabricante='ASUS', modelo=modelo, modelo_referencia=referencia, memoria_gb=memoria,
                   preco=999, consumo_energia=200)
    db.session.add(p); db.session.commit()
    return p


def gpu_fonte(ident, nome, g3d='20000'):
    return dict(id=str(ident), name=nome, g2d_mark='1000', g3d_mark=g3d)


def test_gpu_casa_pelo_chip_do_modelo_referencia_e_nao_pelo_nome_do_anuncio(banco, tmp_path):
    ok = inserir_gpu('DUAL OC V2 Black / Silver', 'GeForce GTX 1650', 4)
    ti = inserir_gpu('Gaming X Trio', 'GeForce RTX 4060 Ti 8 GB', 8)
    arq = arquivo(tmp_path, 'gpu', [gpu_fonte(1, 'GeForce GTX 1650', '7000'), gpu_fonte(2, 'GeForce RTX 4060 Ti', '22000'),
                                    gpu_fonte(3, 'GeForce RTX 4060', '19000')])
    ImportarBenchmarksService().executar(gpu=arq)
    assert ok.benchmark_g3d == Decimal('7000') and ok.benchmark_nome_fonte == 'GeForce GTX 1650'
    assert ti.benchmark_g3d == Decimal('22000')


def test_gpu_sem_chip_unico_ou_com_memoria_diferente_fica_sem_benchmark(banco, tmp_path):
    a = inserir_gpu('Anúncio A', 'GeForce RTX 3060 12GB', 8)
    b = inserir_gpu('Anúncio B', 'GeForce GTX 1060', 3)
    c = inserir_gpu('Anúncio C', None, 8)
    arq = arquivo(tmp_path, 'gpu', [gpu_fonte(1, 'GeForce RTX 3060 12GB'), gpu_fonte(2, 'GeForce GTX 1060', '9000'),
                                    gpu_fonte(3, 'GeForce GTX 1060 3GB', '8000'), gpu_fonte(4, 'GeForce GTX 1060 6GB', '9500')])
    resumo = ImportarBenchmarksService().executar(gpu=arq)
    assert a.benchmark_g3d is None and c.benchmark_g3d is None
    assert b.benchmark_g3d == Decimal('8000')
    assert resumo['por_tipo']['gpu']['atualizadas'] == 1


def test_cpu_casa_pelo_modelo_ignorando_o_clock_da_fonte(banco, tmp_path):
    p = inserir('Core i7-6700K')
    arq = arquivo(tmp_path, 'cpu', [fonte(**{}) | dict(id='9', name='Intel Core i7-6700K @ 4.00GHz'),
                                    fonte(**{}) | dict(id='10', name='Intel Core i7-6700')])
    ImportarBenchmarksService().executar(cpu=arq)
    assert p.benchmark_nome_fonte == 'Intel Core i7-6700K @ 4.00GHz'
