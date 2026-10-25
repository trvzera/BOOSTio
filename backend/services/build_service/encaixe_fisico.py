"""Regras puras de encaixe. Dados ausentes permanecem não verificados.

As fans de fábrica são mantidas. Opções 120/140 mm na mesma posição são
alternativas, não capacidades somáveis. Não simula espessura/interferência.
"""
import math
from functools import lru_cache
from .armazenamento import avaliar_baias


def n(valor):
    if valor is None or isinstance(valor, bool) or valor == "":
        return None
    try:
        valor = float(valor)
        return valor if math.isfinite(valor) and valor >= 0 else None
    except (ValueError, TypeError):
        return None


def inteiro(valor, minimo=0):
    valor = n(valor)
    return int(valor) if valor is not None and valor.is_integer() and minimo <= valor <= 64 else None


def tamanhos(valor):
    if not isinstance(valor, list) or any(n(v) is None or n(v) <= 0 for v in valor):
        return None
    return [n(v) for v in valor]


def posicoes(gabinete):
    grupos = gabinete.get("posicoes_fans")
    if not isinstance(grupos, list) or not 1 <= len(grupos) <= 12:
        return None
    for grupo in grupos:
        if not isinstance(grupo, dict):
            return None
        opcoes, inclusas = grupo.get("opcoes"), grupo.get("fans_inclusas")
        if not isinstance(opcoes, list) or not 1 <= len(opcoes) <= 8 or not isinstance(inclusas, list):
            return None
        if any(not isinstance(v, dict) or not n(v.get("tamanho_mm")) or inteiro(v.get("quantidade"), 1) is None
               for v in opcoes + inclusas):
            return None
        if tamanhos(grupo.get("radiadores_mm")) is None:
            return None
    return [{**g, "opcoes": [{"tamanho_mm": n(o["tamanho_mm"]), "quantidade": inteiro(o["quantidade"], 1)} for o in g["opcoes"]],
             "fans_inclusas": [{"tamanho_mm": n(o["tamanho_mm"]), "quantidade": inteiro(o["quantidade"], 1)} for o in g["fans_inclusas"]],
             "radiadores_mm": tamanhos(g["radiadores_mm"])} for g in grupos]


def distribuir_fans(grupos, demanda, water, inclusas, completas=True):
    if grupos is None or inclusas is None:
        return None
    if sum(f["quantidade"] for g in grupos for f in g["fans_inclusas"]) != inclusas:
        return None
    if water is not None and (not n(water.get("tamanho_fan_mm")) or inteiro(water.get("quantidade_fans"), 1) is None
                  or not n(water.get("tamanho_radiador_mm"))):
        return None
    if water is not None:
        water = {**water, "tamanho_fan_mm": n(water["tamanho_fan_mm"]),
                 "quantidade_fans": inteiro(water["quantidade_fans"], 1), "tamanho_radiador_mm": n(water["tamanho_radiador_mm"])}
    # Mesmo uma lista parcial de arranjos tem limites superiores por diâmetro.
    # Uma mistura não documentada, por outro lado, não é conflito confirmado.
    totais = dict(demanda)
    for grupo in grupos:
        for fan in grupo["fans_inclusas"]:
            d = fan["tamanho_mm"]
            totais[d] = totais.get(d, 0) + fan["quantidade"]
    if water is not None:
        d = water["tamanho_fan_mm"]
        totais[d] = totais.get(d, 0) + water["quantidade_fans"]
    for d, quantidade in totais.items():
        limite = sum(max((o["quantidade"] for o in g["opcoes"] if o["tamanho_mm"] == d), default=0) for g in grupos)
        if quantidade > limite:
            return False
    diametros = sorted(demanda)
    inicial = tuple(demanda[d] for d in diametros)

    @lru_cache(maxsize=None)
    def tentar(indice, restante, radiador_pendente):
        if indice == len(grupos):
            return not any(restante) and not radiador_pendente
        grupo = grupos[indice]
        for opcao in grupo["opcoes"]:
            diametro, capacidade = opcao["tamanho_mm"], opcao["quantidade"]
            if any(f["tamanho_mm"] != diametro for f in grupo["fans_inclusas"]):
                continue
            livres = capacidade - sum(f["quantidade"] for f in grupo["fans_inclusas"])
            for instalar in (False, True) if radiador_pendente else (False,):
                if instalar and (water["tamanho_radiador_mm"] not in grupo["radiadores_mm"] or water["tamanho_fan_mm"] != diametro):
                    continue
                vagas = livres - (water["quantidade_fans"] if instalar else 0)
                if vagas < 0:
                    continue
                atual = list(restante)
                if diametro in diametros:
                    i = diametros.index(diametro)
                    atual[i] = max(0, atual[i] - vagas)
                if tentar(indice + 1, tuple(atual), radiador_pendente and not instalar):
                    return True
        return False

    resultado = tentar(0, inicial, water is not None)
    return resultado if resultado or completas else None


def avaliar_fans(gabinete, fans, water=None, substituir=False):
    """fans: pares (item selecionado, peça). Quantidade do produto = fans por kit."""
    grupos = posicoes(gabinete)
    maximo = inteiro(gabinete.get("quantidade_max_fans"))
    if grupos is not None:
        capacidade = sum(max(o["quantidade"] for o in g["opcoes"]) for g in grupos)
        maximo = min(maximo, capacidade) if maximo is not None else capacidade
    inclusas = inteiro(gabinete.get("fans_inclusos"))
    radiador = inteiro(water.get("quantidade_fans"), 1) if water is not None else 0
    suportados = tamanhos(gabinete.get("tamanhos_fan_suportados_mm"))
    if grupos is not None:
        suportados = sorted({o["tamanho_mm"] for g in grupos for o in g["opcoes"]})
    quantidade = 0
    completos = True
    medidas_conhecidas = True
    demanda = {}
    tamanho_ok = None if suportados is None else True
    for item, peca in fans:
        peca = peca or {}
        kit, repeticoes = inteiro(peca.get("quantidade"), 1), inteiro(item.get("quantidade", 1), 1)
        tamanho = n(peca.get("tamanho_mm")) or None
        if kit is None or repeticoes is None:
            completos = False
        else:
            unidades = kit * repeticoes
            quantidade += unidades
            if tamanho:
                demanda[tamanho] = demanda.get(tamanho, 0) + unidades
        if tamanho is None:
            medidas_conhecidas = False
        elif suportados is not None and tamanho not in suportados:
            tamanho_ok = False
    if tamanho_ok is not False and not medidas_conhecidas:
        tamanho_ok = None
    substituidas = min(quantidade, radiador or 0) if substituir and completos else 0
    substituicao_ok = True
    tamanho_water = n((water or {}).get("tamanho_fan_mm")) or None
    if substituir and water is not None:
        substituicao_ok = None
        if radiador is not None and completos and tamanho_water is not None:
            substituicao_ok = demanda.get(tamanho_water, 0) >= radiador
        if radiador is not None and completos and quantidade < radiador:
            substituicao_ok = False
        if substituicao_ok is True:
            demanda[tamanho_water] -= radiador
        elif substituicao_ok is False:
            substituidas = 0
    minimo = quantidade + (inclusas or 0) + (radiador or 0) - substituidas
    total = minimo if completos and inclusas is not None and radiador is not None else None
    quantidade_ok = False if maximo is not None and minimo > maximo else total <= maximo if total is not None and maximo is not None else None
    distribuicao = False if quantidade_ok is False or substituicao_ok is False else distribuir_fans(grupos, demanda, water, inclusas, gabinete.get("posicoes_fans_completas") is not False) if completos and medidas_conhecidas and substituicao_ok is True else None
    return {"selecionadas": quantidade if completos else None, "inclusas": inclusas, "radiador": radiador,
            "total": total, "capacidade": maximo, "livres": max(0, maximo - total) if maximo is not None and total is not None else None,
            "tamanhos": tamanho_ok, "quantidade": quantidade_ok, "distribuicao": distribuicao,
            "substituidas": substituidas, "substituicao": substituicao_ok}


def encaixe_cooler_placa(cooler, placa):
    normalizar = lambda v: " ".join(str(v or "").split()).upper()
    if not placa.get("fabricante") or not placa.get("modelo") or not isinstance(cooler.get("placas_mae_incompativeis"), list):
        return None
    fabricante, modelo = normalizar(placa["fabricante"]), normalizar(placa["modelo"])
    nome = modelo if modelo.startswith(fabricante + " ") else fabricante + " " + modelo
    return False if any(normalizar(p) == nome for p in cooler["placas_mae_incompativeis"]) else None


def avaliar_medidas(itens, registrar, substituir=False):
    def get(tipo):
        return next((p for t, _, p in itens if t == tipo), None) or {}
    def tem(tipo):
        return any(t == tipo for t, _, _ in itens)
    for tipo in ("air_cooler", "water_cooler"):
        if tem("placa_mae") and get(tipo).get("placas_mae_incompativeis"):
            registrar(tipo + "-placa-excecao", "Interferência física entre cooler e placa-mãe",
                      encaixe_cooler_placa(get(tipo), get("placa_mae")),
                      "O fabricante do cooler declara incompatibilidade com os modelos exatos da lista. Não estar na lista não certifica todas as folgas ou kits de montagem.")
    gabinete = get("gabinete")
    if not tem("gabinete"):
        return None
    for tipo, campo, limite, codigo, titulo in (
        ("placa_video", "comprimento_mm", "tamanho_max_gpu_mm", "placa_video-medida", "Comprimento da GPU"),
        ("placa_video", "altura_mm", "tamanho_max_altura_gpu_mm", "gpu-altura", "Altura da GPU"),
        ("placa_video", "espessura_mm", "tamanho_max_espessura_gpu_mm", "gpu-espessura", "Espessura da GPU"),
        ("placa_video", "slots_ocupados", "slots_expansao", "gpu-slots", "Espessura da GPU em slots"),
        ("air_cooler", "altura_mm", "tamanho_max_cooler_mm", "air_cooler-medida", "Altura do air cooler"),
        ("fonte", "comprimento_mm", "tamanho_max_fonte_mm", "fonte-medida", "Comprimento da fonte"),
    ):
        if tem(tipo):
            medida, maximo = n(get(tipo).get(campo)) or None, n(gabinete.get(limite)) or None
            registrar(codigo, titulo, medida <= maximo if medida is not None and maximo is not None else None,
                      f"{titulo}: {medida:g} / {maximo:g}" if medida is not None and maximo is not None else
                      f"Faltam {campo} da peça ou {limite} do gabinete; medidas genéricas não são interpretadas.")
    if tem("fonte"):
        formatos, formato = gabinete.get("formatos_fonte"), get("fonte").get("formato")
        norm = lambda v: str(v).upper().replace(" ", "").replace("-", "")
        registrar("fonte-formato", "Formato da fonte", norm(formato) in [norm(v) for v in formatos] if formato and isinstance(formatos, list) else None,
                  "Compare os formatos de fonte explicitamente aceitos pelo gabinete.")
    if tem("water_cooler"):
        water = get("water_cooler")
        radiadores = tamanhos(gabinete.get("radiadores_suportados_mm"))
        tamanho = n(water.get("tamanho_radiador_mm")) or None
        condicao = False if gabinete.get("suporte_water_cooler") is False else tamanho in radiadores if tamanho and radiadores is not None else None
        registrar("radiador", "Tamanho do radiador", condicao, "Suporte genérico a water cooler não garante espaço para qualquer radiador.")
        registrar("radiador-posicao", "Espessura e interferências do radiador", None,
                  "O tamanho nominal não confirma espessura, folga sobre a RAM ou interferência com a GPU.")
        registrar("radiador-dimensoes", "Dimensões reais do radiador e das fans", encaixe_radiador(gabinete, water),
                  "Compare comprimento/largura externos e espessura radiador + fans com os limites por posição. Não há margem universal de 3–5 cm; tanques, conexões e tubos precisam de medidas reais.")
    if tem("placa_video"):
        registrar("gpu-interferencias", "Espaço completo da GPU", None,
                  "Conferir cabos e folgas com radiador/fans frontais; comprimento isolado não confirma o conjunto.")
    discos = [(item, p) for tipo, item, p in itens if tipo in ("ssd", "hd")]
    for r in avaliar_baias(gabinete, discos):
        registrar(r['codigo'], r['titulo'], r['condicao'], r['mensagem'])
    if not tem("fan") and not tem("water_cooler"):
        return avaliar_fans(gabinete, [])
    fans = [(item, p) for tipo, item, p in itens if tipo == "fan"]
    info = avaliar_fans(gabinete, fans, get("water_cooler") if tem("water_cooler") else None, substituir)
    registrar("fans-tamanho", "Tamanho das fans", info["tamanhos"], "O diâmetro de cada fan deve constar nos encaixes do gabinete.")
    registrar("fans-quantidade", "Quantidade total de fans", info["quantidade"],
              "Fans selecionadas: {}; inclusas: {}; radiador: {}; capacidade: {}. Fans do water cooler já ocupam posições; não some outro kit nessas posições sem configurar a substituição.".format(
                  *(info[campo] if info[campo] is not None else "não informada" for campo in ("selecionadas", "inclusas", "radiador", "capacidade"))))
    registrar("fans-posicoes", "Posições das fans e do radiador", info["distribuicao"],
              "Verifica distribuição entre posições compartilhadas e mantém as fans de fábrica. Dados ausentes não confirmam a instalação.")
    if substituir and tem("water_cooler"):
        registrar("fans-substituicao", "Substituição das fans do water cooler", info["substituicao"],
                  "É necessário selecionar fans suficientes do mesmo tamanho das fans originais do radiador. Verifique furação, espessura, pressão estática, conectores e parafusos corretos; parafusos longos podem danificar o radiador.")
    return info


def encaixe_radiador(gabinete, water):
    limites = gabinete.get("limites_radiador_mm")
    if not isinstance(limites, list) or not limites:
        return None
    nominal = n(water.get("tamanho_radiador_mm")) or None
    medidas = [n(water.get(c)) or None for c in ("comprimento_radiador_mm", "largura_radiador_mm")]
    espessuras = [n(water.get(c)) or None for c in ("espessura_radiador_mm", "espessura_fan_mm")]
    medidas.append(sum(espessuras) if all(v is not None for v in espessuras) else None)
    resultados = []
    for limite in limites:
        if not isinstance(limite, dict):
            resultados.append(None)
            continue
        tamanhos_posicao = tamanhos(limite.get("tamanhos_mm"))
        if nominal and tamanhos_posicao is not None and nominal not in tamanhos_posicao:
            continue
        maximos = [n(limite.get(c)) or None for c in ("comprimento_mm", "largura_mm", "espessura_conjunto_mm")]
        if any(m is not None and l is not None and m > l for m, l in zip(medidas, maximos)):
            resultados.append(False)
        elif all(v is not None for v in medidas + maximos) and nominal and tamanhos_posicao is not None:
            resultados.append(True)
        else:
            resultados.append(None)
    return True if True in resultados else None if None in resultados else False
