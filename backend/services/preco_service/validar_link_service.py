import re
from urllib.parse import urlsplit, parse_qs


class ValidarLinkService:
    def executar(self, url: str, loja: str) -> str:
        partes = urlsplit(url)
        dominios = {
            "kabum": {"kabum.com.br", "www.kabum.com.br"},
            "meli": {"mercadolivre.com.br", "www.mercadolivre.com.br", "produto.mercadolivre.com.br"},
        }
        if (partes.scheme != "https" or partes.hostname not in dominios[loja]
                or partes.username or partes.password or partes.port not in (None, 443)):
            raise ValueError(f"Informe um link HTTPS de produto da loja {loja}")
        if loja == "kabum" and not re.match(r"^/produto/\d+(?:/|$)", partes.path):
            raise ValueError("O link da KaBuM deve ser de produto, não de busca")
        if loja == "meli" and not self._anuncio_id(url):
            raise ValueError("O link do Mercado Livre deve identificar o anúncio (item_id), não apenas o catálogo")
        return url

    def _anuncio_id(self, url):
        partes = urlsplit(url)
        anuncio = re.search(r"(?:^|/)MLB-(\d+)(?:-|/|$)", partes.path)
        if anuncio:
            return "MLB" + anuncio.group(1)
        params = parse_qs(partes.query)
        params.update(parse_qs(partes.fragment))
        for filtro in params.get("pdp_filters", []):
            anuncio = re.search(r"(?:^|[|,])item_id:(MLB\d+)(?:$|[|,])", filtro)
            if anuncio:
                return anuncio.group(1)
        for item in params.get("wid", []) + params.get("item_id", []):
            if re.fullmatch(r"MLB\d+", item):
                return item
        return None
