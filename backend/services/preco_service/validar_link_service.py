import re
from urllib.parse import urlsplit


class ValidarLinkService:
    def executar(self, url: str) -> str:
        partes = urlsplit(url)
        if (partes.scheme != "https" or partes.hostname not in {"kabum.com.br", "www.kabum.com.br"}
                or partes.username or partes.password or partes.port not in (None, 443)):
            raise ValueError("Informe um link HTTPS de produto da KaBuM")
        if not re.match(r"^/produto/\d+(?:/|$)", partes.path):
            raise ValueError("O link da KaBuM deve ser de produto, não de busca")
        return url
