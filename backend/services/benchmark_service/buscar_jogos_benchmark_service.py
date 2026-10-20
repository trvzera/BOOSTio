from .consultar_benchmark_service import SLUG
from .fpshq_service import cliente_fpshq, ErroBenchmark


class BuscarJogosBenchmarkService:
    def __init__(self, cliente=None):
        self.cliente = cliente or cliente_fpshq

    def executar(self, dados, usuario_id):
        with self.cliente.travar("games", dados):
            return self._buscar(dados, usuario_id)

    def _buscar(self, dados, usuario_id):
        texto = dados.get("q", "")
        if not isinstance(texto, str) or not 2 <= len(texto.strip()) <= 60:
            raise ValueError("Digite entre 2 e 60 caracteres para buscar um jogo.")
        parametros = {"q": texto.strip()}
        resposta = self.cliente.executar("games", parametros, usuario_id)
        if resposta["cache"]:
            return resposta
        jogos = resposta["dados"].get("results")
        if not isinstance(jogos, list):
            raise ErroBenchmark("A busca retornou uma resposta inválida.", "resposta")
        resultado = {
            "jogos": [{"slug": item["slug"], "name": item["name"][:180]} for item in jogos
                      if isinstance(item, dict) and isinstance(item.get("slug"), str)
                      and SLUG.fullmatch(item["slug"]) and isinstance(item.get("name"), str)][:10],
            "cache": False, "consultadoEm": resposta["consultadoEm"],
        }
        self.cliente.salvar("games", parametros, resultado)
        return resultado
