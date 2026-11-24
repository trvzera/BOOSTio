from urllib.parse import urlsplit


def validar_url_gigantec(url, *, afiliado=False):
    try:
        partes = urlsplit(url)
        host = 'www.awin1.com' if afiliado else 'www.gigantec.com.br'
        return (partes.scheme == 'https' and partes.hostname == host
                and not partes.username and not partes.password and partes.port in (None, 443))
    except (ValueError, TypeError):
        return False
