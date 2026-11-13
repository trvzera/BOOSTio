import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests

from .buscar_imagem_kabum_service import BuscarImagemKabumService
from .buscar_imagem_mercado_livre_service import BuscarImagemMercadoLivreService
from .buscar_imagem_shopee_service import BuscarImagemShopeeService
from models import Oferta, VinculoMercadoLivre
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

    @classmethod
    def _baixar(cls, peca):
        """Tenta KaBuM, catálogo do Mercado Livre e Shopee, nessa ordem, até uma entregar a foto."""
        erros = []
        for fonte in (cls._da_kabum, cls._do_mercado_livre, cls._da_shopee):
            try:
                resultado = fonte(peca)
            except requests.HTTPError as erro:
                status = erro.response.status_code if erro.response is not None else 0
                if status in (401, 403, 429) or status >= 500:
                    raise  # bloqueio ou instabilidade: o comando interrompe em vez de insistir nas outras peças
                erros.append(erro)
            except (requests.RequestException, ValueError) as erro:
                erros.append(erro)
            else:
                if resultado is not None:
                    return resultado
        if erros:
            raise erros[0] if len(erros) == 1 else ValueError("; ".join(str(erro) for erro in erros))
        raise ValueError("Peça sem anúncio da KaBuM, vínculo com o Mercado Livre ou oferta da Shopee")

    @staticmethod
    def _da_kabum(peca):
        return BuscarImagemKabumService().executar(peca.kabum_external) if peca.kabum_external else None

    @staticmethod
    def _do_mercado_livre(peca):
        vinculo = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id)
        return BuscarImagemMercadoLivreService().executar(vinculo.catalogo_id) if vinculo else None

    @staticmethod
    def _da_shopee(peca):
        anuncio = Oferta.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id,
                                         loja="shopee", ativa=True).order_by(Oferta.preco.asc()).first()
        if anuncio is None:
            return None
        return BuscarImagemShopeeService().executar(anuncio.vendedor_id, anuncio.produto_id_loja.split(":")[-1])

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
