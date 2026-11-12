import re


def normalizar_ddr(valor):
    if not isinstance(valor, str):
        return None
    encontrado = re.fullmatch(r"DDR[\s-]*([1-9][0-9]*)", valor.strip(), re.I)
    return f"DDR{encontrado[1]}" if encontrado else None
