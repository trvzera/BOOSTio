import hashlib
import json
from pathlib import Path
import pytest
from flask import Flask
from sqlalchemy import text, inspect
from models import db, ControleColeta, Processador, MemoriaRAM, Oferta, Mouse
from services.dataset_pecas_service.gravar_dataset_pecas_service import GravarDatasetPecasService
from services.dataset_pecas_service.normalizar_peca_service import NormalizarPecaDatasetService
from services.dataset_pecas_service.importar_dataset_service import ImportarDatasetService
from services.catalogo_service.validar_ficha_tecnica_service import ValidarFichaTecnicaService
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from migrations.catalogo_parcial import preparar_catalogo_parcial

@pytest.fixture
def banco():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        yield
        db.session.remove();db.engine.dispose()


def cpu(**extras):return {'name':'AMD Ryzen 5 5500','price':200,'core_count':6,'core_clock':3.6,'boost_clock':4.2,'tdp':65,**extras}

def normalizar(linha,arquivo='cpu'):
    return NormalizarPecaDatasetService().executar(arquivo,linha,{'url':'https://example.org/cpu.json','sha256':'a'*64})


def test_sem_inferir_socket_threads_mpn_preco_ou_estoque(banco):
    r=normalizar(cpu());repo=GravarDatasetPecasService()
    assert repo.executar_lote([r],simular=True)[0]['acao']=='proposta'
    assert Processador.query.count()==0
    assert repo.executar_lote([r],simular=False)[0]['acao']=='criada'
    p=Processador.query.one()
    assert p.modelo=='Ryzen 5 5500' and p.fabricante=='AMD'
    assert p.soquete is p.thread is p.part_number is p.preco is p.esgotado is p.cooler is None
    assert p.status_validacao=='em_revisao' and p.ficha_montagem_validada is False
    assert Processador.consulta_para_montagem().count()==Oferta.query.count()==0
    assert GravarDatasetPecasService().executar_lote([normalizar(cpu(price=900))],simular=False)[0]['acao']=='inalterada'
    assert Processador.query.count()==1


def test_variantes_ram_cores_e_kits_preservados(banco):
    rows=[{'name':'Corsair Vengeance 32 GB','speed':[5,6000],'modules':[2,16],'cas_latency':36,'color':cor} for cor in ('Black','White')]
    rows.append({**rows[0],'modules':[1,32]})
    rs=[normalizar(r,'memory') for r in rows]
    resultados=GravarDatasetPecasService().executar_lote(rs,simular=False)
    assert all(r['acao']=='criada' for r in resultados)
    assert MemoriaRAM.query.count()==3
    assert {p.quantidade_pentes for p in MemoriaRAM.query}=={1,2}
    assert all(p.capacidade_gb==32 for p in MemoriaRAM.query)


def test_nome_legado_ambiguo_nao_duplica_nem_sobrescreve(banco):
    db.session.add(Processador(fabricante='AMD',modelo='Ryzen 5 5500',nucleo=8,clockbase=3.6,preco=999,esgotado=False));db.session.commit()
    r=GravarDatasetPecasService().executar_lote([normalizar(cpu())],simular=False)[0]
    assert r['acao']=='revisao' and Processador.query.count()==1
    p=Processador.query.one();assert p.nucleo==8 and p.preco==999


def test_identidade_nao_inventa_nvme_nem_quantidade_fan():
    s=NormalizarPecaDatasetService()
    r=s.executar('internal-hard-drive',{'name':'Samsung SSD','type':'SSD','capacity':500,'interface':'PCIe 3.0 x4'}, {})
    assert 'tipo' not in r['dados']
    r=s.executar('case-fan',{'name':'Noctua NF-A12','size':120},{})
    assert 'quantidade' not in r['dados']
    assert s.executar('case-fan',{'name':'Noctua NF-A12 3-Pack','size':120},{})['dados']['quantidade']==3


def test_nullable_nao_enfraquece_validador_tecnico(banco):
    prod=ProdutoNormalizado(loja='fonte',id_externo='1',categoria='processador',titulo='AMD Ryzen',marca='AMD',modelo='Ryzen',ativo=True,categoria_confirmada=True)
    v=ValidarFichaTecnicaService().executar('processador',{'fabricante':'AMD','modelo':'Ryzen'},prod,finalidade='catalogo')
    assert {'soquete','thread','clockbase','clockmax','nucleo'}<=set(v['campos_pendentes'])
    assert not v['pronto']


def arquivos(tmp_path,linhas):
    corpo=json.dumps(linhas).encode();(tmp_path/'cpu.json').write_bytes(corpo)
    manifesto={'repositorio':'https://github.com/docyx/pc-part-dataset','commit':'a'*40,'arquivos':{'cpu.json':{
        'url':'https://raw.githubusercontent.com/docyx/pc-part-dataset/'+('a'*40)+'/data/json/cpu.json','sha256':hashlib.sha256(corpo).hexdigest()}}}
    (tmp_path/'manifesto.json').write_text(json.dumps(manifesto))


def test_hash_preflight_simulacao_lotes_e_idempotencia(banco,tmp_path):
    arquivos(tmp_path,[cpu(),cpu(price=500),cpu(name='AMD Ryzen 5 5600')])
    r=ImportarDatasetService().executar(tmp_path,tamanho_lote=1)
    assert r['propostas']==2 and r['duplicadas']==1 and Processador.query.count()==0
    r=ImportarDatasetService().executar(tmp_path,simular=False,tamanho_lote=1)
    assert r['criadas']==2 and not r['interrompido']
    r=ImportarDatasetService().executar(tmp_path,simular=False)
    assert r['inalteradas']==2 and Processador.query.count()==2
    (tmp_path/'cpu.json').write_text('[]')
    with pytest.raises(ValueError,match='manifesto'):ImportarDatasetService().executar(tmp_path,simular=False)
    assert Processador.query.count()==2


def test_migracao_preserva_registros_indices_e_reexecucao(banco):
    # Reconstrói uma tabela com as antigas restrições para testar o upgrade real.
    db.session.remove()
    with db.engine.begin() as conn:
        conn.exec_driver_sql('DROP TABLE processador')
        ddl=str(__import__('sqlalchemy').schema.CreateTable(Processador.__table__).compile(db.engine))
        for campo in ('soquete','nucleo','thread','clockbase','clockmax'):
            import re
            ddl=re.sub(r'(\n\s*'+campo+r'\s+[^,\n]+)' ,r'\1 NOT NULL',ddl)
        conn.exec_driver_sql(ddl)
        conn.exec_driver_sql("CREATE INDEX ix_cpu_teste ON processador(modelo)")
        conn.exec_driver_sql("INSERT INTO processador (id,fabricante,modelo,soquete,nucleo,thread,clockbase,clockmax,criado_em) VALUES (1,'AMD','Legado','AM4',6,12,3.6,4.2,CURRENT_TIMESTAMP)")
    assert preparar_catalogo_parcial()['alteracoes']
    preparar_catalogo_parcial(simular=False)
    assert Processador.query.one().modelo=='Legado'
    assert all(c['nullable'] for c in inspect(db.engine).get_columns('processador') if c['name'] in ('thread','soquete'))
    assert 'ix_cpu_teste' in {i['name'] for i in inspect(db.engine).get_indexes('processador')}
    assert preparar_catalogo_parcial(simular=False)['alteracoes']==[]
