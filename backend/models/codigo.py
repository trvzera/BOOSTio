from . import db
from .base import ModeloBase
from datetime import datetime, timedelta, timezone

class Codigo(ModeloBase):
  __tablename__ = "codigo"

  usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"),nullable = False)
  codigo = db.Column(db.String(6),nullable = False)
  tentativas = db.Column(db.Integer, default=0, server_default="0", nullable=False)
  data_expiracao = db.Column(
    db.DateTime(timezone=True),
    default=lambda: datetime.now(timezone.utc) + timedelta(minutes=5)
)
  usado = db.Column(db.Boolean, default=False ,nullable = False)

  usuario = db.relationship('Usuario', backref='codigo')

  def marcar_como_usado(self):
    self.usado = True
    db.session.commit()

  def registrar_tentativa(self):
    atualizados = Codigo.query.filter(
      Codigo.id == self.id,
      Codigo.usado.is_(False),
      Codigo.tentativas < 5,
    ).update({Codigo.tentativas: Codigo.tentativas + 1}, synchronize_session=False)
    db.session.commit()
    return atualizados == 1

  def esta_expirado(self):
    expiracao = self.data_expiracao
    if expiracao.tzinfo is None:
      expiracao = expiracao.replace(tzinfo=timezone.utc)
    return expiracao <= datetime.now(timezone.utc)

  @staticmethod
  def buscar_codigo_recente(usuario_id:int):
    codigo = Codigo.query.filter_by(usuario_id = usuario_id,
      usado = False).order_by(Codigo.criado_em.desc()).first()
    
    return codigo

  @staticmethod
  def verificar_limite_envio(usuario_id: int):
    agora = datetime.now(timezone.utc)
    ultimo = Codigo.query.filter_by(usuario_id=usuario_id).order_by(Codigo.criado_em.desc()).first()
    if ultimo:
      criado_em = ultimo.criado_em
      if criado_em.tzinfo is None:
        criado_em = criado_em.replace(tzinfo=timezone.utc)
      if criado_em > agora - timedelta(seconds=30):
        raise ValueError("Aguarde 30 segundos antes de pedir outro código")

    enviados = Codigo.query.filter(
      Codigo.usuario_id == usuario_id,
      Codigo.criado_em >= agora - timedelta(hours=1),
    ).count()
    if enviados >= 5:
      raise ValueError("Limite de códigos por hora atingido. Tente novamente mais tarde")

  @staticmethod
  def deletar_codigos_usuario(usuario_id:int):
    Codigo.query.filter_by(usuario_id = usuario_id).delete()

    db.session.commit()
