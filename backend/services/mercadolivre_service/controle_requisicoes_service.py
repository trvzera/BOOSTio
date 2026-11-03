import math
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime


class ErroMercadoLivre(ValueError):
    def __init__(self, status, retry_after=None):
        self.status = status
        self.espera = 0
        try:
            self.espera = max(0, float(retry_after))
        except (ValueError, TypeError):
            try:
                data = parsedate_to_datetime(retry_after)
                self.espera = max(0, (data - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
        super().__init__(f'Mercado Livre HTTP {status}; consulta não concluída')


class OrcamentoRequisicoesEsgotado(ValueError):
    pass


class ControleRequisicoesService:
    def __init__(self, limite=100, intervalo=1.0, dormir=time.sleep, relogio=time.monotonic, jitter=random.random):
        if type(limite) is not int or limite < 1 or type(intervalo) not in (int, float) or not math.isfinite(intervalo) or intervalo < 0.1:
            raise ValueError('Limite positivo e intervalo mínimo de 0,1 segundo são obrigatórios')
        self.limite, self.intervalo = limite, intervalo
        self.dormir, self.relogio, self.jitter = dormir, relogio, jitter
        self.total = 0
        self.ultima = None

    def executar(self, chamada):
        for tentativa in range(3):
            if self.total >= self.limite:
                raise OrcamentoRequisicoesEsgotado('Limite de requisições da execução atingido')
            if self.ultima is not None:
                self.dormir(max(0, self.intervalo - (self.relogio() - self.ultima)))
            self.total += 1
            self.ultima = self.relogio()
            try:
                return chamada()
            except ErroMercadoLivre as erro:
                if erro.status != 429 or tentativa == 2:
                    raise
                pausa = max(erro.espera, 2 ** tentativa + self.jitter())
                # Pausas maiores exigem nova execução; não ignorar Retry-After longo.
                if pausa > 60:
                    raise
                self.dormir(pausa)
