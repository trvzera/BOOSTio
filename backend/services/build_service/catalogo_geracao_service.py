from decimal import Decimal

from services.build_service.constantes_build import CAMPOS_PECAS, PERIFERICOS
from services.build_service.planejar_perifericos_service import PlanejarPerifericosService
from services.build_service.preferencias_cores_service import PreferenciasCoresService
from services.build_service.preferencias_gabinete_service import PreferenciasGabineteService
from services.build_service.planejamento_geracao import ErroPlanejamentoBuild, sugerir_total


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
