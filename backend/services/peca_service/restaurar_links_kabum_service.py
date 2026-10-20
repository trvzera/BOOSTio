import json
from pathlib import Path

from .modelos_pecas import MODELOS_PECAS


class RestaurarLinksKabumService:
    def executar(self):
        arquivo = Path(__file__).resolve().parents[2] / "data" / "links_kabum_seed.json"
        links = json.loads(arquivo.read_text())
        return {
            modelo.__tablename__: modelo.restaurar_links_ausentes(links)
            for modelo in MODELOS_PECAS
        }
