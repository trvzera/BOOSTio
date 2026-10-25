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
            ficha = peca.get("modelo_ficha_tecnica")
            if isinstance(ficha, str) and ficha.strip():
                cores, _ = cls.identificar({"modelo": ficha, "categoria": peca.get("categoria")})
                if cores:
                    return cores, "nome_ficha_tecnica"
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

    @classmethod
    def alternativas_equivalentes(cls, peca, pecas, preferencia):
        if preferencia not in ("preto", "branco", "misto") or cls.prioridade(peca, preferencia) < 2:
            return []
        def familia(item):
            texto = cls._texto(str(item.get("modelo") or ""))
            texto = re.sub(r"\b(?:preto|preta|branco|branca|black|white)\b", " ", texto)
            return re.sub(r"[^a-z0-9]+", "", texto)
        # Mesma família e ficha. Não troca GPU por outra inferior só para combinar a cor.
        campos = ("capacidade_gb", "memoria_gb", "ddr", "frequencia_mhz", "quantidade_pentes",
                  "resolucao", "taxa_atualizacao_hz", "tipo_painel", "tamanho_polegadas",
                  "mecanico", "switch", "layout", "conexao", "potencia_w", "tamanho_mm", "quantidade")
        def mesma_versao(item):
            chip = peca.get("gpu_chip")
            if peca.get("categoria") == "placa_video" and isinstance(chip, str) and chip.strip():
                # Variantes da MESMA GPU e memória; não é comparação de FPS.
                return (item.get("gpu_chip") == chip and bool(peca.get("memoria_gb"))
                        and all(peca.get(c) is not None and peca[c] == item.get(c)
                                for c in ("memoria_gb", "tipo_memoria", "interface_memoria")))
            return (familia(peca) and familia(item) == familia(peca)
                    and item.get("fabricante") == peca.get("fabricante")
                    and all(item.get(c) == peca.get(c) for c in campos))
        return sorted((p for p in pecas if mesma_versao(p)
            and cls.prioridade(p, preferencia) < cls.prioridade(peca, preferencia)
            and cls.prioridade(p, preferencia) <= 1),
            key=lambda p: (cls.prioridade(p, preferencia), p["preco"], p["id"]))
