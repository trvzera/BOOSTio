import json
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet
from flask import Flask

from models import db, TokenIntegracao
from services.mercadolivre_service.transferir_tokens_mercado_livre_service import TransferirTokensMercadoLivreService

@pytest.fixture
def origem(tmp_path):
    app=Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',INTEGRACOES_TOKEN_CHAVE=Fernet.generate_key().decode(),MERCADO_LIVRE_CLIENT_ID='123',MERCADO_LIVRE_CONTA_ID='42')
    db.init_app(app)
    arquivo=tmp_path/'tokens.json'
    arquivo.write_text(json.dumps({'access_token':'access','refresh_token':'refresh','expires_at':1000.1234567,'renovacao_pendente':False}))
    with app.app_context():
        TokenIntegracao.__table__.create(db.engine)
        yield arquivo
        db.session.remove(); db.engine.dispose()

def test_transfere_cifrado_e_idempotente(origem):
    s=TransferirTokensMercadoLivreService()
    assert s.executar(origem)['transferidos']==1
    assert s.executar(origem)['inalterados']==1
    assert TokenIntegracao.query.count()==1
    token=TokenIntegracao.query.one()
    assert token.access_token=='access' and token._access_token!='access'
    assert origem.exists()
    assert s.executar(origem,remover_arquivo=True)['arquivo_removido'] is True
    assert not origem.exists()

def test_nunca_sobrescreve_tokens_renovados_com_arquivo_antigo(origem):
    s=TransferirTokensMercadoLivreService(); s.executar(origem)
    token=TokenIntegracao.query.one(); token.definir_tokens('novo','refresh-novo',token.expira_em); db.session.commit()
    with pytest.raises(ValueError,match='outro par'): s.executar(origem,remover_arquivo=True)
    assert origem.exists() and token.refresh_token=='refresh-novo'

def test_falha_gravacao_preserva_origem(origem):
    with patch.object(TokenIntegracao,'gravar_estado',side_effect=ValueError('falha')),pytest.raises(ValueError):
        TransferirTokensMercadoLivreService().executar(origem,remover_arquivo=True)
    assert origem.exists() and TokenIntegracao.query.count()==0
