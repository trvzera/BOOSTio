from decimal import Decimal
from itertools import product
from math import isfinite


class PlanejarPerifericosService:
    """Calcula exemplos viáveis no teto reservado, sem escolher peças pelo usuário."""

    TIPOS = ("monitor", "teclado", "mouse", "fone")

    def executar(self, catalogo, teto, proprias=None):
        teto = Decimal(str(teto))
        tipos = [tipo for tipo in self.TIPOS if tipo not in (proprias or {})]
        opcoes = []
        for tipo in tipos:
            pecas = [peca for peca in catalogo.get(tipo, [])
                     if type(peca.get("id")) is int and peca.get("esgotado") is not True
                     and type(peca.get("preco")) in (int, float, Decimal)
                     and isfinite(peca["preco"]) and peca["preco"] > 0]
            pecas.sort(key=lambda peca: (Decimal(str(peca["preco"])), peca["id"]))
            if len(pecas) > 8:
                pecas = [pecas[i * (len(pecas) - 1) // 7] for i in range(8)]
            if not pecas:
                return {"viavel": False, "categoria_ausente": tipo, "combinacoes": []}
            opcoes.append(pecas)
        minimo = sum((Decimal(str(pecas[0]["preco"])) for pecas in opcoes), Decimal(0))
        if minimo > teto:
            return {"viavel": False, "minimo_catalogado": float(minimo), "teto": float(teto), "combinacoes": []}
        combinacoes = []
        for conjunto in product(*opcoes):
            total = sum((Decimal(str(peca["preco"])) for peca in conjunto), Decimal(0))
            if total <= teto:
                combinacoes.append((total, conjunto))
        combinacoes.sort(key=lambda item: (item[0], tuple(peca["id"] for peca in item[1])))
        if len(combinacoes) > 12:
            combinacoes = [combinacoes[i * (len(combinacoes) - 1) // 11] for i in range(12)]
        return {"viavel": True, "teto": float(teto), "minimo_catalogado": float(minimo),
                "combinacoes": [{"total": float(total), "componentes": [
                    {"tipo": tipo, "id": peca["id"], "quantidade": 1}
                    for tipo, peca in zip(tipos, conjunto)]} for total, conjunto in combinacoes]}
