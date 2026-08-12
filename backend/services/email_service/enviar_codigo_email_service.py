from flask_mail import Message
from models import Codigo,mail,Usuario
from utils.validacoes import validacao_campos
import random


class EnviarEmailService:
  def executar(self,usuario_id:int):
    if not usuario_id:
      raise ValueError("Id do usuario invalido")

    usuario = Usuario.buscar_por_id(usuario_id)

    if not usuario:
      raise ValueError("Nenhum usuario encontrado")
    
    msg = Message(
        subject='Confirme seu email - BOOSTio',
        recipients=[usuario.email], 
    )

    codigo = self._gerar_codigo()
    self._monta_mensagem(msg,codigo)

    mail.send(msg)

    codigo = Codigo(
      usuario_id = usuario.id,
      codigo = codigo
    )

    codigo.salvar()

    return True

  @staticmethod
  def _gerar_codigo():
    return str(random.randint(1000,9999))

  @staticmethod
  def _monta_mensagem(msg:Message,codigo:str):
    msg.body = f'Seu código de verificação é: {codigo}'
    msg.html = f'''
        <div style="font-family: Arial, sans-serif;">
            <h2>Confirme seu email</h2>
            <p>Seu código de verificação é:</p>
            <h1 style="letter-spacing: 4px;">{codigo}</h1>
            <p>Esse código expira em 5 minutos.</p>
        </div>
    '''