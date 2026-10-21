import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .buscar_imagem_kabum_service import BuscarImagemKabumService
from .modelos_pecas import MODELOS_PECAS


PROJETO = Path(__file__).resolve().parents[3]
PASTA_IMAGENS = PROJETO / "frontend" / "imgs" / "produtos"
MANIFESTO = PROJETO / "frontend" / "data" / "imagens-produtos.json"


class AtualizarImagemPecaService:
    def executar(self, peca):
        conteudo, extensao = BuscarImagemKabumService().executar(peca.kabum_external)
        PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)
        nome = f"{peca.__tablename__}-{peca.id}.{extensao}"
        destino = PASTA_IMAGENS / nome
        with NamedTemporaryFile(dir=PASTA_IMAGENS, delete=False) as temporario:
            temporario.write(conteudo)
        os.replace(temporario.name, destino)
        destino.chmod(0o644)
        peca.definir_imagem(f"../imgs/produtos/{nome}")
        return destino

    @staticmethod
    def exportar_manifesto():
        imagens = {peca.part_number: peca.imagem_url
                   for classe in MODELOS_PECAS for peca in classe.mostrar_pecas()
                   if peca.part_number and peca.imagem_url}
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=MANIFESTO.parent, delete=False) as temporario:
            temporario.write(json.dumps(imagens, ensure_ascii=False, indent=2) + "\n")
        os.replace(temporario.name, MANIFESTO)
        MANIFESTO.chmod(0o644)
        return len(imagens)
