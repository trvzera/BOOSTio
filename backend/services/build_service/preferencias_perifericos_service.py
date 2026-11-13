from decimal import Decimal
from math import isfinite
import re


class PreferenciasPerifericosService:

    @staticmethod
    def jogos(utilidade):
        return any(termo in str(utilidade).casefold() for termo in ("jogo", "gamer", "gaming", "game", "um pouco de tudo"))

    @staticmethod
    def painel_permitido(peca, tipos_exigidos=None):
        if tipos_exigidos is None:
            return True
        painel = re.sub(r"[\s_-]+", "", str(peca.get("tipo_painel") or "")).upper()
        exigidos={re.sub(r"[\s_-]+", "", str(v)).upper() for v in tipos_exigidos}
        return bool(painel) and painel in exigidos

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
    def qualidade(cls, tipo, peca, utilidade):
        """Chave de ordenação pela ficha técnica; maior é melhor."""
        if tipo == "monitor":
            return cls.monitor(peca, utilidade)
        if tipo == "mouse":
            return (min(cls.numero(peca.get("dpi_max")), 16000),)
        if tipo == "teclado":
            return (int(cls.teclado_documentado(peca)), int(peca.get("mecanico") is True))
        if tipo == "fone":
            return (int(bool(peca.get("microfone"))),)
        return (0,)

    @classmethod
    def atende_piso(cls, tipo, peca, utilidade):
        """Piso mínimo de qualidade para jogos; sem piso para os demais usos e tipos."""
        if tipo == "mouse" and cls.jogos(utilidade):
            return cls.numero(peca.get("dpi_max")) >= 3200 and str(peca.get("conexao") or "").strip().casefold() != "bluetooth"
        return True

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
