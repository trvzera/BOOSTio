"""Tipos e quantidades de conectores; não simula potência por cabo ou adaptadores."""
from .armazenamento import contagem, conexao_disco, formato_disco


TIPOS = {'atx_24', 'eps_8', 'atx12v_4', 'eps_4_4', 'pcie_6', 'pcie_8', 'pcie_6_2',
         '12vhpwr', '12v_2x6', 'sata', 'molex_4'}
ROTULOS = {'atx_24': 'ATX de 24 pinos', 'eps_8': 'EPS/CPU de 8 pinos', 'atx12v_4': 'CPU de 4 pinos',
           'eps_4_4': 'EPS/CPU 4+4', 'pcie_6': 'PCIe de 6 pinos', 'pcie_8': 'PCIe de 8 pinos',
           'pcie_6_2': 'PCIe 6+2', '12vhpwr': '12VHPWR', '12v_2x6': '12V-2x6', 'sata': 'SATA', 'molex_4': 'Molex de 4 pinos'}


def avaliar_conectores(fonte, consumidores):
    exigidos, pendente, gpu_multiplos = {}, False, False
    for categoria, item, peca in consumidores:
        peca = peca or {}
        quantidade = contagem(item.get('quantidade', 1))
        if quantidade is None or quantidade < 1:
            pendente = True
            continue
        if categoria in ('ssd', 'hd'):
            # M.2 é alimentado pelo slot. SATA de 2,5/3,5 usa alimentação SATA;
            # interfaces/formas desconhecidas não são tratadas como estes padrões.
            conexao = conexao_disco(peca)
            if conexao in ('m2', 'm2-sata') and str(peca.get('formato') or '').upper().replace('.', '').startswith('M2'):
                continue
            if conexao == 'sata' and formato_disco(peca) in ('2.5', '3.5'):
                exigidos['sata'] = exigidos.get('sata', 0) + quantidade
                continue
        mapa = peca.get('conectores_alimentacao')
        if not isinstance(mapa, dict):
            pendente = True
            continue
        if peca.get('conectores_alimentacao_completos') is not True:
            pendente = True
        for tipo, valor in mapa.items():
            n = contagem(valor)
            if tipo not in TIPOS or n is None:
                pendente = True
            else:
                necessario = {'eps_4_4': 'eps_8', 'pcie_6_2': 'pcie_8'}.get(tipo, tipo)
                exigidos[necessario] = exigidos.get(necessario, 0) + n * quantidade
        if categoria == 'placa_video' and sum(contagem(mapa.get(t, 0)) or 0 for t in ('pcie_6', 'pcie_8', 'pcie_6_2')) > 1:
            gpu_multiplos = True
    inventario = fonte.get('conectores_alimentacao')
    completo = fonte.get('conectores_alimentacao_completos') is True
    if not isinstance(inventario, dict):
        inventario, completo, pendente = {}, False, True
    if any(t not in TIPOS or contagem(n) is None for t, n in inventario.items()):
        completo, pendente = False, True
    disponivel = lambda tipo: contagem(inventario.get(tipo, 0 if completo else None))
    conflitos = []
    grupos = [('eps_8', 'atx12v_4', 'eps_4_4'), ('pcie_8', 'pcie_6', 'pcie_6_2')]
    dezesseis = ('12vhpwr', '12v_2x6')
    if any(exigidos.get(t, 0) for t in dezesseis):
        diretos = all(disponivel(t) is not None and exigidos.get(t, 0) <= disponivel(t) for t in dezesseis if exigidos.get(t, 0))
        if not diretos:
            totais = [disponivel(t) for t in dezesseis]
            if all(v is not None for v in totais) and sum(exigidos.get(t, 0) for t in dezesseis) > sum(totais):
                conflitos.append('conectores de 16 pinos')
            else:
                pendente = True  # Variações de 16 pinos não são declaradas incompatíveis só pelo nome.
    agrupados = {t for g in grupos for t in g} | set(dezesseis)
    for tipos in grupos + [(t,) for t in TIPOS - agrupados]:
        fixos, flex = tipos[:-1], tipos[-1]
        if len(tipos) == 1:
            fixos, flex = tipos, None
        usados_flex = exigidos.get(flex, 0) if flex else 0
        falta, todos_conhecidos = usados_flex, True
        if not any(exigidos.get(t, 0) for t in tipos):
            continue
        for tipo in fixos:
            precisa, possui = exigidos.get(tipo, 0), disponivel(tipo)
            if precisa:
                falta += max(0, precisa - (possui or 0))
                todos_conhecidos = todos_conhecidos and possui is not None
                f = disponivel(flex) if flex else 0
                if possui is not None and f is not None and precisa > possui + max(0, f - usados_flex):
                    conflitos.append(ROTULOS[tipo])
        livres_flex = disponivel(flex) if flex else 0
        if livres_flex is not None and falta <= livres_flex:
            continue
        if todos_conhecidos and livres_flex is not None:
            conflitos.extend(ROTULOS[t] for t in tipos if exigidos.get(t, 0))
        else:
            pendente = True
    if gpu_multiplos:
        gpu = next((p for c, _, p in consumidores if c == 'placa_video'), {}) or {}
        minimo, cabos = contagem(gpu.get('cabos_pcie_independentes_minimos')), contagem(fonte.get('cabos_pcie_independentes'))
        if minimo is None or cabos is None:
            pendente = True
        elif minimo > cabos:
            conflitos.append('cabos PCIe independentes')
    if conflitos:
        return False, 'A fonte não oferece conectores suficientes para: ' + ', '.join(sorted(set(conflitos))) + '. EPS/CPU e PCIe não são intercambiáveis.'
    if pendente or not consumidores:
        return None, 'Faltam tipos/quantidades de conectores ou a exigência de cabos PCIe independentes. Não foi presumido adaptador nem que EPS/CPU seja PCIe.'
    return True, 'Tipos e quantidades de conectores da placa-mãe, GPU e discos atendidos. Fans, hubs, adaptadores e limites elétricos por cabo precisam de conferência separada.'
