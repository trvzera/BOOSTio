import math
import re

from .fpshq_service import cliente_fpshq, ErroBenchmark

SLUG = re.compile(r"[a-z0-9-]{1,190}")
RESOLUCOES = ("1080p", "1440p", "4k")
QUALIDADES = ("low", "medium", "high", "ultra")


def numero(valor):
    return valor if type(valor) in (int, float) and math.isfinite(valor) and valor >= 0 else None


class ConsultarBenchmarkService:
    def __init__(self, cliente=None):
        self.cliente = cliente or cliente_fpshq

    def executar(self, dados, usuario_id):
        if not isinstance(dados, dict):
            raise ValueError("Informe dados como um objeto válido")

        with self.cliente.travar("fps", dados):
            return self._consultar(dados, usuario_id)

    def _consultar(self, dados, usuario_id):
        escopo = dados.get("escopo", "build")
        if escopo not in ("build", "gpu") or escopo == "gpu" and "cpu" in dados:
            raise ValueError("Selecione a combinação da build ou uma referência da GPU sem CPU.")
        campos = ("game", "gpu") if escopo == "gpu" else ("game", "cpu", "gpu")
        consulta = {chave: dados.get(chave) for chave in campos}
        if not all(isinstance(valor, str) and SLUG.fullmatch(valor) for valor in consulta.values()):
            raise ValueError("Informe IDs válidos do jogo, processador e placa de vídeo.")
        consulta.update(res=dados.get("res", "1080p"), preset=dados.get("preset", "high"))
        if consulta["res"] not in RESOLUCOES or consulta["preset"] not in QUALIDADES:
            raise ValueError("Selecione uma resolução e uma qualidade válidas.")
        resposta = self.cliente.executar("fps", consulta, usuario_id)


        if resposta["cache"]:
            return resposta
        bruto = resposta["dados"]

        for chave in campos:
            if not isinstance(bruto.get(chave), dict) or bruto[chave].get("slug") != consulta[chave]:
                raise ErroBenchmark("O provedor não confirmou os modelos exatos solicitados.", "resposta")
        if escopo == "gpu" and bruto.get("cpu") is not None:
            raise ErroBenchmark("O provedor incluiu uma CPU em uma referência solicitada apenas para a GPU.", "resposta")

        if str(bruto.get("res", "")).lower() != consulta["res"] or bruto.get("preset") != consulta["preset"]:
            raise ErroBenchmark("O provedor retornou ajustes diferentes dos solicitados.", "resposta")
        fps = numero(bruto.get("fps"))

        if fps is None:
            raise ErroBenchmark("Não há desempenho disponível para esta combinação e configuração.", "sem-dados", 422)
        intervalo = bruto.get("fps_range")

        if not (isinstance(intervalo, list) and len(intervalo) == 2 and all(numero(n) is not None for n in intervalo) and intervalo[0] <= intervalo[1]):
            intervalo = None
        matriz = bruto.get("matrix") if isinstance(bruto.get("matrix"), dict) else {}
        linhas = {res: matriz.get(res, matriz.get(res.lower())) for res in ("1080p", "1440p", "4K")}

        resultado = {
            "escopo": escopo,
            "consulta": consulta, "jogo": str(bruto["game"].get("name") or consulta["game"])[:180],
            "fps": fps, "low1": numero(bruto.get("low1")), "intervalo": intervalo,
            "origem": bruto.get("source") if bruto.get("source") in ("measured", "model") else "unknown",
            "base": bruto.get("basis") if bruto.get("basis") in ("measured", "aggregate", "model") else None,
            "confianca": bruto.get("confidence") if bruto.get("confidence") in ("high", "medium", "low") else None,
            "matriz": {res: {q: numero(linhas[res].get(q)) if isinstance(linhas[res], dict) else None for q in QUALIDADES} for res in linhas},
            "url": "https://fpshq.com/pt/games/" + consulta["game"] + "/",
            "consultadoEm": resposta["consultadoEm"], "cache": False,
            "requisitosVerificados": False, "ramAvaliada": False,
        }
        self.cliente.salvar("fps", consulta, resultado)
        return resultado
