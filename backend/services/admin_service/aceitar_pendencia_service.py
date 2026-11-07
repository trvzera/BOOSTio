from datetime import datetime, timezone

from models import ProdutoPendente
from repositories.ofertas_repository import atualizar_ofertas_validadas
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.peca_service.modelos_pecas import MODELOS_PECAS
from services.shopee_service.normalizar_produto_service import NormalizarProdutoShopeeService
from utils.identidade_peca import assinatura_peca
from .apresentar_pendencia_service import apresentar_pendencia


class ConflitoPendencia(ValueError):
    """A pendência existe, mas não pode receber esta decisão agora."""


class AceitarPendenciaService:
    def executar(self, pendencia_id, administrador_id, referencia_peca):
        pendencia = ProdutoPendente.buscar_por_id(pendencia_id)
        if pendencia is None:
            raise LookupError("Pendência não encontrada")
        if pendencia.status not in ("pendente", "em_revisao"):
            raise ConflitoPendencia("Esta pendência já foi decidida")
        if pendencia.loja != "shopee":
            raise ConflitoPendencia("O aceite do Mercado Livre ainda é feito pelo comando mercadolivre-vincular")
        peca = self._peca_candidata(pendencia, referencia_peca)
        produto = ProdutoNormalizado(**pendencia.dados_originais["normalizado"])
        _, oferta = NormalizarProdutoShopeeService().executar(pendencia.dados_originais["anuncio"], peca.__tablename__)
        revisao = {"acao": "aceitar", "peca": referencia_peca, "administrador_id": administrador_id,
                   "em": datetime.now(timezone.utc).replace(tzinfo=None).isoformat()}
        # A gravação é a mesma da busca automática: trava, posse do anúncio, histórico e vínculo.
        propostas = atualizar_ofertas_validadas(peca, "shopee", [(oferta, produto)], assinatura_peca(peca),
                                                simular=False, revisao_manual=revisao)
        return {"pendencia": apresentar_pendencia(ProdutoPendente.buscar_por_id(pendencia_id)), "ofertas": propostas}

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
        if peca is None or not peca.publicavel:
            raise ValueError("Peça ausente ou ainda não aprovada")
        if categoria != pendencia.categoria_sugerida:
            raise ValueError("A categoria da peça é diferente da do anúncio")
        return peca
