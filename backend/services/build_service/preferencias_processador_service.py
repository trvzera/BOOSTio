import re

from utils.sockets import normalizar_socket
from .preferencias_perifericos_service import PreferenciasPerifericosService


class PreferenciasProcessadorService:
    """Preferência de plataforma para jogos, não um ranking de desempenho."""

    @staticmethod
    def ryzen(peca):
        return (str(peca.get("fabricante") or "").strip().casefold() == "amd"
                and bool(re.search(r"\bryzen\b", str(peca.get("modelo") or ""), re.I)))

    @classmethod
    def destaques(cls, pecas, utilidade):
        if not PreferenciasPerifericosService.jogos(utilidade):
            return []
        ryzen = sorted((p for p in pecas if cls.ryzen(p)), key=lambda p: (p["preco"], p["id"]))
        if not ryzen:
            return []
        escolhidas = {}
        for peca in ryzen:
            socket = normalizar_socket(peca.get("soquete"))
            if socket and socket not in escolhidas:
                escolhidas[socket] = peca
        # Opções em diferentes faixas; preço não é prova de desempenho.
        extras = [ryzen[0], ryzen[len(ryzen) // 2], ryzen[-1]]
        return list({p["id"]: p for p in [*escolhidas.values(), *extras]}.values())[:4]

    @classmethod
    def ids_prioritarios(cls, catalogo, utilidade, proprias=None):
        proprias = proprias or {}
        if not PreferenciasPerifericosService.jogos(utilidade) or "processador" in proprias:
            return []
        if "placa_mae" in proprias:
            detalhes = proprias["placa_mae"]
            campos = detalhes.get("especificacoes_confirmadas", {}) if isinstance(detalhes, dict) else {}
            sockets = {normalizar_socket(campos.get("socket"))}
        else:
            sockets = {normalizar_socket(p.get("socket")) for p in catalogo.get("placa_mae", [])}
        sockets.discard(None)
        return [p["id"] for p in catalogo.get("processador", []) if cls.ryzen(p)
                and normalizar_socket(p.get("soquete")) in sockets]
