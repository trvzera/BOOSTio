"""Credenciais locais: arquivo privado, substituição atômica e lock por host."""
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path


class ArquivoMercadoLivreTokenRepository:
    def __init__(self, caminho):
        self.caminho = Path(caminho)

    @contextmanager
    def bloquear(self):
        try:
            import fcntl
        except ImportError:
            raise ValueError("O armazenamento OAuth requer Linux ou macOS") from None
        try:
            self.caminho.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            fd = os.open(str(self.caminho) + '.lock', os.O_CREAT | os.O_RDWR, 0o600)
            with os.fdopen(fd, 'a') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lock, fcntl.LOCK_UN)
        except OSError:
            raise ValueError("Não foi possível acessar o armazenamento OAuth do Mercado Livre") from None

    def ler(self):
        if not self.caminho.exists():
            return None
        try:
            dados = json.loads(self.caminho.read_text())
            if not isinstance(dados, dict):
                raise ValueError()
            return dados
        except (OSError, ValueError):
            raise ValueError("Armazenamento OAuth inválido; restaure as credenciais com segurança") from None

    def salvar(self, dados):
        temporario = None
        try:
            fd, temporario = tempfile.mkstemp(dir=self.caminho.parent, prefix='.meli-')
            with os.fdopen(fd, 'w') as arquivo:
                json.dump(dados, arquivo)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, self.caminho)
        except OSError:
            raise ValueError("Não foi possível persistir as credenciais OAuth do Mercado Livre") from None
        finally:
            if temporario and os.path.exists(temporario):
                os.unlink(temporario)


class MercadoLivreTokenRepository:
    """Adapter SQL; operações de persistência e concorrência pertencem ao model."""
    def __init__(self, client_id, conta_id):
        self.client_id, self.conta_id = client_id, conta_id
        self.versao = None
        self.lido = False

    @contextmanager
    def bloquear(self):
        # CAS no model reserva a renovação antes da rede, sem manter locks HTTP.
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
