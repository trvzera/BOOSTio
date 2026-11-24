from copy import deepcopy

from utils.validacoes import numero_nao_negativo


class AjustarMemoriaAosSlotsService:
    """Se a IA pede mais pentes de RAM do que a placa-mãe tem de slots, reduz a quantidade ao que cabe.
    Acontece muito em perfis que priorizam 32 GB (a IA pede 4 pentes de 8 GB). Não mexe em RAM ou placa-mãe próprias."""

    def executar(self, build, catalogo, proprias=None, detalhes_proprias=None):
        proprias = proprias or {}
        if "memoria_ram" in proprias or not isinstance(build, dict) or not isinstance(build.get("componentes"), list):
            return build
        itens = [i for i in build["componentes"] if isinstance(i, dict)]
        ram = next((i for i in itens if i.get("tipo") == "memoria_ram"), None)
        placa = next((i for i in itens if i.get("tipo") == "placa_mae"), None)
        if ram is None or type(ram.get("quantidade", 1)) is not int:
            return build

        ficha_ram = self._peca(catalogo, "memoria_ram", ram.get("id"))
        if placa is not None:
            ficha_placa = self._peca(catalogo, "placa_mae", placa.get("id"))
        else:
            ficha_placa = (detalhes_proprias or {}).get("placa_mae", {}).get("especificacoes_confirmadas", {})
        slots = numero_nao_negativo((ficha_placa or {}).get("quantidade_slots_ram"))
        pentes = numero_nao_negativo((ficha_ram or {}).get("quantidade_pentes"))
        if not slots or not pentes or not slots.is_integer() or not pentes.is_integer():
            return build

        cabem = int(slots // pentes)
        if cabem < 1 or ram.get("quantidade", 1) <= cabem:
            return build
        resultado = deepcopy(build)
        for item in resultado["componentes"]:
            if isinstance(item, dict) and item.get("tipo") == "memoria_ram":
                item["quantidade"] = cabem
        return resultado

    @staticmethod
    def _peca(catalogo, tipo, ident):
        return next((p for p in catalogo.get(tipo, []) if p.get("id") == ident), None)
