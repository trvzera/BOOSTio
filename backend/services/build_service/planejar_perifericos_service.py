from decimal import Decimal
from itertools import product
from math import isfinite
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .preferencias_cores_service import PreferenciasCoresService


class PlanejarPerifericosService:
    TIPOS = ("monitor", "teclado", "mouse", "fone")
    PESOS = {"monitor": 2, "teclado": 1, "mouse": 1, "fone": 1}
    PESOS_JOGOS = {"monitor": 2, "teclado": 1, "mouse": 2, "fone": 1}
    PENALIDADE_ABAIXO_DO_PISO = 0.3
    LIMITE_COMBINACOES = 12

    def executar(self, catalogo, teto, proprias=None, utilidade="", cor="sem-preferencia"):
        if not isinstance(catalogo, dict):
            raise ValueError("Informe catalogo como um objeto válido")

        teto = Decimal(str(teto))
        tipos = [tipo for tipo in self.TIPOS if tipo not in (proprias or {})]
        disponiveis = {tipo: self._disponiveis(catalogo, tipo) for tipo in tipos}
        for tipo in tipos:
            if not disponiveis[tipo]:
                return {"viavel": False, "categoria_ausente": tipo, "combinacoes": []}
        minimo = sum((Decimal(str(disponiveis[tipo][0]["preco"])) for tipo in tipos), Decimal(0))
        opcoes = []
        notas = {}
        abaixo_do_piso = {}
        for tipo in tipos:
            # peça mais cara do que sobra depois dos itens mais baratos dos outros tipos nunca cabe
            limite = teto - (minimo - Decimal(str(disponiveis[tipo][0]["preco"])))
            cabem = [peca for peca in disponiveis[tipo] if Decimal(str(peca["preco"])) <= limite] or disponiveis[tipo][:1]
            notas[tipo] = self._notas(tipo, cabem, utilidade)
            abaixo_do_piso[tipo] = {peca["id"] for peca in cabem
                                    if not PreferenciasPerifericosService.atende_piso(tipo, peca, utilidade)}
            opcoes.append(self._amostrar(cabem, cor))
        if minimo > teto:
            return {"viavel": False, "minimo_catalogado": float(minimo), "teto": float(teto), "combinacoes": []}
        combinacoes = []
        for conjunto in product(*opcoes):
            total = sum((Decimal(str(peca["preco"])) for peca in conjunto), Decimal(0))
            if total <= teto:
                combinacoes.append((total, conjunto))
        combinacoes.sort(key=lambda item: (item[0], tuple(peca["id"] for peca in item[1])))

        pesos = self.PESOS_JOGOS if PreferenciasPerifericosService.jogos(utilidade) else self.PESOS

        def pontuacao(item):
            return self._pontuar(tipos, notas, item[1], pesos, abaixo_do_piso)

        def ordem(item):
            return (-pontuacao(item), item[0], tuple(peca["id"] for peca in item[1]))

        prioritarias = self._priorizar_combinacoes(combinacoes, tipos, opcoes, utilidade, cor, pontuacao)
        escolhidas = []
        for item in prioritarias + sorted(combinacoes, key=ordem):
            if len(escolhidas) == self.LIMITE_COMBINACOES:
                break
            if item not in escolhidas:
                escolhidas.append(item)
        # preferências de uso e cor vêm primeiro; dentro de cada grupo, a maior pontuação
        escolhidas.sort(key=lambda item: (item not in prioritarias, *ordem(item)))
        return {"viavel": True, "teto": float(teto), "minimo_catalogado": float(minimo),
                "combinacoes": [self._apresentar(tipos, total, conjunto, pontuacao((total, conjunto)))
                                for total, conjunto in escolhidas]}

    @staticmethod
    def _apresentar(tipos, total, conjunto, pontuacao):
        combinacao = {"total": float(total), "componentes": [
            {"tipo": tipo, "id": peca["id"], "quantidade": 1} for tipo, peca in zip(tipos, conjunto)]}
        if tipos:
            combinacao["pontuacao"] = round(pontuacao * 100)
        return combinacao

    @staticmethod
    def _disponiveis(catalogo, tipo):
        pecas = [peca for peca in catalogo.get(tipo, [])
                 if type(peca.get("id")) is int and peca.get("esgotado") is not True
                 and type(peca.get("preco")) in (int, float, Decimal)
                 and isfinite(peca["preco"]) and peca["preco"] > 0]
        pecas.sort(key=lambda peca: (Decimal(str(peca["preco"])), peca["id"]))
        return pecas

    @staticmethod
    def _notas(tipo, pecas, utilidade):
        """Nota de 0 a 1 por peça: metade posição de preço, metade ficha técnica."""
        def posicoes(ordenadas):
            total = len(ordenadas) - 1
            return {peca["id"]: (indice / total if total else 1.0) for indice, peca in enumerate(ordenadas)}
        por_preco = posicoes(pecas)
        por_ficha = posicoes(sorted(pecas, key=lambda peca: (
            PreferenciasPerifericosService.qualidade(tipo, peca, utilidade), Decimal(str(peca["preco"])), peca["id"])))
        return {peca["id"]: (por_preco[peca["id"]] + por_ficha[peca["id"]]) / 2 for peca in pecas}

    @classmethod
    def _pontuar(cls, tipos, notas, conjunto, pesos, abaixo_do_piso):
        total_pesos = sum(pesos[tipo] for tipo in tipos)
        if not total_pesos:
            return 0
        base = sum(pesos[tipo] * notas[tipo][peca["id"]] for tipo, peca in zip(tipos, conjunto)) / total_pesos
        penalidade = sum(cls.PENALIDADE_ABAIXO_DO_PISO for tipo, peca in zip(tipos, conjunto)
                         if peca["id"] in abaixo_do_piso[tipo])
        return max(0, base - penalidade)

    @staticmethod
    def _amostrar(pecas, cor):
        if len(pecas) > 8:
            originais = pecas
            pecas = [originais[i * (len(originais) - 1) // 7] for i in range(8)]
            for indice, destaque in enumerate(PreferenciasCoresService.destaques(originais, cor)):
                if not any(p["id"] == destaque["id"] for p in pecas):
                    pecas[-2-indice] = destaque
            pecas.sort(key=lambda peca: (Decimal(str(peca["preco"])), peca["id"]))
        return pecas

    @staticmethod
    def _priorizar_combinacoes(combinacoes, tipos, opcoes, utilidade, cor, nota):
        prioritarias = []
        if utilidade:
            def criterio(item):
                conjunto = dict(zip(tipos,item[1]))
                monitor = conjunto.get("monitor",{})
                teclado = conjunto.get("teclado",{})
                mecanico = PreferenciasPerifericosService.teclado_documentado(teclado) if PreferenciasPerifericosService.jogos(utilidade) else False
                abaixo_do_piso = sum(not PreferenciasPerifericosService.atende_piso(tipo, peca, utilidade)
                                     for tipo, peca in conjunto.items())
                return (abaixo_do_piso, -int(mecanico), *(-v for v in PreferenciasPerifericosService.monitor(monitor,utilidade)), -nota(item), item[0])
            prioritarias = sorted(combinacoes, key=criterio)[:3]
        if cor in ("preto", "branco", "misto"):


            pesos = {id(p): PreferenciasCoresService.prioridade(p, cor) for grupo in opcoes for p in grupo}
            cores = {id(p): PreferenciasCoresService.identificar(p)[0] for grupo in opcoes for p in grupo}
            prioritarias += sorted(combinacoes, key=lambda item: (
                sum(pesos[id(p)] for p in item[1]),
                int(cor == "misto" and not {"preto", "branco"} <= set().union(*(cores[id(p)] for p in item[1]))),
                -nota(item), item[0], tuple(p["id"] for p in item[1])))[:3]
        return prioritarias
