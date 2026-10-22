from . import db
from .base import ModeloBase
from datetime import datetime, timedelta, timezone

class Codigo(ModeloBase):
  __tablename__ = "codigo"

  usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"),nullable = False)
  codigo = db.Column(db.String(6),nullable = False)
  email_destino = db.Column(db.String(150), nullable=True)
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

  @staticmethod
  def invalidar_anteriores(usuario_id):
    # A transação é concluída por quem altera o email ou emite o novo código.
    Codigo.query.filter_by(usuario_id=usuario_id, usado=False).update(
      {Codigo.usado: True}, synchronize_session=False,
    )

  @staticmethod
  def emitir(usuario_id, email_destino, codigo):
    from .usuario import Usuario
    # Serializa emissão, confirmação e troca de email pela linha do usuário.
    atualizados = Usuario.query.filter_by(
      id=usuario_id, email=email_destino, ativo=True, verificado=False,
    ).update({Usuario.verificado: False}, synchronize_session=False)
    if atualizados != 1:
      db.session.rollback()
      raise ValueError("Email alterado ou já confirmado. Solicite outro código")
    try:
      Codigo.verificar_limite_envio(usuario_id)
    except ValueError:
      db.session.rollback()
      raise
    Codigo.invalidar_anteriores(usuario_id)
    novo = Codigo(usuario_id=usuario_id, email_destino=email_destino, codigo=codigo)
    db.session.add(novo)
    db.session.commit()
    return novo

  def confirmar_email(self):
    from .usuario import Usuario
    atualizados = Usuario.query.filter_by(
      id=self.usuario_id, email=self.email_destino, ativo=True, verificado=False,
    ).update({Usuario.verificado: True}, synchronize_session=False)
    consumidos = Codigo.query.filter(
      Codigo.id == self.id, Codigo.usado.is_(False),
      Codigo.email_destino.is_not(None),
      Codigo.data_expiracao > datetime.now(timezone.utc),
    ).update({Codigo.usado: True}, synchronize_session=False)
    if atualizados != 1 or consumidos != 1:
      db.session.rollback()
      raise ValueError("Código inválido ou expirado. Solicite outro código")
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
    codigo = Codigo.query.filter_by(usuario_id=usuario_id).order_by(Codigo.id.desc()).first()
    
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
