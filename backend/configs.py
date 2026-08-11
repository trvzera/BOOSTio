import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") #Sempre maiuscula, ate os nomes das variaveis se não o flask não reconhece
    SQLALCHEMY_DATABASE_URI = os.getenv("URL_DATABASE")
    
    MAIL_SERVER = 'smtp.gmail.com'        # endereço do servidor SMTP
    MAIL_PORT = 587                        # porta (587 = TLS, 465 = SSL, 25 = sem criptografia/raro hoje)
    MAIL_USE_TLS = True                    # criptografia via STARTTLS (usa com porta 587)
    MAIL_USE_SSL = False                   # criptografia via SSL direto (usa com porta 465) — nunca True junto com USE_TLS
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')      # seu email de envio
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')      # senha de app (não a senha normal)
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')  # remetente padrão, se não especificar em cada Message
    MAIL_MAX_EMAILS = None                 # limite de emails por conexão (None = sem limite)
    MAIL_SUPPRESS_SEND = False             # se True, NÃO envia de verdade (usado em testes automatizados)
    MAIL_ASCII_ATTACHMENTS = False         # força nomes de anexos em ASCII puro

class Desenvolvimento(Config):
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False


class Producao(Config):
    SESSION_COOKIE_SAMESITE = 'None'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

ambientes = {
    'producao': Producao,
    'desenvolvimento': Desenvolvimento
}