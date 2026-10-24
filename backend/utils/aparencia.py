def validar_aparencia(valor=None):
    if valor is None:
        valor = {}
    if not isinstance(valor, dict) or set(valor) - {"estilo", "porte", "cor", "gabinete_id"}:
        raise ValueError("Preferências de aparência inválidas")
    estilo, cor, gabinete = valor.get("estilo", "sem-preferencia"), valor.get("cor", "sem-preferencia"), valor.get("gabinete_id")
    if estilo not in ("sem-preferencia", "discreto", "vidro", "compacto", "panoramico", "panoramico-3-faces") or cor not in ("sem-preferencia", "preto", "branco", "misto"):
        raise ValueError("Escolha um estilo e uma cor válidos")
    porte=valor.get("porte","sem-preferencia")
    if porte not in ("sem-preferencia","mini-tower","mid-tower","full-tower"):
        raise ValueError("Escolha um porte de gabinete válido")
    if gabinete is not None and (type(gabinete) is not int or not 1 <= gabinete <= 1000000000):
        raise ValueError("Referência de gabinete inválida")
    return {"estilo": estilo, "porte": porte, "cor": cor, "gabinete_id": gabinete}
