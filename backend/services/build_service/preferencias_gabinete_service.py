import re
from .preferencias_cores_service import PreferenciasCoresService


class PreferenciasGabineteService:

    @classmethod
    def identificar(cls, peca):
        texto = PreferenciasCoresService._texto(" ".join(str(peca.get(c) or "")
            for c in ("modelo", "modelo_ficha_tecnica", "formato")))
        porte = next((valor for padrao, valor in ((r"\bmini[ -]?tower\b", "mini-tower"),
            (r"\bmid[ -]?tower\b", "mid-tower"), (r"\bfull[ -]?tower\b", "full-tower")) if re.search(padrao, texto)), None)
        estilo = None
        # A presença de "frontal" em LED/USB não indica vidro na frente.
        trechos_vidro = []
        continuacao = False
        for trecho in re.split(r"[,;|]", texto):
            vidro = bool(re.search(r"\bvidro\b|\bglass\b", trecho))
            continuacao = vidro or (continuacao and bool(re.match(
                r"\s*(?:e\s+)?(?:frontal|frente|lateral|teto|superior|front|side|top)\b", trecho)))
            if continuacao:
                trechos_vidro.append(trecho)
        paineis = " ".join(trechos_vidro)
        if re.search(r"\b(?:sem vidro|sem janela)\b", texto):
            estilo = "discreto"
        elif all(re.search(p, paineis) for p in (r"\bfrontal\b|\bfrente\b|\bfront\b", r"\blateral\b|\bside\b", r"\bteto\b|\bsuperior\b|\btop\b")):
            estilo = "panoramico-3-faces"
        elif re.search(r"\baquario\b|\bpanoramico\b", texto) or (
                re.search(r"\bfrontal\b|\bfrente\b|\bfront\b", paineis) and re.search(r"\blateral\b|\bside\b", paineis)):
            estilo = "panoramico"
        elif re.search(r"\blateral\b|\bside\b", paineis):
            estilo = "vidro"
        return {"porte": porte, "estilo": estilo}

    @classmethod
    def prioridade(cls, peca, aparencia):
        dados = cls.identificar(peca)
        preferencias = [(dados[c], aparencia.get(c)) for c in ("porte", "estilo")
                        if aparencia.get(c) not in (None, "sem-preferencia", "compacto")]

        return (-sum(valor == pedido for valor, pedido in preferencias),
                sum(valor is not None and valor != pedido for valor, pedido in preferencias),
                PreferenciasCoresService.prioridade(peca, aparencia.get("cor")))

    @classmethod
    def destaques(cls, pecas, aparencia):
        return sorted(pecas, key=lambda p: (cls.prioridade(p, aparencia), p["preco"], p["id"]))[:3]

    @classmethod
    def orientacoes(cls, estado, itens):
        aparencia = estado.get("aparencia")
        if not isinstance(aparencia, dict):
            return []
        mensagens = []
        gabinete = next((p for tipo, _, p in itens if tipo == "gabinete" and p), None)
        if gabinete:
            dados = cls.identificar(gabinete)
            rotulos = {"mini-tower": "Mini Tower", "mid-tower": "Mid Tower", "full-tower": "Full Tower",
                       "discreto": "sem vidro", "vidro": "vidro lateral", "panoramico": "aquário",
                       "panoramico-3-faces": "panorâmico de três faces"}
            pendentes = [rotulos[aparencia[c]] for c in ("porte", "estilo")
                         if aparencia.get(c) in rotulos and aparencia[c] != dados[c]]
            if pendentes:
                mensagens.append({"codigo": "aparencia-gabinete", "mensagem":
                    "O catálogo não confirma a preferência de gabinete (" + ", ".join(pendentes) +
                    ") neste modelo. A montagem priorizou o orçamento e as verificações de encaixe; confira as fotos e a ficha antes de comprar."})
        cor = aparencia.get("cor")
        if cor in ("preto", "branco", "misto"):
            novos = [p for _, selecao, p in itens if p and not selecao.get("proprio") and p.get("categoria") != "processador"]
            diferentes = sum(PreferenciasCoresService.prioridade(p, cor) == 4 for p in novos)
            desconhecidas = sum(not PreferenciasCoresService.identificar(p)[0] for p in novos)
            if diferentes or desconhecidas:
                detalhes = []
                if diferentes:
                    detalhes.append(f"{diferentes} item(ns) têm indicação de outra cor")
                if desconhecidas:
                    detalhes.append(f"{desconhecidas} item(ns) não têm cor identificada no catálogo")
                mensagens.append({"codigo": "aparencia-cor", "mensagem": "Preferência de cor: " +
                    {"preto": "preto", "branco": "branco", "misto": "preto e branco"}[cor] + ". " +
                    "; ".join(detalhes) + ". Confira a versão e a cor de cada produto antes de comprar."})
        return mensagens
