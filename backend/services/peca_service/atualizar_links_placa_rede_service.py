from models import db, PlacaRede
from repositories.ofertas_kabum_repository import definir_link


class AtualizarLinksPlacaRedeService:
    def executar(self, trocas):
        alteradas = 0
        for antigo, novo in trocas.items():
            for peca in PlacaRede.listar_por_link_kabum(antigo):
                definir_link(peca, novo)
                peca.imagem_url = None
                alteradas += 1
        if alteradas:
            db.session.commit()
        return alteradas
