import base64
import hashlib
import json
import secrets
import time
from urllib.parse import urlencode, urlsplit

import requests
from flask import current_app

from models import AutorizacaoMercadoLivre
from .token_mercado_livre_service import TokenMercadoLivreService


class AutorizarContaMercadoLivreService:
    @staticmethod
    def hash(valor):
        if not isinstance(valor, str) or not 20 <= len(valor) <= 512 or any(c.isspace() for c in valor):
            raise ValueError('Autorização inválida')
        return hashlib.sha256(valor.encode()).hexdigest()

    def _config(self):
        client = TokenMercadoLivreService._credencial(current_app.config.get('MERCADO_LIVRE_CLIENT_ID'))
        conta = TokenMercadoLivreService._credencial(current_app.config.get('MERCADO_LIVRE_CONTA_ID'))
        api = str(current_app.config.get('API_PUBLIC_URL') or '').rstrip('/')
        redirect = current_app.config.get('MERCADO_LIVRE_REDIRECT_URI') or api + '/auth/mercadolivre/callback'
        url = urlsplit(redirect)
        if (url.scheme != 'https' or not url.hostname or url.username or url.password or url.query or url.fragment
                or url.path != '/auth/mercadolivre/callback' or url.netloc != urlsplit(api).netloc):
            raise ValueError('Configure API_PUBLIC_URL e MERCADO_LIVRE_REDIRECT_URI com callback HTTPS na API /auth/mercadolivre/callback')
        TokenMercadoLivreService._credencial(current_app.config.get('MERCADO_LIVRE_CLIENT_SECRET'))
        return client, conta, redirect

    def convite(self):
        config = self._config()
        segredo = secrets.token_urlsafe(32)
        AutorizacaoMercadoLivre.criar(self.hash(segredo), 'convite', *config)
        return config[2].removesuffix('/callback') + '/conectar#convite=' + segredo

    def iniciar(self, convite, navegador):
        config = self._config()
        AutorizacaoMercadoLivre.consumir(self.hash(convite), 'convite', *config)
        estado, verificador = secrets.token_urlsafe(32), secrets.token_urlsafe(64)
        AutorizacaoMercadoLivre.criar(self.hash(estado), 'estado', *config,
            navegador_hash=self.hash(navegador), verificador=verificador)
        desafio = base64.urlsafe_b64encode(hashlib.sha256(verificador.encode()).digest()).rstrip(b'=').decode()
        return 'https://auth.mercadolivre.com.br/authorization?' + urlencode(dict(
            response_type='code', client_id=config[0], redirect_uri=config[2], state=estado,
            code_challenge=desafio, code_challenge_method='S256'))

    def concluir(self, estado, navegador, codigo, *, recusado=False):
        config = self._config()
        verificador = AutorizacaoMercadoLivre.consumir(self.hash(estado), 'estado', *config,
            navegador_hash=self.hash(navegador))
        if recusado:
            raise ValueError('Autorização recusada; nenhum token alterado')
        if not isinstance(codigo, str) or not 1 <= len(codigo) <= 2048 or any(c.isspace() for c in codigo):
            raise ValueError('Código de autorização ausente ou inválido; gere outro convite')
        repository = TokenMercadoLivreService().repository
        with repository.bloquear():
            repository.ler()
            inicio = time.time()
            dados = self._trocar(dict(grant_type='authorization_code', client_id=config[0],
                client_secret=current_app.config['MERCADO_LIVRE_CLIENT_SECRET'], code=codigo,
                redirect_uri=config[2], code_verifier=verificador))
            if str(dados.get('user_id')) != config[1]:
                raise ValueError('A conta autorizada difere de MERCADO_LIVRE_CONTA_ID; nenhum token local alterado')
            access = TokenMercadoLivreService._credencial(dados.get('access_token'))
            refresh = TokenMercadoLivreService._credencial(dados.get('refresh_token'))
            duracao = dados.get('expires_in')
            if type(duracao) is not int or not 60 < duracao <= 31536000 or str(dados.get('token_type','')).lower() != 'bearer':
                raise ValueError('Resposta de autorização inválida; gere outro convite')
            repository.salvar(dict(access_token=access, refresh_token=refresh,
                expires_at=inicio + duracao, renovacao_pendente=False))
        return {'conectado': True}

    @staticmethod
    def _trocar(parametros):
        from services.marketplace_service.controle_requisicoes_service import executar_requisicao
        executar_requisicao(lambda: None)
        try:
            resposta = requests.post('https://api.mercadolibre.com/oauth/token', data=parametros,
                headers={'Accept': 'application/json'}, timeout=(10,30), stream=True, allow_redirects=False)
            try:
                if resposta.status_code != 200:
                    raise ValueError(f'Mercado Livre OAuth HTTP {resposta.status_code}; gere uma nova autorização')
                if resposta.headers.get('Content-Type','').split(';')[0].strip().lower() != 'application/json':
                    raise ValueError('Resposta OAuth não é JSON')
                partes, tamanho = [], 0
                for bloco in resposta.iter_content(8192):
                    tamanho += len(bloco)
                    if tamanho > 65536:
                        raise ValueError('Resposta OAuth excedeu o tamanho permitido')
                    partes.append(bloco)
                try:
                    dados = json.loads(b''.join(partes))
                except (ValueError, UnicodeError):
                    raise ValueError('Resposta OAuth inválida') from None
                if not isinstance(dados, dict):
                    raise ValueError('Resposta OAuth inválida')
                return dados
            finally:
                resposta.close()
        except requests.RequestException:
            raise ValueError('Falha de rede na autorização; gere outro convite, sem reutilizar o código') from None
