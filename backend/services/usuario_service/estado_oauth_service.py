from urllib.parse import parse_qs, urlsplit


def estado_da_autorizacao(url):
    return parse_qs(urlsplit(url).query)["state"][0]
