from flask_mail import Message
from models import mail
from models import Codigo,Usuario
import random

class EnviarRecuperarSenha:
    def executar(self,dados:dict):
        
        usuario = Usuario.buscar_por_id(dados["id"])
        if not usuario:
            raise ValueError("Esse usuario não existe")

        codigo = self._gerar_codigo()


        msg = Message(
        subject='Confirme seu email - BOOSTio',
        recipients=[dados["email"]])

        msg.body = f'Seu código de verificação é: {codigo}'
        msg.html = f'''
            <div style="font-family: Arial, sans-serif;">
                <h2>Confirme seu email</h2>
                <p>Seu código de verificação é:</p>
                <h1 style="letter-spacing: 4px;">{codigo}</h1>
                <p>Esse código expira em 5 minutos.</p>
            </div>
        '''
        mail.send(msg)


    @staticmethod
    def _gerar_codigo():
        return random.randint(1000,9999)