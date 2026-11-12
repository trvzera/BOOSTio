import re


class RequisitosUsoService:
    @staticmethod
    def exige_gpu_dedicada(utilidade):
        uso = re.sub(r"[\s_-]+", " ", str(utilidade or "").casefold()).strip()
        return bool(re.search(r"\btrabalho pesado\b", uso))

    @classmethod
    def validar_gpu(cls, utilidade, categorias):
        if cls.exige_gpu_dedicada(utilidade) and "placa_video" not in categorias:
            raise ValueError(
                "A IA não completou as peças obrigatórias para trabalho pesado: placa_video dedicada. "
                "Inclua uma placa de vídeo do catálogo, mesmo com vídeo integrado na CPU, "
                "preservando o orçamento e as peças próprias."
            )
