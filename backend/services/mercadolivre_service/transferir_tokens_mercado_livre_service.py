import math
from pathlib import Path

from .token_mercado_livre_service import TokenMercadoLivreService
from repositories.mercado_livre_token_repository import ArquivoMercadoLivreTokenRepository


class TransferirTokensMercadoLivreService:
    def executar(self, arquivo, *, remover_arquivo=False):
        origem = ArquivoMercadoLivreTokenRepository(arquivo)
        destino = TokenMercadoLivreService().repository
        with origem.bloquear():
            dados = origem.ler()
            if not isinstance(dados, dict) or dados.get('renovacao_pendente'):
                raise ValueError('Arquivo ausente ou renovação inconclusiva')
            TokenMercadoLivreService._credencial(dados.get('access_token'))
            TokenMercadoLivreService._credencial(dados.get('refresh_token'))
            expiracao = dados.get('expires_at')
            if type(expiracao) not in (int, float) or not math.isfinite(expiracao):
                raise ValueError('Expiração inválida no arquivo')
            normalizado = {k: dados[k] for k in ('access_token', 'refresh_token', 'expires_at')}
            normalizado['renovacao_pendente'] = False
            with destino.bloquear():
                atual = destino.ler()
                if atual is not None and not self._mesmos(atual, normalizado):
                    raise ValueError('O banco já possui outro par de tokens; origem não será aplicada')
                transferido = atual is None
                if transferido:
                    destino.salvar(normalizado)
                if not self._mesmos(destino.ler(), normalizado):
                    raise ValueError('Não foi possível verificar a transferência')
                if remover_arquivo:
                    Path(arquivo).unlink()
        return {'transferidos': int(transferido), 'inalterados': int(not transferido),
                'arquivo_removido': remover_arquivo}


    @staticmethod
    def _mesmos(a, b):
        return (a is not None and all(a.get(k) == b.get(k) for k in
                ('access_token', 'refresh_token', 'renovacao_pendente'))
                and abs(a['expires_at'] - b['expires_at']) < 1)
