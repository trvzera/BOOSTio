import re

from utils.sockets import normalizar_socket
from .preferencias_perifericos_service import PreferenciasPerifericosService


class PreferenciasProcessadorService:

    @staticmethod
    def marca(peca, preferencia):
        return (preferencia in ("intel", "amd")
                and str(peca.get("fabricante") or "").strip().casefold() == preferencia)

    @staticmethod
    def ryzen(peca):
        return (str(peca.get("fabricante") or "").strip().casefold() == "amd"
                and bool(re.search(r"\bryzen\b", str(peca.get("modelo") or ""), re.I)))

    @classmethod
    def destaques(cls, pecas, utilidade, preferencia=None):
        if preferencia == "sem-preferencia" or (preferencia is None and not PreferenciasPerifericosService.jogos(utilidade)):
            return []
        preferidas = [p for p in pecas if (cls.marca(p, preferencia) if preferencia else cls.ryzen(p))]
        preferidas.sort(key=lambda p: (p["preco"], p["id"]))
        if not preferidas:
            return []
        escolhidas = {}
        for peca in preferidas:
            socket = normalizar_socket(peca.get("soquete"))
            if socket and socket not in escolhidas:
                escolhidas[socket] = peca

        extras = [preferidas[0], preferidas[len(preferidas) // 2], preferidas[-1]]
        return list({p["id"]: p for p in [*escolhidas.values(), *extras]}.values())[:4]

    @classmethod
    def ids_prioritarios(cls, catalogo, utilidade, proprias=None, preferencia=None):
        proprias = proprias or {}
        if preferencia == "sem-preferencia" or "processador" in proprias or (preferencia is None and not PreferenciasPerifericosService.jogos(utilidade)):
            return []
        if "placa_mae" in proprias:
            detalhes = proprias["placa_mae"]
            campos = detalhes.get("especificacoes_confirmadas", {}) if isinstance(detalhes, dict) else {}
            sockets = {normalizar_socket(campos.get("socket"))}
        else:
            sockets = {normalizar_socket(p.get("socket")) for p in catalogo.get("placa_mae", [])}
        sockets.discard(None)
        return [p["id"] for p in catalogo.get("processador", []) if (cls.marca(p, preferencia) if preferencia else cls.ryzen(p))
                and normalizar_socket(p.get("soquete")) in sockets]
