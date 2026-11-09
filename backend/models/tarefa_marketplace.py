"""Fila durável; a chave impede duplicação e a reserva permite recuperar crashes."""
from datetime import datetime, timezone
from . import db, ModeloBase
from sqlalchemy.dialects.mysql import DATETIME

DATA_PRECISA = db.DateTime().with_variant(DATETIME(fsp=6), 'mysql')


def _agora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class TarefaMarketplace(ModeloBase):
    __tablename__ = 'tarefa_marketplace'
    loja = db.Column(db.String(20), nullable=False)
    chave = db.Column(db.String(64), nullable=False)
    tipo = db.Column(db.String(40), nullable=False)
    dados = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pendente')
    disponivel_em = db.Column(DATA_PRECISA, nullable=False, default=_agora)
    reserva = db.Column(db.String(32), nullable=True)
    tentativas = db.Column(db.Integer, nullable=False, default=0)
    resultado = db.Column(db.JSON, nullable=True)
    erro = db.Column(db.String(120), nullable=True)
    __table_args__ = (
        db.UniqueConstraint('loja', 'chave', name='uq_tarefa_marketplace_chave'),
        db.CheckConstraint("status IN ('pendente','executando','concluida','falhou','bloqueada','cancelada')", name='ck_tarefa_marketplace_status'),
        db.Index('ix_tarefa_marketplace_fila', 'loja', 'status', 'disponivel_em', 'id'),
    )


class LimiteMarketplace(ModeloBase):
    __tablename__ = 'limite_marketplace'
    loja = db.Column(db.String(20), nullable=False, unique=True)
    proxima_requisicao = db.Column(DATA_PRECISA, nullable=False, default=_agora)
    pausado_ate = db.Column(DATA_PRECISA, nullable=False, default=_agora)
    bloqueado = db.Column(db.Boolean, nullable=False, default=False)
    limitacoes = db.Column(db.Integer, nullable=False, default=0)
