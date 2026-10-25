"""Identificadores explícitos; socket igual não certifica CPU/BIOS."""
import re


PADRAO = r"(?:FC)?LGA[\s-]*[0-9]{3,5}(?:-v?[0-9]+)?|AM\s*[1-9][0-9]*\+?|FM\s*[1-9][0-9]*\+?|s?TRX?[1-9][0-9]*|SP[1-9][0-9]*"


def normalizar_socket(valor):
    if not isinstance(valor, str):
        return None
    valor = re.sub(r"^(?:(?:AMD|INTEL)\s+)?(?:(?:SOCKET|SOQUETE)\s*)?", "", valor.strip(), flags=re.I)
    if not re.fullmatch(PADRAO, valor, re.I):
        return None
    valor = re.sub(r"\s+", "", valor).upper()
    valor = re.sub(r"^(?:FC)?LGA-?", "LGA", valor).replace("-V", "-")
    return re.sub(r"^STR", "TR", valor)


def listar_sockets(valor):
    if not isinstance(valor, str):
        return []
    valor = re.sub(r"\bLGA\s*115[xX]\b", "LGA1150, LGA1151, LGA1155, LGA1156", valor)
    return sorted({normalizar_socket(m.group()) for m in re.finditer(r"(?<![a-z0-9])(?:" + PADRAO + r")(?![a-z0-9+]|-[a-z0-9])", valor, re.I)})


def suporte_socket_cooler(socket, cooler):
    socket = normalizar_socket(socket)
    condicionais = cooler.get("sockets_suporte_condicional", [])
    if not socket or not isinstance(condicionais, list):
        return None
    if socket in [normalizar_socket(s) for s in condicionais]:
        return None
    sockets = listar_sockets(cooler.get("compatibilidade"))
    return socket in sockets if sockets else None
