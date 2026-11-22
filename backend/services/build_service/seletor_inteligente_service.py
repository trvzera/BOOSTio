from .selecionar_plataforma_service import selecionar_placas_mae, selecionar_memorias, aplicar_teto, ficha_catalogo, id_numerico
from services.build_service.prompt_build_service import criar_prompt
from services.build_service.constantes_build import PERIFERICOS

from models import Processador, PlacaVideo
from models.modelos_pecas import MODELOS_PECAS
from utils.sockets import normalizar_socket
from .pedido_build import validar_pedido, para_prompt
from .planejamento_geracao import ErroPlanejamentoBuild, validar_disponibilidade, planejar_perifericos
from .planejar_rede_service import PlanejarRedeService
from .amostrar_catalogo_service import AmostrarCatalogoService
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .amostra_inteligente_service import AmostraInteligenteService
from .planejar_orcamento_componentes_service import PlanejarOrcamentoComponentesService
from .planejar_armazenamento_service import PlanejarArmazenamentoService
from .ajustar_orcamento_build_service import AjustarOrcamentoBuildService
from .preferencias_processador_service import PreferenciasProcessadorService
from .preco_exibido_service import PrecoExibidoService


class SeletorInteligenteService:
    """Escolhe no banco as peças candidatas de cada categoria e monta o prompt da IA."""
    MODELOS_BENCHMARK = (Processador, PlacaVideo)
    LIMITE_PADRAO = 12
    LIMITE_PLACAS_MAE = 24
    LIMITE_MEMORIAS = 24

    def preparar_geracao(self, pedido):
        """Recebe o pedido já validado e devolve o catálogo e o prompt da geração."""
        contexto = self._novo_contexto(pedido, self._limites(), categoria=None)
        selecionados, excluidas = self._selecionar(contexto)
        catalogo = {}
        for peca in selecionados:
            catalogo.setdefault(peca["categoria"], []).append(ficha_catalogo(peca))

        validar_disponibilidade(catalogo, pedido["proprias"], pedido["percentual"])
        plano_perifericos = planejar_perifericos(catalogo, pedido["teto_perifericos"], pedido["proprias"],
                                                 pedido["utilidade"], pedido["aparencia"]["cor"], pedido["percentual"])
        PreferenciasProcessadorService.exigir_catalogo(catalogo, pedido["preferencia_processador"],
                                                       pedido["proprias"], pedido["detalhes_proprias"])
        prompt = criar_prompt(para_prompt(pedido), pedido["orcamento"], pedido["margem"], catalogo, pedido["percentual"],
                              pedido["detalhes_proprias"], plano_perifericos,
                              planejamento_componentes=contexto["planejamento"], preferencia_neutra=True)
        return {"catalogo": catalogo,                                                       # candidatas enviadas à IA
                "catalogo_reparo": self._catalogo_reparo(contexto, catalogo, excluidas),    # catálogo + todas as RAM, SSD, HD e fans
                "prompt": prompt, "plano_perifericos": plano_perifericos}

    def executar(self, dados):
        """Diagnóstico sem IA: valida o pedido e mostra as candidatas e o planejamento escolhidos."""
        pedido = validar_pedido(dados)
        contexto = self._novo_contexto(
            pedido, self._limites(dados.get("limite", self.LIMITE_PADRAO), dados.get("limites_candidatos", {})),
            categoria=self._categoria(dados.get("categoria")))
        selecionados, _ = self._selecionar(contexto)
        presentes = {p["categoria"] for p in selecionados} | pedido["proprias"].keys()
        faltantes = sorted({"processador", "placa_mae", "memoria_ram", "fonte", "gabinete"} - presentes)
        if not {"ssd", "hd"} & presentes:
            faltantes.append("armazenamento")
        return {
            "planejamento_orcamento": contexto["planejamento"],
            "amostragem": contexto["amostragem"], "categorias_pendentes": faltantes,
            "mensagem": "Candidatos por peça selecionados dentro do teto informado.",
            "prioridade_montagem": pedido["prioridade"],
            "armazenamento_minimo_gb": pedido["armazenamento_minimo_gb"],
            "componentes_selecionados": selecionados,
        }

    @staticmethod
    def _novo_contexto(pedido, limites, categoria):
        """O que o seletor sabe enquanto escolhe. As chaves de baixo começam vazias e são preenchidas em ordem."""
        return {
            "pedido": pedido,
            "limites": limites,        # quantas candidatas cada categoria pode ter
            "categoria": categoria,    # restringe a seleção a uma categoria (diagnóstico)
            "pools": {},               # todas as peças elegíveis por categoria
            "fallbacks_benchmark": set(),  # CPU/GPU escolhidas sem benchmark medido
            "planejamento": {},        # tetos por peça, avisos e flexibilizações
            "amostragem": {},          # diagnóstico da amostra de CPU e GPU
            "cpus_candidatas": [],     # CPUs amostradas, usadas para escolher placas-mãe
        }

    def _selecionar(self, contexto):
        """Carrega as peças elegíveis, planeja o orçamento por peça e amostra as candidatas."""
        contexto["pools"] = self._carregar_pools(contexto)
        contexto["planejamento"] = PlanejarOrcamentoComponentesService().executar(contexto["pedido"], contexto["pools"])
        self._avisar_benchmark(contexto)
        excluidas = self._categorias_excluidas(contexto)
        selecionados = self._selecionar_por_benchmark(contexto, excluidas)
        selecionados.extend(self._selecionar_demais_pecas(contexto, excluidas, selecionados))
        return selecionados, excluidas

    def _avisar_benchmark(self, contexto):
        pedido = contexto["pedido"]
        for modelo in self.MODELOS_BENCHMARK:
            tipo = modelo.__tablename__
            if tipo in pedido["proprias"]:
                continue
            if tipo in contexto["fallbacks_benchmark"]:
                contexto["planejamento"]["avisos"].append(
                    f"{tipo}: fallback por preço e recursos técnicos, sem classificação de desempenho medida.")
            elif not contexto["pools"].get(tipo):
                contexto["planejamento"]["avisos"].append(
                    f"Sem {tipo} com benchmark comparável; não foi inventada uma pontuação de fallback.")

    def _catalogo_reparo(self, contexto, catalogo, excluidas):
        reparo = {tipo: list(fichas) for tipo, fichas in catalogo.items()}
        for tipo in AjustarOrcamentoBuildService.AJUSTAVEIS:
            if tipo in excluidas:
                continue
            fichas = [ficha_catalogo(p) for p in contexto["pools"].get(tipo, [])]
            reparo[tipo] = list({p["id"]: p for p in [*reparo.get(tipo, []), *fichas]}.values())
        return reparo

    def _limites(self, limite=LIMITE_PADRAO, limites=None):
        limites = {} if limites is None else limites
        if type(limite) is not int or not 1 <= limite <= 200:
            raise ValueError("O limite deve ser um inteiro entre 1 e 200")
        if not isinstance(limites, dict) or set(limites) - {m.__tablename__ for m in MODELOS_PECAS}:
            raise ValueError("Limites de candidatos por categoria inválidos")
        if any(type(v) is not int or not 1 <= v <= 200 for v in limites.values()):
            raise ValueError("Cada limite de candidatos deve ser um inteiro entre 1 e 200")
        padrao = {"placa_mae": self.LIMITE_PLACAS_MAE, "memoria_ram": self.LIMITE_MEMORIAS}
        return {m.__tablename__: limites.get(m.__tablename__, limite if m in self.MODELOS_BENCHMARK
                                             else padrao.get(m.__tablename__, self.LIMITE_PADRAO))
                for m in MODELOS_PECAS}

    @staticmethod
    def _categoria(categoria):
        if categoria is not None and categoria not in tuple(m.__tablename__ for m in MODELOS_PECAS):
            raise ValueError("Categoria de peça inválida")
        return categoria

    @staticmethod
    def _categorias_excluidas(contexto):
        pedido = contexto["pedido"]
        excluidas = set(pedido["proprias"])

        for grupo in ({"ssd", "hd"}, {"air_cooler", "water_cooler"}):
            if grupo & excluidas:
                excluidas.update(grupo)

        excluidas.update({"adaptador_wifi", "cabo_rede"} - PlanejarRedeService.categorias(pedido["rede"]))

        if contexto["categoria"] is not None:
            excluidas.update(m.__tablename__ for m in MODELOS_PECAS
                     if m.__tablename__ != contexto["categoria"])
        return excluidas

    def _carregar_pools(self, contexto):
        pedido = contexto["pedido"]
        pools = {}
        for modelo in MODELOS_PECAS:
            periferico = modelo.__tablename__ in PERIFERICOS
            teto = pedido["teto_perifericos"] if periferico else pedido["teto_peca"]
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
            pools[modelo.__tablename__] = PrecoExibidoService.catalogo(pecas, teto)
        for tipo in ("cabo_rede", "adaptador_wifi"):
            if pedido["rede"]:
                pools[tipo] = [p for conexao in PlanejarRedeService.conexoes(pedido["rede"])
                               if PlanejarRedeService.TIPOS.get(conexao.get("tipo")) == tipo
                               for p in PlanejarRedeService.opcoes(pools, conexao, pedido["proprias"])]
        PreferenciasProcessadorService.exigir_catalogo(pools, pedido["preferencia_processador"],
                                                       pedido["proprias"], pedido["detalhes_proprias"])
        return pools

    def _selecionar_por_benchmark(self, contexto, excluidas):
        """Escolhe as candidatas de processador e de placa de vídeo, nesta ordem: o que sobra para a
        placa de vídeo depende dos processadores candidatos."""
        pedido = contexto["pedido"]
        selecionados = []
        for modelo in self.MODELOS_BENCHMARK:
            tipo = modelo.__tablename__
            dependencia = tipo == "processador" and contexto["categoria"] in ("placa_mae", "memoria_ram")
            if tipo in pedido["proprias"] or (tipo in excluidas and not dependencia):
                continue
            pecas = (self._candidatas_processador(contexto) if tipo == "processador"
                     else self._candidatas_placa_video(contexto))
            teto_faixas = contexto["planejamento"]["tetos_sugeridos"].get(tipo, pedido["teto_peca"])
            teto_faixas = max([teto_faixas, *[p["preco"] for p in pecas]])
            amostra, diagnostico = AmostraInteligenteService().executar(
                pecas, tipo, pedido["prioridade"], teto_faixas, contexto["limites"][tipo],
                pedido["aparencia"]["cor"], preferencia_processador=pedido["preferencia_processador"])
            diagnostico["sem_benchmark"] = tipo in contexto["fallbacks_benchmark"]
            contexto["amostragem"][tipo] = diagnostico
            if tipo == "processador":
                contexto["cpus_candidatas"] = amostra
            if tipo not in excluidas:
                selecionados.extend(amostra)
        return selecionados

    def _candidatas_processador(self, contexto):
        """Processadores que cabem na plataforma, no teto de preço e na marca pedida."""
        marca = contexto["pedido"]["preferencia_processador"]
        pecas = self._filtrar_plataformas(contexto, contexto["pools"].get("processador", []))
        pecas = aplicar_teto(contexto, "processador", pecas)
        if marca == "sem-preferencia":
            return pecas
        preferidas = [p for p in pecas if PreferenciasProcessadorService.marca(p, marca)]
        if not preferidas:
            raise ErroPlanejamentoBuild("Não há plataforma da marca escolhida dentro dos limites recebidos. Revise a marca, as peças próprias ou o orçamento.",
                                       "marca-processador", "Revise a marca do processador", "preferencias")
        return preferidas

    def _candidatas_placa_video(self, contexto):
        """Placas de vídeo que cabem no teto e no que sobra para a GPU depois de cada processador candidato."""
        pedido = contexto["pedido"]
        pecas = aplicar_teto(contexto, "placa_video", contexto["pools"].get("placa_video", []))
        estimativas = contexto["planejamento"]["estimativas_cpu"]
        ids = [p["id"] for p in contexto["cpus_candidatas"]] or (["proprio"] if "processador" in pedido["proprias"] else [])
        reservas = [estimativas[i]["disponivel_gpu"] for i in ids if estimativas.get(i)]
        if reservas:
            pecas = [p for p in pecas if p["preco"] <= max(reservas)]
        return pecas

    def _filtrar_plataformas(self, contexto, pecas):
        propria = contexto["pedido"]["detalhes_proprias"].get("placa_mae", {}).get("especificacoes_confirmadas", {})
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
            return [p for p in pecas if estimativas.get(p["id"]) is None]
        return pecas

    def _selecionar_demais_pecas(self, contexto, excluidas, selecionados):
        pedido = contexto["pedido"]
        catalogo = {}
        especiais = {"processador", "placa_video", "placa_mae", "memoria_ram"}
        for tipo, pecas in contexto["pools"].items():
            if tipo in excluidas or tipo in especiais:
                continue
            if tipo == "monitor":
                pecas = [p for p in pecas if PreferenciasPerifericosService.painel_permitido(p)]
            fichas = [ficha_catalogo(p) for p in aplicar_teto(contexto, tipo, pecas)]
            if fichas:
                catalogo[tipo] = AmostrarCatalogoService().executar(
                    tipo, fichas, contexto["limites"][tipo], pedido["utilidade"],
                    cor=pedido["aparencia"]["cor"])[:contexto["limites"][tipo]]
        self._preservar_referencia_gabinete(contexto, excluidas, catalogo)
        self._preservar_armazenamento(contexto, excluidas, catalogo)

        placas = []
        precisa_placas = "placa_mae" not in excluidas
        precisa_ddr = "memoria_ram" not in excluidas and "placa_mae" not in pedido["proprias"]
        if precisa_placas or precisa_ddr:
            placas = selecionar_placas_mae(contexto, selecionados)
        if precisa_placas and placas:
            catalogo["placa_mae"] = placas
        if "memoria_ram" not in excluidas:
            memorias = selecionar_memorias(contexto, placas)
            if memorias:
                catalogo["memoria_ram"] = memorias
        self._ajustar_acessorio_rede(catalogo, contexto, excluidas)
        for tipo, itens in catalogo.items():
            catalogo[tipo] = list({p["id"]: p for p in itens}.values())[:contexto["limites"][tipo]]
        return self._formatar_catalogo(catalogo)

    @staticmethod
    def _garantir_na_amostra(catalogo, tipo, peca, limite):
        """Põe a peça na amostra da categoria. Se a amostra já estiver cheia, tira a última para abrir espaço."""
        amostra = catalogo.setdefault(tipo, [])
        if any(p["id"] == id_numerico(peca["id"]) for p in amostra):
            return
        if len(amostra) >= limite:
            amostra.pop()
        amostra.append(ficha_catalogo(peca))

    def _preservar_armazenamento(self, contexto, excluidas, catalogo):
        pedido = contexto["pedido"]
        minimo = pedido["armazenamento_minimo_gb"]
        if minimo is None or {"ssd", "hd"} & pedido["proprias"].keys():
            return
        pools = {tipo: contexto["pools"].get(tipo, []) for tipo in ("ssd", "hd") if tipo not in excluidas}
        referencia = PlanejarArmazenamentoService().executar(pools, minimo)
        if referencia is None:
            contexto["planejamento"]["avisos"].append("Sem opção confirmável para o armazenamento solicitado.")
            return
        itens = []
        for item in referencia["itens"]:
            tipo, peca = item["tipo"], item["peca"]
            self._garantir_na_amostra(catalogo, tipo, peca, contexto["limites"][tipo])
            itens.append({"tipo": tipo, "id": id_numerico(peca["id"]), "quantidade": item["quantidade"]})
        contexto["planejamento"]["armazenamento_referencia"] = {
            "itens": itens, "capacidade_total_gb": referencia["capacidade_total_gb"], "custo": referencia["custo"]}

    def _preservar_referencia_gabinete(self, contexto, excluidas, catalogo):
        referencia = contexto["pedido"]["aparencia"]["gabinete_id"]
        if referencia is None or "gabinete" in excluidas:
            return
        peca = next((p for p in contexto["pools"].get("gabinete", []) if id_numerico(p["id"]) == referencia), None)
        if peca:
            self._garantir_na_amostra(catalogo, "gabinete", peca, contexto["limites"]["gabinete"])

    @staticmethod
    def _ajustar_acessorio_rede(catalogo, contexto, excluidas):
        pedido = contexto["pedido"]
        for conexao in PlanejarRedeService.conexoes(pedido["rede"]):
            for acessorio in PlanejarRedeService.categorias(conexao) - excluidas:
                catalogo[acessorio] = PlanejarRedeService.opcoes(catalogo, conexao, pedido["proprias"])

    @staticmethod
    def _formatar_catalogo(catalogo):
        return [{**peca, "id": f"{tipo}:{peca['id']}", "categoria": tipo}
                for tipo, pecas in catalogo.items() for peca in pecas]
