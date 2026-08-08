import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") #Sempre maiuscula, ate os nomes das variaveis se não o flask não reconhece
    SQLALCHEMY_DATABASE_URI = os.getenv("URL_DATABASE")


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