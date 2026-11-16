from math import isfinite

from models import Oferta


class PrecoExibidoService:
    """Dá à geração o mesmo preço e estoque que o site mostra na build. Quando a peça tem oferta válida
    (KaBuM, Mercado Livre vinculado ao catálogo certo ou Shopee conferida), vale a melhor delas; uma
    oferta mais barata que o site não exibe não entra. Peça esgotada ou acima do teto fica fora."""

    @staticmethod
    def catalogo(pecas, teto=None):
        dados = [peca.to_catalogo() for peca in pecas]
        Oferta.anexar_a_catalogo(dados)
        return [item for item in dados if PrecoExibidoService.valida(item, teto)]

    @staticmethod
    def valida(item, teto=None):
        preco = item.get("preco")
        if item.get("esgotado") is True:
            return False
        if type(preco) not in (int, float) or not isfinite(preco) or preco <= 0:
            return False
        return teto is None or preco <= float(teto)

    @staticmethod
    def id_numerico(item):
        return int(str(item["id"]).rsplit(":", 1)[1])
