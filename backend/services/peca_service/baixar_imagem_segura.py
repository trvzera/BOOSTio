import requests

TAMANHO_MAXIMO = 5 * 1024 * 1024
EXTENSOES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}


def _formato_confere(conteudo, tipo):
    return (tipo == "image/jpeg" and conteudo.startswith(b"\xff\xd8\xff")
            or tipo == "image/png" and conteudo.startswith(b"\x89PNG\r\n\x1a\n")
            or tipo == "image/webp" and conteudo.startswith(b"RIFF") and conteudo[8:12] == b"WEBP")


def baixar_imagem_segura(url, origem, headers=None):
    """Baixa a imagem sem seguir redirecionamento, limitada a 5 MB e só JPEG, PNG ou WebP.

    `origem` entra nas mensagens de erro (por exemplo "do anúncio"). Devolve (bytes, extensão).
    """
    resposta = requests.get(url, timeout=(10, 30), stream=True, allow_redirects=False,
                            headers={"User-Agent": "Mozilla/5.0", **(headers or {})})
    try:
        resposta.raise_for_status()
        if resposta.is_redirect:
            raise ValueError("A imagem redirecionou para outro endereço")
        tipo = resposta.headers.get("Content-Type", "").split(";", 1)[0].lower()
        if tipo not in EXTENSOES:
            raise ValueError(f"A resposta {origem} não é uma imagem suportada")
        partes, tamanho = [], 0
        for bloco in resposta.iter_content(64 * 1024):
            tamanho += len(bloco)
            if tamanho > TAMANHO_MAXIMO:
                raise ValueError(f"Imagem {origem} maior que 5 MB")
            partes.append(bloco)
    finally:
        resposta.close()
    conteudo = b"".join(partes)
    if not _formato_confere(conteudo, tipo):
        raise ValueError("O arquivo retornado não corresponde ao formato da imagem")
    return conteudo, EXTENSOES[tipo]
