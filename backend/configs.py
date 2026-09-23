import os
from dotenv import load_dotenv
from authlib.integrations.flask_client import OAuth


load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) #pasta backend/, usada para resolver o caminho do sqlite independente de onde o app é executado

def resolver_uri_banco(uri):
    #Caminho relativo do sqlite (ex: sqlite:///../database/banco.db) é resolvido pelo sqlite3 com base no cwd do processo, não no instance_path do Flask.
    #Por isso convertemos para um caminho absoluto baseado neste arquivo, e garantimos que a pasta exista (o sqlite não cria diretórios sozinho).
    if uri and uri.startswith("sqlite:///") and not uri.startswith("sqlite:////"):
        caminho_relativo = uri[len("sqlite:///"):]
        caminho_absoluto = os.path.normpath(os.path.join(BASE_DIR, caminho_relativo))
        os.makedirs(os.path.dirname(caminho_absoluto), exist_ok=True)
        return f"sqlite:///{caminho_absoluto}"
    return uri

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") #Sempre maiuscula, ate os nomes das variaveis se não o flask não reconhece
    SQLALCHEMY_DATABASE_URI = resolver_uri_banco(os.getenv("URL_DATABASE"))
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://127.0.0.1:5500/frontend") #Base usada para montar links enviados por email (ex: recuperar senha)
    
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


#Login google

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