from . import db, Peca


class PlacaRede(Peca):
    # O editor já usa adaptador_wifi como identificador desta categoria.
    __tablename__ = "adaptador_wifi"

    interface = db.Column(db.String(20), nullable=False)
    padrao_wifi = db.Column(db.String(20), nullable=False)
    velocidade_mbps = db.Column(db.Integer, nullable=False)
    bluetooth = db.Column(db.Boolean, nullable=False, default=False)

    @classmethod
    def atualizar_links_antigos(cls, trocas):
        alteradas = 0
        for antigo, novo in trocas.items():
            for peca in cls.query.filter_by(kabum_external=antigo).all():
                peca.kabum_external = novo
                peca.preco = 0
                peca.esgotado = True
                peca.preco_atualizado_em = None
                peca.imagem_url = None
                alteradas += 1
        if alteradas:
            db.session.commit()
        return alteradas
