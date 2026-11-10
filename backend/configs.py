import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def resolver_uri_banco(uri):
    if uri and uri.startswith("sqlite:///") and not uri.startswith("sqlite:////"):
        caminho_relativo = uri[len("sqlite:///"):]
        caminho_absoluto = os.path.normpath(os.path.join(BASE_DIR, caminho_relativo))
        os.makedirs(os.path.dirname(caminho_absoluto), exist_ok=True)
        return f"sqlite:///{caminho_absoluto}"
    return uri

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    MAX_CONTENT_LENGTH = 64 * 1024
    MAX_FORM_MEMORY_SIZE = 16 * 1024
    MAX_FORM_PARTS = 20
    TRUSTED_PROXY_HOPS = int(os.getenv("TRUSTED_PROXY_HOPS", "0"))
    TRUSTED_PROXY_PROTO_HOPS = int(os.getenv("TRUSTED_PROXY_PROTO_HOPS", "0"))
    API_PUBLIC_URL = os.getenv("API_PUBLIC_URL")
    INTEGRACOES_TOKEN_CHAVE = os.getenv("INTEGRACOES_TOKEN_CHAVE")
    MERCADO_LIVRE_CONTA_ID = os.getenv("MERCADO_LIVRE_CONTA_ID")
    MERCADO_LIVRE_REDIRECT_URI = os.getenv("MERCADO_LIVRE_REDIRECT_URI")
    MERCADO_LIVRE_CLIENT_ID = os.getenv("MERCADO_LIVRE_CLIENT_ID")
    MERCADO_LIVRE_CLIENT_SECRET = os.getenv("MERCADO_LIVRE_CLIENT_SECRET")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS")
    SQLALCHEMY_DATABASE_URI = resolver_uri_banco(os.getenv("URL_DATABASE"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500/frontend")
    
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.hostinger.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '465'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'false').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'true').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    MAIL_MAX_EMAILS = None
    MAIL_SUPPRESS_SEND = False
    MAIL_ASCII_ATTACHMENTS = False

    CATALOGO_CACHE_SEGUNDOS = 0

class Desenvolvimento(Config):
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    RATELIMIT_STORAGE_URI = "memory://"


class Producao(Config):
    FRONTEND_URL = os.getenv("FRONTEND_URL")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI")
    CATALOGO_CACHE_SEGUNDOS = int(os.getenv("CATALOGO_CACHE_SEGUNDOS", "60"))

ambientes = {
    'producao': Producao,
    'desenvolvimento': Desenvolvimento
}


oauth = OAuth()

def configurar_oauth(app):
    oauth.init_app(app)
    oauth.register(
        name="google",
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
