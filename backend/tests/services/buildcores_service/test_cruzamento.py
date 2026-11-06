import hashlib
import json
from copy import deepcopy
from pathlib import Path
import pytest
from flask import Flask
from sqlalchemy import null
from models import db,ControleColeta,Processador,Oferta
from repositories.enriquecimento_buildcores_repository import RepositorioEnriquecimentoBuildcores
from services.buildcores_service.cruzar_catalogo_service import CruzarCatalogoBuildcoresService
from services.buildcores_service.normalizar_ficha_service import NormalizarFichaBuildcoresService
from services.buildcores_service.comparar_fichas_service import CompararFichasBuildcoresService,chave_modelo

ID='11111111-1111-4111-8111-111111111111'

def ficha():
    return dict(opendb_id=ID,metadata=dict(name='AMD Ryzen 5 5500',manufacturer='AMD',part_numbers=['AMD Ryzen 5 5500']),
      socket='AM4',cores=dict(total=6,threads=12),clocks=dict(performance=dict(base=3.6,boost=4.2)),
      specifications=dict(tdp=65,includesCooler=True,integratedGraphics=dict(model='None')),
      identifiers=dict(identifiers=[dict(type='mpn',value='100-100000457BOX'),dict(type='mpn',value='AMD Ryzen 5 5500')]))


def snapshot(pasta,registros=None):
    registros=registros or [ficha()];arquivos={}
    for d in registros:
        nome='open-db/CPU/'+d['opendb_id']+'.json';arquivo=pasta/nome;arquivo.parent.mkdir(parents=True,exist_ok=True)
        corpo=json.dumps(d).encode();arquivo.write_bytes(corpo);arquivos[nome]={'sha256':hashlib.sha256(corpo).hexdigest()}
    (pasta/'manifesto.json').write_text(json.dumps({'repositorio':'https://github.com/buildcores/buildcores-open-db','commit':'a'*40,'arquivos':arquivos}))

@pytest.fixture
def banco():
    app=Flask('cruzamento');app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();ControleColeta.inicializar()
        p=Processador(fabricante='AMD',modelo='Ryzen 5 5500',nucleo=6,clockbase=3.6,clockmax=4.2,consumo_energia=65,
          preco=None,esgotado=None,videointegrado=null(),cooler=null(),status_validacao='em_revisao',ficha_montagem_validada=False,
          fontes_especificacoes={'_pc_part_dataset':{'nome_original':'AMD Ryzen 5 5500','dados_originais':{'core_count':6}}})
        db.session.add(p);db.session.commit()
        yield p
        db.session.remove();db.engine.dispose()


def test_simulacao_aplicacao_repeticao_sem_publicar_ou_criar(banco,tmp_path):
    snapshot(tmp_path);s=CruzarCatalogoBuildcoresService()
    r=s.executar(tmp_path);assert r['confirmadas']==1 and r['com_alteracoes']==1,r
    db.session.refresh(banco);assert banco.thread is banco.soquete is None
    r=s.executar(tmp_path,simular=False)
    assert r['atualizadas']==1 and banco.thread==12 and banco.soquete=='AM4'
    assert banco.videointegrado is False
    assert banco.cooler is banco.part_number is None  # Box/Tray não identificado no docyx.
    assert banco.preco is None and banco.status_validacao=='em_revisao' and banco.ficha_montagem_validada is True
    assert Processador.query.count()==1 and Oferta.query.count()==0
    fontes=deepcopy(banco.fontes_especificacoes)
    r=s.executar(tmp_path,simular=False)
    assert r['inalteradas']==1 and r['atualizadas']==r['campos_preenchidos']==0
    assert banco.fontes_especificacoes==fontes


def test_conflito_tecnico_nao_atualiza(banco,tmp_path):
    d=ficha();d['cores']['total']=8;snapshot(tmp_path,[d])
    r=CruzarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert r['conflitos']==1 and r['atualizadas']==0 and banco.thread is None


def test_fontes_concorrentes_e_duplicados_locais_exigem_revisao(banco,tmp_path):
    d=ficha();e=deepcopy(d);e['opendb_id']='22222222-2222-4222-8222-222222222222';snapshot(tmp_path,[d,e])
    assert CruzarCatalogoBuildcoresService().executar(tmp_path)['ambiguas']==1
    (tmp_path/'open-db/CPU'/(e['opendb_id']+'.json')).unlink();snapshot(tmp_path)
    db.session.add(Processador(fabricante='AMD',modelo='Ryzen 5 5500',nucleo=6,clockbase=3.6,clockmax=4.2,consumo_energia=65,
       videointegrado=null(),cooler=null(),fontes_especificacoes=banco.fontes_especificacoes));db.session.commit()
    assert CruzarCatalogoBuildcoresService().executar(tmp_path)['ambiguas']==2


def test_hash_invalido_recusado_antes_de_gravar(banco,tmp_path):
    snapshot(tmp_path);(tmp_path/'open-db/CPU'/(ID+'.json')).write_text('{}')
    with pytest.raises(ValueError,match='manifesto'):CruzarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert banco.thread is None


def test_nome_nunca_apaga_sufixos_ou_funde_tokens():
    assert chave_modelo('processador','AMD Ryzen 5 5600X','amd')!=chave_modelo('processador','AMD Ryzen 5 5600','amd')
    assert chave_modelo('placa_video','MSI RTX 4060 Ti','msi')!=chave_modelo('placa_video','MSI RTX 4060','msi')
    assert chave_modelo('mouse','AB C','')!=chave_modelo('mouse','A BC','')


def test_identificadores_e_zeros_nao_viram_fatos():
    d=ficha();d['specifications']['tdp']=0;d['socket']=None
    r=NormalizarFichaBuildcoresService().executar('CPU',d,{})
    assert r['mpns']==['100-100000457BOX']
    assert 'soquete' not in r['dados'] and 'consumo_energia' not in r['dados']


def test_nao_perde_atualizacao_concorrente(banco,tmp_path):
    snapshot(tmp_path);repo=RepositorioEnriquecimentoBuildcores();p=repo.listar()[0]
    banco.nucleo=8;db.session.commit()
    r=repo.aplicar_lote([dict(**{k:p[k] for k in ('id','categoria','assinatura')},alteracoes={'thread':12},fontes={'thread':{'url':'https://example.org'}})],simular=False)
    assert r[0]['acao']=='conflito_concorrencia' and banco.thread is None


def test_ram_preserva_kit_cor_e_frequencia():
    raw=dict(name='Corsair Vengeance RGB 32 GB',color='Black')
    local=dict(categoria='memoria_ram',dados=dict(fabricante='Corsair',modelo='Vengeance RGB 32GB',capacidade_gb=32,quantidade_pentes=2,ddr='DDR5',frequencia_mhz=6000,latencia='36'),
      fontes={'_pc_part_dataset':dict(nome_original=raw['name'],dados_originais=raw)})
    remoto=dict(metadata=dict(name='Corsair Vengeance RGB 32GB (2x16GB) DDR5-6000 CL36 Black',manufacturer='Corsair'),
      color=['BLACK'],capacity=32,modules=dict(quantity=2,capacity_gb=16),ram_type='DDR5',speed=6000,cas_latency=36,form_factor='288-pin DIMM')
    motor=CompararFichasBuildcoresService();normalizador=NormalizarFichaBuildcoresService()
    r=normalizador.executar('RAM',remoto,{})
    assert motor.avaliar(local,r)['confirmada']
    r['dados']['quantidade_pentes']=1
    assert 'campo_divergente:quantidade_pentes' in motor.avaliar(local,r)['conflitos']
    r['dados']['quantidade_pentes']=2;r['cores']=('white',)
    assert not motor.avaliar(local,r)['confirmada']
    r['cores']=('black',);r['dados']['frequencia_mhz']=6400
    assert not motor.avaliar(local,r)['confirmada']


def test_falha_no_lote_reverte_campos_e_proveniencia(banco,tmp_path):
    snapshot(tmp_path);repo=RepositorioEnriquecimentoBuildcores();p=repo.listar()[0]
    inicial=deepcopy(banco.fontes_especificacoes)
    primeira=dict(id=p['id'],categoria=p['categoria'],assinatura=p['assinatura'],alteracoes={'thread':12},fontes={'thread':{'url':'https://example.org'}})
    segunda={**primeira,'assinatura':p['assinatura']}
    # Falha deliberada antes de confirmar o lote, após a primeira alteração.
    from unittest.mock import patch
    with patch.object(db.session,'flush',side_effect=ValueError('Falha de persistência')):
        with pytest.raises(ValueError):repo.aplicar_lote([primeira,segunda],simular=False)
    db.session.refresh(banco)
    assert banco.thread is None and banco.fontes_especificacoes==inicial


def test_download_snapshot_fixo_com_manifesto(tmp_path,mocker):
    import io,zipfile
    from services.buildcores_service.baixar_snapshot_service import BaixarSnapshotBuildcoresService
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        z.writestr('snapshot/open-db/CPU/'+ID+'.json',json.dumps(ficha()))
        z.writestr('snapshot/LICENSE.txt','Licença de teste')
    resposta=mocker.MagicMock();resposta.status_code=200;resposta.iter_content.return_value=[buf.getvalue()]
    resposta.__enter__.return_value=resposta
    get=mocker.patch('services.buildcores_service.baixar_snapshot_service.requests.get',return_value=resposta)
    r=BaixarSnapshotBuildcoresService().executar(tmp_path,commit='a'*40)
    assert r['arquivos']==2
    manifesto=json.loads((tmp_path/'manifesto.json').read_text())
    corpo=(tmp_path/'open-db/CPU'/(ID+'.json')).read_bytes()
    assert manifesto['arquivos']['open-db/CPU/'+ID+'.json']['sha256']==hashlib.sha256(corpo).hexdigest()
    assert 'codeload.github.com' in get.call_args.args[0]


def test_cli_simula_por_padrao_e_exporta_relatorio(banco,tmp_path):
    from flask import current_app
    from commands.buildcores import registrar_comandos_buildcores
    snapshot(tmp_path);registrar_comandos_buildcores(current_app)
    destino=tmp_path/'resultado.json'
    r=current_app.test_cli_runner().invoke(args=['buildcores-cruzar','--pasta',str(tmp_path),'--resumo',str(destino)])
    assert r.exit_code==0,r.output
    assert json.loads(destino.read_text())['simulacao'] is True
    db.session.refresh(banco);assert banco.thread is None
