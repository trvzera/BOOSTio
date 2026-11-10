from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from . import db, ModeloBase, TokenIntegracao


class AutorizacaoMercadoLivre(ModeloBase):
    __tablename__ = 'autorizacao_mercado_livre'
    segredo_hash = db.Column(db.String(64), nullable=False, unique=True)
    tipo = db.Column(db.String(12), nullable=False)
    client_id = db.Column(db.String(80), nullable=False)
    conta_id = db.Column(db.String(80), nullable=False)
    redirect_uri = db.Column(db.Text, nullable=False)
    navegador_hash = db.Column(db.String(64), nullable=True)
    verificador_cifrado = db.Column(db.Text, nullable=True)
    expira_em = db.Column(db.DateTime, nullable=False)
    consumido = db.Column(db.Boolean, nullable=False, default=False)

    @classmethod
    def criar(cls, segredo_hash, tipo, client_id, conta_id, redirect_uri, *, navegador_hash=None, verificador=None):
        cifrado = TokenIntegracao._cifra().encrypt(verificador.encode()).decode() if verificador else None
        with Session(db.engine) as sessao:
            sessao.add(cls(segredo_hash=segredo_hash, tipo=tipo, client_id=client_id, conta_id=conta_id,
                redirect_uri=redirect_uri, navegador_hash=navegador_hash, verificador_cifrado=cifrado,
                expira_em=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=10)))
            sessao.commit()

    @classmethod
    def consumir(cls, segredo_hash, tipo, client_id, conta_id, redirect_uri, *, navegador_hash=None):
        with Session(db.engine) as sessao:
            consulta = sessao.query(cls).filter_by(segredo_hash=segredo_hash, tipo=tipo, client_id=client_id,
                conta_id=conta_id, redirect_uri=redirect_uri, navegador_hash=navegador_hash, consumido=False)
            consulta = consulta.filter(cls.expira_em > datetime.now(timezone.utc).replace(tzinfo=None))
            if consulta.update({cls.consumido: True}, synchronize_session=False) != 1:
                sessao.rollback()
                raise ValueError('Link ou autorização inválida, expirada ou já utilizada; gere outro convite no terminal')
            obj = sessao.query(cls).filter_by(segredo_hash=segredo_hash).one()
            cifrado = obj.verificador_cifrado
            sessao.commit()
        if cifrado:
            from cryptography.fernet import InvalidToken
            try:
                return TokenIntegracao._cifra().decrypt(cifrado.encode()).decode()
            except (InvalidToken, UnicodeError):
                raise ValueError('Não foi possível recuperar a autorização; gere outro convite') from None
        return None
