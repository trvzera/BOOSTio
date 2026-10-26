"""Laboratório offline. Consulta medições; ainda não prevê hardware não medido."""
import argparse
from copy import deepcopy
from datetime import date
import json
import math
from pathlib import Path
from statistics import median

JOGOS = ("valorant", "cs2", "fortnite", "cyberpunk-2077", "red-dead-redemption-2")
CAMPOS = ("jogo", "versao_jogo", "cenario", "cpu", "gpu", "ram_gb", "ram_pentes",
          "ram_mts", "resolucao", "qualidade", "api_grafica", "ray_tracing", "upscaling", "frame_generation")
BASE = Path(__file__).resolve().parent / "dados" / "medicoes.json"


def validar_consulta(consulta):
    if not isinstance(consulta, dict) or set(consulta) != set(CAMPOS):
        raise ValueError("Informe todos os campos do modelo de consulta, sem campos extras.")
    for campo in ("versao_jogo", "cenario", "cpu", "gpu"):
        if not isinstance(consulta[campo], str) or not consulta[campo].strip() or len(consulta[campo]) > 180:
            raise ValueError(f"Informe um texto de até 180 caracteres para {campo}.")
    for campo, maximo in (("ram_gb", 2048), ("ram_pentes", 16), ("ram_mts", 20000)):
        if type(consulta[campo]) is not int or not 1 <= consulta[campo] <= maximo:
            raise ValueError(f"Quantidade inválida para {campo}.")
    for campo, opcoes in (("jogo", JOGOS), ("resolucao", ("1080p", "1440p", "4k")),
                          ("qualidade", ("low", "medium", "high", "ultra")),
                          ("api_grafica", ("dx11", "dx12", "vulkan"))):
        if consulta[campo] not in opcoes:
            raise ValueError(f"Selecione um valor suportado para {campo}.")
    if consulta["ray_tracing"] is not False or consulta["frame_generation"] is not False or consulta["upscaling"] != "nativo":
        raise ValueError("A primeira fase aceita apenas resolução nativa, sem ray tracing nem geração de quadros.")
    return deepcopy(consulta)


def numero_positivo(valor):
    return type(valor) in (int, float) and math.isfinite(valor) and valor > 0


def validar_base(base):
    if not isinstance(base, dict) or type(base.get("versao")) is not int or base["versao"] != 1 or not isinstance(base.get("medicoes"), list):
        raise ValueError("Base inválida: use versao 1 e uma lista medicoes.")
    ids = set()
    for medicao in base["medicoes"]:
        if not isinstance(medicao, dict):
            raise ValueError("Cada medição deve ser um objeto.")
        identificador = medicao.get("id")
        if not isinstance(identificador, str) or not identificador.strip() or len(identificador) > 120 or identificador in ids:
            raise ValueError("Cada medição deve ter um ID textual único de até 120 caracteres.")
        ids.add(identificador)
        validar_consulta(medicao.get("configuracao"))
        if not numero_positivo(medicao.get("fps_medio")) or not numero_positivo(medicao.get("duracao_s")):
            raise ValueError("Informe FPS médio e duração positivos e finitos.")
        low = medicao.get("fps_1_low")
        if low is not None:
            if not numero_positivo(low) or low > medicao["fps_medio"]:
                raise ValueError("1% low deve ser positivo e não ultrapassar o FPS médio da mesma captura.")
            if not isinstance(medicao.get("metodo_1_low"), str) or not medicao["metodo_1_low"].strip():
                raise ValueError("Documente como o 1% low foi calculado.")
        fonte = medicao.get("fonte")
        if not isinstance(fonte, dict) or fonte.get("tipo") not in ("propria", "autorizada") or fonte.get("uso_confirmado") is not True:
            raise ValueError("Informe a origem e confirme manualmente o direito de usar a medição.")
        for campo in ("referencia", "permissao", "sistema", "driver_gpu"):
            if not isinstance(fonte.get(campo), str) or not fonte[campo].strip():
                raise ValueError(f"Complete {campo} na fonte da medição.")
        try:
            if date.fromisoformat(fonte["coletado_em"]).isoformat() != fonte["coletado_em"]:
                raise ValueError("Formato de data inválido.")
        except (KeyError, ValueError, TypeError):
            raise ValueError("Informe coletado_em no formato AAAA-MM-DD.") from None
    return deepcopy(base["medicoes"])


def consultar(base, consulta):
    consulta = validar_consulta(consulta)
    medicoes = validar_base(base)
    correspondentes = [m for m in medicoes if m["configuracao"] == consulta]
    if not correspondentes:
        return {"status": "dados-insuficientes", "fps_medio": None, "fps_1_low": None,
                "amostras": 0, "mensagem": "Ainda não há medições para esse hardware, jogo e ajustes. Nenhum FPS foi calculado."}
    medios = [m["fps_medio"] for m in correspondentes]
    completos = all(m.get("fps_1_low") is not None for m in correspondentes)
    mesmo_metodo = completos and len({m.get("metodo_1_low") for m in correspondentes}) == 1
    return {"status": "referencia-medida", "tipo": "mediana-dos-fps-medios", "fps_medio": median(medios),
            "fps_1_low": median(m["fps_1_low"] for m in correspondentes) if completos and mesmo_metodo else None,
            "faixa_observada": [min(medios), max(medios)], "amostras": len(correspondentes),
            "fontes": [{"id": m["id"], **m["fonte"]} for m in correspondentes],
            "mensagem": "Referência de execuções cadastradas, não previsão validada nem medição desta máquina. A faixa observada não é um intervalo de confiança."}


def ler_json(caminho):
    def rejeitar_constante(_valor):
        raise ValueError("JSON não aceita NaN ou infinito.")
    return json.loads(Path(caminho).read_text(encoding="utf-8"), parse_constant=rejeitar_constante)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("acao", choices=("validar", "consultar"))
    parser.add_argument("--base", type=Path, default=BASE)
    parser.add_argument("--consulta", type=Path)
    args = parser.parse_args()
    try:
        base = ler_json(args.base)
        if args.acao == "validar":
            resultado = {"status": "base-valida", "medicoes": len(validar_base(base)), "modelo_calibrado": False}
        else:
            if args.consulta is None:
                raise ValueError("Informe --consulta com um arquivo JSON.")
            resultado = consultar(base, ler_json(args.consulta))
        print(json.dumps(resultado, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except (OSError, ValueError) as erro:
        print(json.dumps({"status": "entrada-invalida", "mensagem": str(erro)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
