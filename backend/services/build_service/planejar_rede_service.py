from decimal import Decimal
from math import isfinite
from copy import deepcopy
import re


class PlanejarRedeService:
    """Separa acessórios utilizáveis de uma pendência, sem inventar um produto."""

    TIPOS = {"cabo": "cabo_rede", "wifi": "adaptador_wifi"}

    @staticmethod
    def _cat6(peca):
        texto = " ".join(str(peca.get(campo) or "") for campo in ("categoria_cabo", "categoria", "modelo"))
        return bool(re.search(r"\bcat(?:egoria)?[\s.-]*6a?\b", texto, re.I))

    @staticmethod
    def _numero(valor):
        return float(valor) if type(valor) in (int, float, Decimal) and isfinite(valor) and valor > 0 else None

    @classmethod
    def opcoes(cls, catalogo, rede=None, proprias=None):
        rede = rede or {}
        tipo = cls.TIPOS.get(rede.get("tipo"))
        if not tipo or rede.get("possuiAcessorio") is not False or tipo in (proprias or {}):
            return []
        opcoes = []
        for peca in catalogo.get(tipo, []):
            if peca.get("esgotado") is True or cls._numero(peca.get("preco")) is None:
                continue
            comprimento = cls._numero(peca.get("comprimento_m"))
            solicitado = cls._numero(rede.get("comprimentoCaboM"))
            if tipo == "cabo_rede" and solicitado and (comprimento is None or comprimento < solicitado):
                continue
            velocidade = cls._numero(peca.get("velocidade_mbps"))
            solicitada = cls._numero(rede.get("velocidadeMbps"))
            # Taxa ausente não vira uma garantia; o editor continua orientando a conferência.
            if velocidade and solicitada and velocidade < solicitada:
                continue
            if tipo == "adaptador_wifi" and solicitada and velocidade is None:
                continue
            opcoes.append(peca)
        # Preferência de catálogo, sem afirmar que um cabo de padrão desconhecido é Cat6.
        # Mantém as alternativas para não inviabilizar o PC quando só elas cabem no teto.
        if tipo == "cabo_rede":
            opcoes.sort(key=lambda p: not cls._cat6(p))
        return opcoes

    @classmethod
    def executar(cls, catalogo, rede=None, proprias=None):
        rede = rede or {}
        tipo = cls.TIPOS.get(rede.get("tipo"))
        comprar = tipo if rede.get("possuiAcessorio") is False and tipo not in (proprias or {}) else None
        opcoes = cls.opcoes(catalogo, rede, proprias)
        return {"tipo": comprar, "ids_permitidos": [p["id"] for p in opcoes],
                "pendente": bool(comprar and not opcoes)}

    @classmethod
    def completar(cls, build, catalogo, rede=None, proprias=None):
        plano = cls.executar(catalogo, rede, proprias)
        if not plano["tipo"] or not isinstance(build, dict) or not isinstance(build.get("componentes"), list):
            return build
        nova = deepcopy(build)
        itens = [i for i in nova["componentes"] if isinstance(i, dict) and i.get("tipo") == plano["tipo"]]
        if len(itens) > 1:
            return nova  # Duplicações continuam sendo rejeitadas pelo contrato da montagem.
        if plano["pendente"]:
            nova["componentes"] = [i for i in nova["componentes"] if i not in itens]
        elif not itens or itens[0].get("id") not in plano["ids_permitidos"]:
            peca = min(cls.opcoes(catalogo, rede, proprias), key=lambda p: (Decimal(str(p["preco"])), p["id"]))
            if itens:
                nova["componentes"].remove(itens[0])
            nova["componentes"].append({"tipo": plano["tipo"], "id": peca["id"], "quantidade": 1})
        return nova
