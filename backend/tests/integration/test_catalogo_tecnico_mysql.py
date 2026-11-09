"""MySQL local descartável; nunca executar contra o banco da aplicação."""
import os
import pytest
from flask import Flask
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from models import db, SSD, Usuario, Oferta
from migrations.catalogo_tecnico import preparar_catalogo_tecnico
from services.catalogo_tecnico_service.importar_base_tecnica_service import ImportarBaseTecnicaService

URI=os.getenv('BOOSTIO_MYSQL_TEST_URI')
pytestmark=pytest.mark.skipif(not URI,reason='Requer MySQL descartável local')


def test_migrar_importar_e_repetir_mysql():
    url=make_url(URI)
    if url.host not in ('127.0.0.1','localhost') or url.database!='boostio_ml_teste' or url.get_backend_name()!='mysql':
        pytest.fail('Use somente MySQL local descartável boostio_ml_teste')
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']=URI;db.init_app(app)
    with app.app_context():
        try:
            db.drop_all();db.create_all()
            db.session.add(Usuario(nome='Preservado',email='preservado@example.test',senha='hash'));db.session.commit()
            with db.engine.begin() as conn:
                conn.exec_driver_sql('ALTER TABLE ssd MODIFY COLUMN preco FLOAT NOT NULL, MODIFY COLUMN esgotado BOOL NOT NULL, MODIFY COLUMN consumo_energia FLOAT NOT NULL, DROP COLUMN ficha_montagem_validada')
                conn.execute(text("INSERT INTO ssd (fabricante,modelo,preco,esgotado,consumo_energia,capacidade_gb,tipo,interface,criado_em) VALUES ('Marca','Original',100,0,5,500,'SSD','SATA',CURRENT_TIMESTAMP)"))
            assert preparar_catalogo_tecnico()['alteracoes']
            preparar_catalogo_tecnico(simular=False)
            assert preparar_catalogo_tecnico()['alteracoes']==[]
            assert all(c['nullable'] for c in inspect(db.engine).get_columns('ssd') if c['name'] in ('preco','esgotado','consumo_energia'))
            assert SSD.query.one().modelo=='Original'
            assert Usuario.query.one().nome=='Preservado'
            identidade=dict(fabricante='Kingston',modelo='A400 480GB',mpn='SA400S37/480G')
            spec=dict(capacidade_gb=480,tipo='SSD',interface='SATA',formato='2.5',consumo_energia=1.5)
            documento=dict(versao=1,provedor='teste',id_externo='ssd-1',categoria='ssd',identidade=identidade,
                especificacoes=spec,fontes={c:{'url':'https://example.org/ficha'} for c in [*identidade,*spec]})
            s=ImportarBaseTecnicaService()
            assert s.processar(documento)['acao']=='proposta'
            assert SSD.query.count()==1
            assert s.processar(documento,simular=False)['acao']=='criada'
            assert s.processar(documento,simular=False)['acao']=='inalterada'
            p=SSD.query.filter_by(part_number='SA400S37/480G').one()
            assert p.preco is None and p.esgotado is None
            assert Oferta.query.count()==0
            documento['provedor']='segunda-fonte'
            assert s.processar(documento,simular=False)['acao']=='associada'
            assert SSD.query.count()==2
        finally:
            db.session.remove();db.drop_all();db.engine.dispose()
