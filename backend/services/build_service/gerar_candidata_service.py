from services.build_service.ajustar_aparencia_service import ajustar_aparencia
from services.build_service.erros_build import ErroGeracaoBuild
from services.validacoes_service.validar_build_gerada_service import validar_build_gerada
from services.build_service.custos_build_service import dividir_orcamento, resumo_custos
from services.build_service.prompt_build_service import criar_prompt_correcao, codigo_falha
import json
import logging
from time import perf_counter
from copy import deepcopy
from decimal import Decimal
from requests.exceptions import RequestException
from models import BuildSalva
from services.llm_service.llm_service import LLMService
from services.llm_service.reservar_chamada_service import CotaGlobalIAError, ControleIAIndisponivelError
from .completar_ventilacao_service import CompletarVentilacaoService
from services.validacoes_service.requisitos_armazenamento_service import RequisitosArmazenamentoService
from .ajustar_orcamento_build_service import AjustarOrcamentoBuildService
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .planejar_rede_service import PlanejarRedeService

logger = logging.getLogger("services.build_service.criar_build_service")

def gerar_candidata(usuario_id, prompt, modelo, catalogo, orcamento,
                   percentual, proprias, detalhes_proprias, rede, tentativas_correcao=1, revisar_investimento=False, cor="sem-preferencia", aparencia=None, armazenamento_minimo_gb=None, ajustar_orcamento=False, catalogo_reparo=None, utilidade=None):
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
        validada = _validar_candidata_completa(build, catalogo, orcamento, percentual, proprias,
                                                    detalhes_proprias, rede, aparencia or {"cor": cor}, armazenamento_minimo_gb, utilidade)
      except ValueError as erro:
        if not ajustar_orcamento or codigo_falha(erro) != "orcamento":
          raise
        pool_reparo = catalogo_reparo if catalogo_reparo is not None else catalogo
        teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
        def validar_reparo(candidata):
          candidata = CompletarVentilacaoService().executar(
              candidata, pool_reparo, teto_pc, proprias, detalhes_proprias, cor=cor)
          return _validar_candidata_completa(candidata, pool_reparo, orcamento, percentual, proprias,
                                                 detalhes_proprias, rede, aparencia or {"cor": cor}, armazenamento_minimo_gb, utilidade)
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

      if tentativa < limite and revisar_investimento and _ha_margem_para_melhorar(validada, catalogo, teto_pc, proprias):
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


def _validar_candidata_completa(build, catalogo, orcamento, percentual, proprias,
                               detalhes_proprias, rede, aparencia, armazenamento_minimo_gb, utilidade=None):
  validada = validar_build_gerada(build, catalogo, orcamento, percentual, proprias, detalhes_proprias, rede, utilidade=utilidade)
  validada = ajustar_aparencia(validada, catalogo, orcamento, percentual, proprias,
                                   detalhes_proprias, rede, aparencia)
  RequisitosArmazenamentoService.validar_build(
      validada, catalogo, armazenamento_minimo_gb, proprias, detalhes_proprias)
  return validada


def perfil_revisa_investimento(utilidade):
  return PreferenciasPerifericosService.jogos(utilidade) or any(
    termo in utilidade.casefold() for termo in ("pesado", "render", "3d"))


def _ha_margem_para_melhorar(build, catalogo, teto_pc, proprias):
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
