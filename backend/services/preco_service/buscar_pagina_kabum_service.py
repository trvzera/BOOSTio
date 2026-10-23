import re
from collections.abc import Mapping
from urllib.parse import urljoin, urlsplit

import requests

from .validar_link_service import ValidarLinkService


class BuscarPaginaKabumService:
    TAMANHO_MAXIMO = 2 * 1024 * 1024
    MAX_REDIRECIONAMENTOS = 3

    def executar(self, url):
        ValidarLinkService().executar(url)
        codigo = self._codigo(url)
        atual = url
        for _ in range(self.MAX_REDIRECIONAMENTOS + 1):
            resposta = requests.get(
                atual, timeout=(10, 30), stream=True, allow_redirects=False,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "text/html"},
            )
            try:
                resposta.raise_for_status()
                if resposta.status_code in (301, 302, 303, 307, 308):
                    destino = resposta.headers.get("Location")
                    if not isinstance(destino, str) or not destino:
                        raise ValueError("Redirecionamento da KaBuM sem destino")
                    atual = urljoin(atual, destino)
                    self._validar_mesmo_produto(atual, codigo)
                    continue

                self._validar_mesmo_produto(resposta.url, codigo)
                tipo = resposta.headers.get("Content-Type", "") if isinstance(resposta.headers, Mapping) else ""
                if tipo and "text/html" not in tipo.lower():
                    raise ValueError("A KaBuM não retornou uma página HTML")
                partes = []
                tamanho = 0
                for bloco in resposta.iter_content(64 * 1024):
                    tamanho += len(bloco)
                    if tamanho > self.TAMANHO_MAXIMO:
                        raise ValueError("Página da KaBuM maior que 2 MB")
                    partes.append(bloco)
                codificacao = resposta.encoding if isinstance(resposta.encoding, str) else "utf-8"
                return b"".join(partes).decode(codificacao, errors="replace")
            finally:
                resposta.close()
        raise ValueError("A KaBuM redirecionou muitas vezes")

    @staticmethod
    def _codigo(url):
        return re.match(r"/produto/(\d+)(?:/|$)", urlsplit(url).path).group(1)

    def _validar_mesmo_produto(self, url, codigo):
        ValidarLinkService().executar(url)
        if self._codigo(url) != codigo:
            raise ValueError("A KaBuM redirecionou para outro produto; preço preservado")
