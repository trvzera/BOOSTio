from services.marketplace_service.gravar_ofertas_service import aplicar_lote_mercado_livre
from repositories.identificadores_peca_repository import separar_identificadores
"""Somente banco MySQL descartável local; rede Mercado Livre simulada."""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from cryptography.fernet import Fernet
from flask import Flask
from sqlalchemy import event, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError

from models import db, Usuario, Processador, ControleColeta, Oferta, HistoricoOferta, VinculoMercadoLivre, TokenIntegracao
from migrations.ofertas_mercado_livre import preparar_ofertas_mercado_livre
from migrations.tokens_integracao import preparar_tokens_integracao
from repositories.mercado_livre_token_repository import MercadoLivreTokenRepository
from services.mercadolivre_service.token_mercado_livre_service import TokenMercadoLivreService
from utils.identidade_peca import assinatura_peca, assinatura_catalogo

URI=os.getenv('BOOSTIO_MYSQL_TEST_URI')
pytestmark=pytest.mark.skipif(not URI,reason='Requer MySQL descartável local em BOOSTIO_MYSQL_TEST_URI')

@pytest.fixture
def banco():
    url=make_url(URI)
    if url.host not in ('127.0.0.1','localhost') or url.database!='boostio_ml_teste' or url.get_backend_name()!='mysql':
        pytest.fail('Teste recusado: use apenas MySQL local descartável boostio_ml_teste')
    app=Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI=URI,INTEGRACOES_TOKEN_CHAVE=Fernet.generate_key().decode(),
        MERCADO_LIVRE_CLIENT_ID='123',MERCADO_LIVRE_CONTA_ID='42',MERCADO_LIVRE_CLIENT_SECRET='teste')
    db.init_app(app)
    with app.app_context():
        db.drop_all()
        db.metadata.create_all(db.engine,tables=[Usuario.__table__,Processador.__table__,ControleColeta.__table__])
        usuario=Usuario(nome='Preservado',email='validacao@example.test',senha='hash-de-teste')
        p=Processador(fabricante='AMD',modelo='Ryzen 5 5500',part_number='100-100000457BOX',soquete='AM4',
            nucleo=6,thread=12,clockbase=3.6,clockmax=4.2,consumo_energia=65,preco=600,esgotado=False)
        db.session.add_all([usuario,p]);db.session.commit()
        yield app,p
        db.session.remove();db.drop_all();db.engine.dispose()


def preparar():
    preparar_tokens_integracao();preparar_ofertas_mercado_livre()


def test_migrations_preservam_usuarios_e_sao_repetiveis(banco):
    antes=list(db.session.execute(text('SELECT * FROM usuario')))
    preparar()
    assert preparar_tokens_integracao()['criada'] is False
    assert preparar_ofertas_mercado_livre()['criadas']==[]
    assert list(db.session.execute(text('SELECT * FROM usuario')))==antes


def aplicar(peca,preco,simular=False):
    dados={'produto_id_loja':'MLB11','vendedor_id':'5','preco':preco,'url':'https://produto.mercadolivre.com.br/MLB-11-_JM'}
    return aplicar_lote_mercado_livre(peca,'MLB123',assinatura_peca(peca),assinatura_catalogo({'id':'MLB123'}),
                                          'mpn',[dados],datetime(2026,11,3,0,0,0,123456),simular=simular)


def test_gravacao_idempotencia_historico_e_rollback(banco):
    _,p=banco;preparar()
    aplicar(p,100,simular=True)
    assert Oferta.query.count()==0
    aplicar(p,100);aplicar(p,100)
    assert Oferta.query.count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==1
    aplicar(p,90)
    assert Oferta.query.one().preco==90 and HistoricoOferta.query.count()==2
    assert p.preco==600 and Oferta.query.one().esgotado is None
    def falhar(conn,cursor,statement,*args):
        if statement.lower().startswith('insert into historico_oferta'):
            raise OperationalError('falha de teste',{},None)
    event.listen(db.engine,'before_cursor_execute',falhar)
    try:
        with pytest.raises(OperationalError):aplicar(p,80)
    finally:event.remove(db.engine,'before_cursor_execute',falhar)
    assert Oferta.query.one().preco==90 and HistoricoOferta.query.count()==2
    assert Usuario.query.one().nome=='Preservado'


def test_renovacao_cifrada_e_concorrencia_mysql(banco):
    import json
    app,_=banco;preparar()
    repo=MercadoLivreTokenRepository('123','42')
    with repo.bloquear():
        repo.ler();repo.salvar({'access_token':'antigo','refresh_token':'refresh-antigo','expires_at':0,'renovacao_pendente':False})
    resposta=Mock(status_code=200,headers={'Content-Type':'application/json'},iter_content=Mock(return_value=[json.dumps({
        'access_token':'novo','refresh_token':'refresh-novo','expires_in':21600,'token_type':'bearer'}).encode()]))
    config=dict(app.config)
    def executar(_):
        outro=Flask('worker');outro.config.update(config);db.init_app(outro)
        with outro.app_context():
            try:return TokenMercadoLivreService(relogio=lambda:1000).executar()
            except ValueError:return 'concorrente'
            finally:db.session.remove();db.engine.dispose()
    with patch('requests.post',return_value=resposta) as post,ThreadPoolExecutor(max_workers=2) as pool:
        resultados=list(pool.map(executar,range(2)))
    assert 'novo' in resultados and post.call_count==1
    assert TokenMercadoLivreService(relogio=lambda:1100).executar()=='novo'
    token=TokenIntegracao.query.one()
    assert token.refresh_token=='refresh-novo' and token._refresh_token!='refresh-novo'


def test_revalida_identidade_alterada_por_outra_conexao(banco):
    from sqlalchemy.orm import Session
    _,p=banco;preparar()
    identidade=assinatura_peca(p)
    VinculoMercadoLivre.buscar('processador',p.id)
    with Session(db.engine) as outra:
        outra.query(Processador).filter_by(id=p.id).update({'modelo':'Modelo alterado'})
        outra.commit()
    with pytest.raises(ValueError,match='identificação'):
        aplicar_lote_mercado_livre(p,'MLB123',identidade,assinatura_catalogo({'id':'MLB123'}),
            'mpn',[{'produto_id_loja':'MLB11','vendedor_id':'5','preco':100,'url':'url'}],datetime(2026,11,3),simular=False)
    assert Oferta.query.count()==VinculoMercadoLivre.query.count()==0


def test_duas_escritas_concorrentes_nao_duplicam_oferta_ou_historico(banco):
    app,p=banco;preparar();peca_id=p.id;config=dict(app.config)
    def gravar(_):
        worker=Flask('ofertas');worker.config.update(config);db.init_app(worker)
        with worker.app_context():
            try:return aplicar(Processador.buscar_por_id(peca_id),100)
            finally:db.session.remove();db.engine.dispose()
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados=list(pool.map(gravar,range(2)))
    assert len(resultados)==2
    db.session.rollback()
    assert Oferta.query.count()==HistoricoOferta.query.count()==VinculoMercadoLivre.query.count()==1


def test_ofertas_para_catalogo_no_mysql(banco):
    _,p=banco;preparar();aplicar(p,100)
    dados=Oferta.anexar_a_catalogo([p.to_catalogo()])[0]
    assert dados['preco']==600
    oferta=dados['ofertas'][0]
    assert oferta['loja']=='mercado_livre' and oferta['preco']==100 and oferta['esgotado'] is None
    assert oferta['atualizadoEm'].endswith('+00:00') and oferta['vendedor_id']=='5'


def test_identidade_fabricante_preserva_referencia_e_valida_especificacoes(banco):
    from models import IdentidadeFabricante
    from services.mercadolivre_service.registrar_identidade_fabricante_service import RegistrarIdentidadeFabricanteService
    from migrations.identidades_fabricante import preparar_identidades_fabricante
    _, p = banco
    original = p.part_number
    assert preparar_identidades_fabricante()['criadas'] == ['identidade_fabricante']
    assert preparar_identidades_fabricante()['criadas'] == []
    db.session.rollback()
    specs = {'soquete': 'AM4', 'nucleo': 6}
    assert RegistrarIdentidadeFabricanteService().executar(p, original, 'https://www.amd.com/', specs, simular=True) == 'proposta'
    assert IdentidadeFabricante.query.count() == 0
    assert RegistrarIdentidadeFabricanteService().executar(p, original, 'https://www.amd.com/', specs, simular=False) == 'cadastrada'
    assert RegistrarIdentidadeFabricanteService().executar(p, original, 'https://www.amd.com/', specs, simular=False) == 'inalterada'
    assert p.part_number == original and IdentidadeFabricante.buscar(p).mpn == original
    p.soquete = 'AM5'; db.session.commit()
    assert IdentidadeFabricante.buscar(p) is None


def test_autorizacao_oauth_convite_consumido_uma_vez_no_mysql(banco):
    from models import AutorizacaoMercadoLivre
    from migrations.autorizacao_mercado_livre import preparar_autorizacao_mercado_livre
    from services.mercadolivre_service.autorizar_conta_service import AutorizarContaMercadoLivreService as Service
    app,_=banco
    assert preparar_autorizacao_mercado_livre()['criadas']==['autorizacao_mercado_livre']
    assert preparar_autorizacao_mercado_livre()['criadas']==[]
    db.session.rollback()
    config=('123','42','https://api.example.test/auth/mercadolivre/callback')
    AutorizacaoMercadoLivre.criar(Service.hash('s'*32),'estado',*config,navegador_hash=Service.hash('n'*32),verificador='v'*64)
    def consumir():
        with app.app_context():
            try:
                return AutorizacaoMercadoLivre.consumir(Service.hash('s'*32),'estado',*config,navegador_hash=Service.hash('n'*32))
            except ValueError:
                return 'recusado'
    with ThreadPoolExecutor(max_workers=2) as executor:
        resultados=list(executor.map(lambda _:consumir(),range(2)))
    assert sorted(resultados)==sorted(['v'*64,'recusado'])


def test_migracao_e_importacao_manual_preservam_vinculos_mysql(banco):
    from migrations.vinculos_revisados import preparar_vinculos_revisados
    app,p=banco
    preparar()
    VinculoMercadoLivre.registrar_revisado(p,'MLB111',assinatura_peca(p),'c'*64)
    pid=p.id
    db.session.remove()
    with db.engine.begin() as conn:
        conn.execute(text('ALTER TABLE vinculo_mercado_livre DROP COLUMN especificacoes_revisadas'))
    assert len(preparar_vinculos_revisados()['alteracoes'])==1
    assert preparar_vinculos_revisados()['alteracoes']==[]
    p=Processador.buscar_por_id(pid)
    args=(p,'MLB111',assinatura_peca(p),'c'*64,{'nucleo':6,'soquete':'AM4'})
    assert VinculoMercadoLivre.aplicar_revisado(*args,simular=True)=='proposto'
    assert VinculoMercadoLivre.buscar('processador',pid).especificacoes_revisadas is None
    assert VinculoMercadoLivre.aplicar_revisado(*args,simular=False)=='cadastrado'
    assert VinculoMercadoLivre.aplicar_revisado(*args,simular=False)=='inalterado'
    assert Usuario.query.count()==1 and VinculoMercadoLivre.query.count()==1


def test_catalogo_aditivo_preserva_legado_e_define_novos_como_pendentes(banco):
    from migrations.catalogo_automatizado import preparar_catalogo_automatizado
    from models import ProdutoPendente
    _, p = banco
    preparar()
    aplicar(p, 100)
    antes_usuario = list(db.session.execute(text('SELECT * FROM usuario')))
    antes_oferta = list(db.session.execute(text('SELECT * FROM oferta')))
    antes_historico = list(db.session.execute(text('SELECT * FROM historico_oferta')))
    db.session.remove()
    with db.engine.begin() as conn:
        conn.execute(text('ALTER TABLE processador DROP CHECK ck_processador_validacao'))
        conn.execute(text('DROP INDEX ix_processador_publicacao ON processador'))
        for campo in ('status_validacao', 'validacao_motivo', 'validado_em'):
            conn.execute(text(f'ALTER TABLE processador DROP COLUMN {campo}'))
    assert preparar_catalogo_automatizado()['alteracoes']
    preparar_catalogo_automatizado(simular=False)
    assert preparar_catalogo_automatizado()['alteracoes'] == []
    assert Processador.query.one().status_validacao is None
    assert Processador.listar_publicadas()
    assert list(db.session.execute(text('SELECT * FROM usuario'))) == antes_usuario
    assert list(db.session.execute(text('SELECT * FROM oferta'))) == antes_oferta
    assert list(db.session.execute(text('SELECT * FROM historico_oferta'))) == antes_historico
    assert ProdutoPendente.query.count() == 0
    with db.engine.begin() as conn:
        conn.execute(text("INSERT INTO processador (fabricante, modelo, soquete, nucleo, thread, clockbase, clockmax, consumo_energia, preco, esgotado, criado_em, atualizado_em) VALUES ('Teste','Novo','AM4',6,12,3,4,65,100,0,NOW(),NOW())"))
    db.session.remove()
    assert Processador.query.order_by(Processador.id.desc()).first().status_validacao == 'pendente'
    assert len(Processador.listar_publicadas()) == 1


def test_descoberta_mysql_grava_fila_e_auditoria_sem_publicar(banco):
    from models import ProdutoPendente, ExecucaoDescoberta
    from migrations.catalogo_automatizado import preparar_catalogo_automatizado
    from services.mercadolivre_service.descobrir_produtos_service import DescobrirProdutosService
    from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
    preparar_catalogo_automatizado(simular=False)
    cliente = BuscarOfertasMercadoLivreService()
    pagina = lambda linhas: {'results':linhas, 'paging':{'offset':0, 'total':len(linhas)}}
    respostas = [pagina([{'id':'MLB20','name':'Kingston DDR4'}]), pagina([{
        'item_id':'MLB1','seller_id':7,'site_id':'MLB','currency_id':'BRL','price':100,'condition':'new'}])]
    tokens = Mock();tokens.executar.return_value = 'teste'
    for chave in ('novos', 'ja_coletados'):
        cliente._consultar = Mock(side_effect=respostas)
        r = DescobrirProdutosService(cliente=cliente, tokens=tokens).executar(
            categoria='memoria_ram', consulta='Kingston DDR4', simular=False)
        assert r[chave] == 1 and not r['interrompido']
    assert ProdutoPendente.query.count() == 1 and ExecucaoDescoberta.query.count() == 2
    assert ProdutoPendente.query.one().status == 'pendente'
    assert Oferta.query.count() == 0


def test_trava_worker_e_checkpoint_mysql(banco):
    from repositories.controle_catalogo_repository import RepositorioControleCatalogo
    from models import EstadoCatalogo
    from migrations.catalogo_automatizado import preparar_catalogo_automatizado
    preparar_catalogo_automatizado(simular=False)
    um,dois=RepositorioControleCatalogo(),RepositorioControleCatalogo()
    with um.bloquear() as ok:
        assert ok
        with dois.bloquear() as outro:assert not outro
        um.verificar()
    with dois.bloquear() as ok:assert ok
    plano={'nome':'teste','categoria':'processador','consulta':'AMD Ryzen'}
    e=EstadoCatalogo.obter(plano);e.registrar_progresso(cursor_descoberta={'origem':'catalogo','offset':20})
    db.session.remove()
    assert EstadoCatalogo.obter(plano).cursor_descoberta['offset']==20


def test_importacao_concorrente_nao_duplica_componente_mysql(banco):
    from threading import Barrier
    from models import HD, ProdutoPendente, IdentidadeFabricante
    from migrations.catalogo_automatizado import preparar_catalogo_automatizado
    from migrations.identidades_fabricante import preparar_identidades_fabricante
    from services.mercadolivre_service.importar_produto_service import ImportarProdutoService
    from services.mercadolivre_service.buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
    app,_=banco;preparar();preparar_catalogo_automatizado(simular=False);preparar_identidades_fabricante()
    HD.__table__.create(db.engine)
    produto=dict(id='MLB99',name='Seagate Exos 8TB',status='active',domain_id='MLB-HARD_DRIVES_AND_SSDS',attributes=[
        dict(id=k,value_name=v) for k,v in [('BRAND','Seagate'),('MODEL','ST8000NM017B'),('MPN','ST8000NM017B'),('CAPACITY','8 TB'),('DRIVE_STORAGE_TYPE','HDD'),('HARD_DRIVE_AND_SSD_POWER_CONSUMPTION','7 W')]])
    ids=[]
    for num in (10,11):
        p=ProdutoPendente(loja='mercado_livre',produto_id_loja='MLB'+str(num),vendedor_id='7',titulo='Seagate',url='https://example.test',categoria_sugerida='hd',
            dados_originais={'catalogo':{'id':'MLB99'},'anuncio':{}},coletado_em=datetime(2026,11,3))
        db.session.add(p);db.session.flush();ids.append(p.id)
    db.session.commit();barreira=Barrier(2)
    def executar(item):
        pid,num=item
        with app.app_context():
            c=BuscarOfertasMercadoLivreService();c._consultar=Mock(return_value=produto)
            anuncio=c._normalizar(dict(item_id='MLB'+str(num),seller_id=7,site_id='MLB',currency_id='BRL',price=100,condition='new',available_quantity=3),'MLB99')
            def consultar(*a,**kw):barreira.wait(timeout=10);return {'ofertas':[anuncio]}
            c.executar=consultar;t=Mock();t.executar.return_value='teste'
            return ImportarProdutoService(cliente=c,tokens=t).executar(pid,simular=False,permitir_novos=True)['acao']
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert list(executor.map(executar,zip(ids,(10,11))))==['importada','importada']
    db.session.remove()
    assert HD.query.count()==IdentidadeFabricante.query.count()==1
    assert Oferta.query.count()==HistoricoOferta.query.count()==2


def test_ram_formato_nulo_migracao_e_importacao_sem_mpn_mysql(banco):
    from models import MemoriaRAM,ProdutoPendente
    from migrations.catalogo_automatizado import preparar_catalogo_automatizado
    from migrations.identidades_fabricante import preparar_identidades_fabricante
    from services.catalogo_service.produto_normalizado import ProdutoNormalizado
    from services.catalogo_service.importar_catalogo_service import ImportarCatalogoService
    from utils.identidade_peca import assinatura_documento
    app,p=banco;preparar();preparar_identidades_fabricante()
    MemoriaRAM.__table__.create(db.engine)
    db.session.add(MemoriaRAM(fabricante='Teste',modelo='RAM',preco=100,consumo_energia=5,capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1));db.session.commit();db.session.remove()
    with db.engine.begin() as conn:conn.execute(text('ALTER TABLE memoria_ram DROP COLUMN formato'))
    preparar_catalogo_automatizado(simular=False)
    assert MemoriaRAM.query.one().formato is None
    p=Processador.query.one();p.part_number='SEED-CPU-1';p.status_validacao='aprovado';db.session.commit()
    dto=ProdutoNormalizado(loja='outra_loja',id_externo='cpu',categoria='processador',categoria_confirmada=True,titulo='AMD Ryzen 5 5500',modelo='Ryzen 5 5500',marca='AMD',ativo=True,especificacoes={'soquete':'AM4','nucleo':6,'thread':12})
    bruto={'teste':'multiloja'}
    pend=ProdutoPendente(loja='outra_loja',produto_id_loja='1',titulo=dto.titulo,url='https://loja.example/cpu',categoria_sugerida='processador',dados_originais=bruto,coletado_em=datetime(2026,11,3));db.session.add(pend);db.session.commit()
    ficha={'dados':{},'identidade':{},'pronto':False,'conflitos':[],'produto':{'id':'cpu'}}
    anuncio={'produto_id_loja':'1','url':'https://loja.example/cpu','preco':'500.00','esgotado':False}
    r=ImportarCatalogoService().executar(pend.id,dto,ficha,anuncio,assinatura_documento(bruto),simular=False)
    assert r['acao']=='importada' and r['criterio']=='modelo_especificacoes'
    assert Oferta.query.count()==HistoricoOferta.query.count()==1


def test_separacao_identificadores_aditiva_preserva_usuario_e_cotacao_mysql(banco):
    from migrations.catalogo_automatizado import preparar_catalogo_automatizado
    p = Processador.query.one()
    ident, preco = p.id, p.preco
    db.session.execute(text("UPDATE processador SET part_number='KABUM-999', kabum_external='https://www.kabum.com.br/produto/999/teste' WHERE id=:id"), {'id': ident})
    db.session.commit()
    with db.engine.begin() as conn:
        conn.execute(text('DROP INDEX ix_processador_referencia ON processador'))
        conn.execute(text('ALTER TABLE processador DROP COLUMN referencia_interna'))
    db.session.expire_all()
    assert any('referencia_interna' in i.get('sql', '') for i in preparar_catalogo_automatizado()['alteracoes'])
    preparar_catalogo_automatizado(simular=False)
    p = Processador.query.one()
    assert separar_identificadores(p)['alterada']
    assert p.part_number == 'KABUM-999' and Oferta.query.count() == 0
    separar_identificadores(p, simular=False)
    assert p.part_number is None and p.referencia_interna == 'KABUM-999'
    assert Oferta.query.one().produto_id_loja == '999'
    assert p.id == ident and p.preco == preco and Usuario.query.count() == 1
    assert not separar_identificadores(p, simular=False)['alterada']
    assert Oferta.query.count() == 1


def test_especificacoes_json_migracao_aditiva_e_idempotencia_mysql(banco):
    from models import MemoriaRAM
    from migrations.catalogo_automatizado import preparar_catalogo_automatizado
    from services.catalogo_service.produto_normalizado import ProdutoNormalizado
    from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService
    MemoriaRAM.__table__.create(db.engine)
    with db.engine.begin() as conn:
        conn.execute(text('ALTER TABLE memoria_ram DROP COLUMN fontes_especificacoes'))
    assert any('fontes_especificacoes' in item.get('sql','') for item in preparar_catalogo_automatizado()['alteracoes'])
    preparar_catalogo_automatizado(simular=False)
    assert preparar_catalogo_automatizado()['alteracoes'] == []
    p = MemoriaRAM(fabricante='Crucial',modelo='CT8G4DFRA32A',consumo_energia=5,preco=123,
        capacidade_gb=8,ddr='DDR4',frequencia_mhz=3200,quantidade_pentes=1,latencia='CL22')
    db.session.add(p); db.session.commit()
    dto = ProdutoNormalizado(loja='outra_loja',id_externo='memoria-1',categoria='memoria_ram',
        categoria_confirmada=True,titulo='Crucial CT8G4DFRA32A',modelo='CT8G4DFRA32A',marca='Crucial',
        ativo=True,fonte='https://loja.example/1',especificacoes={'capacidade_gb':'8 GB','ddr':'DDR4',
        'frequencia_mhz':'3200 MHz','quantidade_pentes':1,'latencia':'CL22','formato_ram':'UDIMM'})
    s = EnriquecerPecaExistenteService()
    assert s.executar(p,dto)['status'] == 'proposta'
    assert p.formato is None
    assert s.executar(p,dto,simular=False)['status'] == 'atualizada'
    assert p.fontes_especificacoes['formato']['valor'] == 'DIMM'
    assert s.executar(p,dto,simular=False)['status'] == 'inalterada'
    assert p.preco == 123 and Usuario.query.one().nome == 'Preservado'
