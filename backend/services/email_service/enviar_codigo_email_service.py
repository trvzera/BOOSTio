from flask_mail import Message
from models import Codigo,mail,Usuario
from utils.validacoes import validacao_campos
import random


class EnviarEmailService:
  def executar(self,usuario:Usuario):
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
        <div style="font-family: Arial, sans-serif; background-color:#1c1c1e; padding: 32px; border-radius: 16px; max-width: 480px; margin: 0 auto; border: 1px solid #3a3a3c;">
  <img src="https://github.com/trvzera/BOOSTio/blob/main/frontend/imgs/logo.webp?raw=true" alt="BOOSTio" width="140" height="30" style="display:block; margin: 0 auto 24px auto;">
  <h2 style="color:#ffffff; text-align:center;">Confirme seu email</h2>
  <p style="color:#8e8e93; text-align:center;">Seu código de verificação é:</p>
  <div style="text-align:center; margin: 16px 0;">
    <span style="display:inline-block; background-color:#000000; border: 1px solid #007bff; border-radius: 12px; padding: 12px 28px;">
      <h1 style="letter-spacing: 4px; color:#ffffff; margin:0; font-size:28px;">{codigo}</h1>
    </span>
  </div>
  <p style="color:#696969; text-align:center; font-size:13px;">Esse código expira em <strong style="color:#8e8e93;">5 minutos</strong>.</p>
</div>
    '''