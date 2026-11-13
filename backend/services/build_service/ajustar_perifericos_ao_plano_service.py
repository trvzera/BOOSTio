from copy import deepcopy
from decimal import Decimal


class AjustarPerifericosAoPlanoService:
    """Se a IA escolhe periféricos fora do plano do servidor e gasta muito menos que a reserva,
    usa a melhor combinação do plano, que o servidor já calculou dentro do teto."""

    LIMITE_GASTO = Decimal("0.7")

    def executar(self, build, plano, catalogo):
        if not isinstance(build, dict) or not isinstance(plano, dict) or not plano.get("viavel"):
            return build, None
        combinacoes = plano.get("combinacoes") or []
        if not combinacoes or not combinacoes[0].get("componentes"):
            return build, None
        tipos = {item["tipo"] for item in combinacoes[0]["componentes"]}
        itens = [item for item in build.get("componentes", []) if isinstance(item, dict)]
        escolhidos = {(item.get("tipo"), item.get("id"), item.get("quantidade", 1)) for item in itens if item.get("tipo") in tipos}
        if any(escolhidos == {(c["tipo"], c["id"], c.get("quantidade", 1)) for c in combinacao["componentes"]}
               for combinacao in combinacoes):
            return build, None
        gasto = self._gasto(escolhidos, catalogo)
        teto = Decimal(str(plano["teto"]))
        if gasto is None or gasto >= teto * self.LIMITE_GASTO:
            return build, None
        melhor = combinacoes[0]
        ajustada = deepcopy(build)
        ajustada["componentes"] = [item for item in itens if item.get("tipo") not in tipos] + [
            {"tipo": c["tipo"], "id": c["id"], "quantidade": c.get("quantidade", 1)} for c in melhor["componentes"]]
        diagnostico = {"motivo": "periféricos fora do plano com gasto abaixo de 70% da reserva",
                       "gasto_anterior": float(gasto), "gasto_novo": melhor["total"], "reserva": float(teto)}
        return ajustada, diagnostico

    @staticmethod
    def _gasto(escolhidos, catalogo):
        total = Decimal(0)
        for tipo, identificador, quantidade in escolhidos:
            peca = next((p for p in (catalogo or {}).get(tipo, []) if p.get("id") == identificador), None)
            if peca is None or type(quantidade) is not int or quantidade < 1:
                return None
            total += Decimal(str(peca["preco"])) * quantidade
        return total
