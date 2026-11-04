import json
import pytest
from flask import Flask
from models import db, SSD
from commands.catalogo_tecnico import registrar_comandos_catalogo_tecnico
from migrations.fichas_tecnicas import preparar_fichas_tecnicas
from .test_importar import documento

@pytest.fixture
def app():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    registrar_comandos_catalogo_tecnico(app)
    with app.app_context():
        db.create_all();preparar_fichas_tecnicas(simular=False)
        yield app
        db.session.remove();db.engine.dispose()

def test_comando_simula_aplica_repete_e_lista(app,documento,tmp_path):
    arquivo=tmp_path/'ficha.json';arquivo.write_text(json.dumps(documento))
    cli=app.test_cli_runner();args=['catalogo-tecnico-importar','--arquivo',str(arquivo)]
    assert cli.invoke(args=args).exit_code==0
    assert SSD.query.count()==0
    r=cli.invoke(args=args+['--aplicar'])
    assert r.exit_code==0,r.output
    assert SSD.query.count()==1
    assert json.loads(cli.invoke(args=args+['--aplicar']).output)['acoes']=={'inalterada':1}
    assert json.loads(cli.invoke(args=['catalogo-tecnico-listar']).output)[0]['estado']=='importada'

def test_lote_com_origens_repetidas_recusa_antes_de_gravar(app,documento,tmp_path):
    arquivo=tmp_path/'ficha.json';arquivo.write_text(json.dumps([documento,documento]))
    r=app.test_cli_runner().invoke(args=['catalogo-tecnico-importar','--arquivo',str(arquivo),'--aplicar'])
    assert r.exit_code!=0
    assert SSD.query.count()==0
