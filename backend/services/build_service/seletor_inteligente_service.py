from decimal import Decimal

from models import Processador, PlacaVideo, PlacaMae, MemoriaRAM
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.aparencia import validar_aparencia
from utils.validacoes import validacao_campos
from utils.sockets import normalizar_socket
from utils.memorias import normalizar_ddr
from .criar_build_service import CriarBuildService
from .planejamento_geracao import validar_minimos
from .requisitos_armazenamento_service import RequisitosArmazenamentoService
from .planejar_rede_service import PlanejarRedeService
from .amostrar_catalogo_service import AmostrarCatalogoService
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .amostra_inteligente_service import AmostraInteligenteService
from .preferencias_cores_service import PreferenciasCoresService
from .planejar_orcamento_componentes_service import PlanejarOrcamentoComponentesService
from .planejar_armazenamento_service import PlanejarArmazenamentoService


class SeletorInteligenteService:
    MODELOS_BENCHMARK = (Processador, PlacaVideo)
    LIMITE_PLACAS_MAE = 24
    LIMITE_MEMORIAS = 24

    def executar(self, dados):
        contexto = self._preparar_contexto(dados)
        contexto["detalhes_proprias"] = CriarBuildService._detalhes_proprias(contexto["proprias"])
        contexto["pools"] = self._carregar_pools(contexto)
        contexto["planejamento"] = PlanejarOrcamentoComponentesService().executar(contexto, contexto["pools"])
        contexto["amostragem"] = {}
        for modelo in self.MODELOS_BENCHMARK:
            tipo = modelo.__tablename__
            if tipo not in contexto["proprias"] and tipo in contexto["fallbacks_benchmark"]:
                contexto["planejamento"]["avisos"].append(
                    f"{tipo}: fallback por preço e recursos técnicos, sem classificação de desempenho medida.")
            elif tipo not in contexto["proprias"] and not contexto["pools"].get(tipo):
                contexto["planejamento"]["avisos"].append(
                    f"Sem {tipo} com benchmark comparável; não foi inventada uma pontuação de fallback.")
        excluidas = self._categorias_excluidas(contexto)
        selecionados = self._selecionar_por_benchmark(contexto, excluidas)
        selecionados.extend(self._selecionar_demais_pecas(contexto, excluidas, selecionados))
        presentes = {p["categoria"] for p in selecionados} | contexto["proprias"].keys()
        faltantes = sorted({"processador", "placa_mae", "memoria_ram", "fonte", "gabinete"} - presentes)
        if not {"ssd", "hd"} & presentes:
            faltantes.append("armazenamento")
        return {
            "planejamento_orcamento": contexto["planejamento"],
            "amostragem": contexto["amostragem"], "categorias_pendentes": faltantes,
            "mensagem": "Candidatos por peça selecionados dentro do teto informado.",
            "prioridade_montagem": contexto["prioridade"],
            "armazenamento_minimo_gb": contexto["armazenamento_minimo_gb"],
            "componentes_selecionados": selecionados,
        }

    def preparar_geracao(self, dados):
        """Adapta a seleção experimental ao gerador existente, sem chamar IA nem salvar."""
        if not isinstance(dados, dict):
            raise ValueError("Informe um objeto com os dados da geração")
        validacao_campos(dados, ["nome", "descricao", "utilidade", "orcamento"])
        CriarBuildService._validar_textos_pedido(dados)
        resultado = self.executar(dados)
        catalogo = {}
        for peca in resultado["componentes_selecionados"]:
            catalogo.setdefault(peca["categoria"], []).append(self._ficha(peca))
        gerador = CriarBuildService()
        proprias = gerador._pecas_proprias(dados.get("pecas_proprias", {}))
        detalhes = gerador._detalhes_proprias(proprias)
        percentual = dados.get("percentual_perifericos", 0)
        orcamento = gerador._validar_orcamento(dados["orcamento"])
        _, teto_perifericos = gerador._dividir_orcamento(orcamento, percentual)
        aparencia = validar_aparencia(dados.get("aparencia"))
        gerador._validar_disponibilidade(catalogo, proprias, percentual)
        perifericos = gerador._planejar_perifericos(catalogo, teto_perifericos, proprias,
                                                   dados["utilidade"], aparencia["cor"], percentual)
        margem = min(orcamento / 2, max(800, orcamento * 0.25))
        pedido = {**dados, "prioridade_montagem": resultado["prioridade_montagem"]}
        prompt = gerador._criar_prompt(pedido, orcamento, margem, catalogo, percentual, detalhes,
                                      perifericos, planejamento_componentes=resultado["planejamento_orcamento"],
                                      preferencia_neutra=True)
        return {**resultado, "catalogo": catalogo, "prompt": prompt, "proprias": proprias,
                "detalhes_proprias": detalhes}

    def _preparar_contexto(self, dados):
        if not isinstance(dados, dict):
            raise ValueError("Informe um objeto com os dados da seleção")
        
        validacao_campos(dados, ["orcamento"])
        armazenamento = RequisitosArmazenamentoService.validar_parametro(dados.get("armazenamento_minimo_gb"))
        prioridade = dados.get("prioridade_montagem", dados.get("preferencias"))

        if prioridade == "custo-beneficio":
            prioridade = "custo_beneficio"
        
        if prioridade not in ("desempenho", "custo_beneficio"):
            raise ValueError("A preferência deve ser desempenho ou custo_beneficio")
        
        limite = dados.get("limite", 12)
        
        if type(limite) is not int or not 1 <= limite <= 200:
            raise ValueError("O limite deve ser um inteiro entre 1 e 200")
        
        limites = dados.get("limites_candidatos", {})
        if not isinstance(limites, dict) or set(limites) - {m.__tablename__ for m in MODELOS_PECAS}:
            raise ValueError("Limites de candidatos por categoria inválidos")
        if any(type(v) is not int or not 1 <= v <= 200 for v in limites.values()):
            raise ValueError("Cada limite de candidatos deve ser um inteiro entre 1 e 200")
        utilidade = dados.get("utilidade", "")
        if not isinstance(utilidade, str) or len(utilidade) > 120:
            raise ValueError("A utilidade deve ser um texto de até 120 caracteres")
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
                "utilidade": utilidade, "armazenamento_minimo_gb": armazenamento,
                "teto_pc": float(CriarBuildService._dividir_orcamento(dados["orcamento"], dados.get("percentual_perifericos", 0))[0]),
                "limites": {m.__tablename__: limites.get(m.__tablename__, limite if m in self.MODELOS_BENCHMARK
                            else self.LIMITE_PLACAS_MAE if m.__tablename__ == "placa_mae"
                            else self.LIMITE_MEMORIAS if m.__tablename__ == "memoria_ram" else 12) for m in MODELOS_PECAS}}

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

    def _carregar_pools(self, contexto):
        pools = {}
        contexto["fallbacks_benchmark"] = set()
        for modelo in MODELOS_PECAS:
            periferico = modelo.__tablename__ in CriarBuildService.PERIFERICOS
            teto = contexto["teto_perifericos"] if periferico else contexto["teto_peca"]
            if not teto:
                continue
            pecas = (modelo.listar_pool_benchmark(teto) if modelo in self.MODELOS_BENCHMARK
                     else modelo.listar_candidatos_disponiveis(teto))
            if modelo in self.MODELOS_BENCHMARK and not pecas:
                pecas = [p for p in modelo.listar_candidatos_disponiveis(teto)
                         if getattr(p, modelo.BENCHMARK_CAMPO) is None
                         and p.benchmark_teste in (None, modelo.BENCHMARK_TESTE)
                         and p.benchmark_versao is None]
                if pecas:
                    contexto["fallbacks_benchmark"].add(modelo.__tablename__)
            pools[modelo.__tablename__] = [p.to_catalogo() for p in pecas]
        for tipo in ("cabo_rede", "adaptador_wifi"):
            if contexto["rede"]:
                pools[tipo] = PlanejarRedeService.opcoes(pools, contexto["rede"], contexto["proprias"])
        return pools

    def _selecionar_por_benchmark(self, contexto, excluidas):
        selecionados = []
        for modelo in self.MODELOS_BENCHMARK:
            tipo = modelo.__tablename__
            dependencia = tipo == "processador" and contexto["categoria"] in ("placa_mae", "memoria_ram")
            if tipo in contexto["proprias"] or (tipo in excluidas and not dependencia):
                continue
            pecas = contexto["pools"].get(tipo, [])
            if tipo == "processador":
                pecas = self._filtrar_plataformas(contexto, pecas)
            pecas = self._aplicar_teto(contexto, tipo, pecas)
            if tipo == "placa_video":
                estimativas = contexto["planejamento"]["estimativas_cpu"]
                cpus = contexto.get("cpus_candidatas", [])
                ids = [p["id"] for p in cpus] or (["proprio"] if "processador" in contexto["proprias"] else [])
                reservas = [estimativas[i]["disponivel_gpu"] for i in ids if estimativas.get(i)]
                if reservas:
                    pecas = [p for p in pecas if p["preco"] <= max(reservas)]
            teto_faixas = contexto["planejamento"]["tetos_sugeridos"].get(tipo, contexto["teto_peca"])
            teto_faixas = max([teto_faixas, *[p["preco"] for p in pecas]])
            amostra, diagnostico = AmostraInteligenteService().executar(
                pecas, tipo, contexto["prioridade"], teto_faixas,
                contexto["limites"][tipo], contexto["aparencia"]["cor"])
            diagnostico["sem_benchmark"] = tipo in contexto["fallbacks_benchmark"]
            contexto["amostragem"][tipo] = diagnostico
            if tipo == "processador":
                contexto["cpus_candidatas"] = amostra
            if tipo not in excluidas:
                selecionados.extend(amostra)
        return selecionados

    @staticmethod
    def _id_numerico(identificador):
        return int(str(identificador).split(":")[-1])

    def _filtrar_plataformas(self, contexto, pecas):
        propria = contexto["detalhes_proprias"].get("placa_mae", {}).get("especificacoes_confirmadas", {})
        if propria and normalizar_socket(propria.get("socket")):
            pecas = [p for p in pecas if normalizar_socket(p.get("soquete")) == normalizar_socket(propria["socket"])]
        plano = contexto["planejamento"]
        estimativas = plano["estimativas_cpu"]
        viaveis = [p for p in pecas if (e := estimativas.get(p["id"])) and e["viavel"]]
        if viaveis:
            alvo = [p for p in viaveis if estimativas[p["id"]]["plataforma_minima"] <= plano["meta_plataforma"]]
            if alvo:
                return alvo
            plano["flexibilizacoes"].append("Meta de plataforma flexibilizada para preservar combinações viáveis.")
            return viaveis
        if any(estimativas.get(p["id"]) is not None for p in pecas):
            plano["avisos"].append("Nenhuma plataforma confirmável cabe com as reservas mínimas do conjunto.")
            # Ausência de ficha não prova inviabilidade: manter as alternativas pendentes.
            return [p for p in pecas if estimativas.get(p["id"]) is None]
        return pecas  # Dados incompletos: preservar alternativas, sem afirmar viabilidade.

    @staticmethod
    def _aplicar_teto(contexto, tipo, pecas):
        absoluto = contexto["teto_perifericos"] if tipo in CriarBuildService.PERIFERICOS else contexto["teto_peca"]
        teto = contexto["planejamento"]["tetos_sugeridos"].get(tipo, absoluto)
        dentro = [p for p in pecas if Decimal(str(p["preco"])) <= Decimal(str(teto))]
        if dentro:
            cor = contexto["aparencia"]["cor"]
            if cor != "sem-preferencia" and not any(PreferenciasCoresService.prioridade(p, cor) <= 1 for p in dentro):
                preferidas = [p for p in pecas if PreferenciasCoresService.prioridade(p, cor) <= 1]
                if preferidas:
                    dentro = [*dentro, min(preferidas, key=lambda p: (p["preco"], p["id"]))]
                    contexto["planejamento"]["flexibilizacoes"].append(
                        f"{tipo}: preservada alternativa da cor pedida fora da meta, dentro do teto absoluto.")
            return dentro
        if not pecas:
            return []
        menor = min(Decimal(str(p["preco"])) for p in pecas)
        contexto["planejamento"]["flexibilizacoes"].append(
            f"{tipo}: teto de busca {teto} insuficiente; preservadas opções de menor preço {menor}.")
        return [p for p in pecas if Decimal(str(p["preco"])) == menor]

    @staticmethod
    def _ficha(peca):
        ficha = CriarBuildService._campos_catalogo({**peca, "id": SeletorInteligenteService._id_numerico(peca["id"])})
        for campo in ("benchmark_multi_core", "benchmark_single_thread", "benchmark_g3d", "benchmark_g2d",
                      "benchmark_teste", "benchmark_versao"):
            valor = peca.get(campo)
            if valor is not None:
                ficha[campo] = float(valor) if isinstance(valor, Decimal) else valor
        return ficha

    def _selecionar_demais_pecas(self, contexto, excluidas, selecionados):
        aparencia, rede = contexto["aparencia"], contexto["rede"]
        
        catalogo = {}
        especiais = {"processador", "placa_video", "placa_mae", "memoria_ram"}
        for tipo, pecas in contexto["pools"].items():
            if tipo in excluidas or tipo in especiais:
                continue
            if tipo == "monitor":
                pecas = [p for p in pecas if PreferenciasPerifericosService.painel_permitido(p)]
            fichas = [self._ficha(p) for p in self._aplicar_teto(contexto, tipo, pecas)]
            if fichas:
                catalogo[tipo] = AmostrarCatalogoService().executar(
                    tipo, fichas, contexto["limites"][tipo], contexto["utilidade"], cor=aparencia["cor"])[:contexto["limites"][tipo]]
        self._preservar_referencia_gabinete(contexto, excluidas, catalogo)
        self._preservar_armazenamento(contexto, excluidas, catalogo)

        placas = []
        precisa_placas = "placa_mae" not in excluidas
        precisa_ddr = "memoria_ram" not in excluidas and "placa_mae" not in contexto["proprias"]
        if precisa_placas or precisa_ddr:
            placas = self._selecionar_placas_mae(contexto, selecionados)
        if precisa_placas and placas:
            catalogo["placa_mae"] = placas
        if "memoria_ram" not in excluidas:
            memorias = self._selecionar_memorias(contexto, placas)
            if memorias:
                catalogo["memoria_ram"] = memorias
        self._ajustar_acessorio_rede(catalogo, contexto, excluidas)
        for tipo, itens in catalogo.items():
            catalogo[tipo] = list({p["id"]: p for p in itens}.values())[:contexto["limites"][tipo]]
        return self._formatar_catalogo(catalogo)

    def _selecionar_placas_mae(self, contexto, selecionados):
        sockets = self._sockets_processadores(contexto, selecionados)
        grupos = {s: [] for s in sockets}
        propria_ram = contexto["detalhes_proprias"].get("memoria_ram", {}).get("especificacoes_confirmadas", {})
        ddr_proprio = normalizar_ddr(propria_ram.get("ddr"))
        for p in contexto["pools"].get("placa_mae", []):
            if ddr_proprio and normalizar_ddr(p.get("tipo_memoria")) != ddr_proprio:
                continue
            socket = normalizar_socket(p.get("socket"))
            if socket in grupos:
                grupos[socket].append(p)
        return self._amostrar_grupos(contexto, "placa_mae", grupos)

    def _selecionar_memorias(self, contexto, placas):
        nome_proprio = contexto["proprias"].get("placa_mae")
        if nome_proprio:
            placa = PlacaMae.buscar_por_nome(nome_proprio)
            valores = [placa.tipo_memoria] if placa else []
        else:
            valores = [placa.get("tipo_memoria") for placa in placas]
        ddrs = sorted({ddr for valor in valores if (ddr := normalizar_ddr(valor))})
        grupos = {ddr: [] for ddr in ddrs}
        for p in contexto["pools"].get("memoria_ram", []):
            ddr = normalizar_ddr(p.get("ddr"))
            if ddr in grupos:
                grupos[ddr].append(p)
        return self._amostrar_grupos(contexto, "memoria_ram", grupos)

    def _amostrar_grupos(self, contexto, tipo, grupos):
        for grupo, pecas in grupos.items():
            pecas = self._aplicar_teto(contexto, tipo, pecas)
            # Preservar alternativas de cor dentro das cotas, sem ultrapassá-las.
            pecas.sort(key=lambda p: (PreferenciasCoresService.prioridade(p, contexto["aparencia"]["cor"]),
                                      p["preco"], self._id_numerico(p["id"])))
            grupos[grupo] = pecas
        escolhidas = self._distribuir_vagas(grupos, contexto["limites"][tipo])
        return [self._ficha(p) for p in escolhidas]

    def _preservar_armazenamento(self, contexto, excluidas, catalogo):
        minimo = contexto["armazenamento_minimo_gb"]
        if minimo is None or {"ssd", "hd"} & contexto["proprias"].keys():
            return
        pools = {tipo: contexto["pools"].get(tipo, []) for tipo in ("ssd", "hd") if tipo not in excluidas}
        referencia = PlanejarArmazenamentoService().executar(pools, minimo)
        if referencia is None:
            contexto["planejamento"]["avisos"].append("Sem opção confirmável para o armazenamento solicitado.")
            return
        itens = []
        for item in referencia["itens"]:
            tipo, peca = item["tipo"], item["peca"]
            amostra = catalogo.setdefault(tipo, [])
            ident = self._id_numerico(peca["id"])
            if not any(p["id"] == ident for p in amostra):
                if len(amostra) >= contexto["limites"][tipo]:
                    amostra.pop()
                amostra.append(self._ficha(peca))
            itens.append({"tipo": tipo, "id": ident, "quantidade": item["quantidade"]})
        contexto["planejamento"]["armazenamento_referencia"] = {
            "itens": itens, "capacidade_total_gb": referencia["capacidade_total_gb"], "custo": referencia["custo"]}

    def _preservar_referencia_gabinete(self, contexto, excluidas, catalogo):
        referencia = contexto["aparencia"]["gabinete_id"]
        if referencia is None or "gabinete" in excluidas:
            return
        peca = next((p for p in contexto["pools"].get("gabinete", []) if self._id_numerico(p["id"]) == referencia), None)
        if peca:
            amostra = catalogo.setdefault("gabinete", [])
            if not any(p["id"] == referencia for p in amostra):
                if len(amostra) >= contexto["limites"]["gabinete"]:
                    amostra.pop()
                amostra.append(self._ficha(peca))

    @staticmethod
    def _sockets_processadores(contexto, selecionados):
        nome_proprio = contexto["proprias"].get("processador")
        if nome_proprio:
            cpu = Processador.buscar_por_nome(nome_proprio)
            valores = [cpu.soquete] if cpu else []
        elif contexto["categoria"] in ("placa_mae", "memoria_ram"):
            # Seleciona CPUs como dependência, mas não as inclui na resposta desta categoria.
            valores = [cpu.get("soquete") for cpu in contexto.get("cpus_candidatas", [])]
        else:
            valores = [p.get("soquete") for p in selecionados if p["categoria"] == "processador"]
        return sorted({socket for valor in valores if (socket := normalizar_socket(valor))})

    @staticmethod
    def _distribuir_vagas(grupos, limite):
        # Rodadas por grupo (socket ou DDR), com redistribuição automática de sobras.
        escolhidas, ids = [], set()
        ativos = [iter(grupos[socket]) for socket in sorted(grupos) if grupos[socket]]
        while ativos and len(escolhidas) < limite:
            proximos = []
            for grupo in ativos:
                peca = next(grupo, None)
                if peca is None:
                    continue
                proximos.append(grupo)
                ident = peca["id"] if isinstance(peca, dict) else peca.id
                if ident not in ids:
                    escolhidas.append(peca)
                    ids.add(ident)
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
