"""O pedido de build validado uma única vez: um dicionário com os valores que o resto da geração usa."""
from models.build_salva import MODELOS
from utils.aparencia import validar_aparencia
from utils.validacoes import validacao_campos
from services.validacoes_service.validar_pedido_build_service import (
  validar_orcamento, validar_rede, validar_prioridade_montagem, validar_preferencia_processador, pecas_proprias)
from services.validacoes_service.requisitos_armazenamento_service import RequisitosArmazenamentoService
from .custos_build_service import dividir_orcamento
from .fichas_catalogo import campos_pecas
from .planejamento_geracao import validar_minimos, validar_percentual
from .preferencias_perifericos_service import PreferenciasPerifericosService


def montar_pedido(utilidade, orcamento, percentual, rede, aparencia, proprias, revisa_investimento,
                  prioridade="custo_beneficio", preferencia_processador="sem-preferencia",
                  armazenamento_minimo_gb=None, nome="", descricao="", detalhes_proprias=None):
  """Junta os campos do pedido e os valores que o resto da geração calcula a partir deles."""
  teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
  margem = min(orcamento / 2, max(800, orcamento * 0.25))   # folga que o seletor deixa abaixo do orçamento para a IA
  return {
    "nome": nome, "descricao": descricao, "utilidade": utilidade,
    "orcamento": orcamento, "percentual": percentual, "rede": rede, "aparencia": aparencia,
    "proprias": proprias, "prioridade": prioridade, "preferencia_processador": preferencia_processador,
    "armazenamento_minimo_gb": armazenamento_minimo_gb, "revisa_investimento": revisa_investimento,
    "teto_pc": teto_pc, "teto_perifericos": teto_perifericos, "margem": margem,
    "teto_peca": min(orcamento - margem, teto_pc),           # preço máximo de uma peça do PC no catálogo enviado à IA
    "detalhes_proprias": obter_detalhes_proprias(proprias) if detalhes_proprias is None else detalhes_proprias,
  }


def para_prompt(pedido):
  return {"nome": pedido["nome"], "descricao": pedido["descricao"], "utilidade": pedido["utilidade"],
          "prioridade_montagem": pedido["prioridade"], "preferencia_processador": pedido["preferencia_processador"],
          "armazenamento_minimo_gb": pedido["armazenamento_minimo_gb"], "rede": pedido["rede"],
          "aparencia": pedido["aparencia"]}


def validar_pedido(dados):
  """Confere o pedido e devolve o dicionário do pedido. Só consulta o banco se houver peças próprias."""
  if not isinstance(dados, dict):
    raise ValueError("Informe um objeto com os dados da build")
  validacao_campos(dados, ["orcamento"])
  preferencia = validar_preferencia_processador(dados)
  armazenamento = RequisitosArmazenamentoService.validar_parametro(dados.get("armazenamento_minimo_gb"))
  aparencia = validar_aparencia(dados.get("aparencia"))
  prioridade = validar_prioridade_montagem(dados)
  utilidade = dados.get("utilidade", "")
  if not isinstance(utilidade, str) or len(utilidade) > 120:
    raise ValueError("A utilidade deve ser um texto de até 120 caracteres")

  orcamento = validar_orcamento(dados["orcamento"])
  percentual = validar_percentual(dados.get("percentual_perifericos", 0))
  rede = dados.get("rede")
  rede = {} if rede is None else rede
  validar_rede(rede)
  proprias = pecas_proprias(dados.get("pecas_proprias", {}))
  teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
  validar_minimos(teto_pc, teto_perifericos, percentual, utilidade)

  return montar_pedido(
    utilidade, orcamento, percentual, rede, aparencia, proprias, perfil_revisa_investimento(utilidade),
    prioridade=prioridade, preferencia_processador=preferencia, armazenamento_minimo_gb=armazenamento,
    nome=dados.get("nome", ""), descricao=dados.get("descricao", ""))


def perfil_revisa_investimento(utilidade):
  """Perfis pesados (jogos, render, edição, programação) devem usar bem o teto do PC."""
  return PreferenciasPerifericosService.jogos(utilidade) or any(
    termo in utilidade.casefold() for termo in ("pesado", "render", "3d", "edição", "edicao", "programa"))


def obter_detalhes_proprias(proprias):
  detalhes = {}
  for tipo, nome in proprias.items():
    peca = MODELOS[tipo].buscar_por_nome(nome) if tipo in MODELOS else None
    especificacoes = campos_pecas(peca) if peca else {}
    especificacoes.pop("id", None)
    especificacoes.pop("preco", None)
    detalhes[tipo] = {"modelo_informado": nome, "especificacoes_confirmadas": especificacoes}
  return detalhes
