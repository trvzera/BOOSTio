import gzip

TAMANHO_MINIMO = 1024


def comprimir_resposta(resposta):
    """Compacta respostas JSON grandes quando o navegador aceita gzip (o catálogo passa de 1 MB)."""
    from flask import request
    if (resposta.status_code != 200 or resposta.direct_passthrough or resposta.mimetype != 'application/json'
            or 'Content-Encoding' in resposta.headers
            or 'gzip' not in request.headers.get('Accept-Encoding', '').lower()):
        return resposta
    conteudo = resposta.get_data()
    if len(conteudo) < TAMANHO_MINIMO:
        return resposta
    resposta.set_data(gzip.compress(conteudo, compresslevel=5))
    resposta.headers['Content-Encoding'] = 'gzip'
    resposta.headers.add('Vary', 'Accept-Encoding')
    resposta.headers['Content-Length'] = str(len(resposta.get_data()))
    return resposta


def configurar_compressao(app):
    app.after_request(comprimir_resposta)
