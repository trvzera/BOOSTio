import pytest
from flask import Flask
from sqlalchemy import MetaData, inspect, text, event
from models import db, SSD, Usuario, Build
from migrations.catalogo_tecnico import preparar_catalogo_tecnico
from services.peca_service.modelos_pecas import MODELOS_PECAS


@pytest.fixture
def legado():
    a=Flask(__name__);a.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(a)
    with a.app_context():
        db.create_all()
        SSD.__table__.drop(db.engine)
        antiga=SSD.__table__.to_metadata(MetaData())
        for campo in ('consumo_energia',):antiga.c[campo].nullable=False
        antiga.create(db.engine)
        with db.engine.begin() as c:
            c.exec_driver_sql('ALTER TABLE ssd DROP COLUMN ficha_montagem_validada')
            c.exec_driver_sql('CREATE TABLE teste_auditoria (peca INTEGER)')
            c.exec_driver_sql('CREATE TRIGGER teste_trigger AFTER UPDATE OF modelo ON ssd BEGIN INSERT INTO teste_auditoria VALUES (NEW.id); END')
            c.exec_driver_sql('CREATE INDEX teste_indice ON ssd(modelo) WHERE consumo_energia > 0')
        # A fixture usa SQL para inserir antes da migração, pois o model novo
        # inclui a coluna que propositalmente não existe no esquema antigo.
        with db.engine.begin() as c:
            c.execute(text("INSERT INTO ssd (id,fabricante,modelo,consumo_energia,capacidade_gb,tipo,interface,criado_em) VALUES (1,'Marca','Original',5,500,'NVMe','PCIe 3.0',CURRENT_TIMESTAMP)"))
        db.session.add(Usuario(nome='Preservado',email='teste@example.test',senha='hash'));db.session.commit()
        # Registro externo que referencia a peça, sem precisar construir uma
        # montagem artificial: comprova preservação de FKs e dos seus valores.
        with db.engine.begin() as c:
            c.exec_driver_sql('CREATE TABLE referencia_teste (id INTEGER PRIMARY KEY, ssd_id INTEGER REFERENCES ssd(id))')
            c.exec_driver_sql('INSERT INTO referencia_teste VALUES (1,1)')
        with db.engine.connect() as c:
            c.exec_driver_sql('PRAGMA foreign_keys=ON');c.commit()
        yield a
        db.session.remove();db.engine.dispose()


def test_migracao_preserva_dados_referencias_indices_e_triggers(legado):
    assert preparar_catalogo_tecnico()['alteracoes']
    assert not inspect(db.engine).get_columns('ssd')[0].get('nullable')  # PK não muda.
    preparar_catalogo_tecnico(simular=False)
    assert preparar_catalogo_tecnico()['alteracoes']==[]
    p=db.session.get(SSD,1)
    assert (p.modelo,p.consumo_energia)==('Original',5)
    assert p.ficha_montagem_validada is None
    assert Usuario.query.one().nome=='Preservado'
    assert db.session.execute(text('SELECT ssd_id FROM referencia_teste')).scalar_one()==1
    assert db.session.execute(text('PRAGMA foreign_key_check')).all()==[]
    assert 'teste_indice' in {i['name'] for i in inspect(db.engine).get_indexes('ssd')}
    p.modelo='Alterado';db.session.commit()
    assert db.session.execute(text('SELECT peca FROM teste_auditoria')).scalar_one()==1
    p.consumo_energia=None;db.session.commit()
    assert p.consumo_energia is None


def test_falha_no_rebuild_reverte_toda_alteracao(legado):
    def falhar(conn,cursor,statement,*args):
        if statement.startswith('ALTER TABLE __tecnico_ssd RENAME'):raise RuntimeError('Falha simulada')
    event.listen(db.engine,'before_cursor_execute',falhar)
    try:
        with pytest.raises(RuntimeError):preparar_catalogo_tecnico(simular=False)
    finally:event.remove(db.engine,'before_cursor_execute',falhar)
    cols={c['name']:c for c in inspect(db.engine).get_columns('ssd')}
    assert not cols['consumo_energia']['nullable'] and 'ficha_montagem_validada' not in cols
    with db.engine.connect() as c:
        assert c.exec_driver_sql('SELECT modelo,consumo_energia FROM ssd').one()==('Original',5)
        assert c.exec_driver_sql('PRAGMA foreign_keys').scalar_one()==1
        assert not c.exec_driver_sql('PRAGMA foreign_key_check').all()
