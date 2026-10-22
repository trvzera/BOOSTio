from urllib.parse import urlsplit

from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix


class ConfigurarAcessoService:
  def executar(self, app, producao=False):
    frontend = self._validar_url(app.config.get("FRONTEND_URL"), "FRONTEND_URL", producao)
    api = app.config.get("API_PUBLIC_URL")
    if api or producao:
      api = self._validar_url(api, "API_PUBLIC_URL", producao)
      app.config["API_PUBLIC_URL"] = api
      app.config["GOOGLE_REDIRECT_URI"] = f"{api}/auth/google/entrar"
      if producao:
        app.config["TRUSTED_HOSTS"] = [urlsplit(api).hostname]
    app.config["FRONTEND_URL"] = frontend

    origens = app.config.get("CORS_ORIGINS")
    if origens:
      origens = [self._validar_origem(item.strip(), producao) for item in origens.split(",")]
    elif producao:
      partes = urlsplit(frontend)
      origens = [f"{partes.scheme}://{partes.netloc}"]
    else:
      origens = [f"http://{host}:{porta}" for host in ("localhost", "127.0.0.1") for porta in (5500, 5501)]
    CORS(app, supports_credentials=True, origins=origens, expose_headers=["Retry-After"],
         allow_headers=["Content-Type", "X-CSRF-Token"])

    hops = app.config.get("TRUSTED_PROXY_HOPS", 0)
    proto_hops = app.config.get("TRUSTED_PROXY_PROTO_HOPS", 0)
    if any(not isinstance(valor, int) or valor < 0 for valor in (hops, proto_hops)):
      raise ValueError("As quantidades de proxies confiáveis devem ser inteiros não negativos")
    if hops or proto_hops:
      app.wsgi_app = ProxyFix(app.wsgi_app, x_for=hops, x_proto=proto_hops,
                             x_host=0, x_port=0, x_prefix=0)
    if app.config.get("SESSION_COOKIE_SAMESITE") not in ("Lax", "Strict", "None"):
      raise ValueError("SESSION_COOKIE_SAMESITE deve ser Lax, Strict ou None")

  def _validar_url(self, valor, nome, producao):
    if not isinstance(valor, str) or not valor.strip():
      raise ValueError(f"Configure {nome} com o endereço público")
    valor = valor.strip().rstrip("/")
    partes = urlsplit(valor)
    if (partes.scheme not in ("http", "https") or not partes.hostname
        or partes.username or partes.password or partes.query or partes.fragment
        or any(c.isspace() for c in valor)):
      raise ValueError(f"{nome} deve ser uma URL HTTP(S), sem credenciais, parâmetros ou fragmento")
    if producao and (partes.scheme != "https" or partes.hostname in ("localhost", "127.0.0.1", "::1")):
      raise ValueError(f"{nome} deve usar HTTPS e um domínio público em produção")
    return valor

  def _validar_origem(self, valor, producao):
    origem = self._validar_url(valor, "CORS_ORIGINS", producao)
    if urlsplit(origem).path:
      raise ValueError("CORS_ORIGINS aceita apenas protocolo, domínio e porta, sem caminho")
    return origem
