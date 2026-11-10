from models import db
from models.modelos_pecas import MODELOS_PECAS
from services.preco_service.validar_link_service import ValidarLinkService
from repositories.ofertas_kabum_repository import definir_link

_SEM_LINK = object()


class SalvarPecaService:
    def executar(self, classe, dados: dict, peca_id: int | None = None):
        if not isinstance(dados, dict):
            raise ValueError("Informe dados como um objeto válido")

        if classe not in MODELOS_PECAS:
            raise ValueError("Tipo de peça inválido")
        peca = classe.buscar_por_id(peca_id) if peca_id is not None else classe()
        if peca is None:
            raise ValueError("Peça não encontrada")
        campos = dict(dados)
        link = self._validar_link(peca, campos)
        for campo, valor in campos.items():
            if campo not in classe.__table__.columns or campo in {"id", "criado_em", "atualizado_em", "preco_atualizado_em", "imagem_url"}:
                raise ValueError(f"Campo de peça inválido: {campo}")
            setattr(peca, campo, valor)
        try:
            db.session.add(peca)
            db.session.flush()
            if link is not _SEM_LINK:
                definir_link(peca, link)
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return peca

    @staticmethod
    def _validar_link(peca, campos):
        if "kabum_external" not in campos:
            return _SEM_LINK
        url = (campos.pop("kabum_external") or "").strip() or None
        if url:
            ValidarLinkService().executar(url)
        if url != peca.kabum_external:
            peca.imagem_url = None
        return url
