"""Auditoria da descoberta; sem credenciais ou respostas HTTP completas."""
from datetime import datetime, timezone
from . import db, ModeloBase


class ExecucaoDescoberta(ModeloBase):
    __tablename__ = 'execucao_descoberta'
    loja = db.Column(db.String(20), nullable=False, default='mercado_livre')
    parametros = db.Column(db.JSON, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='executando')
    resumo = db.Column(db.JSON, nullable=True)
    encerrada_em = db.Column(db.DateTime, nullable=True)
    __table_args__ = (
        db.CheckConstraint("status IN ('executando','concluida','interrompida')", name='ck_descoberta_status'),
        db.Index('ix_descoberta_status_data', 'status', 'criado_em'),
    )

    @classmethod
    def iniciar(cls, parametros):
        registro = cls(parametros=parametros)
        db.session.add(registro)
        db.session.commit()
        return registro.id

    @classmethod
    def finalizar(cls, identificador, resumo):
        registro = db.session.get(cls, identificador)
        registro.status = 'interrompida' if resumo['interrompido'] else 'concluida'
        registro.resumo = resumo
        registro.encerrada_em = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
