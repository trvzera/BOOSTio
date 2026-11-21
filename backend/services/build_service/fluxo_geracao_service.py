"""Uma geração de build com um modelo de IA: validar o pedido, escolher as peças, pedir à IA e gravar."""
import logging
from time import perf_counter

from models import BuildSalva, Usuario
from utils.validacoes import validacao_campos
from services.validacoes_service.validar_pedido_build_service import validar_textos_pedido
from .conferir_pecas_proprias_service import ConferirPecasPropriasService
from .gerar_candidata_service import gerar_candidata
from .pedido_build import validar_pedido
from .salvar_build_gerada_service import salvar_build
from .seletor_inteligente_service import SeletorInteligenteService

logger = logging.getLogger(__name__)


class FluxoGeracaoService:

  def executar(self, usuario_id, dados, modelo="gemini-3.5-flash-lite", tentativas_correcao=1):
    # 1. Pedido: campos do formulário e valores da build, validados uma única vez.
    validacao_campos(dados, ["nome", "descricao", "utilidade", "orcamento"])
    validar_textos_pedido(dados)
    pedido = validar_pedido(dados)

    # 2. Usuário: existe, tem e-mail verificado e ainda tem vaga para mais uma build.
    if not Usuario.buscar_por_id(usuario_id):
      raise ValueError("Usuario não encontrado")
    BuildSalva.verificar_espaco(usuario_id)
    ConferirPecasPropriasService.executar(pedido["proprias"])

    # 3. Seleção: candidatas do banco, plano de periféricos e prompt.
    inicio = perf_counter()
    preparado = SeletorInteligenteService().preparar_geracao(pedido)
    logger.info("Geração: etapa=prompt duracao_ms=%d caracteres=%d", (perf_counter() - inicio) * 1000, len(preparado["prompt"]))

    # 4. IA: build validada (com reparo e uma correção, se preciso).
    build = gerar_candidata(usuario_id, pedido, preparado, modelo, tentativas_correcao)

    # 5. Gravação em build_salva.
    return salvar_build(usuario_id, build, pedido)
