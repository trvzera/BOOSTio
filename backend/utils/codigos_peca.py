"""Separa códigos internos de referências do fabricante, sem adivinhar MPNs."""
import re


def codigo_interno(valor):
    return isinstance(valor, str) and bool(re.match(r'^(?:KABUM|SEED|REDE|DEMO|BOOSTIO)[-_]', valor.strip(), re.I))


def separar_codigos(dados):
    dados = dict(dados)
    numero = dados.get('part_number')
    if codigo_interno(numero):
        referencia = dados.get('referencia_interna')
        if referencia and referencia != numero:
            raise ValueError('Referências internas divergentes')
        dados.update(part_number=None, referencia_interna=numero)
    return dados
