from urllib.parse import parse_qs, urlsplit


def estado_da_autorizacao(url):
    """Valor de `state` que o provedor OAuth colocou na URL de autorização."""
    return parse_qs(urlsplit(url).query)["state"][0]
