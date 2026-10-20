import json
from math import isfinite

from models import Build, BuildSalva, Usuario
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.validacoes import validacao_campos
from services.llm_service.llm_service import LLMService

class CriarBuildService:
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

    if isinstance(dados["orcamento"], bool):
      raise ValueError("O orçamento deve ser um número positivo")
    orcamento = float(dados["orcamento"])

    if not isfinite(orcamento) or orcamento <= 0:
      raise ValueError("O orçamento deve ser um número positivo")

    margem = min(800, orcamento / 2)

    catalogo = self._gerar_catalogo(orcamento - margem)

    obrigatorias = ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete")

    if any(tipo not in catalogo for tipo in obrigatorias) or not ("ssd" in catalogo or "hd" in catalogo):
      raise ValueError("Não há peças suficientes para montar um PC nesse orçamento")

    resposta = LLMService().executar(self._criar_prompt(dados, orcamento, margem, catalogo), modelo)

    build = json.loads(resposta) if isinstance(resposta, str) else resposta

    dados_build = self._validar_build(build, catalogo, orcamento)
    
    BuildSalva.migrar_geradas(usuario_id)
    gerada = Build.criar_gerada(usuario_id, dados_build)
    BuildSalva.migrar_geradas(usuario_id)
    salva = BuildSalva.buscar(usuario_id, gerada.id)
    salva.salvar_estado({**salva.estado, "descricao": dados_build["descricao"][:300], "orcamento": orcamento})
    return salva.to_dict()

  @classmethod
  def _campos_pecas(cls, peca):
    return {
      campo: valor for campo in cls.CAMPOS_PECAS
      if (valor := getattr(peca, campo, None)) is not None
    }

  @classmethod
  def _gerar_catalogo(cls, preco_maximo):
    catalogo = {}
    for modelo in MODELOS_PECAS:
      if modelo.__tablename__ in ("monitor", "teclado", "mouse", "fone"):
        continue
      pecas = modelo.listar_disponiveis_ate(preco_maximo, limite=8)
      if pecas:
        catalogo[modelo.__tablename__] = [cls._campos_pecas(peca) for peca in pecas]
    return catalogo

  @staticmethod
  def _criar_prompt(dados, orcamento, margem, catalogo):
    pedido = {campo: dados[campo] for campo in ("nome", "descricao", "utilidade")}
    return (
      "Monte um PC para o pedido abaixo usando somente peças do catálogo. "
      "Responda apenas com JSON contendo nome, descricao, utilidade e componentes; "
      "cada componente deve ter tipo, id e quantidade.\n"
      f"Pedido: {json.dumps(pedido, ensure_ascii=False)}\n"
      f"Orçamento total: R$ {orcamento:.2f}. "
      f"Cada peça custa no máximo R$ {orcamento - margem:.2f}; "
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
  def _validar_build(build, catalogo, orcamento):
    if not isinstance(build, dict) or not isinstance(build.get("componentes"), list):
      raise ValueError("A IA não retornou uma build válida")
    validacao_campos(build, ["nome", "descricao", "utilidade", "componentes"])

    pecas = {(tipo, peca["id"]): peca for tipo, itens in catalogo.items() for peca in itens}

    total = 0

    for componente in build["componentes"]:
      if not isinstance(componente, dict):
        raise ValueError("A IA retornou um componente inválido")
      peca = pecas.get((componente.get("tipo"), componente.get("id")))
      quantidade = componente.get("quantidade", 1)

      if peca is None or type(quantidade) is not int or quantidade < 1:
        raise ValueError("A IA escolheu uma peça ou quantidade inválida")
      componente["nome"] = f'{peca["fabricante"]} {peca["modelo"]}'
      componente["preco"] = peca["preco"]
      total += peca["preco"] * quantidade

    if total > orcamento:
      raise ValueError("A build gerada ultrapassou o orçamento")

    build["orcamento"] = orcamento
    build["preco_total"] = round(total, 2)

    return build
