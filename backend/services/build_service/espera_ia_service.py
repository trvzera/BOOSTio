def espera_do_provedor(erro_http):
    """Segundos pedidos pelo provedor de IA em Retry-After, ou None se o valor não for confiável."""
    if erro_http.response is None:
        return None
    espera = erro_http.response.headers.get("Retry-After", "")
    if espera.isascii() and espera.isdigit() and len(espera) <= 4 and 0 < int(espera) <= 3600:
        return espera
    return None
