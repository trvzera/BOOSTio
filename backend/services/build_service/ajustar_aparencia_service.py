from services.validacoes_service.validar_build_gerada_service import validar_build_gerada
from services.build_service.custos_build_service import dividir_orcamento
import logging
from copy import deepcopy
from .completar_ventilacao_service import CompletarVentilacaoService
from .preferencias_cores_service import PreferenciasCoresService
from .preferencias_gabinete_service import PreferenciasGabineteService

logger = logging.getLogger("services.build_service.criar_build_service")

def ajustar_aparencia(build, catalogo, orcamento, percentual, proprias, detalhes, rede, aparencia):
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
