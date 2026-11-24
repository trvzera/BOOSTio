"""Conversa com a IA e só devolve uma build que passou na validação.

Cada tentativa segue as mesmas etapas:
  1. chamar a IA com o prompt;
  2. completar o que a IA costuma esquecer (periféricos do plano, rede e ventilação);
  3. validar; se falhar só por orçamento, reparar trocando RAM, SSD, HD ou fan;
  4. em perfis pesados, melhorar o investimento quando sobra margem no teto do PC.
Se a build for inválida, ou válida mas gastando pouco, há uma única nova tentativa com prompt de correção.
"""
import json
import logging
from copy import deepcopy
from decimal import Decimal
from time import perf_counter

from requests.exceptions import RequestException

from models import BuildSalva
from services.llm_service.llm_service import LLMService
from services.llm_service.reservar_chamada_service import CotaGlobalIAError, ControleIAIndisponivelError
from services.validacoes_service.validar_build_gerada_service import validar_build_gerada
from services.validacoes_service.requisitos_armazenamento_service import RequisitosArmazenamentoService
from .ajustar_aparencia_service import ajustar_aparencia
from .ajustar_memoria_aos_slots_service import AjustarMemoriaAosSlotsService
from .ajustar_orcamento_build_service import AjustarOrcamentoBuildService
from .ajustar_perifericos_ao_plano_service import AjustarPerifericosAoPlanoService
from .completar_ventilacao_service import CompletarVentilacaoService
from .custos_build_service import resumo_custos
from .erros_build import ErroGeracaoBuild
from .melhorar_investimento_build_service import MelhorarInvestimentoBuildService
from .planejar_rede_service import PlanejarRedeService
from .prompt_build_service import criar_prompt_correcao, codigo_falha

logger = logging.getLogger("services.build_service.fluxo_geracao_service")

ERROS_DO_PROVEDOR = (RequestException, CotaGlobalIAError, ControleIAIndisponivelError)


def gerar_candidata(usuario_id, pedido, preparado, modelo, tentativas_correcao=1):
  ultima = 1 if tentativas_correcao else 0
  instrucao = preparado["prompt"]
  catalogo = preparado["catalogo"]
  primeira_valida = None
  for tentativa in range(ultima + 1):
    if tentativa:
      BuildSalva.verificar_espaco(usuario_id)
    resposta = build = None
    inicio = perf_counter()
    try:
      resposta = LLMService().executar(instrucao, modelo)
      logger.info("Geração: etapa=llm tentativa=%d duracao_ms=%d caracteres_prompt=%d",
                  tentativa + 1, (perf_counter() - inicio) * 1000, len(instrucao))
      inicio = perf_counter()
      build = json.loads(resposta) if isinstance(resposta, str) else resposta
      build = completar_build(build, pedido, catalogo, preparado["plano_perifericos"])
      validada, catalogo = validar_ou_reparar(build, pedido, catalogo, preparado["catalogo_reparo"])
      if pedido["revisa_investimento"]:
        validada, catalogo = melhorar_investimento(validada, pedido, catalogo, preparado["catalogo_reparo"])

      if tentativa < ultima and pedido["revisa_investimento"] and ha_margem_para_melhorar(validada, catalogo, pedido):
        primeira_valida = deepcopy(validada)
        build = validada
        raise ValueError(mensagem_gasto_baixo(resumo_custos(validada, catalogo)["pc"], pedido["teto_pc"]))
      logger.info("Geração: etapa=validada tentativa=%d duracao_ms=%d", tentativa + 1, (perf_counter() - inicio) * 1000)
      return validada

    except ValueError as erro:
      logger.warning("Geração: etapa=revisao tentativa=%d codigo=%s", tentativa + 1, codigo_falha(erro))
      if tentativa == ultima:
        if primeira_valida is not None:
          return primeira_valida
        raise ErroGeracaoBuild(erro, pedido["orcamento"], pedido["percentual"], resumo_custos(build, catalogo)) from erro
      instrucao = criar_prompt_correcao(preparado["prompt"], erro, resposta, build, catalogo, pedido["orcamento"],
                                        pedido["percentual"], pedido["armazenamento_minimo_gb"])

    except ERROS_DO_PROVEDOR:
      logger.warning("Geração: etapa=provedor tentativa=%d duracao_ms=%d", tentativa + 1, (perf_counter() - inicio) * 1000)
      if primeira_valida is not None:
        return primeira_valida
      raise


def completar_build(build, pedido, catalogo, plano_perifericos):
  """Ajusta os periféricos ao plano e completa a rede e a ventilação que a IA deixou de fora."""
  build, ajuste = AjustarPerifericosAoPlanoService().executar(build, plano_perifericos, catalogo)
  if ajuste:
    logger.info("Geração: etapa=perifericos_no_plano gasto_anterior=%.2f gasto_novo=%.2f reserva=%.2f",
                ajuste["gasto_anterior"], ajuste["gasto_novo"], ajuste["reserva"])
  build = PlanejarRedeService.completar(build, catalogo, pedido["rede"], pedido["proprias"])
  build = AjustarMemoriaAosSlotsService().executar(build, catalogo, pedido["proprias"], pedido["detalhes_proprias"])
  return CompletarVentilacaoService().executar(build, catalogo, pedido["teto_pc"], pedido["proprias"],
                                               pedido["detalhes_proprias"], cor=pedido["aparencia"]["cor"])


def validar(build, pedido, catalogo):
  """Compatibilidade, preços, tetos, aparência e armazenamento mínimo. Lança ValueError se falhar."""
  validada = validar_build_gerada(build, catalogo, pedido["orcamento"], pedido["percentual"], pedido["proprias"],
                                  pedido["detalhes_proprias"], pedido["rede"], utilidade=pedido["utilidade"])
  validada = ajustar_aparencia(validada, catalogo, pedido["orcamento"], pedido["percentual"], pedido["proprias"],
                               pedido["detalhes_proprias"], pedido["rede"], pedido["aparencia"])
  RequisitosArmazenamentoService.validar_build(validada, catalogo, pedido["armazenamento_minimo_gb"],
                                               pedido["proprias"], pedido["detalhes_proprias"])
  return validada


def validador_no_reparo(pedido, catalogo_reparo):
  """Validação usada pelos serviços de troca: completa a ventilação de novo e valida no catálogo de reparo."""
  def validar_troca(candidata):
    candidata = CompletarVentilacaoService().executar(candidata, catalogo_reparo, pedido["teto_pc"], pedido["proprias"],
                                                      pedido["detalhes_proprias"], cor=pedido["aparencia"]["cor"])
    return validar(candidata, pedido, catalogo_reparo)
  return validar_troca


def validar_ou_reparar(build, pedido, catalogo, catalogo_reparo):
  """Valida a build. Se falhar só por orçamento, troca RAM, SSD, HD ou fan por opções mais baratas.
  Devolve a build validada e o catálogo em que ela foi validada."""
  try:
    return validar(build, pedido, catalogo), catalogo
  except ValueError as erro:
    if codigo_falha(erro) != "orcamento":
      raise
    reparo = AjustarOrcamentoBuildService().executar(
      build, catalogo_reparo, pedido["orcamento"], pedido["teto_pc"], pedido["teto_perifericos"],
      validador_no_reparo(pedido, catalogo_reparo), pedido["proprias"], pedido["aparencia"]["cor"])
    if reparo is None:
      raise
  validada = reparo["build"]
  validada["ajuste_orcamento"] = reparo["diagnostico"]
  logger.info("Geração: etapa=ajuste_orcamento economia=%.2f trocas=%d",
              reparo["diagnostico"]["economia"], len(reparo["diagnostico"]["trocas"]))
  return validada, catalogo_reparo


def melhorar_investimento(validada, pedido, catalogo, catalogo_reparo):
  """Em perfis pesados, troca peças por opções melhores enquanto couber no teto do PC."""
  melhoria = MelhorarInvestimentoBuildService().executar(
    validada, catalogo_reparo, pedido["teto_pc"], pedido["proprias"], validador_no_reparo(pedido, catalogo_reparo))
  if melhoria is None:
    return validada, catalogo
  validada, trocas = melhoria
  validada["melhoria_investimento"] = {"trocas": trocas}
  logger.info("Geração: etapa=melhoria_investimento trocas=%d", len(trocas))
  return validada, catalogo_reparo


def ha_margem_para_melhorar(build, catalogo, pedido):
  """A build gasta menos que o LIMIAR do teto do PC e existe CPU, GPU, RAM ou SSD melhor que ainda caberia."""
  teto_pc, proprias = pedido["teto_pc"], pedido["proprias"]
  gasto = Decimal(str(resumo_custos(build, catalogo)["pc"]))
  if gasto >= teto_pc * MelhorarInvestimentoBuildService.LIMIAR:
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


def mensagem_gasto_baixo(gasto_pc, teto_pc):
  return (f"A configuração é válida, mas usa somente R$ {gasto_pc:.2f} do teto de R$ {teto_pc:.2f} do PC. "
          f"Reavalie combinações próximas de 80% a 100% desse teto (R$ {teto_pc * Decimal('0.8'):.2f} a R$ {teto_pc:.2f}), "
          "buscando melhorias adequadas de CPU/GPU/RAM/SSD para o perfil solicitado, inclusive uso misto. "
          "Não trate o pedido como o PC mais barato possível. Considere incluir GPU dedicada quando fizer sentido para jogar. "
          "O valor maior, sozinho, não comprova desempenho melhor. Preserve tetos, peças próprias e compatibilidades; "
          "não acrescente itens supérfluos. A sobra dos periféricos continua reservada ao usuário, sem reforçar o PC.")
