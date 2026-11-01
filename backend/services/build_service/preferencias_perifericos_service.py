from decimal import Decimal
from math import isfinite
import re


class PreferenciasPerifericosService:

    @staticmethod
    def jogos(utilidade):
        return any(termo in str(utilidade).casefold() for termo in ("jogo", "gamer", "gaming", "game", "um pouco de tudo"))

    @staticmethod
    def painel_permitido(peca):
        painel = re.sub(r"[\s_-]+", "", str(peca.get("tipo_painel") or "")).upper()
        return painel in ("IPS", "FASTIPS", "RAPIDIPS", "NANOIPS", "SSIPS", "VA", "FASTVA")

    @staticmethod
    def numero(valor):
        return float(valor) if type(valor) in (int, float, Decimal) and isfinite(valor) and valor > 0 else 0

    @classmethod
    def monitor(cls, peca, utilidade):
        resolucao = re.fullmatch(r"\s*(\d{3,5})\s*[x×]\s*(\d{3,5})\s*", str(peca.get("resolucao") or ""), re.I)
        pixels = int(resolucao[1])*int(resolucao[2]) if resolucao else 0
        hz, tamanho = cls.numero(peca.get("taxa_atualizacao_hz")), cls.numero(peca.get("tamanho_polegadas"))

        return (hz, pixels, tamanho) if cls.jogos(utilidade) else (pixels, tamanho, hz)

    @staticmethod
    def teclado_documentado(peca):
        return peca.get("mecanico") is True and isinstance(peca.get("switch"), str) and bool(peca["switch"].strip())

    @classmethod
    def destaques(cls, tipo, pecas, utilidade):
        if not utilidade:
            return []
        if tipo == "monitor":
            return sorted(pecas, key=lambda p: (*(-v for v in cls.monitor(p,utilidade)), p["preco"], p["id"]))[:3]
        if tipo == "teclado" and cls.jogos(utilidade):
            documentados = [p for p in pecas if cls.teclado_documentado(p)]
            return documentados[:2]
        return []
