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
    return Oferta.aplicar_lote_mercado_livre(peca,'MLB123',assinatura_peca(peca),assinatura_catalogo({'id':'MLB123'}),
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
    # A sessão do job já fez leituras antes da chamada HTTP.
    VinculoMercadoLivre.buscar('processador',p.id)
    with Session(db.engine) as outra:
        outra.query(Processador).filter_by(id=p.id).update({'modelo':'Modelo alterado'})
        outra.commit()
    with pytest.raises(ValueError,match='identificação'):
        Oferta.aplicar_lote_mercado_livre(p,'MLB123',identidade,assinatura_catalogo({'id':'MLB123'}),
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
    # A sessão principal estava no snapshot anterior às gravações dos workers.
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
    from migrations.identidades_fabricante import preparar_identidades_fabricante
    _, p = banco
    original = p.part_number
    assert preparar_identidades_fabricante()['criadas'] == ['identidade_fabricante']
    assert preparar_identidades_fabricante()['criadas'] == []
    # A CLI executa migração e importação em processos separados.
    db.session.rollback()
    specs = {'soquete': 'AM4', 'nucleo': 6}
    assert IdentidadeFabricante.registrar(p, original, 'https://www.amd.com/', specs, simular=True) == 'proposta'
    assert IdentidadeFabricante.query.count() == 0
    assert IdentidadeFabricante.registrar(p, original, 'https://www.amd.com/', specs, simular=False) == 'cadastrada'
    assert IdentidadeFabricante.registrar(p, original, 'https://www.amd.com/', specs, simular=False) == 'inalterada'
    assert p.part_number == original and IdentidadeFabricante.buscar(p).mpn == original
    p.soquete = 'AM5'; db.session.commit()
    assert IdentidadeFabricante.buscar(p) is None
