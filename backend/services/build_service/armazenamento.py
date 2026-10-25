"""Regras puras de armazenamento; metadados ausentes não são capacidade livre."""
import math
import re
from functools import lru_cache


def contagem(valor):
    if isinstance(valor, bool) or not isinstance(valor, (str, int, float)) or not str(valor).strip():
        return None
    try:
        if isinstance(valor, str) and not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', valor.strip()):
            return None
        n = float(valor)
        return int(n) if math.isfinite(n) and n.is_integer() and 0 <= n <= 4096 else None
    except (ValueError, OverflowError):
        return None


def conexao_disco(peca):
    peca = peca or {}
    formato = str(peca.get('formato') or '').upper()
    interface = str(peca.get('interface') or peca.get('tipo') or '').upper()
    if formato_disco(peca).upper() in ('2.5', '3.5', 'U.2', 'U.3', 'PCIE', 'ADD-IN-CARD') and re.search(r'NVME|PCI[E-]', interface):
        return None  # NVMe também existe em outros formatos; não é um M.2 confirmado.
    if re.search(r'M\.?2|NVME|PCI[E-]', formato + ' ' + interface):
        return 'm2-sata' if 'SATA' in interface else 'm2'
    return 'sata' if 'SATA' in interface else None


def formato_disco(peca):
    valor = str((peca or {}).get('formato') or '').strip().replace(',', '.')
    return re.sub(r'[\s"\u2033]|polegadas|inch', '', valor, flags=re.I)


def formato_m2(peca):
    valor = str((peca or {}).get('formato_m2') or (peca or {}).get('formato') or '').upper().strip()
    m = re.fullmatch(r'(?:M\.?2[\s-]*)?(2230|2242|2260|2280|22110)', valor)
    return m[1] if m else None


def encaixe_m2(placa, discos, sata):
    """Procura uma distribuição real; não atribui vários discos ao mesmo slot.

    True exige padrão/tamanho e topologia confirmados. None permite informar
    lacunas sem rejeitar um encaixe possível. A busca tem limite de trabalho.
    """
    slots, portas = placa.get('slots_m2'), placa.get('portas_sata')
    if not isinstance(slots, list) or len(slots) > 16:
        return None
    if any(not isinstance(s, dict) or not isinstance(s.get('nome'), str) or not s['nome'].strip() for s in slots):
        return None
    if len({s['nome'] for s in slots}) != len(slots):
        return None
    declarados = contagem(placa.get('quantidade_slots_m2'))
    if declarados is not None and declarados != len(slots):
        return None
    qtd = sum(q for _, q in discos)
    if qtd > len(slots):
        return False if declarados is not None or placa.get('topologia_armazenamento_verificada') is True else None
    unidades = [(p, formato_m2(p)) for p, q in discos for _ in range(q)]
    portas_ok = (isinstance(portas, list) and len(portas) <= 64
                 and all(isinstance(p, str) and p.strip() for p in portas)
                 and len(set(portas)) == len(portas))
    if portas is not None and not portas_ok:
        return None
    limite = contagem(placa.get('quantidade_portas_sata'))
    if portas_ok and limite is not None and len(portas) != limite:
        return None
    limite = len(portas) if portas_ok else limite
    visitas = 0
    class LimiteBusca(Exception):
        pass

    @lru_cache(maxsize=10000)
    def tentar(i, ocupados, desativadas):
        nonlocal visitas
        visitas += 1
        if visitas > 10000:
            raise LimiteBusca
        if limite is not None and sata + len(desativadas) > limite:
            return False
        if i == len(unidades):
            return True if not sata or limite is not None else None
        peca, formato = unidades[i]
        conexao = conexao_disco(peca)
        pendente = False
        for j, slot in enumerate(slots):
            if ocupados & (1 << j):
                continue
            interfaces, formatos = slot.get('interfaces'), slot.get('formatos')
            interfaces_ok = (isinstance(interfaces, list) and bool(interfaces)
                             and all(v in ('m2', 'm2-sata') for v in interfaces))
            formatos_ok = (isinstance(formatos, list) and bool(formatos)
                          and all(formato_m2({'formato': f}) == f for f in formatos))
            if interfaces_ok and conexao not in interfaces or formatos_ok and formato and formato not in formatos:
                continue
            conhecido = interfaces_ok and formatos_ok and formato is not None and slot.get('condicional_cpu') is False
            removidas = ()
            if sata:
                mapa = slot.get('portas_sata_desativadas')
                removidas = mapa.get(conexao) if isinstance(mapa, dict) else None
                perdas_ok = (isinstance(removidas, list) and limite is not None
                             and all(isinstance(p, str) and 0 < len(p.strip()) <= 64 for p in removidas)
                             and len(set(removidas)) <= limite
                             and (not portas_ok or all(p in portas for p in removidas)))
                conhecido = conhecido and perdas_ok
                removidas = tuple(removidas) if perdas_ok else ()
            resultado = tentar(i + 1, ocupados | (1 << j), tuple(sorted(set(desativadas) | set(removidas))))
            if resultado is True and conhecido:
                return True
            if resultado is None or resultado is True:
                pendente = True
        return None if pendente else False

    try:
        resultado = tentar(0, 0, ())
    except LimiteBusca:
        return None
    if resultado is False and declarados is None and placa.get('topologia_armazenamento_verificada') is not True:
        return None
    if resultado is True and placa.get('topologia_armazenamento_verificada') is not True:
        return None
    return resultado


def avaliar_armazenamento(placa, discos):
    """discos: pares (item selecionado, ficha ou None). Não altera o estado."""
    regras = []
    def adicionar(codigo, titulo, condicao, mensagem):
        regras.append(dict(codigo=codigo, titulo=titulo, condicao=condicao, mensagem=mensagem))
    conhecidos, quantidades_ok, m2, sata, m2sata = True, True, [], 0, 0
    for item, peca in discos:
        q, conexao = contagem(item.get('quantidade', 1)), conexao_disco(peca)
        if q is None or q < 1:
            quantidades_ok = False
            continue
        if conexao in ('m2', 'm2-sata'):
            m2.append((peca, q))
            m2sata += q if conexao == 'm2-sata' else 0
        elif conexao == 'sata':
            sata += q
        else:
            conhecidos = False
    adicionar('discos-interface', 'Identificação dos discos', True if conhecidos and quantidades_ok else None,
              'As conexões dos discos estão identificadas.' if conhecidos and quantidades_ok else
              'Falta identificar a conexão ou a quantidade de algum SSD/HD; não foi presumido NVMe ou SATA.')
    usados_m2 = sum(q for _, q in m2)
    for usados, campo, codigo, nome in (
        (usados_m2, 'quantidade_slots_m2', 'discos-m2', 'slots M.2'),
        (m2sata, 'quantidade_slots_m2_sata', 'm2-sata', 'slots M.2 com suporte a SATA'),
    ):
        if usados:
            limite = contagem(placa.get(campo))
            adicionar(codigo, 'Conexões ' + nome, usados <= limite if limite is not None else None,
                      f'{usados} SSD(s) para {limite} {nome}.' if limite is not None else f'Falta a quantidade de {nome} da placa-mãe.')
    limite = contagem(placa.get('quantidade_portas_sata'))
    perdas = contagem(placa.get('portas_sata_desativadas_por_m2_sata'))
    por_slot = isinstance(placa.get('slots_m2'), list) and placa.get('topologia_armazenamento_verificada') is True
    limite_sata = limite if por_slot or not m2sata else max(0, limite - m2sata * perdas) if limite is not None and perdas is not None else None
    encaixe = encaixe_m2(placa, m2, sata) if usados_m2 and quantidades_ok else None
    if sata:
        condicao = sata <= limite_sata if limite_sata is not None else False if limite is not None and sata > limite else None
        if por_slot and usados_m2 and condicao is True:
            condicao = True if encaixe is True else None
        adicionar('discos-sata', 'Portas SATA disponíveis', condicao,
                  f'{sata} disco(s) SATA; capacidade física: {limite_sata}. A distribuição dos M.2 define quais portas ficam disponíveis.' if por_slot and limite_sata is not None else
                  f'{sata} disco(s); limite SATA considerando as perdas cadastradas: {limite_sata}.' if limite_sata is not None else
                  'Falta confirmar as portas SATA disponíveis após instalar os SSDs M.2.')
    if not usados_m2 and conhecidos and quantidades_ok and limite is not None:
        encaixe = sata <= limite
    if not conhecidos or not quantidades_ok:
        encaixe = None if encaixe is not False else False
    adicionar('discos-compartilhamento', 'Encaixe e compartilhamento M.2/SATA', encaixe,
              'Os padrões e tamanhos dos SSDs cabem nos slots cadastrados, com portas SATA suficientes.' if encaixe is True else
              'Não há distribuição dos SSDs nos slots e portas cadastrados: confira padrão, tamanho e portas SATA desativadas.' if encaixe is False else
              'Faltam detalhes dos slots: padrões aceitos, comprimento dos SSDs ou portas SATA compartilhadas. As baias são verificadas separadamente.')
    return regras


def avaliar_baias(gabinete, discos):
    usados = {'baias_25': 0, 'baias_35': 0}
    conhecidos = True
    regras = []
    for item, peca in discos:
        if conexao_disco(peca) in ('m2', 'm2-sata'):
            continue
        formato, q = formato_disco(peca), contagem(item.get('quantidade', 1))
        if formato not in ('2.5', '3.5') or q is None or q < 1:
            conhecidos = False
            continue
        usados['baias_25' if formato == '2.5' else 'baias_35'] += q
    if not conhecidos:
        regras.append(dict(codigo='discos-baias-identificacao', titulo='Formato dos discos e baias', condicao=None,
                           mensagem='Falta identificar o formato físico de algum SSD/HD para conferir as baias.'))
    for campo, q in usados.items():
        if q:
            limite = contagem(gabinete.get(campo))
            regras.append(dict(codigo='baias-' + campo, titulo='Baias de ' + ('2,5' if campo == 'baias_25' else '3,5') + ' polegadas',
                               condicao=q <= limite if limite is not None else None,
                               mensagem=f'{q} disco(s); limite cadastrado: {limite}.' if limite is not None else 'Falta a quantidade de baias deste tamanho no gabinete.'))
    arranjos = gabinete.get('configuracoes_baias')
    if not any(usados.values()):
        return regras
    if arranjos is None and not all(usados.values()):
        return regras
    resultado = None
    if isinstance(arranjos, list) and 1 <= len(arranjos) <= 32:
        validos = [a for a in arranjos if isinstance(a, dict) and all(contagem(a.get(c)) is not None for c in usados)]
        if any(all(usados[c] <= contagem(a[c]) for c in usados) for a in validos):
            resultado = True if conhecidos else None
        elif len(validos) == len(arranjos) and gabinete.get('configuracoes_baias_completas') is True:
            resultado = False
    regras.append(dict(codigo='baias-conjunto', titulo='Baias usadas ao mesmo tempo', condicao=resultado,
                       mensagem='Os discos cabem juntos em um arranjo de baias cadastrado.' if resultado is True else
                       'Os SSDs/HDs não cabem juntos nas baias compartilhadas deste gabinete.' if resultado is False else
                       'Falta confirmar quais baias podem ser usadas ao mesmo tempo; não some montagens alternativas.'))
    return regras
