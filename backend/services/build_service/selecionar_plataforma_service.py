from decimal import Decimal
from models import Processador, PlacaMae
from utils.sockets import normalizar_socket
from utils.memorias import normalizar_ddr
from .constantes_build import PERIFERICOS
from .catalogo_geracao_service import campos_catalogo
from .preferencias_cores_service import PreferenciasCoresService


def id_numerico(identificador):
    return int(str(identificador).split(":")[-1])


def aplicar_teto(contexto, tipo, pecas):
    absoluto = contexto["teto_perifericos"] if tipo in PERIFERICOS else contexto["teto_peca"]
    teto = contexto["planejamento"]["tetos_sugeridos"].get(tipo, absoluto)
    dentro = [p for p in pecas if Decimal(str(p["preco"])) <= Decimal(str(teto))]
    if dentro:
        cor = contexto["aparencia"]["cor"]
        if cor != "sem-preferencia" and not any(PreferenciasCoresService.prioridade(p, cor) <= 1 for p in dentro):
            preferidas = [p for p in pecas if PreferenciasCoresService.prioridade(p, cor) <= 1]
            if preferidas:
                dentro = [*dentro, min(preferidas, key=lambda p: (p["preco"], p["id"]))]
                contexto["planejamento"]["flexibilizacoes"].append(
                    f"{tipo}: preservada alternativa da cor pedida fora da meta, dentro do teto absoluto.")
        return dentro
    if not pecas:
        return []
    menor = min(Decimal(str(p["preco"])) for p in pecas)
    contexto["planejamento"]["flexibilizacoes"].append(
        f"{tipo}: teto de busca {teto} insuficiente; preservadas opções de menor preço {menor}.")
    return [p for p in pecas if Decimal(str(p["preco"])) == menor]


def ficha_catalogo(peca):
    ficha = campos_catalogo({**peca, "id": id_numerico(peca["id"])})
    for campo in ("benchmark_multi_core", "benchmark_single_thread", "benchmark_g3d", "benchmark_g2d",
                  "benchmark_teste", "benchmark_versao"):
        valor = peca.get(campo)
        if valor is not None:
            ficha[campo] = float(valor) if isinstance(valor, Decimal) else valor
    return ficha


def selecionar_placas_mae(contexto, selecionados):
    sockets = _sockets_processadores(contexto, selecionados)
    grupos = {s: [] for s in sockets}
    propria_ram = contexto["detalhes_proprias"].get("memoria_ram", {}).get("especificacoes_confirmadas", {})
    ddr_proprio = normalizar_ddr(propria_ram.get("ddr"))
    for p in contexto["pools"].get("placa_mae", []):
        if ddr_proprio and normalizar_ddr(p.get("tipo_memoria")) != ddr_proprio:
            continue
        socket = normalizar_socket(p.get("socket"))
        if socket in grupos:
            grupos[socket].append(p)
    return _amostrar_grupos(contexto, "placa_mae", grupos)


def selecionar_memorias(contexto, placas):
    nome_proprio = contexto["proprias"].get("placa_mae")
    if nome_proprio:
        placa = PlacaMae.buscar_por_nome(nome_proprio)
        valores = [placa.tipo_memoria] if placa else []
    else:
        valores = [placa.get("tipo_memoria") for placa in placas]
    ddrs = sorted({ddr for valor in valores if (ddr := normalizar_ddr(valor))})
    grupos = {ddr: [] for ddr in ddrs}
    for p in contexto["pools"].get("memoria_ram", []):
        ddr = normalizar_ddr(p.get("ddr"))
        if ddr in grupos:
            grupos[ddr].append(p)
    return _amostrar_grupos(contexto, "memoria_ram", grupos)


def _amostrar_grupos(contexto, tipo, grupos):
    for grupo, pecas in grupos.items():
        pecas = aplicar_teto(contexto, tipo, pecas)
        pecas.sort(key=lambda p: (PreferenciasCoresService.prioridade(p, contexto["aparencia"]["cor"]),
                                  p["preco"], id_numerico(p["id"])))
        grupos[grupo] = pecas
    escolhidas = _distribuir_vagas(grupos, contexto["limites"][tipo])
    return [ficha_catalogo(p) for p in escolhidas]


def _sockets_processadores(contexto, selecionados):
    nome_proprio = contexto["proprias"].get("processador")
    if nome_proprio:
        cpu = Processador.buscar_por_nome(nome_proprio)
        valores = [cpu.soquete] if cpu else []
    elif contexto["categoria"] in ("placa_mae", "memoria_ram"):
        valores = [cpu.get("soquete") for cpu in contexto.get("cpus_candidatas", [])]
    else:
        valores = [p.get("soquete") for p in selecionados if p["categoria"] == "processador"]
    return sorted({socket for valor in valores if (socket := normalizar_socket(valor))})


def _distribuir_vagas(grupos, limite):
    escolhidas, ids = [], set()
    ativos = [iter(grupos[socket]) for socket in sorted(grupos) if grupos[socket]]
    while ativos and len(escolhidas) < limite:
        proximos = []
        for grupo in ativos:
            peca = next(grupo, None)
            if peca is None:
                continue
            proximos.append(grupo)
            ident = peca["id"] if isinstance(peca, dict) else peca.id
            if ident not in ids:
                escolhidas.append(peca)
                ids.add(ident)
            if len(escolhidas) == limite:
                break
        ativos = proximos
    return escolhidas
