from decimal import Decimal, ROUND_CEILING

from services.validacoes_service.requisitos_uso_service import RequisitosUsoService
from .constantes_build import PERIFERICOS
from .planejar_perifericos_service import PlanejarPerifericosService

MINIMO_PC = Decimal("2500")
MINIMO_PERIFERICOS = Decimal("500")


def sugerir_total(percentual, minimo_pc=MINIMO_PC, minimo_perifericos=MINIMO_PERIFERICOS):
    pc = Decimal(str(minimo_pc)) * 100 / (100 - percentual)
    perifericos = Decimal(str(minimo_perifericos)) * 100 / percentual if percentual else Decimal(0)
    return float((max(pc, perifericos) / 100).to_integral_value(rounding=ROUND_CEILING) * 100)


class ErroPlanejamentoBuild(ValueError):
    def __init__(self, mensagem, motivo, titulo, etapa, sugerido=None):
        super().__init__(mensagem)
        self.geracao = {"motivo": motivo, "titulo": titulo, "etapa": etapa}
        if sugerido is not None and 0 < sugerido <= 1000000:
            self.geracao["orcamentoSugerido"] = sugerido


class RecusaModeloBuild(ValueError):
    def __init__(self, motivo):
        self.motivo = motivo if motivo in ("orcamento", "cor", "aparencia", "catalogo", "compatibilidade") else "resposta"
        super().__init__("A IA não encontrou uma configuração válida para o pedido.")


def validar_percentual(percentual):
    if type(percentual) is not int or percentual != 0 and not 10 <= percentual <= 40:
        raise ErroPlanejamentoBuild("Escolha uma porcentagem inteira entre 10% e 40% do orçamento total para os periféricos, ou 0 se não comprar novos periféricos.",
                                   "perifericos", "A porcentagem deve ficar entre 10% e 40%", "perifericos")
    return percentual


def validar_minimos(pc, perifericos, percentual, utilidade=None):
    validar_percentual(percentual)
    minimo = Decimal(str(RequisitosUsoService.minimo_pc(utilidade)))
    sugerido = sugerir_total(percentual, minimo_pc=minimo)
    if pc < minimo:
        raise ErroPlanejamentoBuild(
            f"Reserve pelo menos R$ {minimo:.2f} para as peças do PC para este uso, depois de descontar os periféricos. "
            f"O valor disponível para o PC é R$ {pc:.2f}. Esse mínimo não garante todas as opções do catálogo.",
            "orcamento", "O valor disponível para o PC está abaixo do mínimo do uso", "orcamento", sugerido)
    if percentual and perifericos < MINIMO_PERIFERICOS:
        raise ErroPlanejamentoBuild(
            f"A reserva para periféricos novos deve ser de pelo menos R$ {MINIMO_PERIFERICOS:.2f}. "
            f"Você reservou R$ {perifericos:.2f}. O conjunto disponível no catálogo pode exigir mais.",
            "perifericos", "A reserva dos periféricos está abaixo do mínimo", "perifericos", sugerido)


def orientar_falha(erro, orcamento=None, percentual=0, custos=None):
    texto = str(erro).casefold()
    motivo = erro.motivo if isinstance(erro, RecusaModeloBuild) else (
        "orcamento" if any(p in texto for p in ("orçamento", "ultrapassou o limite", "limite destinado ao pc")) else
        "compatibilidade" if "incompatibil" in texto else
        "catalogo" if any(p in texto for p in ("indisponível", "id de peça", "fora do catálogo")) else
        "pecas" if any(p in texto for p in ("obrigatórias", "ventilação", "fans", "periféricos solicitados", "armazenamento mínimo")) else "resposta")
    if "limite reservado para periféricos" in texto:
        motivo = "perifericos"
    descricoes = {
        "orcamento": ("Não foi possível montar dentro do orçamento", "orcamento",
                       "A combinação sugerida pela IA não coube no orçamento do pedido. Você pode ajustar o valor ou revisar o objetivo."),
        "perifericos": ("Os periféricos não couberam na reserva", "perifericos",
                        "O conjunto sugerido ultrapassou o valor reservado para os periféricos. Revise a porcentagem ou o orçamento total."),
        "cor": ("A IA não encontrou uma combinação na cor escolhida", "aparencia",
                "Não foi possível concluir a montagem com a cor solicitada. Você pode tentar sem essa preferência; isso não confirma que a cor esteja indisponível em todo o catálogo."),
        "aparencia": ("A IA não concluiu a montagem com esse visual", "aparencia",
                      "As preferências de gabinete e aparência podem limitar as combinações. Revise o visual ou tente sem essas preferências."),
        "catalogo": ("Faltaram opções válidas no catálogo", "pecas",
                     "A IA selecionou uma peça indisponível, não cadastrada ou não encontrou uma combinação com as opções recebidas. Revise as peças ou tente novamente."),
        "compatibilidade": ("As peças sugeridas não passaram na compatibilidade", "pecas",
                             "A combinação da IA apresentou um conflito de compatibilidade. Revise as peças próprias ou solicite outra montagem."),
        "pecas": ("A IA não completou todas as peças necessárias", "pecas",
                  "A resposta ficou sem uma peça obrigatória ou sem a ventilação necessária. Revise as peças e tente novamente."),
        "resposta": ("A IA não concluiu uma resposta válida", "objetivo",
                     "A IA retornou uma resposta incompleta ou em um formato que não conseguimos validar. Você pode tentar novamente ou revisar o pedido."),
    }
    titulo, etapa, mensagem = descricoes[motivo]
    dados = {"motivo": motivo, "titulo": titulo, "etapa": etapa}
    if motivo in ("orcamento", "perifericos") and orcamento is not None:
        custos = custos or {}
        sugerido = sugerir_total(percentual, max(MINIMO_PC, Decimal(str(custos.get("pc", 0)))),
                                 max(MINIMO_PERIFERICOS, Decimal(str(custos.get("perifericos", 0)))))

        dados["orcamentoSugerido"] = min(1000000, max(sugerido, float((Decimal(str(orcamento)) * Decimal("1.1") / 100).to_integral_value(rounding=ROUND_CEILING) * 100)))
    if not isinstance(erro, RecusaModeloBuild) and motivo in ("orcamento", "perifericos", "compatibilidade", "pecas"):

        detalhe = str(erro)
        if detalhe.startswith(("A configuração sugerida", "A IA não completou", "A IA não incluiu")):
            mensagem += " " + detalhe[:600]
    return mensagem + " Nenhuma build foi salva. Suas respostas foram preservadas.", dados


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
