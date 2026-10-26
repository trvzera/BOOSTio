"""Analisa JSONs locais de provedores, sem consultar APIs ou alimentar a calibração."""
import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

from laboratorio import ler_json


def numero(valor):
    return type(valor) in (int, float) and math.isfinite(valor) and valor >= 0


def normalizar_referencia(provedor, consulta, resposta):
    if not isinstance(consulta, dict) or not isinstance(resposta, dict):
        raise ValueError("Consulta e resposta precisam ser objetos JSON; HTML não é um resultado.")
    if provedor not in ("fpshq", "howmanyfps"):
        raise ValueError("Provedor não suportado.")
    campos = ("game", "cpu", "gpu")
    for campo in campos:
        if not isinstance(consulta.get(campo), str) or not consulta[campo].strip() or len(consulta[campo]) > 190:
            raise ValueError(f"Informe {campo} conforme o identificador aceito pelo provedor.")
    solicitado = {campo: consulta[campo] for campo in campos}
    origem, base, confirmado = "unknown", None, None
    if provedor == "fpshq":
        if resposta.get("ok") is not True:
            raise ValueError("A FPSHQ não confirmou um resultado válido.")
        for campo in campos:
            item = resposta.get(campo)
            if not isinstance(item, dict) or item.get("slug") != consulta[campo]:
                raise ValueError("A FPSHQ retornou outro jogo ou hardware.")
        if consulta.get("res") not in ("1080p", "1440p", "4k") or consulta.get("preset") not in ("low", "medium", "high", "ultra"):
            raise ValueError("Resolução ou qualidade inválida para a FPSHQ.")
        if str(resposta.get("res", "")).lower() != consulta["res"] or resposta.get("preset") != consulta["preset"]:
            raise ValueError("A FPSHQ retornou outros ajustes gráficos.")
        solicitado.update(res=consulta["res"], preset=consulta["preset"])
        confirmado = dict(solicitado)
        origem = resposta.get("source") if resposta.get("source") in ("measured", "model") else "unknown"
        base = resposta.get("basis") if resposta.get("basis") in ("measured", "aggregate", "model") else None
        fps, low = resposta.get("fps"), resposta.get("low1")
    else:
        if consulta.get("resolution") not in ("1920x1080", "2560x1440", "3840x2160") or consulta.get("upscaling") != "Native":
            raise ValueError("Esta fase usa as resoluções padrão e upscaling Native do exemplo público da HowManyFPS.")
        solicitado.update(resolution=consulta["resolution"], upscaling="Native")
        # O exemplo público contém só estas métricas; não confirma hardware/preset no retorno.
        fps, low = resposta.get("avgFps"), resposta.get("min1Fps")
    if not numero(fps) or low is not None and (not numero(low) or low > fps):
        raise ValueError("FPS ausente, inválido ou 1% low incompatível com a média.")
    desconhecidos = ["ram_gb", "ram_pentes", "ram_mts", "gpu_vram_gb", "versao_jogo", "cenario",
                     "api_grafica", "sistema", "driver_gpu", "ray_tracing", "frame_generation", "metodo_1_low"]
    desconhecidos.extend(["upscaling"] if provedor == "fpshq" else ["jogo", "cpu", "gpu", "resolucao", "qualidade", "upscaling"])
    return {
        "tipo": "referencia-externa", "provedor": provedor,
        "recebido_em": datetime.now(timezone.utc).isoformat(),
        "consulta_solicitada": solicitado, "consulta_confirmada_no_retorno": confirmado,
        "fps_medio": fps, "fps_1_low": low,
        "origem_declarada": origem, "base_declarada": base,
        "contexto_nao_confirmado": desconhecidos,
        "direitos_de_armazenamento_e_treinamento": "nao-verificados",
        "pronta_para_calibracao": False,
        "observacao": "Referência do provedor, não captura própria. Não completa a base de medições nem comprova a precisão de um modelo independente.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--provedor", choices=("fpshq", "howmanyfps"))
    modo.add_argument("--listar-web", action="store_true", help="Exibir os casos pontuais observados na interface pública.")
    parser.add_argument("--consulta", type=Path)
    parser.add_argument("--resposta", type=Path)
    args = parser.parse_args()
    try:
        if args.listar_web:
            if args.consulta or args.resposta:
                raise ValueError("--listar-web exibe o registro local e não recebe consulta/resposta de API.")
            resultado = ler_json(Path(__file__).resolve().parent / "dados" / "referencias-web.json")
        else:
            if args.consulta is None or args.resposta is None:
                raise ValueError("Informe --consulta e --resposta para normalizar uma referência de API.")
            resultado = normalizar_referencia(args.provedor, ler_json(args.consulta), ler_json(args.resposta))
        print(json.dumps(resultado, ensure_ascii=False, allow_nan=False, indent=2))
        return 0
    except (OSError, ValueError) as erro:
        print(json.dumps({"status": "referencia-invalida", "mensagem": str(erro)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
