import pytest
from flask import Flask
from sqlalchemy import inspect, text

from models import db, ControleColeta, Oferta
from migrations.ofertas_mercado_livre import preparar_ofertas_mercado_livre
from commands.mercadolivre import registrar_comandos_mercadolivre

@pytest.fixture
def banco():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:'
    db.init_app(app);registrar_comandos_mercadolivre(app)
    with app.app_context():
        ControleColeta.__table__.create(db.engine)
        yield app
        db.session.remove();db.engine.dispose()

def test_migracao_aditiva_e_repetivel(banco):
    db.session.execute(text('CREATE TABLE preservada (id INTEGER PRIMARY KEY, nome TEXT)'))
    db.session.execute(text("INSERT INTO preservada VALUES (1,'usuario')"));db.session.commit()
    r=preparar_ofertas_mercado_livre()
    assert set(r['criadas'])=={'oferta','vinculo_mercado_livre','historico_oferta'}
    assert preparar_ofertas_mercado_livre()['criadas']==[]
    assert db.session.execute(text('SELECT nome FROM preservada')).scalar()=='usuario'

def test_migracao_incompativel_nao_cria_outras_tabelas(banco):
    db.session.execute(text('CREATE TABLE oferta (id INTEGER PRIMARY KEY)'));db.session.commit()
    with pytest.raises(ValueError):preparar_ofertas_mercado_livre()
    assert not inspect(db.engine).has_table('historico_oferta')

def test_cli_default_simula_e_reporta_sem_chave(banco):
    from unittest.mock import patch
    with patch('commands.mercadolivre.AtualizarOfertasMercadoLivreService') as service:
        service.return_value.executar.return_value={'simulacao':True,'interrompido':False}
        resultado=banco.test_cli_runner().invoke(args=['mercadolivre-ofertas-atualizar'])
        assert resultado.exit_code==0
        assert service.return_value.executar.call_args.kwargs['simular'] is True
        assert service.return_value.executar.call_args.kwargs['limite_ofertas']==5

def test_cli_vinculo_exige_revisao_explicita(banco):
    r=banco.test_cli_runner().invoke(args=['mercadolivre-vincular','--categoria','processador','--peca-id','1','--catalogo-id','MLB123'])
    assert r.exit_code!=0
