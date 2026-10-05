from models import db
from .modelos_pecas import MODELOS_PECAS
from services.preco_service.validar_link_service import ValidarLinkService


class SalvarPecaService:
    """Cadastra uma peça ou atualiza seus dados e links sem consultar a rede."""

    def executar(self, classe, dados: dict, peca_id: int | None = None):
        if classe not in MODELOS_PECAS:
            raise ValueError("Tipo de peça inválido")
        peca = db.session.get(classe, peca_id) if peca_id is not None else classe()
        if peca is None:
            raise ValueError("Peça não encontrada")
        campos = dict(dados)
        for loja in ("kabum", "meli"):
            campo = f"{loja}_external"
            if campo in campos:
                url = (campos[campo] or "").strip() or None
                if url:
                    ValidarLinkService().executar(url, loja)
                if loja == "meli" and url != peca.meli_external:
                    peca.preco_atualizado_em = None
                    peca.esgotado = True
                    peca.preco = 0
                campos[campo] = url
        if peca_id is None:
            peca.preco = 0
            peca.esgotado = True
        for campo, valor in campos.items():
            if campo not in classe.__table__.columns or campo in {"id", "criado_em", "atualizado_em", "preco_atualizado_em"}:
                raise ValueError(f"Campo de peça inválido: {campo}")
            setattr(peca, campo, valor)
        try:
            db.session.add(peca)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return peca
