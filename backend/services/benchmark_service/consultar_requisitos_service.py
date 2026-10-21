from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path

from .consultar_benchmark_service import SLUG
from .fpshq_service import ErroBenchmark


@lru_cache(maxsize=1)
def catalogo_requisitos():
    # Curadoria versionada; nunca usa uma URL/caminho fornecido pelo usuário.
    return json.loads(Path(__file__).with_name("requisitos_jogos.json").read_text(encoding="utf-8"))


class ConsultarRequisitosService:
    """Prévia parcial: capacidade de RAM, sem ranking por nome de CPU/GPU ou FPS."""

    def executar(self, dados, usuario_id):
        jogo = dados.get("game")
        if not isinstance(jogo, str) or not SLUG.fullmatch(jogo):
            raise ValueError("Selecione um jogo identificado para consultar os requisitos.")
        ram = dados.get("ram_gb")
        if ram is not None:
            if isinstance(ram, bool) or len(str(ram)) > 4 or not str(ram).isascii() or not str(ram).isdigit() or not 1 <= int(ram) <= 4096:
                raise ValueError("Informe a RAM em GB inteiros, de 1 a 4096, ou deixe o campo vazio.")
            ram = int(ram)
        ficha = catalogo_requisitos().get(jogo)
        if ficha is None:
            raise ErroBenchmark("Ainda não há requisitos oficiais revisados para este jogo na BOOSTio.", "sem-requisitos", 404)
        minimo = ficha["minimos"]["ramGb"]
        recomendado = (ficha["recomendados"] or {}).get("ramGb")
        status = "nao_informada" if ram is None else "abaixo_minimo" if ram < minimo else (
            "minimo_sem_recomendacao" if recomendado is None else "abaixo_recomendado" if ram < recomendado else "recomendado")
        return {
            **deepcopy(ficha), "game": jogo, "escopo": "parcial", "origem": "curadoria_fontes_oficiais",
            "ram": {"informadaGb": ram, "minimaGb": minimo, "recomendadaGb": recomendado,
                    "atendeMinimo": None if ram is None else ram >= minimo,
                    "atendeRecomendado": None if ram is None or recomendado is None else ram >= recomendado,
                    "status": status},
            "requisitosVerificados": False, "fpsValidado": False,
            "naoVerificado": ["Equivalência e recursos da CPU/GPU", "VRAM, sistema operacional e espaço livre",
                              "Drivers, instruções da CPU, segurança/anti-cheat e condições reais de uso"],
        }
