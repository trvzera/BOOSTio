from datetime import datetime, timezone, timedelta

import pytest
from cryptography.fernet import Fernet
from flask import Flask
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from models import db, TokenIntegracao
from migrations.tokens_integracao import preparar_tokens_integracao


@pytest.fixture
def banco():
    app = Flask(__name__)
    app.config.update(SQLALCHEMY_DATABASE_URI='sqlite:///:memory:', INTEGRACOES_TOKEN_CHAVE=Fernet.generate_key().decode())
    db.init_app(app)
    with app.app_context():
        preparar_tokens_integracao()
        yield app
        db.session.remove()
        db.engine.dispose()


def registro(conta='42'):
    token = TokenIntegracao(integracao='mercado_livre', client_id='123', conta_id=conta)
    token.definir_tokens('access-secreto', 'refresh-secreto', datetime(2026, 11, 3, 12))
    db.session.add(token)
    db.session.commit()
    return token


def test_banco_guarda_somente_cifrados(banco):
    token = registro()
    linha = db.session.execute(text('SELECT access_token_cifrado, refresh_token_cifrado FROM token_integracao')).one()
    assert all('secreto' not in valor for valor in linha)
    db.session.expire_all()
    recarregado = TokenIntegracao.buscar('mercado_livre', '123', '42')
    assert recarregado.access_token == 'access-secreto' and recarregado.refresh_token == 'refresh-secreto'
    assert 'access-secreto' not in repr(token) and 'refresh-secreto' not in repr(token)


def test_chave_errada_ou_dado_adulterado_falha_sem_vazar(banco):
    token = registro()
    chave = banco.config['INTEGRACOES_TOKEN_CHAVE']
    banco.config['INTEGRACOES_TOKEN_CHAVE'] = Fernet.generate_key().decode()
    with pytest.raises(ValueError, match='decifrar'): _ = token.refresh_token
    banco.config['INTEGRACOES_TOKEN_CHAVE'] = chave
    token._access_token = 'adulterado'
    with pytest.raises(ValueError, match='decifrar'): _ = token.access_token


@pytest.mark.parametrize('chave', [None, '', 'invalida'])
def test_sem_chave_valida_nao_modifica_par(banco, chave):
    token = registro(); anterior = token._access_token
    banco.config['INTEGRACOES_TOKEN_CHAVE'] = chave
    with pytest.raises(ValueError): token.definir_tokens('novo', 'refresh', datetime.now())
    assert token._access_token == anterior


def test_unicidade_por_aplicacao_e_conta(banco):
    registro()
    registro('43')
    with pytest.raises(IntegrityError): registro()
    db.session.rollback()
    assert TokenIntegracao.query.count() == 2


def test_datas_utc_e_margem_expiracao(banco):
    token = registro()
    tz = timezone(timedelta(hours=-3))
    token.definir_tokens('a', 'r', datetime(2026, 11, 3, 9, tzinfo=tz), renovado_em=datetime(2026, 11, 3, 3, tzinfo=tz))
    assert token.expira_em == datetime(2026, 11, 3, 12)
    assert token.ultima_renovacao_em == datetime(2026, 11, 3, 6)
    assert token.esta_expirado(datetime(2026, 11, 3, 11, 59))
    assert not token.esta_expirado(datetime(2026, 11, 3, 11, 58, 59))


@pytest.mark.parametrize('refresh', [None, '', 'com espaco', 123])
def test_rotacao_invalida_preserva_par(banco, refresh):
    token = registro(); antes = (token._access_token, token._refresh_token)
    with pytest.raises(ValueError): token.definir_tokens('novo', refresh, datetime.now())
    assert (token._access_token, token._refresh_token) == antes


def test_rotacao_rollback_e_migracao_idempotente(banco):
    token = registro(); token.renovacao_pendente = True; db.session.commit()
    assert preparar_tokens_integracao()['criada'] is False
    token.definir_tokens('access-2', 'refresh-2', datetime(2026, 11, 4))
    assert token.renovacao_pendente is False
    db.session.rollback()
    assert token.access_token == 'access-secreto' and token.renovacao_pendente is True
    assert TokenIntegracao.query.count() == 1


def test_migracao_rejeita_tabela_incompativel(banco):
    db.session.execute(text('DROP TABLE token_integracao'))
    db.session.execute(text('CREATE TABLE token_integracao (id INTEGER PRIMARY KEY)'))
    db.session.commit()
    with pytest.raises(ValueError, match='incompatível'): preparar_tokens_integracao()
