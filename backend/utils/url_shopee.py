from urllib.parse import urlsplit


def validar_url_shopee(url, *, afiliado=False):
    try:
        partes = urlsplit(url)
        hosts = {'shopee.com.br', 'www.shopee.com.br'}
        if afiliado:
            hosts |= {'s.shopee.com.br', 'shope.ee'}
        return (partes.scheme == 'https' and partes.hostname in hosts
                and not partes.username and not partes.password and partes.port in (None, 443))
    except (ValueError, TypeError):
        return False
