"""Somente atributos observados nas respostas reais da API. Não infere ausências."""
import re
from services.catalogo_service.normalizar_produto import nome


CAMPOS = {
    'cor': ('COLOR','MAIN_COLOR','KEYBOARD_COLOR'),
    'tamanho_polegadas': ('DISPLAY_SIZE',), 'resolucao': ('DISPLAY_RESOLUTION',),
    'taxa_atualizacao_hz': ('MAX_REFRESH_RATE',), 'tipo_painel': ('PANEL_TYPE',),
    'tipo_fone': ('HEADPHONE_FORMAT',), 'microfone': ('WITH_MICROPHONE',),
    'mecanico': ('PC_KEYBOARD_ARCHITECTURE',), 'layout': ('LAYOUT',),
    'switch': ('PC_KEYBOARDS_SWITCH_TYPE',), 'tamanho_mm': ('WIDTH',),
    'quantidade': ('UNITS_PER_PACK',), 'compatibilidade': ('CPU_SOCKETS',),
    'tamanho_radiador_mm': ('RADIATOR_LENGTH',),
    'formatos_placa_mae': ('MOTHERBOARDS_COMPATIBILITY',),
    'tamanho_max_gpu_mm': ('MAX_GRAPHIC_CARD_LENGTH',),
    'velocidade_mbps': ('DATA_TRANSFER_RATE',), 'bluetooth': ('WITH_BLUETOOTH',),
    'comprimento_m': ('LENGTH',), 'categoria_cabo': ('NETWORK_CABLE_CATEGORY',),
    'conector': ('INPUT_CONNECTOR','OUTPUT_CONNECTOR'),
}


def complementar(produto, atributos, categoria, specs):
    def valores(*ids):
        return sorted(set().union(*(atributos.get(i,set()) for i in ids)))
    for campo, ids in CAMPOS.items():
        dados = valores(*ids)
        if dados:
            specs[campo] = dados
    titulo = nome(produto.get('name',''))
    rgb = valores('WITH_RGB_LIGHTING')
    if rgb:
        specs['rgb'] = rgb
    iluminacao = valores('WITH_LIGHTS') if categoria == 'mouse' else valores('WITH_RETROILLUMINATION') if categoria == 'teclado' else []
    cores = valores('LED_COLOR', 'BACKLIGHTING_COLOR', 'KEYBOARD_BACKLIGHTING_COLOR')
    if rgb == ['sim'] or any(re.fullmatch(r'(?:led\s*)?a?rgb', v) for v in cores):
        iluminacao.append('sim')
        specs['rgb'] = sorted(set([*rgb, 'sim']))
    if any(v in {'azul','vermelho','verde','branco','multicolor','multicolorido','rainbow'} for v in cores):
        iluminacao.append('sim')
    if iluminacao:
        specs['iluminacao'] = sorted(set(iluminacao))
    if categoria in ('mouse', 'teclado'):
        conexao = list(specs.get('conexao', []))
        if valores('WITH_WIRE') == ['sim'] or valores('IS_WIRELESS') == ['nao']:
            conexao.append('wired')
        if valores('IS_WIRELESS') == ['sim']:
            conexao.append('wireless')
        if valores('WITH_BLUETOOTH') == ['sim']:
            conexao.append('bluetooth')
        texto_conexao = titulo + ' ' + ' '.join(valores('WIRELESS_TECHNOLOGY'))
        if re.search(r'\busb(?:[ -]?c)?\b', texto_conexao):
            conexao.append('usb-c' if re.search(r'\busb[ -]?c\b', texto_conexao) else 'usb')
        if conexao:
            specs['conexao'] = sorted(set(conexao))
    if categoria == 'fone':
        if specs.get('tipo_fone'):
            specs['formato_fone'] = list(specs['tipo_fone'])
        sem_fio = valores('IS_WIRELESS')
        if sem_fio == ['nao']:
            specs['conexao'] = ['wired', *valores('CONNECTOR_TYPES')]
        elif sem_fio == ['sim']:
            specs['conexao'] = ['wireless']
            if valores('WITH_BLUETOOTH') == ['sim']:
                specs['conexao'].append('bluetooth')
        if re.search(r'\bheadset\b',titulo) and valores('WITH_MICROPHONE') == ['sim']:
            specs['tipo_fone'] = ['headset']
    if categoria == 'teclado':
        if re.search(r'\babnt\s*2\b', titulo):
            specs['layout'] = ['abnt2']
    if categoria == 'adaptador_wifi':
        specs['interface'] = valores('NETWORK_CARD_INTERFACE','CONNECTIONS_TYPE')
        texto = ' '.join(valores('STANDARDS'))
        geracoes = [(4,'802.11n'),(5,'802.11ac'),(6,'802.11ax'),(7,'802.11be')]
        presentes = [n for n, padrao in geracoes if padrao in texto]
        if presentes:
            specs['padrao_wifi'] = ['wifi' + str(max(presentes))]


def tipo_refrigeracao(atributos):
    tipo = atributos.get('PRODUCT_TYPE',set())
    refrigeracao = atributos.get('REFRIGERATION_TYPE',set())
    agua = bool(refrigeracao & {'agua','liquida','liquido','resfriamento a agua','water cooling'})
    ar = bool(refrigeracao & {'ar','air cooling'})
    liquido = bool(tipo & {'cooler liquido aio','cooler liquido custom loop'})
    if (agua and ar) or (liquido and ar):
        return None
    if agua or liquido:
        return 'water_cooler'
    if ar and any(re.search(r'\b(?:intel|amd|lga\s*\d|am[2345])',v) for v in atributos.get('CPU_SOCKETS',set())):
        return 'air_cooler'
    if tipo == {'ventoinha'}:
        return 'fan'
    return None
