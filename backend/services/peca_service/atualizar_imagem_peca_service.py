import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from .buscar_imagem_kabum_service import BuscarImagemKabumService
from .buscar_imagem_mercado_livre_service import BuscarImagemMercadoLivreService
from models import VinculoMercadoLivre
from models.modelos_pecas import MODELOS_PECAS


PROJETO = Path(__file__).resolve().parents[3]
PASTA_COLETADOS = Path(os.getenv("IMAGENS_COLETADAS_DIR") or PROJETO / "frontend" / "coletados")
PASTA_IMAGENS = PASTA_COLETADOS / "imagens"
MANIFESTO = PASTA_COLETADOS / "imagens-produtos.json"


class AtualizarImagemPecaService:
    def executar(self, peca):
        if peca is None:
            raise ValueError("Peça não encontrada")

        conteudo, extensao = self._baixar(peca)
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
    def _baixar(peca):
        if peca.kabum_external:
            return BuscarImagemKabumService().executar(peca.kabum_external)
        vinculo = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id)
        if vinculo is None:
            raise ValueError("Peça sem anúncio da KaBuM nem vínculo com o catálogo do Mercado Livre")
        return BuscarImagemMercadoLivreService().executar(vinculo.catalogo_id)

    @staticmethod
    def exportar_manifesto():
        imagens = {peca.referencia_interna or peca.part_number: peca.imagem_url
                   for classe in MODELOS_PECAS for peca in classe.mostrar_pecas()
                   if (peca.referencia_interna or peca.part_number) and peca.imagem_url}
        MANIFESTO.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(mode="w", encoding="utf-8", dir=MANIFESTO.parent, prefix=".tmp-", delete=False) as temporario:
            temporario.write(json.dumps(imagens, ensure_ascii=False, indent=2) + "\n")
        Path(temporario.name).chmod(0o644)
        os.replace(temporario.name, MANIFESTO)
        return len(imagens)
