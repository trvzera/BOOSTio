import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .buscar_imagem_kabum_service import BuscarImagemKabumService
from .modelos_pecas import MODELOS_PECAS


PROJETO = Path(__file__).resolve().parents[3]
PASTA_COLETADOS = Path(os.getenv("IMAGENS_COLETADAS_DIR") or PROJETO / "frontend" / "coletados")
PASTA_IMAGENS = PASTA_COLETADOS / "imagens"
MANIFESTO = PASTA_COLETADOS / "imagens-produtos.json"


class AtualizarImagemPecaService:
    def executar(self, peca):
        conteudo, extensao = BuscarImagemKabumService().executar(peca.kabum_external)
        PASTA_IMAGENS.mkdir(parents=True, exist_ok=True)
        nome = f"{peca.__tablename__}-{peca.id}.{extensao}"
        destino = PASTA_IMAGENS / nome
        with NamedTemporaryFile(dir=PASTA_IMAGENS, prefix=".tmp-", delete=False) as temporario:
            temporario.write(conteudo)
        Path(temporario.name).chmod(0o644)
        os.replace(temporario.name, destino)
        peca.definir_imagem(f"../coletados/imagens/{nome}")
        return destino

    @staticmethod
    def exportar_manifesto():
        imagens = {peca.part_number: peca.imagem_url
                   for classe in MODELOS_PECAS for peca in classe.mostrar_pecas()
                   if peca.part_number and peca.imagem_url}
        MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=MANIFESTO.parent, prefix=".tmp-", delete=False) as temporario:
            temporario.write(json.dumps(imagens, ensure_ascii=False, indent=2) + "\n")
        Path(temporario.name).chmod(0o644)
        os.replace(temporario.name, MANIFESTO)
        return len(imagens)
