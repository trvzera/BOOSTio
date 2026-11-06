"""Prepara o estado persistido, incluindo peças próprias."""
from models import BuildSalva
from models.build_salva import MODELOS, MULTIPLAS
from services.validacoes_service.validar_estado_build_service import validar_estado


def criar_gerada_com_pecas_proprias(usuario_id, dados, proprias, rede=None, percentual=0, aparencia=None):
    componentes = {}
    for tipo, nome in proprias.items():
        if tipo not in MODELOS:
            continue
        item = {"proprio": nome, "quantidade": 1}
        componentes[tipo] = [item] if tipo in MULTIPLAS else item
    for item in dados["componentes"]:
        tipo = item["tipo"]
        componente = {"id": item["id"], "quantidade": item["quantidade"]}
        componentes[tipo] = [componente] if tipo in MULTIPLAS else componente
    estado = validar_estado({
        "titulo": dados["nome"][:100], "descricao": dados["descricao"][:300],
        "orcamento": dados["orcamento"], "rede": rede or {},
        "incluirPerifericos": percentual > 0 or any(tipo in componentes for tipo in ("monitor", "teclado", "mouse", "fone")),
        "percentualPerifericos": percentual,
        "aparencia": aparencia,
        "incluirRede": (rede or {}).get("tipo") in ("cabo", "wifi"),
        "pecasExtras": {tipo: nome for tipo, nome in proprias.items() if tipo not in MODELOS},
        "componentes": componentes,
    })
    return BuildSalva.criar_limitada(usuario_id, estado)
