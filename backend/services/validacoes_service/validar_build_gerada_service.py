from decimal import Decimal
from math import isfinite
from models import Build
from utils.validacoes import validacao_campos
from services.build_service.constantes_build import PERIFERICOS
from services.build_service.custos_build_service import dividir_orcamento
from services.build_service.planejamento_geracao import RecusaModeloBuild
from services.build_service.planejar_rede_service import PlanejarRedeService
from services.build_service.preferencias_perifericos_service import PreferenciasPerifericosService
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


def validar_build_gerada(build, catalogo, orcamento, percentual=0, proprias=None, detalhes_proprias=None, rede=None):
  if isinstance(build, dict) and build.get("erro"):
    raise RecusaModeloBuild(build.get("motivo"))
  if not isinstance(build, dict) or not isinstance(build.get("componentes"), list):
    raise ValueError("A IA não retornou uma build válida")
  validacao_campos(build, ["nome", "descricao", "utilidade", "componentes"])
  if any(not isinstance(build[campo], str) or not build[campo].strip() for campo in ("nome", "descricao", "utilidade")):
    raise ValueError("A IA retornou textos inválidos para a build")
  pecas = {(tipo, peca["id"]): peca for tipo, itens in catalogo.items() for peca in itens}
  proprias = proprias or {}
  tipos = []
  total = Decimal(0)
  total_perifericos = Decimal(0)
  for componente in build["componentes"]:
    if not isinstance(componente, dict):
      raise ValueError("A IA retornou um componente inválido")
    tipo = componente.get("tipo")
    if not isinstance(tipo, str) or type(componente.get("id")) is not int:
      raise ValueError("A IA retornou um ID de peça inválido")
    if tipo in tipos or tipo in proprias:
      raise ValueError("A IA repetiu uma categoria de peça")
    tipos.append(tipo)
    peca = pecas.get((tipo, componente["id"]))
    quantidade = componente.get("quantidade", 1)
    if peca is None or type(quantidade) is not int or not 1 <= quantidade <= (64 if tipo in Build.QUANTIDADES else 1):
      raise ValueError("A IA escolheu uma peça ou quantidade inválida")
    valor = peca.get("preco")
    if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)) or not isfinite(valor) or valor <= 0:
      raise ValueError("Uma peça sugerida está sem preço válido no catálogo. Revise as peças ou tente novamente.")
    if peca.get("esgotado") is True:
      raise ValueError("Uma peça sugerida está indisponível no catálogo. Tente novamente.")
    if tipo == "monitor" and not PreferenciasPerifericosService.painel_permitido(peca):
      raise ValueError("O monitor sugerido deve ter painel IPS ou VA confirmado, incluindo Fast IPS e Fast VA. Escolha outro monitor do catálogo dentro da reserva.")
    if tipo == "fan" and (type(peca.get("quantidade")) is not int or not 1 <= peca["quantidade"] <= 64):
      raise ValueError("Falta uma quantidade válida de fans por unidade/kit no catálogo. Escolha outro modelo cadastrado.")
    componente["nome"] = f'{peca["fabricante"]} {peca["modelo"]}'
    componente["quantidade"] = quantidade
    componente["preco"] = peca["preco"]
    preco = Decimal(str(peca["preco"])) * quantidade
    total += preco
    if tipo in PERIFERICOS:
      total_perifericos += preco
  if total > Decimal(str(orcamento)):
    raise ValueError("Não foi possível gerar uma configuração dentro do orçamento informado. Ajuste o valor ou revise as peças.")
  teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
  if total_perifericos > teto_perifericos:
    raise ValueError(f"A configuração sugerida ultrapassou o limite reservado para periféricos: subtotal R$ {total_perifericos:.2f}, teto R$ {teto_perifericos:.2f}. Reduza o conjunto em R$ {total_perifericos - teto_perifericos:.2f}, sem transferir verba do PC.")
  if total - total_perifericos > teto_pc:
    raise ValueError(f"A configuração sugerida ultrapassou o limite destinado ao PC: subtotal PC+rede R$ {total - total_perifericos:.2f}, teto R$ {teto_pc:.2f}. Reduza as compras do PC em R$ {total - total_perifericos - teto_pc:.2f}. A sobra dos periféricos não pode ser transferida.")
  finais = set(tipos) | set(proprias)
  rede = rede or {}
  acessorio = {"wifi": "adaptador_wifi", "cabo": "cabo_rede"}.get(rede.get("tipo"))
  escolhidos_rede = set(tipos) & {"adaptador_wifi", "cabo_rede"}
  if "cabo_rede" in escolhidos_rede and rede.get("comprimentoCaboM"):
    item = next(c for c in build["componentes"] if c["tipo"] == "cabo_rede")
    comprimento = pecas[("cabo_rede", item["id"])].get("comprimento_m")
    if type(comprimento) in (int, float, Decimal) and isfinite(comprimento) and comprimento < rede["comprimentoCaboM"]:
      raise ValueError("O cabo de rede sugerido é menor que o comprimento solicitado. Escolha outro cabo cadastrado, respeitando o teto do PC.")
  plano_rede = PlanejarRedeService.executar(catalogo, rede, proprias)
  esperado_rede = {acessorio} if plano_rede["tipo"] and not plano_rede["pendente"] else set()
  if escolhidos_rede != esperado_rede:
    raise ValueError("A IA não respeitou a escolha de conexão da build")
  if esperado_rede:
    item_rede = next(c for c in build["componentes"] if c["tipo"] == acessorio)
    if item_rede["id"] not in plano_rede["ids_permitidos"]:
      raise ValueError("O acessório de rede não atende ao comprimento ou à velocidade solicitada. Escolha um dos IDs permitidos no planejamento de rede.")
  if percentual and not PERIFERICOS <= finais:
    raise ValueError("A IA não incluiu os periféricos solicitados. Tente novamente.")
  if not {"processador", "placa_mae", "memoria_ram", "fonte", "gabinete"} <= finais or not {"ssd", "hd"} & finais:
    raise ValueError("A IA não completou as peças obrigatórias da build")


  verificacao = [{**peca, "categoria": tipo} for tipo, itens in catalogo.items() for peca in itens]
  componentes = {item["tipo"]: {"id": item["id"], "quantidade": item["quantidade"]}
                 for item in build["componentes"]}
  for tipo, nome in proprias.items():
    especificacoes = (detalhes_proprias or {}).get(tipo, {}).get("especificacoes_confirmadas", {})
    if especificacoes:
      identificador = "proprio-" + tipo
      verificacao.append({**especificacoes, "id": identificador, "categoria": tipo})
      componentes[tipo] = {"id": identificador, "quantidade": 1}
    else:
      componentes[tipo] = {"proprio": nome, "quantidade": 1}
  diagnostico = AvaliarCompatibilidadeService().executar({"componentes": componentes}, catalogo=verificacao)
  if diagnostico["erros"]:
    motivos = "; ".join(regra["titulo"] for regra in diagnostico["erros"])
    raise ValueError("A configuração sugerida contém incompatibilidades: " + motivos + ". Revise as peças ou tente novamente.")
  if diagnostico["pecasPendentes"]:
    raise ValueError("A IA não completou as peças obrigatórias da build: " + ", ".join(diagnostico["pecasPendentes"]) + ". Tente novamente.")
  regras_essenciais={'fonte-potencia','air_cooler-socket','water_cooler-socket'}
  desconhecidas=[r['titulo'] for r in diagnostico['naoVerificado'] if r['codigo'] in regras_essenciais]
  if desconhecidas:
    raise ValueError('Faltam dados para validar a combinação: '+', '.join(desconhecidas)+'. Escolha peças com dados confirmados ou complete a ficha.')
  fans = diagnostico.get("fans")
  if fans and fans["total"] is not None and fans["capacidade"] is not None and fans["total"] < fans["capacidade"]:
    raise ValueError("A IA não completou a ventilação do gabinete: faltam " + str(fans["capacidade"] - fans["total"]) +
                     " fans nas posições cadastradas. Desconte as fans de fábrica e do water cooler, use unidades/kits compatíveis e preserve o teto do PC.")
  if "fan" not in finais and not any(
      type((fans or {}).get(campo)) in (int, float) and (fans or {})[campo] > 0
      for campo in ("inclusas", "radiador")
  ):
    raise ValueError("A IA não incluiu fans para a ventilação do gabinete. Inclua fans compatíveis e dentro do teto do PC, sem repetir as inclusas no gabinete ou no water cooler.")
  build["orcamento"] = orcamento
  build["preco_total"] = float(round(total, 2))
  return build
