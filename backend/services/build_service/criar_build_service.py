from services.build_service.gerar_candidata_service import gerar_candidata
from services.build_service.gerar_candidata_service import perfil_revisa_investimento
from services.build_service.salvar_build_gerada_service import salvar_build
from services.validacoes_service.validar_pedido_build_service import validar_orcamento, validar_rede, validar_prioridade_montagem, validar_textos_pedido, pecas_proprias
from services.build_service.custos_build_service import dividir_orcamento
from services.build_service.contexto_build_service import obter_detalhes_proprias
from services.build_service.catalogo_geracao_service import preparar_catalogo, validar_disponibilidade, planejar_perifericos
from services.build_service.prompt_build_service import criar_prompt
import logging
from time import perf_counter

from models import BuildSalva, Usuario
from utils.validacoes import validacao_campos
from utils.aparencia import validar_aparencia
from services.validacoes_service.requisitos_armazenamento_service import RequisitosArmazenamentoService
from .planejamento_geracao import validar_minimos

logger = logging.getLogger(__name__)


class CriarBuildService:

  def executar(self, usuario_id, dados, modelo="gemini-3.5-flash-lite", tentativas_correcao=1, *, selecao_inteligente=False):
    validacao_campos(dados, ["nome", "descricao", "utilidade", "orcamento"])
    validar_textos_pedido(dados)
    armazenamento_minimo = RequisitosArmazenamentoService.validar_parametro(dados.get("armazenamento_minimo_gb"))
    aparencia = validar_aparencia(dados.get("aparencia"))
    dados = {**dados, "aparencia": aparencia,
             "prioridade_montagem": validar_prioridade_montagem(dados)}
    if not Usuario.buscar_por_id(usuario_id):
      raise ValueError("Usuario não encontrado")
    BuildSalva.verificar_espaco(usuario_id)

    orcamento = validar_orcamento(dados["orcamento"])
    percentual = dados.get("percentual_perifericos", 0)
    if type(percentual) is not int or not 0 <= percentual <= 99:
      raise ValueError("A porcentagem para periféricos deve ser de 0 a 99")
    rede = dados.get("rede")
    if rede is None:
      rede = {}
    validar_rede(rede)
    proprias = pecas_proprias(dados.get("pecas_proprias", {}))
    margem = min(orcamento / 2, max(800, orcamento * 0.25))

    teto_pc, teto_perifericos = dividir_orcamento(orcamento, percentual)
    validar_minimos(teto_pc, teto_perifericos, percentual)
    inicio_prompt = perf_counter()
    reparo = {}
    if selecao_inteligente:
      from .seletor_inteligente_service import SeletorInteligenteService
      preparado = SeletorInteligenteService().preparar_geracao(dados)
      catalogo = preparado["catalogo"]
      detalhes_proprias = preparado["detalhes_proprias"]
      prompt = preparado["prompt"]
      reparo = {"ajustar_orcamento": True, "catalogo_reparo": preparado["catalogo_reparo"]}
      plano_perifericos = preparado["plano_perifericos"]
    else:
      catalogo = preparar_catalogo(dados, proprias, rede, aparencia, orcamento, margem, teto_pc, teto_perifericos)
      validar_disponibilidade(catalogo, proprias, percentual)
      plano_perifericos = planejar_perifericos(catalogo, teto_perifericos, proprias, dados["utilidade"], aparencia["cor"], percentual)
      detalhes_proprias = obter_detalhes_proprias(proprias)
      prompt = criar_prompt(dados, orcamento, margem, catalogo, percentual, detalhes_proprias, plano_perifericos)
    logger.info("Geração: etapa=prompt duracao_ms=%d caracteres=%d", (perf_counter()-inicio_prompt)*1000, len(prompt))
    dados_build = gerar_candidata(usuario_id, prompt, modelo, catalogo, orcamento,
                                     percentual, proprias, detalhes_proprias, rede, tentativas_correcao,
                                     revisar_investimento=perfil_revisa_investimento(dados["utilidade"]), cor=aparencia["cor"], aparencia=aparencia,
                                     armazenamento_minimo_gb=armazenamento_minimo, utilidade=dados["utilidade"],
                                     plano_perifericos=plano_perifericos, **reparo)
    return salvar_build(usuario_id, dados_build, proprias, rede, percentual, aparencia, orcamento)
