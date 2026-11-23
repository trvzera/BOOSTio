from contextlib import contextmanager


class MercadoLivreTokenRepository:
    def __init__(self, client_id, conta_id):
        self.client_id, self.conta_id = client_id, conta_id
        self.versao = None
        self.lido = False

    @contextmanager
    def bloquear(self):
        self.lido = False
        yield

    def ler(self):
        from models import TokenIntegracao
        dados = TokenIntegracao.ler_estado(self.client_id, self.conta_id)
        self.versao = dados.pop('versao') if dados else None
        self.lido = True
        return dados

    def salvar(self, dados):
        from models import TokenIntegracao
        if not self.lido:
            raise ValueError('Leia as credenciais antes de alterá-las')
        self.versao = TokenIntegracao.gravar_estado(self.client_id, self.conta_id, dados, self.versao)
