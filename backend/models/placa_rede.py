from . import db, Peca


class PlacaRede(Peca):
    # O editor já usa adaptador_wifi como identificador desta categoria.
    __tablename__ = "adaptador_wifi"

    interface = db.Column(db.String(20), nullable=False)
    padrao_wifi = db.Column(db.String(20), nullable=False)
    velocidade_mbps = db.Column(db.Integer, nullable=True)
    bluetooth = db.Column(db.Boolean, nullable=True, default=False)

    @classmethod
    def atualizar_links_antigos(cls, trocas):
        from repositories.ofertas_kabum_repository import definir_link
        alteradas = 0
        for antigo, novo in trocas.items():
            for peca in cls.query.filter(cls.kabum_external == antigo).all():
                definir_link(peca, novo)
                peca.imagem_url = None
                alteradas += 1
        if alteradas:
            db.session.commit()
        return alteradas
