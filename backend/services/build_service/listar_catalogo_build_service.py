import time
from threading import Lock

from flask import current_app

from models import Oferta
from models.modelos_pecas import MODELOS_PECAS

_guardado = {"catalogo": None, "ate": 0.0}
_trava = Lock()


class ListarCatalogoBuildService:
    def executar(self):
        segundos = current_app.config.get("CATALOGO_CACHE_SEGUNDOS", 0)
        if not segundos:
            return self._montar()
        with _trava:
            if _guardado["catalogo"] is None or time.monotonic() >= _guardado["ate"]:
                _guardado["catalogo"] = self._montar()
                _guardado["ate"] = time.monotonic() + segundos
            return _guardado["catalogo"]

    @staticmethod
    def limpar_cache():
        with _trava:
            _guardado["catalogo"] = None

    @staticmethod
    def _montar():
        return Oferta.anexar_a_catalogo([peca.to_catalogo() for modelo in MODELOS_PECAS for peca in modelo.listar_publicadas()])
