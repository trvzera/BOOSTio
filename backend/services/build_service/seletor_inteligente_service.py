from models import Processador, PlacaVideo, PlacaMae
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.aparencia import validar_aparencia
from utils.validacoes import validacao_campos
from utils.sockets import normalizar_socket
from .criar_build_service import CriarBuildService
from .planejamento_geracao import validar_minimos
from .planejar_rede_service import PlanejarRedeService


class SeletorInteligenteService:
    MODELOS_BENCHMARK = (Processador, PlacaVideo)
    LIMITE_PLACAS_MAE = 24

    def executar(self, dados):
        contexto = self._preparar_contexto(dados)
        excluidas = self._categorias_excluidas(contexto)
        selecionados = self._selecionar_por_benchmark(contexto, excluidas)
        selecionados.extend(self._selecionar_demais_pecas(contexto, excluidas, selecionados))
        return {
            "mensagem": "Candidatos por peça selecionados dentro do teto informado.",
            "prioridade_montagem": contexto["prioridade"],
            "componentes_selecionados": selecionados,
        }

    def _preparar_contexto(self, dados):
        if not isinstance(dados, dict):
            raise ValueError("Informe um objeto com os dados da seleção")
        
        validacao_campos(dados, ["orcamento"])
        prioridade = dados.get("prioridade_montagem", dados.get("preferencias"))

        if prioridade == "custo-beneficio":
            prioridade = "custo_beneficio"
        
        if prioridade not in ("desempenho", "custo_beneficio"):
            raise ValueError("A preferência deve ser desempenho ou custo_beneficio")
        
        limite = dados.get("limite", 12)
        
        if type(limite) is not int or not 1 <= limite <= 200:
            raise ValueError("O limite deve ser um inteiro entre 1 e 200")
        
        categoria = dados.get("categoria")
        
        if categoria is not None and categoria not in tuple(m.__tablename__ for m in MODELOS_PECAS):
          raise ValueError("Categoria de peça inválida")
        
        rede = dados.get("rede")
        rede = {} if rede is None else rede
        
        CriarBuildService._validar_rede(rede)
        aparencia = validar_aparencia(dados.get("aparencia"))
        
        proprias = CriarBuildService._pecas_proprias(dados.get("pecas_proprias", {}))
        teto_peca, teto_perifericos = self._planejar_orcamento(dados)
        
        return {"prioridade": prioridade, "limite": limite, "categoria": categoria,
                "rede": rede, "aparencia": aparencia, "proprias": proprias,
                "teto_peca": teto_peca, "teto_perifericos": teto_perifericos,
                "utilidade": dados.get("utilidade", "")}

    @staticmethod
    def _planejar_orcamento(dados):
        orcamento = CriarBuildService._validar_orcamento(dados["orcamento"])
        percentual = dados.get("percentual_perifericos", 0)
        
        if type(percentual) is not int or not 0 <= percentual <= 99:
            raise ValueError("A porcentagem para periféricos deve ser de 0 a 99")
        
        teto_pc, teto_perifericos = CriarBuildService._dividir_orcamento(orcamento, percentual)
        
        validar_minimos(teto_pc, teto_perifericos, percentual)
        
        margem = min(orcamento / 2, max(800, orcamento * 0.25))
        
        return min(orcamento - margem, teto_pc), teto_perifericos

    @staticmethod
    def _categorias_excluidas(contexto):
        excluidas = set(contexto["proprias"])
        
        for grupo in ({"ssd", "hd"}, {"air_cooler", "water_cooler"}):
            if grupo & excluidas:
                excluidas.update(grupo)
        
        rede = contexto["rede"]
        
        acessorio = {"wifi": "adaptador_wifi", "cabo": "cabo_rede"}.get(rede.get("tipo"))
        
        excluidas.update({"adaptador_wifi", "cabo_rede"} - (
            {acessorio} if rede.get("possuiAcessorio") is False else set()))
        
        if contexto["categoria"] is not None:
            excluidas.update(m.__tablename__ for m in MODELOS_PECAS
                     if m.__tablename__ != contexto["categoria"])
        return excluidas

    def _selecionar_por_benchmark(self, contexto, excluidas):
        selecionados = []
        for modelo in self.MODELOS_BENCHMARK:
            if modelo.__tablename__ in excluidas:
                continue
            pecas = modelo.listar_por_benchmark(contexto["teto_peca"], contexto["prioridade"], contexto["limite"])
            
            selecionados.extend(peca.to_catalogo() for peca in pecas)
        
        return selecionados

    def _selecionar_demais_pecas(self, contexto, excluidas, selecionados):
        aparencia, rede = contexto["aparencia"], contexto["rede"]
        
        catalogo = CriarBuildService._gerar_catalogo(
            contexto["teto_peca"], contexto["teto_perifericos"],
            excluidas | {m.__tablename__ for m in self.MODELOS_BENCHMARK} | {"placa_mae"},
            aparencia["gabinete_id"] if "gabinete" not in excluidas else None,
            contexto["utilidade"], cor=aparencia["cor"], aparencia=aparencia, rede=rede,
        )
        
        if "placa_mae" not in excluidas:
            placas = self._selecionar_placas_mae(contexto, selecionados)
            if placas:
                catalogo["placa_mae"] = placas
        self._ajustar_acessorio_rede(catalogo, contexto, excluidas)
        
        return self._formatar_catalogo(catalogo)

    def _selecionar_placas_mae(self, contexto, selecionados):
        sockets = self._sockets_processadores(contexto, selecionados)
        grupos = PlacaMae.listar_disponiveis_por_sockets(
            contexto["teto_peca"], sockets, self.LIMITE_PLACAS_MAE)
        escolhidas = self._distribuir_vagas(grupos, self.LIMITE_PLACAS_MAE)
        return [CriarBuildService._campos_pecas(peca) for peca in escolhidas]

    @staticmethod
    def _sockets_processadores(contexto, selecionados):
        nome_proprio = contexto["proprias"].get("processador")
        if nome_proprio:
            cpu = Processador.buscar_por_nome(nome_proprio)
            valores = [cpu.soquete] if cpu else []
        elif contexto["categoria"] == "placa_mae":
            # Seleciona CPUs como dependência, mas não as inclui na resposta desta categoria.
            cpus = Processador.listar_por_benchmark(
                contexto["teto_peca"], contexto["prioridade"], contexto["limite"])
            valores = [cpu.soquete for cpu in cpus]
        else:
            valores = [p.get("soquete") for p in selecionados if p["categoria"] == "processador"]
        return sorted({socket for valor in valores if (socket := normalizar_socket(valor))})

    @staticmethod
    def _distribuir_vagas(grupos, limite):
        # Rodadas por socket: cotas equilibradas e sobras redistribuídas automaticamente.
        escolhidas, ids = [], set()
        ativos = [iter(grupos[socket]) for socket in sorted(grupos) if grupos[socket]]
        while ativos and len(escolhidas) < limite:
            proximos = []
            for grupo in ativos:
                peca = next(grupo, None)
                if peca is None:
                    continue
                proximos.append(grupo)
                if peca.id not in ids:
                    escolhidas.append(peca)
                    ids.add(peca.id)
                if len(escolhidas) == limite:
                    break
            ativos = proximos
        return escolhidas

    @staticmethod
    def _ajustar_acessorio_rede(catalogo, contexto, excluidas):
        rede = contexto["rede"]
        acessorio = {"wifi": "adaptador_wifi", "cabo": "cabo_rede"}.get(rede.get("tipo"))
        
        if acessorio and acessorio not in excluidas and rede.get("possuiAcessorio") is False:
            catalogo[acessorio] = PlanejarRedeService.opcoes(catalogo, rede, contexto["proprias"])

    @staticmethod
    def _formatar_catalogo(catalogo):
        return [{**peca, "id": f"{tipo}:{peca['id']}", "categoria": tipo}
                for tipo, pecas in catalogo.items() for peca in pecas]
