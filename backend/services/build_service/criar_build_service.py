import json
from math import isfinite
from decimal import Decimal, ROUND_DOWN

from models import Build, BuildSalva, Usuario
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.validacoes import validacao_campos
from services.llm_service.llm_service import LLMService

class CriarBuildService:
  PERIFERICOS = {"monitor", "teclado", "mouse", "fone"}
  CAMPOS_PECAS = (
    "id", "fabricante", "modelo", "preco", "consumo_energia",
    "soquete", "socket", "tipo_memoria", "ddr", "capacidade_gb",
    "potencia_w", "formato", "formatos_placa_mae", "memoria_gb",
    "videointegrado", "cooler", "quantidade_pentes",
  )

  def executar(self, usuario_id, dados, modelo="gemini-3.5-flash-lite"):
    validacao_campos(dados, ["nome", "descricao", "utilidade", "orcamento"])
    if not Usuario.buscar_por_id(usuario_id):
      raise ValueError("Usuario não encontrado")
    BuildSalva.verificar_espaco(usuario_id)

    if isinstance(dados["orcamento"], bool):
      raise ValueError("O orçamento deve ser um número positivo")
    orcamento = float(dados["orcamento"])

    if not isfinite(orcamento) or not 0 < orcamento <= 1000000:
      raise ValueError("O orçamento deve ser um número positivo")
    if Decimal(str(orcamento)) != Decimal(str(orcamento)).quantize(Decimal("0.01")):
      raise ValueError("O orçamento deve ter no máximo duas casas decimais")
    percentual = dados.get("percentual_perifericos", 0)
    if type(percentual) is not int or not 0 <= percentual <= 99:
      raise ValueError("A porcentagem para periféricos deve ser de 0 a 99")
    limite_pc, limite_perifericos = self._dividir_orcamento(orcamento, percentual)

    margem = min(800, float(limite_pc) / 2)

    catalogo = self._gerar_catalogo(float(limite_pc) - margem, float(limite_perifericos))

    obrigatorias = ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete")

    if any(tipo not in catalogo for tipo in obrigatorias) or not ("ssd" in catalogo or "hd" in catalogo):
      raise ValueError("Não há peças suficientes para montar um PC nesse orçamento")
    if percentual and not self.PERIFERICOS.issubset(catalogo):
      raise ValueError("Não há periféricos suficientes no catálogo para a reserva escolhida. Ajuste a porcentagem ou monte manualmente.")

    resposta = LLMService().executar(self._criar_prompt(dados, orcamento, margem, catalogo, percentual), modelo)

    build = json.loads(resposta) if isinstance(resposta, str) else resposta

    dados_build = self._validar_build(build, catalogo, orcamento, percentual)
    componentes = {}
    for item in dados_build["componentes"]:
      selecao = {"id": item["id"], "quantidade": item.get("quantidade", 1)}
      componentes[item["tipo"]] = [selecao] if item["tipo"] in Build.QUANTIDADES else selecao
    estado = BuildSalva.validar_estado({
      "titulo": dados_build["nome"][:100], "descricao": dados_build["descricao"][:300],
      "orcamento": orcamento, "componentes": componentes,
      "incluirPerifericos": percentual > 0, "percentualPerifericos": percentual,
    })
    salva = BuildSalva.criar_limitada(usuario_id, estado, gerada=dados_build)
    return salva.to_dict()

  @classmethod
  def _campos_pecas(cls, peca):
    return {
      campo: valor for campo in cls.CAMPOS_PECAS
      if (valor := getattr(peca, campo, None)) is not None
    }

  @classmethod
  def _gerar_catalogo(cls, preco_maximo, reserva_perifericos=0):
    catalogo = {}
    for modelo in MODELOS_PECAS:
      periferico = modelo.__tablename__ in cls.PERIFERICOS
      if periferico and not reserva_perifericos:
        continue
      pecas = modelo.listar_disponiveis_ate(reserva_perifericos if periferico else preco_maximo, limite=8)
      if pecas:
        catalogo[modelo.__tablename__] = [cls._campos_pecas(peca) for peca in pecas]
    return catalogo

  @staticmethod
  def _criar_prompt(dados, orcamento, margem, catalogo, percentual=0):
    pedido = {campo: dados[campo] for campo in ("nome", "descricao", "utilidade")}
    pc, perifericos = CriarBuildService._dividir_orcamento(orcamento, percentual)
    return (
      "Monte um PC para o pedido abaixo usando somente peças do catálogo. "
      "Responda apenas com JSON contendo nome, descricao, utilidade e componentes; "
      "cada componente deve ter tipo, id e quantidade.\n"
      f"Pedido: {json.dumps(pedido, ensure_ascii=False)}\n"
      f"Orçamento total: R$ {orcamento:.2f}. "
      f"Limite para o PC: R$ {pc:.2f}. Reserva exclusiva para periféricos: R$ {perifericos:.2f} ({percentual}%). " +
      ("Inclua monitor, teclado, mouse e fone; sua soma não pode exceder essa reserva. " if percentual else "Não inclua periféricos. ") +
      f"Cada peça do PC custa no máximo R$ {float(pc) - margem:.2f}; "
      f"reservei R$ {margem:.2f} para as outras peças. "
      "A soma de todos os componentes deve caber no orçamento total. "
      "Inclua exatamente um processador, uma placa_mae, uma memoria_ram, "
      "uma fonte, um gabinete e ao menos um ssd ou hd. "
      "Não repita categorias; use quantidade 1 para peças que não são RAM, SSD, HD ou fan. "
      "Inclua placa_video se o uso e o orçamento permitirem. "
      "Confira socket, memória, gabinete e potência da fonte. "
      "Use apenas IDs do catálogo; não invente peças nem preços.\n"
      f"Catálogo: {json.dumps(catalogo, ensure_ascii=False, separators=(',', ':'))}"
    )

  @staticmethod
  def _validar_build(build, catalogo, orcamento, percentual=0):
    if not isinstance(build, dict) or not isinstance(build.get("componentes"), list):
      raise ValueError("A IA não retornou uma build válida")
    validacao_campos(build, ["nome", "descricao", "utilidade", "componentes"])
    if any(not isinstance(build[campo], str) or not build[campo].strip() for campo in ("nome", "descricao", "utilidade")):
      raise ValueError("A IA retornou textos inválidos para a build")

    pecas = {(tipo, peca["id"]): peca for tipo, itens in catalogo.items() for peca in itens}

    total = Decimal(0)
    total_perifericos = Decimal(0)

    for componente in build["componentes"]:
      if not isinstance(componente, dict):
        raise ValueError("A IA retornou um componente inválido")
      if not isinstance(componente.get("tipo"), str) or type(componente.get("id")) is not int:
        raise ValueError("A IA retornou um ID de peça inválido")
      peca = pecas.get((componente.get("tipo"), componente.get("id")))
      quantidade = componente.get("quantidade", 1)

      if peca is None or type(quantidade) is not int or not 1 <= quantidade <= 64:
        raise ValueError("A IA escolheu uma peça ou quantidade inválida")
      componente["nome"] = f'{peca["fabricante"]} {peca["modelo"]}'
      componente["quantidade"] = quantidade
      componente["preco"] = peca["preco"]
      preco = Decimal(str(peca["preco"])) * quantidade
      total += preco
      if componente["tipo"] in CriarBuildService.PERIFERICOS:
        total_perifericos += preco

    pc, perifericos = CriarBuildService._dividir_orcamento(orcamento, percentual)
    if total > Decimal(str(orcamento)):
      raise ValueError("A build gerada ultrapassou o orçamento")
    if total_perifericos > perifericos or total - total_perifericos > pc:
      raise ValueError("A build gerada não respeitou a divisão do orçamento entre PC e periféricos. Tente novamente ou ajuste os valores.")
    if percentual and not CriarBuildService.PERIFERICOS.issubset({item["tipo"] for item in build["componentes"]}):
      raise ValueError("A IA não incluiu os periféricos solicitados. Tente novamente.")

    build["orcamento"] = orcamento
    build["preco_total"] = float(round(total, 2))

    return build

  @staticmethod
  def _dividir_orcamento(orcamento, percentual):
    total = Decimal(str(orcamento)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    perifericos = (total * percentual / 100).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return total - perifericos, perifericos
