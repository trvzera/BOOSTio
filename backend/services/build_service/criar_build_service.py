from services.validacoes_service.validar_build_gerada_service import validar_build_gerada
from services.validacoes_service.validar_pedido_build_service import validar_orcamento, validar_rede, validar_prioridade_montagem, validar_textos_pedido, pecas_proprias
from services.build_service.custos_build_service import dividir_orcamento, resumo_custos
from services.build_service.contexto_build_service import obter_detalhes_proprias
from services.build_service.catalogo_geracao_service import preparar_catalogo, validar_disponibilidade, planejar_perifericos
from services.build_service.prompt_build_service import criar_prompt, criar_prompt_correcao, codigo_falha
from services.build_service.constantes_build import PERIFERICOS
from services.build_service.salvar_build_gerada_service import criar_gerada_com_pecas_proprias
from services.validacoes_service.validar_estado_build_service import validar_estado
import json
import logging
from time import perf_counter
from copy import deepcopy
from decimal import Decimal
from math import isfinite
from requests.exceptions import RequestException

from models import Build, BuildSalva, Usuario
from utils.validacoes import validacao_campos
from utils.aparencia import validar_aparencia
from services.llm_service.llm_service import LLMService
from services.llm_service.reservar_chamada_service import CotaGlobalIAError, ControleIAIndisponivelError
from services.validacoes_service.avaliar_compatibilidade_service import AvaliarCompatibilidadeService
from .completar_ventilacao_service import CompletarVentilacaoService
from services.validacoes_service.requisitos_armazenamento_service import RequisitosArmazenamentoService
from .ajustar_orcamento_build_service import AjustarOrcamentoBuildService
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .preferencias_cores_service import PreferenciasCoresService
from .planejar_rede_service import PlanejarRedeService
from .preferencias_gabinete_service import PreferenciasGabineteService
from .planejamento_geracao import RecusaModeloBuild, validar_minimos, orientar_falha

logger = logging.getLogger(__name__)

class ErroGeracaoBuild(ValueError):
  def __init__(self, motivo, orcamento=None, percentual=0, custos=None):
    mensagem, self.geracao = orientar_falha(motivo, orcamento, percentual, custos)
    super().__init__(mensagem)
    self.motivo = str(motivo)

class CriarBuildService:

  def executar(self, usuario_id, dados, modelo="gemini-3.5-flash-lite", tentativas_correcao=1, *, selecao_inteligente=False):
    validacao_campos(dados, ["nome", "descricao", "utilidade", "orcamento"])
    validar_textos_pedido(dados)
    armazenamento_minimo = RequisitosArmazenamentoService.validar_parametro(dados.get("armazenamento_minimo_gb"))
    aparencia = validar_aparencia(dados.get("aparencia"))
    dados = {**dados, "aparencia": aparencia,
             "prioridade_montagem": validar_prioridade_montagem(dados)}
    if not Usuario.buscar_por_id(usuario_id):
      raise ValueError("Usuario não encontrado")
    BuildSalva.verificar_espaco(usuario_id)

    orcamento = validar_orcamento(dados["orcamento"])
    percentual = dados.get("percentual_perifericos", 0)
    if type(percentual) is not int or not 0 <= percentual <= 99:
      raise ValueError("A porcentagem para periféricos deve ser de 0 a 99")
    rede = dados.get("rede")
    if rede is None:
      rede = {}
    validar_rede(rede)
    proprias = pecas_proprias(dados.get("pecas_proprias", {}))
    margem = min(orcamento / 2, max(800, orcamento * 0.25))

    teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
    validar_minimos(teto_pc, teto_perifericos, percentual)
    inicio_prompt = perf_counter()
    reparo = {}
    if selecao_inteligente:
      # Importação tardia: o seletor reutiliza validações e fichas deste gerador.
      # Só prepara candidatos; a trava e o salvamento continuam no fluxo principal.
      from .seletor_inteligente_service import SeletorInteligenteService
      preparado = SeletorInteligenteService().preparar_geracao(dados)
      catalogo = preparado["catalogo"]
      detalhes_proprias = preparado["detalhes_proprias"]
      prompt = preparado["prompt"]
      reparo = {"ajustar_orcamento": True, "catalogo_reparo": preparado["catalogo_reparo"]}
    else:
      catalogo = preparar_catalogo(dados, proprias, rede, aparencia, orcamento, margem, teto_pc, teto_perifericos)
      validar_disponibilidade(catalogo, proprias, percentual)
      plano_perifericos = planejar_perifericos(catalogo, teto_perifericos, proprias, dados["utilidade"], aparencia["cor"], percentual)
      detalhes_proprias = obter_detalhes_proprias(proprias)
      prompt = criar_prompt(dados, orcamento, margem, catalogo, percentual, detalhes_proprias, plano_perifericos)
    logger.info("Geração: etapa=prompt duracao_ms=%d caracteres=%d", (perf_counter()-inicio_prompt)*1000, len(prompt))
    dados_build = self._gerar_validada(usuario_id, prompt, modelo, catalogo, orcamento,
                                     percentual, proprias, detalhes_proprias, rede, tentativas_correcao,
                                     revisar_investimento=self._perfil_revisa_investimento(dados["utilidade"]), cor=aparencia["cor"], aparencia=aparencia,
                                     armazenamento_minimo_gb=armazenamento_minimo, **reparo)
    return self._salvar_build(usuario_id, dados_build, proprias, rede, percentual, aparencia, orcamento)


  def _salvar_build(self, usuario_id, dados_build, proprias, rede, percentual, aparencia, orcamento):
    if proprias:
      return AvaliarCompatibilidadeService().para_resposta(criar_gerada_com_pecas_proprias(usuario_id, dados_build, proprias, rede, percentual, aparencia))

    componentes = {}
    for item in dados_build["componentes"]:
      selecao = {"id": item["id"], "quantidade": item["quantidade"]}
      componentes[item["tipo"]] = [selecao] if item["tipo"] in Build.QUANTIDADES else selecao
    estado = validar_estado({
      "titulo": dados_build["nome"][:100], "descricao": dados_build["descricao"][:300],
      "orcamento": orcamento, "componentes": componentes, "rede": rede,
      "incluirRede": rede.get("tipo") in ("cabo", "wifi"),
      "incluirPerifericos": percentual > 0, "percentualPerifericos": percentual,
      "aparencia": aparencia,
    })
    return AvaliarCompatibilidadeService().para_resposta(BuildSalva.criar_limitada(usuario_id, estado, gerada=dados_build))


  def _gerar_validada(self, usuario_id, prompt, modelo, catalogo, orcamento,
                     percentual, proprias, detalhes_proprias, rede, tentativas_correcao=1, revisar_investimento=False, cor="sem-preferencia", aparencia=None, armazenamento_minimo_gb=None, ajustar_orcamento=False, catalogo_reparo=None):
    armazenamento_minimo_gb = RequisitosArmazenamentoService.validar_parametro(armazenamento_minimo_gb)
    limite = 1 if tentativas_correcao else 0
    instrucao = prompt
    primeira_valida = None
    for tentativa in range(limite + 1):
      if tentativa:
        BuildSalva.verificar_espaco(usuario_id)
      resposta = None
      build = None
      inicio_llm = perf_counter()
      try:
        resposta = LLMService().executar(instrucao, modelo)
        logger.info("Geração: etapa=llm tentativa=%d duracao_ms=%d caracteres_prompt=%d", tentativa+1, (perf_counter()-inicio_llm)*1000, len(instrucao))
        inicio_validacao = perf_counter()
        build = json.loads(resposta) if isinstance(resposta, str) else resposta
        build = PlanejarRedeService.completar(build, catalogo, rede, proprias)
        teto_pc, _ = dividir_orcamento(orcamento, percentual)
        build = CompletarVentilacaoService().executar(build, catalogo, teto_pc, proprias, detalhes_proprias, cor=cor)
        try:
          validada = self._validar_candidata_completa(build, catalogo, orcamento, percentual, proprias,
                                                      detalhes_proprias, rede, aparencia or {"cor": cor}, armazenamento_minimo_gb)
        except ValueError as erro:
          if not ajustar_orcamento or codigo_falha(erro) != "orcamento":
            raise
          pool_reparo = catalogo_reparo if catalogo_reparo is not None else catalogo
          teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
          def validar_reparo(candidata):
            candidata = CompletarVentilacaoService().executar(
                candidata, pool_reparo, teto_pc, proprias, detalhes_proprias, cor=cor)
            return self._validar_candidata_completa(candidata, pool_reparo, orcamento, percentual, proprias,
                                                   detalhes_proprias, rede, aparencia or {"cor": cor}, armazenamento_minimo_gb)
          reparo = AjustarOrcamentoBuildService().executar(
              build, pool_reparo, orcamento, teto_pc, teto_perifericos, validar_reparo, proprias, cor)
          if reparo is None:
            raise
          catalogo = pool_reparo
          validada = reparo["build"]
          validada["ajuste_orcamento"] = reparo["diagnostico"]
          logger.info("Geração: etapa=ajuste_orcamento economia=%.2f trocas=%d",
                      reparo["diagnostico"]["economia"], len(reparo["diagnostico"]["trocas"]))
        resumo = resumo_custos(validada, catalogo)

        if tentativa < limite and revisar_investimento and self._ha_margem_para_melhorar(validada, catalogo, teto_pc, proprias):
          primeira_valida = deepcopy(validada)
          build = validada
          raise ValueError(f"A configuração é válida, mas usa somente R$ {resumo['pc']:.2f} do teto de R$ {teto_pc:.2f} do PC. "
              f"Reavalie combinações próximas de 80% a 100% desse teto (R$ {teto_pc * Decimal('0.8'):.2f} a R$ {teto_pc:.2f}), "
              "buscando melhorias adequadas de CPU/GPU/RAM/SSD para o perfil solicitado, inclusive uso misto. "
              "Não trate o pedido como o PC mais barato possível. Considere incluir GPU dedicada quando fizer sentido para jogar. "
              "O valor maior, sozinho, não comprova desempenho melhor. Preserve tetos, peças próprias e compatibilidades; "
              "não acrescente itens supérfluos. A sobra dos periféricos continua reservada ao usuário, sem reforçar o PC.")
        logger.info("Geração: etapa=validada tentativa=%d duracao_ms=%d", tentativa+1, (perf_counter()-inicio_validacao)*1000)
        return validada
      except ValueError as erro:

        logger.warning("Geração: etapa=revisao tentativa=%d codigo=%s", tentativa+1, codigo_falha(erro))
        if tentativa == limite:
          if primeira_valida is not None:
            return primeira_valida
          raise ErroGeracaoBuild(erro, orcamento, percentual, resumo_custos(build, catalogo)) from erro
        instrucao = criar_prompt_correcao(
            prompt, erro, resposta, build, catalogo, orcamento, percentual, armazenamento_minimo_gb)
      except (RequestException, CotaGlobalIAError, ControleIAIndisponivelError):
        logger.warning("Geração: etapa=provedor tentativa=%d duracao_ms=%d", tentativa+1, (perf_counter()-inicio_llm)*1000)
        if primeira_valida is not None:
          return primeira_valida
        raise

  def _validar_candidata_completa(self, build, catalogo, orcamento, percentual, proprias,
                                 detalhes_proprias, rede, aparencia, armazenamento_minimo_gb):
    validada = validar_build_gerada(build, catalogo, orcamento, percentual, proprias, detalhes_proprias, rede)
    validada = self._ajustar_aparencia(validada, catalogo, orcamento, percentual, proprias,
                                     detalhes_proprias, rede, aparencia)
    RequisitosArmazenamentoService.validar_build(
        validada, catalogo, armazenamento_minimo_gb, proprias, detalhes_proprias)
    return validada


  @staticmethod
  def _perfil_revisa_investimento(utilidade):
    return PreferenciasPerifericosService.jogos(utilidade) or any(
      termo in utilidade.casefold() for termo in ("pesado", "render", "3d"))

  @classmethod
  def _ha_margem_para_melhorar(cls, build, catalogo, teto_pc, proprias):
    gasto = Decimal(str(resumo_custos(build, catalogo)["pc"]))
    if gasto >= teto_pc * Decimal("0.75"):
      return False


    for item in build["componentes"]:
      tipo, quantidade = item["tipo"], item["quantidade"]
      if tipo not in ("processador", "placa_video", "memoria_ram", "ssd") or tipo in proprias:
        continue
      preco_atual = Decimal(str(item["preco"]))
      for candidata in catalogo.get(tipo, []):
        preco = Decimal(str(candidata["preco"]))
        if candidata.get("esgotado") is not True and preco > preco_atual and gasto + (preco - preco_atual) * quantidade <= teto_pc:
          return True
    if "placa_video" not in proprias and not any(item["tipo"] == "placa_video" for item in build["componentes"]):
      return any(p.get("esgotado") is not True and gasto + Decimal(str(p["preco"])) <= teto_pc
                 for p in catalogo.get("placa_video", []))
    return False


  def _ajustar_aparencia(self, build, catalogo, orcamento, percentual, proprias, detalhes, rede, aparencia):
    atual = build
    teto_pc, _ = dividir_orcamento(orcamento, percentual)
    for item in list(build["componentes"]):
      tipo = item["tipo"]
      peca = next((p for p in catalogo.get(tipo, []) if p["id"] == item["id"]), None)
      if not peca:
        continue
      if tipo == "gabinete":
        opcoes = [p for p in PreferenciasGabineteService.destaques(catalogo[tipo], aparencia)
                  if PreferenciasGabineteService.prioridade(p, aparencia) < PreferenciasGabineteService.prioridade(peca, aparencia)]
      else:
        opcoes = PreferenciasCoresService.alternativas_equivalentes(peca, catalogo[tipo], aparencia.get("cor"))
      for candidata in opcoes:
        tentativa = deepcopy(atual)
        next(i for i in tentativa["componentes"] if i["tipo"] == tipo)["id"] = candidata["id"]
        try:
          tentativa = CompletarVentilacaoService().executar(tentativa, catalogo, teto_pc, proprias, detalhes, cor=aparencia.get("cor"))
          tentativa = validar_build_gerada(tentativa, catalogo, orcamento, percentual, proprias, detalhes, rede)
        except ValueError:
          continue
        atual = tentativa
        break
    return atual
