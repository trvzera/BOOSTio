from flask_mail import Message
from models import mail
from smtplib import SMTPException, SMTPAuthenticationError, SMTPRecipientsRefused
import random


class EnviarEmailService:
  def executar(self,dados:dict):
    #Email ja vai estar validado pela funcao de cadastrar usuario,logo nao te necessidade de validar novamente
    
    msg = Message(
        subject='Confirme seu email - BOOSTio',
        recipients=[dados.get("email")],       # lista, pode ter vários(Quem recebe)
    )

    codigo = self._gerar_codigo()

    #Falta salvar no banco o codigo
    msg.body = f'Seu código de verificação é: {codigo}'
    msg.html = f'''
        <div style="font-family: Arial, sans-serif;">
            <h2>Confirme seu email</h2>
            <p>Seu código de verificação é:</p>
            <h1 style="letter-spacing: 4px;">{codigo}</h1>
            <p>Esse código expira em 10 minutos.</p>
        </div>
    '''
    #Se der erro lanca uma execao lembrar de tratar na controllers
    mail.send(msg)

    # except SMTPAuthenticationError:
    #     raise ValueError('Falha na autenticação do servidor de email')
    # except SMTPRecipientsRefused:
    #     raise ValueError('Endereço de email do destinatário foi recusado')
    # except SMTPException as erro:
    #     raise ValueError(f'Erro ao enviar email: {str(erro)}')

  @staticmethod
  def _gerar_codigo():
    return random.randint(1000,9999)
