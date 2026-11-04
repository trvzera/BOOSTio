from copy import deepcopy
import pytest
from flask import Flask
from models import db, SSD, Oferta, FichaTecnicaCatalogo
from migrations.fichas_tecnicas import preparar_fichas_tecnicas
from services.catalogo_tecnico_service.importar_base_tecnica_service import ImportarBaseTecnicaService

@pytest.fixture
def banco():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all();preparar_fichas_tecnicas(simular=False)
        yield
        db.session.remove();db.engine.dispose()

@pytest.fixture
def documento():
    identidade=dict(fabricante='Kingston',modelo='A400 480GB',mpn='SA400S37/480G')
    spec=dict(capacidade_gb=480,tipo='SSD',interface='SATA',formato='2.5',consumo_energia=1.5)
    return dict(versao=1,provedor='fonte-teste',id_externo='ssd-1',categoria='ssd',identidade=identidade,
        especificacoes=spec,fontes={c:{'url':'https://example.org/ficha/ssd-1'} for c in [*identidade,*spec]})

def test_simular_importar_e_repetir_sem_oferta(banco,documento):
    s=ImportarBaseTecnicaService()
    r=s.processar(documento)
    assert r['acao']=='proposta',r
    assert SSD.query.count()==FichaTecnicaCatalogo.query.count()==0
    r=s.processar(documento,simular=False)
    assert r['acao']=='criada',r
    p=SSD.query.one()
    assert p.preco is None and p.esgotado is None
    assert Oferta.query.count()==0
    assert s.processar(documento,simular=False)['acao']=='inalterada'
    assert SSD.query.count()==1

def test_incompleta_fica_na_fila(banco,documento):
    del documento['especificacoes']['capacidade_gb']
    r=ImportarBaseTecnicaService().processar(documento,simular=False)
    assert r['estado']=='pendente_dados',r
    assert SSD.query.count()==0

def test_fonte_diferente_nao_duplica(banco,documento):
    s=ImportarBaseTecnicaService();s.processar(documento,simular=False)
    documento['provedor']='outra-fonte'
    r=s.processar(documento,simular=False)
    assert r['acao']=='associada',r
    assert SSD.query.count()==1

def test_identificador_com_especificacao_divergente_nao_duplica(banco,documento):
    s=ImportarBaseTecnicaService();s.processar(documento,simular=False)
    documento['provedor']='outra-fonte';documento['especificacoes']['capacidade_gb']=960
    r=s.processar(documento,simular=False)
    assert r['acao']=='revisao',r
    assert SSD.query.one().capacidade_gb==480

def test_campos_comerciais_proibidos(banco,documento):
    documento['especificacoes']['preco']=123
    with pytest.raises(ValueError):ImportarBaseTecnicaService().processar(documento,simular=False)
    assert FichaTecnicaCatalogo.query.count()==0

@pytest.mark.parametrize('valor',[float('nan'),float('inf'),object()])
def test_documento_json_finito(banco,documento,valor):
    documento['especificacoes']['consumo_energia']=valor
    with pytest.raises(ValueError):ImportarBaseTecnicaService().processar(documento)

def test_gtin_sem_mpn_deduplica_entre_fontes(banco,documento):
    documento['identidade'].pop('mpn');documento['identidade']['gtin']='740617261219'
    documento['fontes']['gtin']={'url':'https://example.org/gtin'}
    s=ImportarBaseTecnicaService()
    assert s.processar(documento,simular=False)['acao']=='criada'
    documento['provedor']='outra-fonte'
    assert s.processar(documento,simular=False)['acao']=='associada'
    assert SSD.query.count()==1

def test_rejeicao_exige_reabertura_e_aprovacao_nao_pula_validacao(banco,documento):
    from services.catalogo_tecnico_service.revisar_ficha_service import RevisarFichaService
    documento['especificacoes'].pop('capacidade_gb')
    s=ImportarBaseTecnicaService();r=s.processar(documento,simular=False)
    admin=RevisarFichaService()
    args=dict(responsavel='teste',motivo='Conferência',simular=False)
    assert admin.executar(r['id'],'aprovar',**args)['estado']=='pendente_dados'
    admin.executar(r['id'],'rejeitar',**args)
    assert s.processar(documento,simular=False)['acao']=='rejeitada'
    with pytest.raises(ValueError):admin.executar(r['id'],'aprovar',**args)
    admin.executar(r['id'],'reabrir',**args)
    assert SSD.query.count()==0

def test_sem_cotacao_ou_ficha_incompleta_nao_entra_na_montagem(banco,documento):
    documento['especificacoes'].pop('consumo_energia')
    r=ImportarBaseTecnicaService().processar(documento,simular=False)
    assert r['acao']=='criada'
    p=SSD.query.one()
    assert p.ficha_montagem_validada is False
    p.preco=100;p.esgotado=False;db.session.commit()
    assert SSD.consulta_para_montagem().count()==0
