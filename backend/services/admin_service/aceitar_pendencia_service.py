from datetime import datetime, timezone

from models import ProdutoPendente
from services.marketplace_service.gravar_ofertas_service import atualizar_ofertas_validadas
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.mercadolivre_service.controle_requisicoes_service import ControleRequisicoesService
from services.mercadolivre_service.importar_produto_service import ImportarProdutoService
from models.modelos_pecas import MODELOS_PECAS
from services.shopee_service.normalizar_produto_service import NormalizarProdutoShopeeService
from utils.identidade_peca import assinatura_peca
from .apresentar_pendencia_service import apresentar_pendencia
from .catalogo_ocupado import catalogo_que_ocupa_a_peca


class ConflitoPendencia(ValueError):
    """A pendência existe, mas não pode receber esta decisão agora."""


class AceitarPendenciaService:
    def __init__(self, importador_mercado_livre=None):
        self._importador_mercado_livre = importador_mercado_livre

    def executar(self, pendencia_id, administrador_id, referencia_peca, *, origem="administrador"):
        pendencia = ProdutoPendente.buscar_por_id(pendencia_id)
        if pendencia is None:
            raise LookupError("Pendência não encontrada")
        if pendencia.status not in ("pendente", "em_revisao"):
            raise ConflitoPendencia("Esta pendência já foi decidida")
        if pendencia.loja not in ("shopee", "mercado_livre"):
            raise ConflitoPendencia("Esta loja não tem aceite pelo painel")
        peca = self._peca_candidata(pendencia, referencia_peca)
        revisao = {"acao": "aceitar", "peca": referencia_peca, "administrador_id": administrador_id,
                   "origem": origem, "em": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}
        # A gravação é a mesma da busca automática: trava, posse do anúncio, histórico e vínculo.
        propostas = (self._aceitar_shopee if pendencia.loja == "shopee" else self._aceitar_mercado_livre)(
            pendencia, peca, revisao)
        return {"pendencia": apresentar_pendencia(ProdutoPendente.buscar_por_id(pendencia_id)), "ofertas": propostas}

    @staticmethod
    def _aceitar_shopee(pendencia, peca, revisao):
        produto = ProdutoNormalizado(**pendencia.dados_originais["normalizado"])
        _, oferta = NormalizarProdutoShopeeService().executar(pendencia.dados_originais["anuncio"], peca.__tablename__)
        return atualizar_ofertas_validadas(peca, "shopee", [(oferta, produto)], assinatura_peca(peca),
                                           simular=False, revisao_manual=revisao)

    def _aceitar_mercado_livre(self, pendencia, peca, revisao):
        self._recusar_peca_ja_vinculada_a_outro_catalogo(pendencia, peca)
        # O anúncio é reconsultado na API do Mercado Livre (poucas requisições, antes da transação).
        importador = self._importador_mercado_livre or ImportarProdutoService(controle=ControleRequisicoesService(8, 0.5))
        return importador.aceitar_revisado(pendencia.id, peca, revisao)

    @staticmethod
    def _recusar_peca_ja_vinculada_a_outro_catalogo(pendencia, peca):
        """Avisa antes de tentar gravar: cada peça tem um único catálogo do Mercado Livre."""
        ocupante = catalogo_que_ocupa_a_peca(pendencia, peca)
        if ocupante:
            raise ValueError(f"Esta peça já está vinculada a outro catálogo do Mercado Livre ({ocupante}). "
                             "Escolha outra peça ou rejeite esta pendência.")

    @staticmethod
    def _peca_candidata(pendencia, referencia):
        candidato = next((c for c in pendencia.candidatos or [] if c.get("peca") == referencia), None)
        if candidato is None:
            raise ValueError("Escolha uma das peças candidatas desta pendência")
        if candidato.get("conflitos"):
            raise ValueError("Esta peça tem conflito com o anúncio e não pode ser aceita")
        categoria, _, identificador = str(referencia).partition(":")
        modelo = next((m for m in MODELOS_PECAS if m.__tablename__ == categoria), None)
        peca = modelo.buscar_por_id(int(identificador)) if modelo and identificador.isdecimal() else None
        if peca is None:
            raise ValueError("Peça candidata não encontrada")
        if not peca.publicavel:
            raise ValueError("A peça candidata ainda está em revisão (importada, não aprovada). "
                             "Aprove a peça antes de aceitar o anúncio")
        if categoria != pendencia.categoria_sugerida:
            raise ValueError("A categoria da peça é diferente da do anúncio")
        return peca
