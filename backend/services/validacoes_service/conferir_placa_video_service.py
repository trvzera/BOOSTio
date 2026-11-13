import re
from decimal import Decimal

from .requisitos_uso_service import RequisitosUsoService


class ConferirPlacaVideoService:
    """Em jogos e trabalho pesado, a partir deste orçamento a build precisa de placa de vídeo dedicada,
    mesmo com processador de vídeo integrado (Ryzen G)."""

    ORCAMENTO_MINIMO = Decimal("4000")

    @staticmethod
    def uso_exige(utilidade):
        uso = str(utilidade or "").casefold()
        return RequisitosUsoService.exige_gpu_dedicada(uso) or bool(re.search(r"\b(jogos?|gamer|gaming|games?)\b", uso))

    @classmethod
    def exige(cls, utilidade, orcamento):
        try:
            valor = Decimal(str(orcamento))
        except ArithmeticError:
            return False
        return valor.is_finite() and valor >= cls.ORCAMENTO_MINIMO and cls.uso_exige(utilidade)

    @classmethod
    def validar(cls, utilidade, orcamento, categorias):
        if cls.exige(utilidade, orcamento) and "placa_video" not in categorias:
            raise ValueError(
                f"A IA não completou as peças obrigatórias: placa_video dedicada. Para jogos e trabalho pesado "
                f"a partir de R$ {cls.ORCAMENTO_MINIMO:.0f}, inclua uma placa de vídeo do catálogo, "
                "mesmo com processador de vídeo integrado, sem passar dos tetos e preservando as peças próprias."
            )
