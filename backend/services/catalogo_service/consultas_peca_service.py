"""Textos de busca de uma peça, iguais para qualquer loja: MPN, nome comercial limpo e nome original."""
import re

from models import IdentidadeFabricante


def consultas_da_peca(peca):
    """MPN, nome comercial limpo e nome original; nunca remove variantes."""
    modelo = str(peca.modelo or '').strip()
    limpo = re.sub(r'\[([^\]]*)\]', lambda m: '' if re.search(
        r'\b(?:gb|tb|mhz|ghz|sata|nvme|ddr[345])\b', m[1], re.I) else m[0], modelo)
    capacidade = getattr(peca, 'capacidade_gb', None)
    if peca.__tablename__ in ('ssd', 'hd', 'memoria_ram') and capacidade and not re.search(r'\d\s*(?:gb|tb)\b', limpo, re.I):
        limpo += f' {capacidade:g}GB'
    marca = str(peca.fabricante or '').strip()
    candidatos = [mpn_da_peca(peca), f'{marca} {limpo}', f'{marca} {modelo}']
    consultas, vistas = [], set()
    for valor in candidatos:
        valor = re.sub(r'\s+', ' ', valor or '').strip()
        if valor and valor.casefold() not in vistas:
            consultas.append(valor)
            vistas.add(valor.casefold())
    return consultas


def mpn_da_peca(peca):
    from flask import has_app_context
    verificada = IdentidadeFabricante.buscar(peca) if has_app_context() else None
    codigo = verificada.mpn if verificada else str(peca.part_number or '').strip()
    return None if not codigo or re.match(r'^(SEED|DEMO|BOOSTIO|REDE|KABUM)[-_]', codigo, re.I) else codigo
