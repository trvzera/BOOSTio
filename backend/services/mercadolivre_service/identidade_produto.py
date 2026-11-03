"""Normalização conservadora de identidade; nunca remove números ou sufixos."""
import re
import unicodedata
from decimal import Decimal, InvalidOperation


def nome(valor):
    if not isinstance(valor, str):
        return ''
    valor = unicodedata.normalize('NFKD', valor.replace('®', '').replace('™', '')).casefold()
    valor = ''.join(c for c in valor if not unicodedata.combining(c))
    valor = re.sub(r'\b(ddr|rtx|gtx|rx)\s*-?\s*(\d)', r'\1 \2', valor)
    valor = re.sub(r'(\d{3,5})\s+(x3d|kf|ks|ge|hx|hs|x|g|f|k|t|u|h|p)\b', r'\1\2', valor)
    return re.sub(r'\s+', ' ', valor).strip()


def codigo(valor):
    return re.sub(r'\s+', '', nome(valor))


def gtin(valor):
    if not isinstance(valor, str) or not re.fullmatch(r'(?:\d{8}|\d{12}|\d{13}|\d{14})', valor):
        return None
    if len(set(valor)) == 1:
        return None
    soma = sum(int(v) * (3 if i % 2 == 0 else 1) for i, v in enumerate(reversed(valor[:-1])))
    return valor.zfill(14) if (10 - soma % 10) % 10 == int(valor[-1]) else None


def atributos(produto):
    resultado = {}
    for a in produto.get('attributes', []) if isinstance(produto.get('attributes'), list) else []:
        if not isinstance(a, dict) or not isinstance(a.get('id'), str):
            continue
        valores = [a.get('value_name')]
        if isinstance(a.get('values'), list):
            valores += [v.get('name') for v in a['values'] if isinstance(v, dict)]
        resultado.setdefault(a['id'], set()).update(nome(v) for v in valores if isinstance(v, str) and v.strip())
    return resultado


def numero(valor, unidade=None):
    texto = nome(str(valor)).replace(',', '.')
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*([a-z]+)?', texto)
    if not m:
        return None
    try:
        n = Decimal(m[1])
    except InvalidOperation:
        return None
    u = m[2] or ''
    if unidade == 'gb' and u in ('tb', 'gb', 'mb'):
        n *= {'tb':1000, 'gb':1, 'mb':Decimal('0.001')}[u]
    elif unidade and u and u != unidade:
        return None
    elif not unidade and u:
        return None
    return n


def variante(categoria, valor):
    texto = nome(valor)
    if categoria == 'processador':
        m = re.search(r'\b(?:ryzen\s*[3579]|(?:core\s*)?i[3579]|core\s*ultra\s*[3579])\s*-?\s*(\d{3,5}(?:x3d|[a-z]{1,3})?)\b', texto)
        return m[1] if m else None
    if categoria == 'placa_video':
        m = re.search(r'\b(rtx|gtx|rx|arc)\s*([a-z]?\d{3,4})\s*(ti|super|xtx|xt)?\s*(super)?\b', texto)
        return ' '.join(x for x in m.groups() if x) if m else None
    return None
