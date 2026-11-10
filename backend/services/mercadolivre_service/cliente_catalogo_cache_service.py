import json
import hashlib
import time
from collections import OrderedDict
from copy import deepcopy
import requests
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService


class ClienteCatalogoCacheService(BuscarOfertasMercadoLivreService):
    def __init__(self, controle, *, simular=True, capacidade=128, validade=60, relogio=time.monotonic):
        self.sessao = requests.Session()
        super().__init__(controle, http=self.sessao)
        self.simular = simular
        self.capacidade, self.validade, self.relogio = capacidade, validade, relogio
        self.cache = OrderedDict()
        self.reaproveitadas = 0

    def _consultar(self, caminho, token, params=None):
        chave = (hashlib.sha256(token.encode()).hexdigest(), json.dumps([caminho, params], sort_keys=True))
        cacheavel = self.simular or caminho == '/products/search'
        registro = self.cache.get(chave) if cacheavel else None
        if registro and self.relogio() - registro[0] < self.validade:
            self.cache.move_to_end(chave)
            self.reaproveitadas += 1
            return deepcopy(registro[1])
        dados = super()._consultar(caminho, token, params)
        if cacheavel:
            self.cache[chave] = (self.relogio(), deepcopy(dados))
            self.cache.move_to_end(chave)
            while len(self.cache) > self.capacidade:
                self.cache.popitem(last=False)
        return dados

    def fechar(self):
        self.cache.clear()
        self.sessao.close()
