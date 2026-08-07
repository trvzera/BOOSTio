import os
from dotenv import load_dotenv

class Config:
    secret_key = os.getenv("SECRET_KEY")
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