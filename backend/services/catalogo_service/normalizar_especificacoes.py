import re
from decimal import Decimal
from .normalizar_produto import nome, numero


BOOLEANOS = {'microfone', 'mecanico', 'bluetooth', 'hdr', 'iluminacao'}
CONJUNTOS = {'conexao', 'compatibilidade', 'formatos_placa_mae'}


def medida(valor, unidade):
    s = nome(str(valor)).replace(',', '.')
    m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(mm|cm|m)?', s)
    if not m:
        return None
    n = Decimal(m[1])
    if m[2]:
        n *= {'mm': Decimal('.001'), 'cm': Decimal('.01'), 'm': Decimal(1)}[m[2]]
        if unidade == 'mm':
            n *= 1000
    return n


def converter_adicional(campo, valor):
    if valor is None:
        return None
    s = nome(str(valor))
    if campo in BOOLEANOS:
        if type(valor) is bool:
            return valor
        return True if s in {'sim', 'yes', 'true', '1', 'mecanico'} else False if s in {'nao', 'no', 'false', '0', 'membrana'} else None
    if campo == 'tamanho_polegadas':
        m = re.fullmatch(r'(\d+(?:[.,]\d+)?)\s*(?:"|in|inch(?:es)?|polegadas?)?', s)
        return Decimal(m[1].replace(',', '.')) if m else None
    if campo == 'resolucao':
        m = re.search(r'(\d{3,4})\s*(?:px)?\s*[x×]\s*(\d{3,4})\s*(?:px)?', s)
        return f'{m[1]}x{m[2]}' if m else None
    if campo == 'taxa_atualizacao_hz':
        return numero(s, 'hz')
    if campo in {'tamanho_mm', 'tamanho_radiador_mm', 'tamanho_max_gpu_mm', 'tamanho_max_cooler_mm'}:
        return medida(s, 'mm')
    if campo == 'memoria_maxima_gb':
        return numero(s, 'gb')
    if campo in {'quantidade_slots_ram', 'quantidade_slots_m2', 'slots_expansao', 'fans_inclusos'}:
        if type(valor) is bool:
            return None
        m = re.fullmatch(r'(\d+)\s*(?:[x×]\s*)?(?:slots?|portas?|ventoinhas?|fans?|(?:so[ -]?)?dimm)?', s)
        return int(m[1]) if m else None
    if campo == 'comprimento_m':
        return medida(s, 'm')
    if campo in {'quantidade', 'quantidade_fans'}:
        return numero(s)
    if campo == 'velocidade_mbps':
        n = numero(s, 'mbps')
        return n if n is not None else numero(s)
    if campo in {'categoria', 'categoria_cabo'}:
        m = re.fullmatch(r'(?:categoria|cat)?\s*([5678])\s*([ae])?', s)
        return 'cat' + m[1] + (m[2] or '') if m else None
    if campo == 'conector':
        return re.sub(r'[\s-]', '', s)
    if campo == 'tipo_painel':
        return s if s in {'ips', 'va', 'tn', 'oled', 'qd-oled'} else None
    if campo == 'layout':
        return s if s in {'abnt', 'abnt2', 'ansi', 'iso'} else None
    if campo == 'tipo_fone':
        s = {'intra-auricular':'in-ear','intra auricular':'in-ear','circumaural':'over-ear','supra-auricular':'on-ear'}.get(s,s)
        return s if s in {'headset', 'in-ear', 'over-ear', 'on-ear'} else None
    if campo == 'switch':
        return re.sub(r'[\s()\[\]-]+', '', s) if s not in {'nao', 'n/a', 'nao identificado'} else None
    if campo == 'padrao_wifi':
        m = re.fullmatch(r'(?:wi[ -]?fi)\s*([4567])\s*(e)?', s)
        return 'wifi' + m[1] + (m[2] or '') if m else None
    if campo == 'conexao':
        s = s.replace('sem fio', 'wireless').replace('com fio', 'wired')
        s = re.sub(r'\b3[.,]5\s*mm\b', 'jack3.5mm', s)
        s = s.replace('cabo ', '').replace('usb tipo c', 'usb-c').replace('usb type c', 'usb-c')
        s = re.sub(r'\bdisplay\s*port\b|\bdp\b', 'displayport', s)
        s = re.sub(r'(?<!\S)\d+\s+(?=(?:usb|hdmi|displayport|vga)\b)', '', s)
        partes = re.split(r'[,;/+|]|\s+e\s+', s)
        tokens = {re.sub(r'[\s-]', '', p) for p in partes if p.strip()}
        if not tokens or any(t in {'naoidentificado', 'na', 'semconexao'} for t in tokens):
            return None
        return '|'.join(sorted(tokens))
    if campo == 'formatos_placa_mae':
        s = s.replace('micro-atx', 'matx').replace('micro atx', 'matx').replace('mini-itx', 'itx').replace('mini itx', 'itx')
        formatos = set(re.findall(r'\b(?:e[ -]?atx|matx|atx|itx)\b', s))
        return '|'.join(sorted(v.replace('-', '').replace(' ', '') for v in formatos)) if formatos else None
    if campo == 'compatibilidade':
        from utils.sockets import listar_sockets
        sockets = {v.casefold() for v in listar_sockets(s)}
        partes = {re.sub(r'\s+', '', v) for v in sockets}
        if 'intel' in s or any(v.startswith('lga') for v in partes):
            partes.add('familia:intel')
        if 'amd' in s or any(v.startswith(('am', 'fm', 'tr', 'str')) for v in partes):
            partes.add('familia:amd')
        return '|'.join(sorted(partes)) if partes else None
    return NotImplemented


def agregar(valores_convertidos):
    if not valores_convertidos or any(v is None for v in valores_convertidos):
        return None
    return '|'.join(sorted({p for v in valores_convertidos for p in v.split('|')}))


def comparar_conexoes(local, remoto):
    a, b = set(local.split('|')), set(remoto.split('|'))
    if a <= b:
        return True
    meios = {'wired', 'wireless'}
    if a & meios and b & meios and not (a & b & meios):
        return False
    analogicos = {'p2', 'p3'}
    if a & analogicos and b & analogicos and not a & b & analogicos:
        return False
    if ('usba' in a and 'usbc' in b or 'usbc' in a and 'usba' in b) and not a & b & {'usba','usbc'}:
        return False
    faltantes = a - b
    for item in tuple(faltantes):
        if item in {'hdmi','displayport','usb'} and any(re.fullmatch(item + r'\d+(?:\.\d+)*', v) for v in b):
            faltantes.remove(item)
        elif item.startswith(('hdmi','displayport')):
            base = 'hdmi' if item.startswith('hdmi') else 'displayport'
            especificos = {v for v in b if v.startswith(base) and v != base}
            if especificos and item not in especificos:
                return False
    return None if faltantes else True
