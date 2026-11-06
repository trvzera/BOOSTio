from services.marketplace_service.controle_requisicoes_service import controle_em_execucao, executar_requisicao
from services.marketplace_service.erros import FalhaMarketplace, FilaAguardando
import json
import math
import time

import requests
from flask import current_app

from repositories.mercado_livre_token_repository import MercadoLivreTokenRepository


class TokenMercadoLivreService:
    def __init__(self, repository=None, relogio=None):
        self.repository = repository or MercadoLivreTokenRepository(
            self._credencial(current_app.config.get('MERCADO_LIVRE_CLIENT_ID')),
            self._credencial(current_app.config.get('MERCADO_LIVRE_CONTA_ID')))
        self.relogio = relogio or time.time

    def executar(self):
        try:
            return self._executar()
        except (FilaAguardando, FalhaMarketplace):
            raise
        except ValueError:
            controle = controle_em_execucao.get()
            if controle is not None:
                controle.erro = FalhaMarketplace(401)
                raise controle.erro from None
            raise

    def _executar(self):
        with self.repository.bloquear():
            dados = self.repository.ler()
            if dados is None:
                raise ValueError('Cadastre os tokens no banco com mercadolivre-tokens-configurar ou transfira o arquivo')
            if dados.get('renovacao_pendente'):
                raise ValueError('Renovação OAuth anterior inconclusiva; reautorize a aplicação antes de repetir')
            expires = dados.get('expires_at')
            if type(expires) not in (int, float) or not math.isfinite(expires):
                raise ValueError('Validade OAuth armazenada inválida')
            if expires > self.relogio() + 60:
                return self._credencial(dados.get('access_token'))
            return self._renovar(dados)

    def _renovar(self, dados):
        refresh = self._credencial(dados.get('refresh_token'))
        client_id = self._credencial(current_app.config.get('MERCADO_LIVRE_CLIENT_ID'))
        secret = self._credencial(current_app.config.get('MERCADO_LIVRE_CLIENT_SECRET'))
        inicio = self.relogio()
        executar_requisicao(lambda: None)
        # Refresh tokens são de uso único. Após resultado incerto, não repetir às cegas.
        self.repository.salvar({**dados, 'renovacao_pendente': True})
        try:
            resposta = requests.post(
                'https://api.mercadolibre.com/oauth/token',
                data={'grant_type': 'refresh_token', 'client_id': client_id,
                      'client_secret': secret, 'refresh_token': refresh},
                headers={'Accept': 'application/json'}, timeout=(10, 30),
                stream=True, allow_redirects=False,
            )
            try:
                if resposta.status_code != 200:
                    raise ValueError(f'Mercado Livre OAuth HTTP {resposta.status_code}; verifique credenciais ou reautorize')
                if resposta.headers.get('Content-Type', '').split(';')[0].strip().lower() != 'application/json':
                    raise ValueError('Resposta OAuth não é JSON')
                partes, tamanho = [], 0
                for bloco in resposta.iter_content(8192):
                    tamanho += len(bloco)
                    if tamanho > 65536:
                        raise ValueError('Resposta OAuth excedeu o tamanho permitido')
                    partes.append(bloco)
                try:
                    novo = json.loads(b''.join(partes))
                except (ValueError, UnicodeDecodeError):
                    raise ValueError('Resposta OAuth inválida') from None
            finally:
                resposta.close()
        except requests.RequestException:
            raise ValueError('Falha de rede ao renovar OAuth; resultado incerto, reautorize antes de repetir') from None
        if not isinstance(novo, dict):
            raise ValueError('Resposta OAuth inválida')
        access = self._credencial(novo.get('access_token'))
        refresh = self._credencial(novo.get('refresh_token'))
        duracao = novo.get('expires_in')
        tipo = novo.get('token_type')
        if type(duracao) is not int or duracao <= 60 or not isinstance(tipo, str) or tipo.lower() != 'bearer':
            raise ValueError('Validade ou tipo de token OAuth inválido')
        self.repository.salvar({'access_token': access, 'refresh_token': refresh,
                                'expires_at': inicio + duracao, 'renovacao_pendente': False})
        return access

    @staticmethod
    def _credencial(valor):
        if not isinstance(valor, str) or not valor.strip() or any(c.isspace() for c in valor):
            raise ValueError('Credenciais OAuth do Mercado Livre ausentes ou inválidas')
        return valor
