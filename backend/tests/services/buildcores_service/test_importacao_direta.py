import hashlib,json
from pathlib import Path
from copy import deepcopy
import pytest
from flask import Flask
from models import db,ControleColeta,Processador,Gabinete,Oferta
from services.buildcores_service.importar_catalogo_service import ImportarCatalogoBuildcoresService
from services.buildcores_service.normalizar_ficha_service import NormalizarFichaBuildcoresService

ID='11111111-1111-4111-8111-111111111111'

def cpu():
    return dict(opendb_id=ID,metadata=dict(name='AMD Ryzen 5 5500',manufacturer='AMD'),socket='AM4',cores=dict(total=6,threads=12),clocks=dict(performance=dict(base=3.6,boost=4.2)),specifications=dict(tdp=65,includesCooler=True),
      identifiers=dict(identifiers=[dict(type='mpn',value='100-100000457BOX')]))


def escrever(pasta,registros,grupo='CPU'):
    arquivos={}
    for r in registros:
        arq='open-db/'+grupo+'/'+r['opendb_id']+'.json';p=pasta/arq;p.parent.mkdir(parents=True,exist_ok=True);corpo=json.dumps(r).encode();p.write_bytes(corpo)
        arquivos[arq]={'sha256':hashlib.sha256(corpo).hexdigest()}
    (pasta/'manifesto.json').write_text(json.dumps({'repositorio':'https://github.com/buildcores/buildcores-open-db','commit':'a'*40,'arquivos':arquivos}))


@pytest.fixture
def banco():
    a=Flask('importacao-direta');a.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(a)
    with a.app_context():
        db.create_all();ControleColeta.inicializar()
        yield
        db.session.remove();db.engine.dispose()


def test_simular_importar_repetir_sem_preco_ou_aprovacao(banco,tmp_path):
    escrever(tmp_path,[cpu()]);s=ImportarCatalogoBuildcoresService()
    r=s.executar(tmp_path);assert r['propostas']==1 and r['novas_com_minimos']==1
    assert Processador.query.count()==0
    r=s.executar(tmp_path,simular=False);assert r['criadas']==1 and r['novas_com_minimos']==1
    p=Processador.query.one()
    assert p.preco is p.esgotado is None and p.part_number=='100-100000457BOX'
    assert p.referencia_interna.startswith('BUILDCORES:')
    assert p.status_validacao=='em_revisao' and not p.publicavel and Oferta.query.count()==0
    assert p.fontes_especificacoes['_buildcores_importacao']['id_externo']==ID
    r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert r['inalteradas']==1 and r['criadas']==r['campos_completados']==0


def test_dois_uuids_mesmo_mpn_nao_duplicam_e_reexecucao_nao_alterna_origem(banco,tmp_path):
    a=cpu();b=deepcopy(a);b['opendb_id']='22222222-2222-4222-8222-222222222222'
    escrever(tmp_path,[a,b]);r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False,tamanho_lote=1)
    assert r['criadas']==1 and r['existentes']==1 and Processador.query.count()==1
    r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False,tamanho_lote=1)
    assert r['inalteradas']==2 and r['criadas']==0


def test_busca_por_tokens_nao_perde_duplicata_quando_catalogo_cresce():
    from collections import defaultdict
    from services.buildcores_service.gravar_importacao_buildcores_service import GravarImportacaoBuildcoresService

    repo = GravarImportacaoBuildcoresService()
    repo.guarda = defaultdict(set)
    repo.codigos_nome = defaultdict(set)
    repo.tokens = defaultdict(set)
    repo.chaves = defaultdict(set)
    existente = ('processador', 1)
    outro = ('processador', 2)
    chave = 'ryzen|threadripper|1234|5678'
    repo.chaves[existente].add('ryzen|threadripper|1234|5679')
    repo.chaves[outro].add('produto|diferente|5678')
    repo.tokens[('processador', 'amd', '1234')].add(existente)
    repo.tokens[('processador', 'amd', '5678')].add(outro)
    ficha = dict(categoria='processador', fabricante='amd', nome='Novo nome', mpns=[], bruto={})

    assert repo._proximos(ficha, chave) == {existente}
    # O token compartilhado deixa de ser o mais raro. A revisão deve permanecer.
    repo.tokens[('processador', 'amd', '1234')].add(outro)
    assert repo._proximos(ficha, chave) == {existente}


def test_dado_conflitante_nao_sobrescreve_nem_cria_segunda_cpu(banco,tmp_path):
    p=Processador(fabricante='AMD',modelo='Ryzen 5 5500',nucleo=8,clockbase=3.6,clockmax=4.2,preco=500,part_number='100-100000457BOX')
    db.session.add(p);db.session.commit();escrever(tmp_path,[cpu()])
    r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert r['revisao']==1 and r['criadas']==0 and Processador.query.count()==1
    db.session.refresh(p);assert p.nucleo==8 and p.preco==500


def test_nome_descritivo_de_gabinete_nao_cria_duplicata(banco,tmp_path):
    db.session.add(Gabinete(fabricante='Fractal Design',modelo='Meshify C',formato='ATX',preco=600));db.session.commit()
    r=dict(opendb_id=ID,metadata=dict(name='Fractal Design Meshify C ATX Mid Tower Black',manufacturer='Fractal Design'),form_factor='ATX Mid Tower',color=['BLACK'],supported_motherboard_form_factors=['ATX'])
    escrever(tmp_path,[r],'PCCase');r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert r['revisao']==1 and Gabinete.query.count()==1


def test_hash_alterado_recusa_arquivo_antes_da_gravacao(banco,tmp_path):
    escrever(tmp_path,[cpu()]);(tmp_path/'open-db/CPU'/(ID+'.json')).write_text('{}')
    with pytest.raises(ValueError,match='manifesto'):ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert Processador.query.count()==0


def test_ficha_sem_base_clock_nao_recebe_boost_como_base(banco,tmp_path):
    r=cpu();del r['clocks']['performance']['base'];escrever(tmp_path,[r])
    r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert r['invalidas']==1 and r['criadas']==0


def test_ethernet_nao_e_classificado_como_wifi():
    with pytest.raises(ValueError,match='Wi-Fi'):
        NormalizarFichaBuildcoresService().executar('NetworkCard',dict(metadata=dict(name='Intel 10Gb Ethernet PCIe',manufacturer='Intel')), {})


def test_mudanca_na_fonte_exige_revisao_sem_trocar_peca(banco,tmp_path):
    r=cpu();escrever(tmp_path,[r]);ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    r['cores']['total']=8;escrever(tmp_path,[r]);r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert r['revisao']==1 and Processador.query.one().nucleo==6


def test_gabinete_com_descricao_de_painel_nao_duplica(banco,tmp_path):
    db.session.add(Gabinete(fabricante='HYTE',modelo='Y40 [Red / Black]',formato='ATX'));db.session.commit()
    r=dict(opendb_id=ID,metadata=dict(name='HYTE Y40 ATX Mid Tower Red / Black with Tempered Glass Side Panel',manufacturer='HYTE'),form_factor='ATX Mid Tower',color=['RED','BLACK'])
    escrever(tmp_path,[r],'PCCase')
    assert ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)['revisao']==1
    assert Gabinete.query.count()==1


def test_codigo_comercial_no_nome_impede_duplicacao_entre_marca_e_submarca(banco,tmp_path):
    from models import Monitor
    db.session.add(Monitor(fabricante='Dell',modelo='Alienware AW2725DM',tamanho_polegadas=27,resolucao='2560x1440',taxa_atualizacao_hz=180));db.session.commit()
    r=dict(opendb_id=ID,metadata=dict(name='Alienware 27 Gaming Monitor AW2725DM',manufacturer='Alienware',part_numbers=['AW2725DM']),screen_size=27,resolution=dict(horizontalRes=2560,verticalRes=1440),refresh_rate=180)
    escrever(tmp_path,[r],'Monitor')
    assert ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)['revisao']==1
    assert Monitor.query.count()==1


def test_chip_e_familia_comercial_detectam_descricao_diferente_de_gpu(banco,tmp_path):
    from models import PlacaVideo
    db.session.add(PlacaVideo(fabricante='Asus',modelo='ROG STRIX GAMING',memoria_gb=4,fontes_especificacoes={'_pc_part_dataset':{'nome_original':'Asus ROG STRIX GAMING','dados_originais':{'chipset':'Radeon RX 570'}}}));db.session.commit()
    r=dict(opendb_id=ID,metadata=dict(name='Asus ROG STRIX Radeon RX 570 4GB GDDR5 Black',manufacturer='Asus'),chipset='Radeon RX 570',memory=4,memory_type='GDDR5',tdp=150,color=['BLACK'])
    escrever(tmp_path,[r],'GPU')
    assert ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)['revisao']==1
    assert PlacaVideo.query.count()==1


def test_falha_de_lote_reverte_componentes_e_permite_repeticao(banco,tmp_path,mocker):
    from services.buildcores_service.gravar_importacao_buildcores_service import GravarImportacaoBuildcoresService
    from sqlalchemy.exc import SQLAlchemyError
    a=cpu();b=deepcopy(a);b['opendb_id']='22222222-2222-4222-8222-222222222222';b['metadata']['name']='AMD Ryzen 5 5600';b['identifiers']['identifiers']=[{'type':'mpn','value':'100-100000927BOX'}]
    escrever(tmp_path,[a,b]);repo=GravarImportacaoBuildcoresService();original=repo._processar;chamadas=[]
    def falhar(r,simular):
        chamadas.append(r)
        if len(chamadas)==2:raise SQLAlchemyError('falha simulada')
        return original(r,simular)
    mocker.patch.object(repo,'_processar',side_effect=falhar)
    r=ImportarCatalogoBuildcoresService(repo).executar(tmp_path,simular=False)
    assert r['interrompido'] and r['falhas']==2 and Processador.query.count()==0
    r=ImportarCatalogoBuildcoresService().executar(tmp_path,simular=False)
    assert not r['interrompido'] and r['criadas']==2
