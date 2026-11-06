from services.build_service.constantes_build import CAMPOS_PECAS, PERIFERICOS
import logging
from time import perf_counter
from decimal import Decimal
from math import isfinite

from models.build_salva import MODELOS
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.build_service.planejar_perifericos_service import PlanejarPerifericosService
from services.build_service.amostrar_catalogo_service import AmostrarCatalogoService
from services.build_service.preferencias_perifericos_service import PreferenciasPerifericosService
from services.build_service.preferencias_cores_service import PreferenciasCoresService
from services.build_service.planejar_rede_service import PlanejarRedeService
from services.build_service.preferencias_gabinete_service import PreferenciasGabineteService
from services.build_service.planejamento_geracao import ErroPlanejamentoBuild, sugerir_total

logger = logging.getLogger("services.build_service.criar_build_service")



def preparar_catalogo(dados, proprias, rede, aparencia, orcamento, margem, teto_pc, teto_perifericos):
  excluidas = set(proprias)
  if {"ssd", "hd"} & excluidas:
    excluidas.update(("ssd", "hd"))
  if {"air_cooler", "water_cooler"} & excluidas:
    excluidas.update(("air_cooler", "water_cooler"))
  acessorio_rede = {"wifi": "adaptador_wifi", "cabo": "cabo_rede"}.get(rede.get("tipo"))
  excluidas.update({"adaptador_wifi", "cabo_rede"} - ({acessorio_rede} if rede.get("possuiAcessorio") is False else set()))
  inicio_catalogo = perf_counter()
  catalogo = gerar_catalogo(min(orcamento - margem, teto_pc), teto_perifericos, excluidas,
                                aparencia["gabinete_id"] if "gabinete" not in proprias else None, dados["utilidade"], cor=aparencia["cor"], aparencia=aparencia, rede=rede)
  if acessorio_rede and rede.get("possuiAcessorio") is False:
    catalogo[acessorio_rede] = PlanejarRedeService.opcoes(catalogo, rede, proprias)
  logger.info("Geração: etapa=catalogo duracao_ms=%d categorias=%d", (perf_counter()-inicio_catalogo)*1000, len(catalogo))
  return catalogo


def validar_disponibilidade(catalogo, proprias, percentual):
  disponiveis = set(catalogo) | set(proprias)
  obrigatorias = {"processador", "placa_mae", "memoria_ram", "fonte", "gabinete"}
  if not obrigatorias <= disponiveis or not {"ssd", "hd"} & disponiveis:
    raise ErroPlanejamentoBuild("Não há peças suficientes para montar um PC nesse orçamento. Faltam opções disponíveis de componentes obrigatórios no catálogo recebido. Revise o orçamento ou as peças já possuídas.",
                                "catalogo", "Faltam opções para completar o PC", "pecas")
  if percentual and "monitor" not in disponiveis:
    raise ErroPlanejamentoBuild("Não há monitor com painel IPS ou VA confirmado dentro da reserva. Revise o orçamento ou a porcentagem de periféricos; nenhuma build foi salva.",
                                "perifericos", "Não encontramos um monitor dentro da reserva", "perifericos")
  if percentual and not PERIFERICOS <= disponiveis:
    raise ErroPlanejamentoBuild("Não há opções disponíveis para completar os periféricos dentro da reserva. Revise a porcentagem, o orçamento ou os itens já possuídos.",
                                "perifericos", "Não foi possível completar os periféricos", "perifericos")


def planejar_perifericos(catalogo, teto_perifericos, proprias, utilidade, cor, percentual):
  plano_perifericos = PlanejarPerifericosService().executar(catalogo, teto_perifericos, proprias, utilidade, cor=cor) if percentual else None
  if plano_perifericos and not plano_perifericos["viavel"]:
    minimo = plano_perifericos.get("minimo_catalogado")
    detalhe = f" O menor conjunto disponível custa R$ {minimo:.2f}, mas a reserva é de R$ {teto_perifericos:.2f}." if minimo is not None else ""
    raise ErroPlanejamentoBuild("Não há um conjunto completo de periféricos dentro da porcentagem reservada." + detalhe + " Revise a porcentagem ou o orçamento; nenhuma build foi salva.",
                                "perifericos", "O conjunto de periféricos não cabe na reserva", "perifericos",
                                sugerir_total(percentual, minimo_perifericos=minimo) if minimo is not None else None)
  return plano_perifericos


def campos_pecas(peca):
  return campos_catalogo({**peca.to_catalogo(), "id": peca.id})


def campos_catalogo(dados):
  dados = dict(dados)
  dados.update(PreferenciasCoresService.metadados(dados))
  if dados.get("categoria") == "gabinete":
    dados.update({chave + "_referencia": valor for chave, valor in PreferenciasGabineteService.identificar(dados).items() if valor})
  return {
    campo: float(valor) if isinstance(valor, Decimal) else valor for campo in CAMPOS_PECAS
    if (valor := dados.get(campo)) is not None
  }


def gerar_catalogo(preco_maximo, reserva_perifericos=0, excluidas=(), referencia_gabinete=None, utilidade="", cor="sem-preferencia", aparencia=None, rede=None):
  catalogo = {}
  for modelo in MODELOS_PECAS:
    periferico = modelo.__tablename__ in PERIFERICOS
    if modelo.__tablename__ in excluidas or (periferico and not reserva_perifericos):
      continue
    pecas = modelo.listar_disponiveis_ate(reserva_perifericos if periferico else preco_maximo, limite=200)
    if pecas:
      fichas = [campos_pecas(peca) for peca in pecas]
      if modelo.__tablename__ == "monitor":
        fichas = [p for p in fichas if PreferenciasPerifericosService.painel_permitido(p)]
      if modelo.__tablename__ in ("cabo_rede", "adaptador_wifi") and rede:
        fichas = PlanejarRedeService.opcoes({modelo.__tablename__: fichas}, rede)
      if fichas:
        catalogo[modelo.__tablename__] = AmostrarCatalogoService().executar(modelo.__tablename__, fichas, utilidade=utilidade, cor=cor)


        amostra = catalogo[modelo.__tablename__]
        variantes = []
        for selecionada in list(amostra):
          for variante in PreferenciasCoresService.alternativas_equivalentes(selecionada, fichas, cor)[:1]:
            if variante not in amostra and variante not in variantes:
              variantes.append(variante)
        amostra.extend(variantes[:3])
        if modelo.__tablename__ == "gabinete" and aparencia:
          for destaque in PreferenciasGabineteService.destaques(fichas, aparencia):
            if destaque not in amostra:
              amostra.append(destaque)
  if referencia_gabinete is not None and "gabinete" not in excluidas:
    referencia = MODELOS["gabinete"].buscar_por_id(referencia_gabinete)
    if referencia and referencia.publicavel and referencia.ficha_montagem_validada is not False:
      peca = campos_pecas(referencia)
      preco = peca.get("preco")
      if peca.get("esgotado") is False and type(preco) in (int, float) and isfinite(preco) and 0 < preco <= preco_maximo:
        amostra = catalogo.setdefault("gabinete", [])
        if not any(item["id"] == referencia_gabinete for item in amostra):
          if len(amostra) >= 12:
            amostra[-1] = peca
          else:
            amostra.append(peca)
  return catalogo
