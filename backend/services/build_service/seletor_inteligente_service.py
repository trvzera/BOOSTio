from services.build_service.gerar_candidata_service import gerar_candidata
from services.build_service.gerar_candidata_service import perfil_revisa_investimento
from .selecionar_plataforma_service import selecionar_placas_mae, selecionar_memorias, aplicar_teto, ficha_catalogo, id_numerico
from services.validacoes_service.validar_pedido_build_service import validar_orcamento, validar_rede, validar_textos_pedido, pecas_proprias
from services.build_service.custos_build_service import dividir_orcamento
from services.build_service.contexto_build_service import obter_detalhes_proprias
from services.build_service.catalogo_geracao_service import validar_disponibilidade, planejar_perifericos
from services.build_service.prompt_build_service import criar_prompt
from services.build_service.constantes_build import PERIFERICOS

from models import Processador, PlacaVideo, BuildSalva
from models.modelos_pecas import MODELOS_PECAS
from utils.aparencia import validar_aparencia
from utils.validacoes import validacao_campos
from utils.sockets import normalizar_socket
from .planejamento_geracao import validar_minimos
from services.validacoes_service.requisitos_armazenamento_service import RequisitosArmazenamentoService
from .planejar_rede_service import PlanejarRedeService
from .amostrar_catalogo_service import AmostrarCatalogoService
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .amostra_inteligente_service import AmostraInteligenteService
from .planejar_orcamento_componentes_service import PlanejarOrcamentoComponentesService
from .planejar_armazenamento_service import PlanejarArmazenamentoService
from .ajustar_orcamento_build_service import AjustarOrcamentoBuildService
from services.llm_service.bloquear_geracao_service import BloquearGeracaoService


class SeletorInteligenteService:
    MODELOS_BENCHMARK = (Processador, PlacaVideo)
    LIMITE_PLACAS_MAE = 24
    LIMITE_MEMORIAS = 24

    def executar(self, dados):
        return self._executar(dados, incluir_reparo=False)

    def _executar(self, dados, incluir_reparo):
        contexto = self._preparar_contexto(dados)
        contexto["detalhes_proprias"] = obter_detalhes_proprias(contexto["proprias"])
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
        resultado = {
            "planejamento_orcamento": contexto["planejamento"],
            "amostragem": contexto["amostragem"], "categorias_pendentes": faltantes,
            "mensagem": "Candidatos por peça selecionados dentro do teto informado.",
            "prioridade_montagem": contexto["prioridade"],
            "armazenamento_minimo_gb": contexto["armazenamento_minimo_gb"],
            "componentes_selecionados": selecionados,
        }

        if incluir_reparo:
            resultado["catalogo_reparo"] = self._catalogo_reparo(contexto, selecionados, excluidas)
        return resultado

    def preparar_geracao(self, dados):
        """Adapta a seleção experimental ao gerador existente, sem chamar IA nem salvar."""
        if not isinstance(dados, dict):
            raise ValueError("Informe um objeto com os dados da geração")
        validacao_campos(dados, ["nome", "descricao", "utilidade", "orcamento"])
        validar_textos_pedido(dados)
        resultado = self._executar(dados, incluir_reparo=True)
        catalogo = {}
        for peca in resultado["componentes_selecionados"]:
            catalogo.setdefault(peca["categoria"], []).append(ficha_catalogo(peca))
        proprias = pecas_proprias(dados.get("pecas_proprias", {}))
        detalhes = obter_detalhes_proprias(proprias)
        percentual = dados.get("percentual_perifericos", 0)
        orcamento = validar_orcamento(dados["orcamento"])
        _, teto_perifericos = dividir_orcamento(orcamento, percentual)
        aparencia = validar_aparencia(dados.get("aparencia"))
        validar_disponibilidade(catalogo, proprias, percentual)
        perifericos = planejar_perifericos(catalogo, teto_perifericos, proprias,
                                                   dados["utilidade"], aparencia["cor"], percentual)
        margem = min(orcamento / 2, max(800, orcamento * 0.25))
        pedido = {**dados, "prioridade_montagem": resultado["prioridade_montagem"]}
        prompt = criar_prompt(pedido, orcamento, margem, catalogo, percentual, detalhes,
                                      perifericos, planejamento_componentes=resultado["planejamento_orcamento"],
                                      preferencia_neutra=True)
        return {**resultado, "catalogo": catalogo, "prompt": prompt, "proprias": proprias,
                "detalhes_proprias": detalhes}

    def gerar_build(self, usuario_id, dados, modelo="gemini-3.5-flash-lite", tentativas_correcao=1):
        """Gera pela estratégia experimental e repara excesso de custo; não salva a build."""
        with BloquearGeracaoService().executar(usuario_id):
            BuildSalva.verificar_espaco(usuario_id)
            preparado = self.preparar_geracao(dados)
            aparencia = validar_aparencia(dados.get("aparencia"))
            build = gerar_candidata(
                usuario_id, preparado["prompt"], modelo, preparado["catalogo"],
                validar_orcamento(dados["orcamento"]), dados.get("percentual_perifericos", 0),
                preparado["proprias"], preparado["detalhes_proprias"], dados.get("rede") or {},
                tentativas_correcao=tentativas_correcao,
                revisar_investimento=perfil_revisa_investimento(dados["utilidade"]),
                cor=aparencia["cor"], aparencia=aparencia,
                armazenamento_minimo_gb=preparado["armazenamento_minimo_gb"],
                ajustar_orcamento=True, catalogo_reparo=preparado["catalogo_reparo"])
            return {**preparado, "build": build}

    def _catalogo_reparo(self, contexto, selecionados, excluidas):
        catalogo = {}
        for peca in selecionados:
            catalogo.setdefault(peca["categoria"], []).append(ficha_catalogo(peca))
        for tipo in AjustarOrcamentoBuildService.AJUSTAVEIS:
            if tipo in excluidas:
                continue
            # Não enviar o pool inteiro à IA; usá-lo só para reparar a resposta concreta.
            fichas = [ficha_catalogo(p) for p in contexto["pools"].get(tipo, [])]
            catalogo[tipo] = list({p["id"]: p for p in [*catalogo.get(tipo, []), *fichas]}.values())
        return catalogo

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
        
        validar_rede(rede)
        aparencia = validar_aparencia(dados.get("aparencia"))
        
        proprias = pecas_proprias(dados.get("pecas_proprias", {}))
        teto_peca, teto_perifericos = self._planejar_orcamento(dados)
        
        return {"prioridade": prioridade, "limite": limite, "categoria": categoria,
                "rede": rede, "aparencia": aparencia, "proprias": proprias,
                "teto_peca": teto_peca, "teto_perifericos": teto_perifericos,
                "utilidade": utilidade, "armazenamento_minimo_gb": armazenamento,
                "teto_pc": float(dividir_orcamento(dados["orcamento"], dados.get("percentual_perifericos", 0))[0]),
                "limites": {m.__tablename__: limites.get(m.__tablename__, limite if m in self.MODELOS_BENCHMARK
                            else self.LIMITE_PLACAS_MAE if m.__tablename__ == "placa_mae"
                            else self.LIMITE_MEMORIAS if m.__tablename__ == "memoria_ram" else 12) for m in MODELOS_PECAS}}

    @staticmethod
    def _planejar_orcamento(dados):
        orcamento = validar_orcamento(dados["orcamento"])
        percentual = dados.get("percentual_perifericos", 0)
        
        if type(percentual) is not int or not 0 <= percentual <= 99:
            raise ValueError("A porcentagem para periféricos deve ser de 0 a 99")
        
        teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
        
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
            periferico = modelo.__tablename__ in PERIFERICOS
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
            pecas = aplicar_teto(contexto, tipo, pecas)
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


    def _selecionar_demais_pecas(self, contexto, excluidas, selecionados):
        aparencia, rede = contexto["aparencia"], contexto["rede"]
        
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
                    tipo, fichas, contexto["limites"][tipo], contexto["utilidade"], cor=aparencia["cor"])[:contexto["limites"][tipo]]
        self._preservar_referencia_gabinete(contexto, excluidas, catalogo)
        self._preservar_armazenamento(contexto, excluidas, catalogo)

        placas = []
        precisa_placas = "placa_mae" not in excluidas
        precisa_ddr = "memoria_ram" not in excluidas and "placa_mae" not in contexto["proprias"]
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
            ident = id_numerico(peca["id"])
            if not any(p["id"] == ident for p in amostra):
                if len(amostra) >= contexto["limites"][tipo]:
                    amostra.pop()
                amostra.append(ficha_catalogo(peca))
            itens.append({"tipo": tipo, "id": ident, "quantidade": item["quantidade"]})
        contexto["planejamento"]["armazenamento_referencia"] = {
            "itens": itens, "capacidade_total_gb": referencia["capacidade_total_gb"], "custo": referencia["custo"]}

    def _preservar_referencia_gabinete(self, contexto, excluidas, catalogo):
        referencia = contexto["aparencia"]["gabinete_id"]
        if referencia is None or "gabinete" in excluidas:
            return
        peca = next((p for p in contexto["pools"].get("gabinete", []) if id_numerico(p["id"]) == referencia), None)
        if peca:
            amostra = catalogo.setdefault("gabinete", [])
            if not any(p["id"] == referencia for p in amostra):
                if len(amostra) >= contexto["limites"]["gabinete"]:
                    amostra.pop()
                amostra.append(ficha_catalogo(peca))


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
