from decimal import Decimal
from itertools import product
from math import isfinite
from .preferencias_perifericos_service import PreferenciasPerifericosService


class PlanejarPerifericosService:
    """Calcula exemplos viáveis no teto reservado, sem escolher peças pelo usuário."""

    TIPOS = ("monitor", "teclado", "mouse", "fone")

    def executar(self, catalogo, teto, proprias=None, utilidade=""):
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
        # Destaques são alternativas viáveis, não obrigações de gasto. Se um
        # teclado mecânico não couber com o conjunto, a opção econômica continua.
        prioritarias = []
        if utilidade:
            def criterio(item):
                conjunto = dict(zip(tipos,item[1]))
                monitor = conjunto.get("monitor",{})
                teclado = conjunto.get("teclado",{})
                mecanico = PreferenciasPerifericosService.teclado_documentado(teclado) if PreferenciasPerifericosService.jogos(utilidade) else False
                return (-int(mecanico), *(-v for v in PreferenciasPerifericosService.monitor(monitor,utilidade)), item[0])
            prioritarias = sorted(combinacoes, key=criterio)[:3]
        if len(combinacoes) > 12:
            combinacoes = [combinacoes[i * (len(combinacoes) - 1) // 11] for i in range(12)]
            for prioridade in prioritarias:
                if prioridade not in combinacoes:
                    combinacoes.pop(-1)
                    combinacoes.insert(0, prioridade)
        return {"viavel": True, "teto": float(teto), "minimo_catalogado": float(minimo),
                "combinacoes": [{"total": float(total), "componentes": [
                    {"tipo": tipo, "id": peca["id"], "quantidade": 1}
                    for tipo, peca in zip(tipos, conjunto)]} for total, conjunto in combinacoes]}
