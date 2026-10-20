from models import ConsultaPreco


class ReservarConsultaService:
    def executar(self, classe, peca, agora):
        if not peca.kabum_external:
            raise ValueError("A peça não tem link da KaBuM")
        return ConsultaPreco.reservar(
            classe.__tablename__, peca.id, peca.kabum_external,
            agora.date().isoformat(),
        )
