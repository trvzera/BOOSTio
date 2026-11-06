import json
from copy import deepcopy
from pathlib import Path

import pytest
from flask import Flask
from models import db, MemoriaRAM, VinculoMercadoLivre, Oferta, HistoricoOferta
from migrations.vinculos_revisados import preparar_vinculos_revisados
from services.mercadolivre_service.importar_vinculos_revisados_service import ImportarVinculosRevisadosService
from services.mercadolivre_service.associar_catalogo_service import AssociarCatalogoService
from utils.identidade_peca import assinatura_peca


@pytest.fixture
def contexto(tmp_path):
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        db.create_all()
        p=MemoriaRAM(fabricante='Kingston',modelo='Teste DDR4',part_number='SEED-TESTE-1',consumo_energia=5,
            preco=100,capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1,
            kabum_external='https://www.kabum.com.br/produto/123/teste')
        db.session.add(p);db.session.commit()
        item=dict(categoria='memoria_ram',referencia=p.referencia_interna or p.part_number,fabricante=p.fabricante,modelo=p.modelo,
            url_peca=p.kabum_external,revisado_em='2026-11-03',justificativa='Revisão de teste',
            especificacoes=dict(capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1),
            evidencias=['https://www.kabum.com.br/produto/123/teste'],
            catalogo=dict(id='MLB123',name='Modelo exato teste',domain_id='MLB-RAM_MEMORY_MODULES',attributes=[]))
        arquivo=tmp_path/'revisados.json'
        arquivo.write_text(json.dumps([item]))
        yield app,p,item,arquivo
        db.session.remove();db.engine.dispose()


def test_simulacao_aplicacao_idempotencia_e_ficha_alterada(contexto):
    app,p,_,arquivo=contexto
    service=ImportarVinculosRevisadosService()
    assert service.executar(arquivo)['propostos']==1
    assert VinculoMercadoLivre.query.count()==0
    assert service.executar(arquivo,simular=False)['cadastrados']==1
    assert service.executar(arquivo,simular=False)['inalterados']==1
    v=VinculoMercadoLivre.query.one()
    assert v.criterio=='revisado' and v.especificacoes_revisadas['ddr']=='DDR4'
    assert Oferta.query.count()==HistoricoOferta.query.count()==0
    assert MemoriaRAM.query.count()==1 and p.part_number is None and p.referencia_interna=='SEED-TESTE-1'
    p.ddr='DDR5';db.session.commit()
    assert service.executar(arquivo,simular=False)['revisao']==1
    from unittest.mock import Mock
    cliente=Mock()
    assert AssociarCatalogoService().executar(p,cliente,'token')['status']=='revisao'
    cliente._consultar.assert_not_called()


@pytest.mark.parametrize('caso',['ddr','kit','url','ausente','duplicada','outro_catalogo'])
def test_divergencias_e_duplicatas_nao_sobrescrevem(contexto,caso):
    _,p,item,arquivo=contexto
    dados=[deepcopy(item)]
    if caso=='ddr':dados[0]['especificacoes']['ddr']='DDR5'
    if caso=='kit':dados[0]['especificacoes']['quantidade_pentes']=2
    if caso=='url':dados[0]['url_peca']='https://www.kabum.com.br/produto/456/outro'
    if caso=='ausente':dados[0]['referencia']='SEED-AUSENTE'
    if caso=='duplicada':dados.append(deepcopy(item))
    if caso=='outro_catalogo':
        db.session.add(VinculoMercadoLivre(tabela_peca='memoria_ram',peca_id=p.id,catalogo_id='MLB999',
            assinatura_peca=assinatura_peca(p),assinatura_catalogo='0'*64,criterio='revisado'));db.session.commit()
    arquivo.write_text(json.dumps(dados))
    if caso=='duplicada':
        with pytest.raises(ValueError,match='duplicado'):ImportarVinculosRevisadosService().executar(arquivo,simular=False)
    else:assert ImportarVinculosRevisadosService().executar(arquivo,simular=False)['revisao']==1
    assert VinculoMercadoLivre.query.count()==int(caso=='outro_catalogo')


def test_migracao_aditiva_preserva_vinculo_antigo(contexto):
    _,p,_,_=contexto
    from sqlalchemy import text
    with db.engine.begin() as conn:
        conn.execute(text('ALTER TABLE vinculo_mercado_livre DROP COLUMN especificacoes_revisadas'))
        conn.execute(text("INSERT INTO vinculo_mercado_livre (id,tabela_peca,peca_id,catalogo_id,assinatura_peca,assinatura_catalogo,criterio,criado_em,atualizado_em) VALUES (1,'memoria_ram',1,'MLB123','a','b','revisado','2026-11-03','2026-11-03')"))
    assert len(preparar_vinculos_revisados()['alteracoes'])==1
    assert preparar_vinculos_revisados()['alteracoes']==[]
    with db.engine.connect() as conn:assert conn.execute(text('SELECT catalogo_id FROM vinculo_mercado_livre')).scalar()=='MLB123'


def test_popular_aplica_manifesto_sem_rede(contexto):
    from unittest.mock import patch,Mock
    from services.peca_service.popular_pecas_service import PopularPecasService
    with patch('services.mercadolivre_service.importar_vinculos_revisados_service.ImportarVinculosRevisadosService.executar',return_value=dict(cadastrados=1,inalterados=0,revisao=0)) as importar:
        PopularPecasService._aplicar_vinculos_revisados()
        importar.assert_called_once_with(simular=False)


def test_ofertas_e_historico_ocultos_apos_mudar_ficha(contexto):
    from datetime import datetime
    from services.peca_service.consultar_historico_precos_service import ConsultarHistoricoPrecosService
    _,p,_,arquivo=contexto
    ImportarVinculosRevisadosService().executar(arquivo,simular=False)
    oferta=Oferta(tabela_peca='memoria_ram',peca_id=p.id,loja='mercado_livre',produto_id_loja='MLB321',
        vendedor_id='1',url='https://produto.mercadolivre.com.br/MLB-321-_JM',preco=100,
        consultado_em=datetime.now(),ativa=True)
    db.session.add(oferta);db.session.commit()
    assert len(Oferta.anexar_a_catalogo([p.to_catalogo()])[0]['ofertas'])==1
    p.frequencia_mhz=3600;db.session.commit()
    assert Oferta.anexar_a_catalogo([p.to_catalogo()])[0]['ofertas']==[]
    with pytest.raises(LookupError):ConsultarHistoricoPrecosService().executar('memoria_ram',p.id,oferta.id)


def test_coleta_somente_vinculadas_ignora_pecas_pendentes(contexto):
    from services.mercadolivre_service.atualizar_ofertas_service import AtualizarOfertasMercadoLivreService
    from unittest.mock import patch
    _,p,_,arquivo=contexto
    with patch('services.mercadolivre_service.atualizar_ofertas_service.TokenMercadoLivreService') as tokens:
        resumo=AtualizarOfertasMercadoLivreService().executar(categoria='memoria_ram',somente_vinculadas=True)
        assert resumo['pecas']==resumo['requisicoes']==0
        tokens.assert_not_called()
    ImportarVinculosRevisadosService().executar(arquivo,simular=False)
    assert [x.id for x in MemoriaRAM.lote_para_ofertas(somente_vinculadas=True)]==[p.id]
