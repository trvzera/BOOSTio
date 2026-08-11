from flask_mail import Message
from models import mail
from models import Codigo
import random


class EnviarEmailService:
  def executar(self,usuario):
    #Email ja vai estar validado pela funcao de cadastrar usuario,logo nao te necessidade de validar novamente
    
    msg = Message(
        subject='Confirme seu email - BOOSTio',
        recipients=[usuario.email], 
    )

    codigo = self._gerar_codigo()


    msg.body = f'Seu código de verificação é: {codigo}'
    msg.html = f'''
        <div style="font-family: Arial, sans-serif;">
            <h2>Confirme seu email</h2>
            <p>Seu código de verificação é:</p>
            <h1 style="letter-spacing: 4px;">{codigo}</h1>
            <p>Esse código expira em 10 minutos.</p>
        </div>
    '''
    mail.send(msg)

    codigo = Codigo(
      usuario_id = usuario.id,
      codigo = codigo
    )

    codigo.salvar()

    return True

  @staticmethod
  def _gerar_codigo():
    return random.randint(1000,9999)
