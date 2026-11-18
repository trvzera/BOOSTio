import hashlib
import hmac

from . import db


class FatorAdmin(db.Model):
    __tablename__ = "fator_admin"
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    segredo_cifrado = db.Column(db.LargeBinary, nullable=False)
    sessao_hash = db.Column(db.String(64), nullable=True)
    ultimo_intervalo = db.Column(db.BigInteger, nullable=False)

    @staticmethod
    def hash_sessao(token):
        return hashlib.sha256(token.encode("ascii")).hexdigest()

    @classmethod
    def sessao_valida(cls, usuario_id, token):
        if not isinstance(token, str) or len(token) != 64 or not token.isascii():
            return False
        fator = db.session.get(cls, usuario_id)
        return bool(fator and fator.sessao_hash and hmac.compare_digest(fator.sessao_hash, cls.hash_sessao(token)))
