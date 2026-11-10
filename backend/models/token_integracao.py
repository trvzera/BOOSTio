"""Credenciais OAuth recuperáveis, cifradas com chave externa ao banco."""
from datetime import datetime, timezone

from cryptography.fernet import Fernet, InvalidToken
from flask import current_app

from . import db, ModeloBase


class TokenIntegracao(ModeloBase):
    __tablename__ = 'token_integracao'

    integracao = db.Column(db.String(40), nullable=False)
    client_id = db.Column(db.String(80), nullable=False)
    conta_id = db.Column(db.String(80), nullable=False)
    _access_token = db.Column('access_token_cifrado', db.Text, nullable=False)
    _refresh_token = db.Column('refresh_token_cifrado', db.Text, nullable=False)
    expira_em = db.Column(db.DateTime, nullable=False)
    versao = db.Column(db.Integer, nullable=False, default=0)
    renovacao_pendente = db.Column(db.Boolean, nullable=False, default=False)
    ultima_renovacao_em = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint('integracao', 'client_id', 'conta_id', name='uq_token_integracao_aplicacao_conta'),
        db.CheckConstraint("length(trim(integracao)) > 0", name='ck_token_integracao_nome'),
        db.CheckConstraint("length(trim(client_id)) > 0", name='ck_token_integracao_client'),
        db.CheckConstraint("length(trim(conta_id)) > 0", name='ck_token_integracao_conta'),
    )

    @staticmethod
    def _cifra():
        chave = current_app.config.get('INTEGRACOES_TOKEN_CHAVE')
        if not isinstance(chave, (str, bytes)) or not chave:
            raise ValueError('Configure INTEGRACOES_TOKEN_CHAVE fora do banco')
        try:
            return Fernet(chave)
        except (ValueError, TypeError):
            raise ValueError('Chave de criptografia das integrações inválida') from None

    @staticmethod
    def _validar_token(valor):
        if not isinstance(valor, str) or not valor or len(valor) > 16384 or any(c.isspace() for c in valor):
            raise ValueError('Token de integração ausente ou inválido')
        return valor

    def definir_tokens(self, access_token, refresh_token, expira_em, *, renovado_em=None):
        """Altera o par em memória; a transação pertence ao chamador."""
        access_token = self._validar_token(access_token)
        refresh_token = self._validar_token(refresh_token)
        expiracao = self._utc(expira_em)
        renovacao = self._utc(renovado_em) if renovado_em is not None else None
        cifra = self._cifra()
        access = cifra.encrypt(access_token.encode()).decode('ascii')
        refresh = cifra.encrypt(refresh_token.encode()).decode('ascii')
        self._access_token, self._refresh_token = access, refresh
        self.expira_em = expiracao
        self.ultima_renovacao_em = renovacao
        self.renovacao_pendente = False

    @staticmethod
    def _utc(valor):
        if not isinstance(valor, datetime):
            raise ValueError('Data de token inválida')
        return valor.astimezone(timezone.utc).replace(tzinfo=None) if valor.tzinfo is not None else valor

    def _decifrar(self, valor):
        cifra = self._cifra()
        try:
            return cifra.decrypt(valor.encode('ascii')).decode('utf-8')
        except (InvalidToken, UnicodeError, AttributeError):
            raise ValueError('Não foi possível decifrar o token de integração') from None

    @property
    def access_token(self):
        return self._decifrar(self._access_token)

    @property
    def refresh_token(self):
        return self._decifrar(self._refresh_token)

    def esta_expirado(self, agora=None, margem_segundos=60):
        from datetime import timedelta
        if type(margem_segundos) is not int or margem_segundos < 0:
            raise ValueError('Margem de expiração inválida')
        instante = self._utc(agora if agora is not None else datetime.now(timezone.utc))
        return self.expira_em <= instante + timedelta(seconds=margem_segundos)

    @classmethod
    def buscar(cls, integracao, client_id, conta_id, *, bloquear=False):
        """No MySQL, bloquear=True requer transação aberta até commit/rollback."""
        consulta = cls.query.filter_by(integracao=integracao, client_id=client_id, conta_id=conta_id)
        if bloquear:
            consulta = consulta.populate_existing().with_for_update()
        return consulta.one_or_none()


    @classmethod
    def ler_estado(cls, client_id, conta_id):
        from sqlalchemy.orm import Session
        with Session(db.engine) as session:
            obj = session.query(cls).filter_by(integracao='mercado_livre', client_id=client_id, conta_id=conta_id).one_or_none()
            if obj is None:
                return None
            return {'access_token': obj.access_token, 'refresh_token': obj.refresh_token,
                    'expires_at': obj.expira_em.replace(tzinfo=timezone.utc).timestamp(),
                    'renovacao_pendente': obj.renovacao_pendente, 'versao': obj.versao}

    @classmethod
    def gravar_estado(cls, client_id, conta_id, dados, versao_esperada):
        """Transação própria e CAS: não confirma alterações da sessão da build."""
        from sqlalchemy.orm import Session
        from sqlalchemy.exc import IntegrityError
        from datetime import datetime, timezone
        instante = datetime.fromtimestamp(dados['expires_at'], timezone.utc)
        novo = cls(integracao='mercado_livre', client_id=client_id, conta_id=conta_id)
        novo.definir_tokens(dados['access_token'], dados['refresh_token'], instante)
        novo.renovacao_pendente = bool(dados.get('renovacao_pendente', False))
        with Session(db.engine) as session:
            try:
                if versao_esperada is None:
                    novo.versao = 0
                    session.add(novo)
                    versao = 0
                else:
                    versao = versao_esperada + 1
                    campos = {cls._access_token: novo._access_token, cls._refresh_token: novo._refresh_token,
                              cls.expira_em: novo.expira_em, cls.renovacao_pendente: novo.renovacao_pendente,
                              cls.versao: versao, cls.atualizado_em: datetime.now(timezone.utc).replace(tzinfo=None)}
                    if not novo.renovacao_pendente:
                        campos[cls.ultima_renovacao_em] = datetime.now(timezone.utc).replace(tzinfo=None)
                    alterados = session.query(cls).filter_by(integracao='mercado_livre', client_id=client_id,
                                                            conta_id=conta_id, versao=versao_esperada).update(campos, synchronize_session=False)
                    if alterados != 1:
                        raise ValueError('Credenciais alteradas por outro processo; repita a leitura')
                session.commit()
                return versao
            except IntegrityError:
                session.rollback()
                raise ValueError('Credenciais já cadastradas por outro processo; repita a leitura') from None
