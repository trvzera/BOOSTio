"""Agendamento e checkpoint duráveis, separados do processo da API."""
from datetime import datetime, timezone
from . import db, ModeloBase
from utils.identidade_peca import assinatura_documento


class EstadoCatalogo(ModeloBase):
    __tablename__='estado_catalogo'
    nome=db.Column(db.String(80),nullable=False,unique=True)
    assinatura_plano=db.Column(db.String(64),nullable=False)
    fase=db.Column(db.String(20),nullable=False,default='descoberta')
    cursor_descoberta=db.Column(db.JSON,nullable=True)
    cursor_fila=db.Column(db.Integer,nullable=False,default=0)
    proxima_execucao=db.Column(db.DateTime,nullable=False,default=lambda:datetime.now(timezone.utc).replace(tzinfo=None))
    tentativas=db.Column(db.Integer,nullable=False,default=0)
    ultimo_resumo=db.Column(db.JSON,nullable=True)
    __table_args__=(db.CheckConstraint("fase IN ('descoberta','classificacao','enriquecimento','importacao')",name='ck_estado_catalogo_fase'),
                   db.Index('ix_catalogo_agenda','proxima_execucao'))

    @classmethod
    def obter(cls, plano, *, simular=False):
        registro=cls.query.filter_by(nome=plano['nome']).first()
        assinatura=assinatura_documento(plano)
        if registro is None:
            registro=cls(nome=plano['nome'],assinatura_plano=assinatura,fase='descoberta',cursor_fila=0,tentativas=0,
                         proxima_execucao=datetime.now(timezone.utc).replace(tzinfo=None))
            if not simular:registro.salvar()
        if registro.assinatura_plano!=assinatura:
            raise ValueError('Plano mudou: use outro nome de trabalho para não reutilizar cursor incompatível')
        return registro

    def registrar_progresso(self, **campos):
        for chave,valor in campos.items():setattr(self,chave,valor)
        db.session.commit()


    @classmethod
    def reiniciar(cls, plano):
        registro=cls.query.filter_by(nome=plano['nome']).first()
        if registro is None:return cls.obter(plano)
        registro.registrar_progresso(assinatura_plano=assinatura_documento(plano),fase='descoberta',cursor_descoberta=None,
            cursor_fila=0,tentativas=0,proxima_execucao=datetime.now(timezone.utc).replace(tzinfo=None),ultimo_resumo={'reiniciado':True})
        return registro
