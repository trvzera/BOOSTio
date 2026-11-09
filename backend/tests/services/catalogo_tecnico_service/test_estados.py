import pytest
from flask import Flask
from models import db, FichaTecnicaCatalogo, RevisaoFichaTecnica
from migrations.fichas_tecnicas import preparar_fichas_tecnicas


@pytest.fixture
def banco():
    app=Flask(__name__);app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///:memory:';db.init_app(app)
    with app.app_context():
        preparar_fichas_tecnicas(simular=False)
        yield app
        db.session.remove();db.engine.dispose()


def test_estados_e_reabertura_explicita_com_auditoria(banco):
    f=FichaTecnicaCatalogo(provedor='teste',id_externo='1',categoria='ssd',documento={},assinatura_documento='a'*64)
    db.session.add(f);db.session.commit()
    f.transicionar('pendente_dados',motivo='Falta capacidade',responsavel='importador');db.session.commit()
    f.transicionar('rejeitada',motivo='Modelo divergente',responsavel='operador');db.session.commit()
    with pytest.raises(ValueError):f.transicionar('em_revisao',motivo='Retentar',responsavel='importador')
    f.transicionar('em_revisao',motivo='Fonte corrigida',responsavel='operador',reabrir=True);db.session.commit()
    assert RevisaoFichaTecnica.query.count()==3
    assert not f.transicionar('em_revisao',motivo='Sem mudança',responsavel='operador')
    assert preparar_fichas_tecnicas()['criadas']==[]
    with pytest.raises(ValueError):f.transicionar('importada',motivo='Pular validação',responsavel='operador')
