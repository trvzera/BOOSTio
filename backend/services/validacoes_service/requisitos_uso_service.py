import re
import unicodedata


class RequisitosUsoService:
    @staticmethod
    def perfil(utilidade):
        texto = unicodedata.normalize("NFKD", str(utilidade or "")).encode("ascii", "ignore").decode().casefold()
        if re.search(r"\b(jogos?|gamer|gaming|games?)\b", texto):
            return "jogos"
        if "pesado" in texto:
            return "trabalho-pesado"
        if "edicao" in texto or "editar" in texto:
            return "edicao-video"
        if any(t in texto for t in ("modelagem", "3d", "render")):
            return "modelagem-3d"
        if "programa" in texto:
            return "programacao"
        if "planilha" in texto:
            return "planilhas"
        if "reunio" in texto or "reuniao" in texto:
            return "reunioes"
        if "estud" in texto:
            return "estudos"
        return "todos" if "tudo" in texto else "trabalho-casual"

    @classmethod
    def minimo_pc(cls, utilidade):
        return 3500 if cls.perfil(utilidade) in {"jogos", "trabalho-pesado", "edicao-video", "modelagem-3d", "programacao"} else 2500

    @classmethod
    def exige_gpu_dedicada(cls, utilidade):
        return cls.perfil(utilidade) in {"trabalho-pesado", "edicao-video", "modelagem-3d"}

    @classmethod
    def prioridades(cls, utilidade):
        perfil = cls.perfil(utilidade)
        comuns = {"perfil": perfil, "memoria_alvo_gb": 32 if perfil in {"edicao-video", "modelagem-3d", "programacao", "trabalho-pesado"} else 16,
                  "memoria_e_prioridade_nao_promessa_de_catalogo": True}
        return {**comuns, "orientacao": {
            "jogos": "Priorizar GPU, CPU e fluidez do monitor; teclado mecanico com switch identificado e mouse documentado.",
            "planilhas": "Priorizar CPU, RAM, SSD e monitor com espaco para varias janelas; teclado numerico, conexao estavel e fone com microfone para reunioes. Webcam ainda nao disponivel no catalogo de compra.",
            "reunioes": "Priorizar CPU, RAM, SSD, conexao estavel e fone com microfone; webcam ainda nao disponivel no catalogo de compra.",
            "edicao-video": "Priorizar 32 GB de RAM, CPU, GPU dedicada e SSD; monitor com qualidade de imagem e cores, sem exceder o orcamento.",
            "modelagem-3d": "Priorizar CPU, GPU dedicada, RAM e SSD conforme o software e o renderizador; nao inferir desempenho apenas pela VRAM.",
            "programacao": "Priorizar CPU, RAM e SSD. GPU dedicada nao e obrigatoria para programacao comum.",
            "estudos": "Priorizar CPU, RAM e SSD; video integrado pode ser suficiente para estudos.",
            "todos": "Equilibrar CPU, GPU, RAM e SSD para usos variados sem itens superfluos.",
            "trabalho-casual": "Priorizar CPU, RAM e SSD para escritorio.",
            "trabalho-pesado": "Priorizar CPU, GPU dedicada, RAM e SSD para criacao.",
        }[perfil]}

    @classmethod
    def validar_gpu(cls, utilidade, categorias):
        if cls.exige_gpu_dedicada(utilidade) and "placa_video" not in categorias:
            raise ValueError(
                "A IA não completou as peças obrigatórias para trabalho pesado, edição ou modelagem 3D: placa_video dedicada. "
                "Inclua uma placa de vídeo do catálogo, mesmo com vídeo integrado na CPU, "
                "preservando o orçamento e as peças próprias."
            )
