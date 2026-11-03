import math
import time
from datetime import datetime, timezone

from flask import current_app
from models import Oferta, TokenIntegracao
from .token_mercado_livre_service import TokenMercadoLivreService


class ValidarIntegracaoMercadoLivreService:
    def executar(self):
        for campo in ('MERCADO_LIVRE_CLIENT_ID', 'MERCADO_LIVRE_CLIENT_SECRET', 'MERCADO_LIVRE_CONTA_ID'):
            try:
                TokenMercadoLivreService._credencial(current_app.config.get(campo))
            except ValueError:
                raise ValueError(f'Configure {campo} no ambiente da API') from None
        TokenIntegracao._cifra()
        Oferta.verificar_esquema_mercado_livre()
        dados = TokenIntegracao.ler_estado(current_app.config['MERCADO_LIVRE_CLIENT_ID'],
                                          current_app.config['MERCADO_LIVRE_CONTA_ID'])
        if dados is None:
            raise ValueError('Cadastre os tokens com mercadolivre-tokens-configurar')
        if dados.get('renovacao_pendente'):
            raise ValueError('Renovação anterior inconclusiva; reautorize e registre o novo par de tokens')
        validade = dados.get('expires_at')
        if type(validade) not in (float, int) or not math.isfinite(validade):
            raise ValueError('Validade de token inválida')
        return {'pronto': True, 'renovacao_necessaria': validade <= time.time() + 60,
                'expira_em': datetime.fromtimestamp(validade, timezone.utc).isoformat(timespec='seconds')}
