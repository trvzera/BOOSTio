from models import db
from .modelos_pecas import MODELOS_PECAS
from services.preco_service.validar_link_service import ValidarLinkService


class SalvarPecaService:
    """Cadastra uma peça ou atualiza seus dados e links sem consultar a rede."""

    def executar(self, classe, dados: dict, peca_id: int | None = None):
        if classe not in MODELOS_PECAS:
            raise ValueError("Tipo de peça inválido")
        peca = classe.buscar_por_id(peca_id) if peca_id is not None else classe()
        if peca is None:
            raise ValueError("Peça não encontrada")
        campos = dict(dados)
        if "kabum_external" in campos:
            url = (campos["kabum_external"] or "").strip() or None
            if url:
                ValidarLinkService().executar(url)
            if url != peca.kabum_external:
                peca.preco_atualizado_em = None
                peca.esgotado = True
                peca.preco = 0
                peca.imagem_url = None
            campos["kabum_external"] = url
        if peca_id is None:
            peca.preco = 0
            peca.esgotado = True
        for campo, valor in campos.items():
            if campo not in classe.__table__.columns or campo in {"id", "criado_em", "atualizado_em", "preco_atualizado_em", "imagem_url"}:
                raise ValueError(f"Campo de peça inválido: {campo}")
            setattr(peca, campo, valor)
        try:
            peca.salvar()
        except Exception:
            db.session.rollback()
            raise
        return peca
