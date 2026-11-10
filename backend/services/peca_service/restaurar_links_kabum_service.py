import json
from pathlib import Path

from models import db
from repositories.ofertas_kabum_repository import definir_link
from models.modelos_pecas import MODELOS_PECAS


class RestaurarLinksKabumService:
    def executar(self):
        arquivo = Path(__file__).resolve().parents[2] / "data" / "links_kabum_seed.json"
        links = json.loads(arquivo.read_text())
        return {modelo.__tablename__: self._restaurar(modelo, links) for modelo in MODELOS_PECAS}

    @staticmethod
    def _restaurar(modelo, links):
        pecas = modelo.query.filter(db.or_(modelo.part_number.in_(links), modelo.referencia_interna.in_(links))).all()
        atualizadas = 0
        for peca in pecas:
            if not peca.kabum_external:
                definir_link(peca, links.get(peca.referencia_interna) or links.get(peca.part_number))
                atualizadas += 1
        db.session.commit()
        return atualizadas
