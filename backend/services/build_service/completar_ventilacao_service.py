from copy import deepcopy
from decimal import Decimal
from math import isfinite

from .encaixe_fisico import avaliar_fans
from .preferencias_cores_service import PreferenciasCoresService


class CompletarVentilacaoService:
    """Completa uma omissão mecânica da IA só com encaixe e orçamento conhecidos."""

    def executar(self, build, catalogo, teto_pc, proprias=None, detalhes_proprias=None, cor="sem-preferencia"):
        proprias = proprias or {}
        if not isinstance(build, dict) or build.get("erro") or not isinstance(build.get("componentes"), list) or "fan" in proprias:
            return build
        por_tipo = {}
        precos = {}
        for item in build["componentes"]:
            if not isinstance(item, dict) or not isinstance(item.get("tipo"), str) or type(item.get("id")) is not int:
                return build
            tipo = item["tipo"]
            quantidade = item.get("quantidade", 1)
            if tipo in por_tipo or tipo in proprias or type(quantidade) is not int or not 1 <= quantidade <= 64:
                return build
            peca = next((p for p in catalogo.get(tipo, []) if p.get("id") == item["id"]), None)
            if not self._disponivel(peca):
                return build
            por_tipo[tipo] = (item, peca)
            precos[tipo] = Decimal(str(peca["preco"])) * quantidade

        def especificacoes(tipo):
            return por_tipo[tipo][1] if tipo in por_tipo else (detalhes_proprias or {}).get(tipo, {}).get("especificacoes_confirmadas", {})

        gabinete = especificacoes("gabinete")
        water = especificacoes("water_cooler") if "water_cooler" in por_tipo or "water_cooler" in proprias else None
        # Um AIO próprio não identificado não pode ser tratado como zero fans.
        if water == {}:
            return build
        atuais = [por_tipo["fan"]] if "fan" in por_tipo else []
        info = avaliar_fans(gabinete, atuais, water)
        if info["capacidade"] is None or info["inclusas"] is None or info["radiador"] is None:
            return build
        if info["total"] is not None and info["total"] >= info["capacidade"]:
            return build
        faltantes = info["capacidade"] - info["inclusas"] - info["radiador"]
        if faltantes <= 0:
            return build
        subtotal = sum((valor for tipo, valor in precos.items() if tipo not in {"fan", "monitor", "teclado", "mouse", "fone"}), Decimal(0))
        opcoes = [por_tipo["fan"][1]] if atuais else catalogo.get("fan", [])
        candidatas = []
        for fan in opcoes:
            kit = fan.get("quantidade")
            if not self._disponivel(fan) or type(kit) is not int or not 1 <= kit <= 64 or faltantes % kit:
                continue
            quantidade = faltantes // kit
            custo = Decimal(str(fan["preco"])) * quantidade
            if not 1 <= quantidade <= 64 or subtotal + custo > Decimal(str(teto_pc)):
                continue
            componente = {"tipo": "fan", "id": fan["id"], "quantidade": quantidade}
            encaixe = avaliar_fans(gabinete, [(componente, fan)], water)
            if encaixe["total"] != encaixe["capacidade"] or encaixe["quantidade"] is not True or encaixe["tamanhos"] is not True:
                continue
            # Quando há arranjos cadastrados, eles precisam confirmar a distribuição.
            if encaixe["distribuicao"] is False or gabinete.get("posicoes_fans") and encaixe["distribuicao"] is not True:
                continue
            candidatas.append((PreferenciasCoresService.prioridade(fan, cor), custo, fan["id"], componente))
        if not candidatas:
            return build
        candidata = min(candidatas, key=lambda item: item[:3])[3]
        resultado = deepcopy(build)
        resultado["componentes"] = [item for item in resultado["componentes"] if item["tipo"] != "fan"] + [candidata]
        return resultado

    @staticmethod
    def _disponivel(peca):
        return (isinstance(peca, dict) and type(peca.get("id")) is int and peca.get("esgotado") is not True
                and type(peca.get("preco")) in (int, float, Decimal)
                and isfinite(peca["preco"]) and peca["preco"] > 0)
