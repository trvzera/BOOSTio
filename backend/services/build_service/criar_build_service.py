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
    teto_peca = orcamento - margem

    exemplo_saida = {
        "nome": "<nome do pedido>",
        "descricao": "<descricao do pedido>",
        "utilidade": "<utilidade do pedido>",
        "componentes": [
            {"tipo": "processador", "id": "<id do catálogo>", "quantidade": 1},
            {"tipo": "memoria_ram", "id": "<id do catálogo>", "quantidade": 2},
        ],
    }
    exemplo_erro = {"erro": "<motivo objetivo em uma frase>", "componentes": []}

    return (
        "# PAPEL\n"
        "Você é um montador de PCs especialista em compatibilidade de hardware. "
        "Monte o melhor PC possível para o pedido abaixo, usando exclusivamente "
        "peças do catálogo fornecido. Decida apenas por especificações técnicas, "
        "compatibilidade, adequação ao uso e preço.\n\n"

        "# PEDIDO\n"
        f"{json.dumps(pedido, ensure_ascii=False)}\n\n"

        "# ORÇAMENTO\n"
        f"- Orçamento total (teto rígido): R$ {orcamento:.2f}.\n"
        f"- Nenhuma peça individual pode custar mais que R$ {teto_peca:.2f}.\n"
        f"- R$ {margem:.2f} estão reservados para as demais peças; "
        "considere isso ao distribuir o orçamento.\n"
        "- A soma de (preço × quantidade) de todos os componentes deve ser "
        f"menor ou igual a R$ {orcamento:.2f}. Some item por item antes de responder.\n"
        "- Concentre a maior parte do orçamento nas peças obrigatórias "
        "(processador, placa_mae, memoria_ram, armazenamento, fonte e gabinete): "
        "dentro do que o uso pedir e da compatibilidade, prefira as opções de maior "
        "custo (e, portanto, maior capacidade) nessas categorias. "
        "Itens opcionais (placa_video, fan, periféricos) usam o que sobrar.\n"
        "- Não é obrigatório gastar todo o orçamento; compatibilidade vem antes.\n\n"

        "# PASSO 1: ANALISE O USO\n"
        "Leia nome, descricao e utilidade e classifique o uso principal. "
        "Distribua o orçamento conforme o perfil:\n"
        "- Jogos: priorize placa_video e processador; RAM e armazenamento "
        "em nível adequado, sem excesso.\n"
        "- Edição de vídeo/imagem, 3D e renderização: priorize mais memoria_ram "
        "(maior capacidade total), processador com bom desempenho multi-núcleo, "
        "armazenamento rápido e amplo; placa_video conforme o software citado.\n"
        "- Programação, estudo e trabalho de escritório: priorize processador, "
        "memoria_ram e ssd; placa_video dedicada normalmente é dispensável.\n"
        "- Servidor, NAS ou uso misto: priorize armazenamento, RAM e estabilidade "
        "(fonte e gabinete com boa ventilação).\n"
        "- Se o uso combinar perfis, atenda primeiro o mais exigente citado no pedido. "
        "Se o uso não se encaixar em nenhum perfil, escolha pela necessidade descrita "
        "e não por suposição.\n\n"

        "# PASSO 2: REGRAS OBRIGATÓRIAS (em ordem de prioridade)\n"
        "1. Use somente IDs e tipos que existam no catálogo. "
        "Nunca invente peças, IDs, preços ou especificações.\n"
        "2. Inclua exatamente um processador, uma placa_mae, uma memoria_ram "
        "(com quantidade de pentes conforme a regra de dual channel abaixo), "
        "uma fonte e um gabinete.\n"
        "3. Inclua ao menos um armazenamento (ssd ou hd). "
        "Prefira ssd quando o orçamento permitir.\n"
        "4. Não repita categorias. Use quantidade 1 para tudo, "
        "exceto memoria_ram, ssd, hd e fan.\n"
        "5. Use apenas peças disponíveis, se o catálogo tiver esse campo.\n"
        "6. Sem preferência pessoal: não favoreça marca, linha ou fabricante. "
        "Entre opções equivalentes, decida por especificação, compatibilidade e preço.\n\n"

        "# MEMÓRIA RAM: DUAL CHANNEL\n"
        "- Priorize configurações que ativem dual channel: quantidade par de pentes "
        "(2 ou 4, conforme os slots da placa_mae), todos do mesmo modelo.\n"
        "- Prefira 2 pentes de capacidade menor a 1 pente de capacidade maior "
        "com a mesma capacidade total, desde que a placa_mae tenha 2 ou mais slots.\n"
        "- Use 1 único pente apenas se a placa_mae tiver um só slot ou se não houver "
        "opção compatível no catálogo.\n"
        "- A quantidade nunca pode exceder os slots da placa_mae, e a capacidade total "
        "deve respeitar o máximo suportado por ela.\n\n"

        "# VÍDEO INTEGRADO E PLACA DE VÍDEO\n"
        "- Primeiro verifique se o processador escolhido tem vídeo integrado "
        "(use apenas o dado do catálogo; se o catálogo não informar, considere que não tem).\n"
        "- Se tiver vídeo integrado, a placa_video NÃO é necessária: omita-a "
        "e redirecione o orçamento para as peças obrigatórias, "
        "a menos que o uso exija GPU dedicada (por exemplo, jogos pesados, "
        "renderização 3D ou aceleração por GPU citada no pedido).\n"
        "- Se não tiver vídeo integrado, inclua uma placa_video compatível "
        "(o PC precisa ter saída de vídeo).\n\n"

        "# PERIFÉRICOS\n"
        "- Inclua periféricos (por exemplo monitor, teclado, mouse, headset) "
        "somente se o pedido mencionar que precisa deles, e apenas dos tipos "
        "que existirem no catálogo.\n"
        "- Cada periférico entra com quantidade 1 e conta no orçamento total.\n"
        "- Se o pedido pedir um periférico que não exista no catálogo, "
        "não invente: monte o PC sem ele.\n"
        "- Se o pedido não mencionar periféricos, não inclua nenhum.\n\n"

        "# COMPATIBILIDADE (confira cada item)\n"
        "- Socket: o do processador deve ser igual ao da placa_mae.\n"
        "- Memória: tipo (ex.: DDR4/DDR5), quantidade de módulos e capacidade "
        "devem ser suportados pela placa_mae.\n"
        "- Gabinete: o formato da placa_mae (ATX, mATX, ITX) deve caber no gabinete; "
        "confira também o comprimento da placa_video, se o catálogo informar.\n"
        "- Fonte: a potência deve cobrir o consumo estimado de processador, placa_video "
        "e demais peças, com folga de pelo menos 30%, e ter os conectores necessários.\n"
        "- Armazenamento: a interface (SATA/M.2) deve ser suportada pela placa_mae.\n"
        "- Se o catálogo não trouxer um dado necessário para confirmar uma compatibilidade, "
        "prefira outra peça cujo dado esteja disponível.\n\n"

        "# VERIFICAÇÃO ANTES DE RESPONDER (faça internamente, sem escrever)\n"
        "1. Todos os IDs existem no catálogo e o tipo bate com o do catálogo?\n"
        "2. A soma total respeita o orçamento e cada peça respeita o teto por peça?\n"
        "3. Socket, memória, gabinete, fonte e armazenamento são compatíveis?\n"
        "4. A memória usa quantidade par de pentes (dual channel) quando possível?\n"
        "5. O vídeo integrado foi verificado antes de decidir pela placa_video?\n"
        "6. Os periféricos só aparecem se foram pedidos?\n"
        "7. Há categorias repetidas ou quantidades fora da regra?\n"
        "8. A montagem reflete o perfil de uso e a maior parte do orçamento "
        "está nas peças obrigatórias?\n"
        "Se alguma verificação falhar, corrija a montagem antes de responder.\n\n"

        "# FORMATO DE SAÍDA\n"
        "Responda apenas com um objeto JSON válido, sem markdown, sem comentários "
        "e sem texto antes ou depois. Campos: nome, descricao, utilidade e componentes. "
        "Cada componente tem tipo (string), id (exatamente como no catálogo) "
        "e quantidade (inteiro >= 1). Copie nome, descricao e utilidade do pedido.\n"
        f"Estrutura (valores ilustrativos):\n{json.dumps(exemplo_saida, ensure_ascii=False)}\n\n"
        "Se for impossível montar um PC compatível dentro do orçamento com este catálogo, "
        f"responda apenas com:\n{json.dumps(exemplo_erro, ensure_ascii=False)}\n\n"

        "# CATÁLOGO\n"
        f"{json.dumps(catalogo, ensure_ascii=False, separators=(',', ':'))}"
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
