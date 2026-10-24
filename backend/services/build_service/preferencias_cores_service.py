import re
import unicodedata
from decimal import Decimal


class PreferenciasCoresService:
    """Preferência visual, nunca uma regra de compatibilidade ou cor inventada."""

    CORES = {"preto": "preto", "preta": "preto", "black": "preto",
             "branco": "branco", "branca": "branco", "white": "branco"}
    OUTRAS = {"azul", "blue", "vermelho", "vermelha", "red", "verde", "green",
              "rosa", "pink", "roxo", "roxa", "purple", "cinza", "gray", "grey",
              "prata", "silver", "dourado", "gold", "amarelo", "yellow", "laranja", "orange"}

    @staticmethod
    def _texto(valor):
        return "".join(c for c in unicodedata.normalize("NFKD", valor.casefold()) if not unicodedata.combining(c))

    @classmethod
    def identificar(cls, peca):
        cor = peca.get("cor")
        if isinstance(cor, str) and cor.strip():
            texto, origem = cls._texto(cor), "cor_cadastrada"
        elif cor is not None and not isinstance(cor, str):
            return frozenset(), None
        else:
            # Não usar fotos, slug da loja, fabricante ou código do produto.
            if peca.get("categoria") == "processador" or not isinstance(peca.get("modelo"), str):
                return frozenset(), None
            texto, origem = cls._texto(peca["modelo"]), "nome_cadastrado"
            texto = re.sub(r"\b(?:wd[_\s]+black|black\s+edition|white\s+label|80\s*(?:plus|\+)\s*white)\b", "", texto)
        # Cor do switch/iluminação não é a cor da carcaça. Nomes ambíguos ficam desconhecidos.
        cores_texto = "|".join(sorted(set(cls.CORES) | cls.OUTRAS, key=len, reverse=True))
        texto = re.sub(r"\b(?:switch(?:es)?|led|luz|iluminacao|rgb|argb)\s+(?:de\s+)?(?:" + cores_texto + r")\b", "", texto)
        texto = re.sub(r"\bswitch(?:es)?\s+[a-z]+\s+(?:" + cores_texto + r")\b", "", texto)
        palavras = set(re.findall(r"\b[a-z]+\b", texto))
        cores = {cls.CORES[p] for p in palavras if p in cls.CORES}
        if palavras & cls.OUTRAS:
            cores.add("outra")
        return frozenset(cores), origem if cores else None

    @classmethod
    def metadados(cls, peca):
        cores, origem = cls.identificar(peca)
        if not cores or "outra" in cores:
            return {}
        return {"cor_referencia": sorted(cores), "fonte_cor_referencia": origem}

    @classmethod
    def prioridade(cls, peca, preferencia):
        if preferencia not in ("preto", "branco", "misto"):
            return 0
        cores, origem = cls.identificar(peca)
        if not cores:
            return 3
        alvo = {"preto", "branco"} if preferencia == "misto" else {preferencia}
        if cores <= alvo:
            return 0 if origem == "cor_cadastrada" else 1
        return 2 if cores & alvo and "outra" not in cores else 4

    @classmethod
    def destaques(cls, pecas, preferencia, campos=(), limite=2):
        if preferencia not in ("preto", "branco", "misto"):
            return []
        ordenadas = sorted((p for p in pecas if cls.prioridade(p, preferencia) <= 2),
                           key=lambda p: (cls.prioridade(p, preferencia), Decimal(str(p["preco"])), p["id"]))
        grupos = {}
        for peca in ordenadas:
            chave = tuple(str(peca.get(campo, "")).casefold() for campo in campos)
            if preferencia == "misto":
                chave += (tuple(sorted(cls.identificar(peca)[0])),)
            grupos.setdefault(chave, peca)
        return list(grupos.values())[:limite]
