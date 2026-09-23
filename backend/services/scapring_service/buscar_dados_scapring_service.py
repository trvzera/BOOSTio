import json
import requests
from bs4 import BeautifulSoup


class ProdutoEsgotadoError(Exception):
    pass


class PrecoNaoEncontradoError(Exception):
    pass


class BuscarDadosScapringService:
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def __init__(self):
        self.lojas = {
            "kabum.com.br": self._pega_preco_kabum,
        }

    def executar(self, url: str) -> float:
        for dominio, extrator in self.lojas.items():
            if dominio in url:
                html = self._baixar_html(url)
                return extrator(html)
        raise ValueError("URL inválida ou loja não suportada")

    def _baixar_html(self, url: str) -> str:
        response = requests.get(url, headers=self.HEADERS, timeout=15)
        response.raise_for_status()
        return response.text

    def _pega_preco_kabum(self, html: str) -> float:
        site = BeautifulSoup(html, "html.parser")

        componente = site.find("number-flow-react", attrs={"data": True})
        if componente:
            dados = json.loads(componente["data"])
            if "value" in dados:
                return float(dados["value"])
            return self._tratar_preco(dados.get("valueAsString"))

        if "esgotado" in site.get_text(" ").lower():
            raise ProdutoEsgotadoError("Esse produto está esgotado")

        raise PrecoNaoEncontradoError(f"Preço não encontrado (o layout da página pode ter mudado)")

    @staticmethod
    def _tratar_preco(texto: str | None) -> float | None:
        if texto is None:
            return None
        texto_limpo = (
            texto.replace("R$", "")
            .replace("\xa0", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        return float(texto_limpo)