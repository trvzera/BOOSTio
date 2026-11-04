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
    if categoria == 'fone':
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
    if tipo == {'ventoinha'}:
        return 'fan'
    if refrigeracao & {'agua','liquida','liquido'}:
        return 'water_cooler'
    if refrigeracao == {'ar'} and any(re.search(r'\b(?:intel|amd|lga|am[2345])',v) for v in atributos.get('CPU_SOCKETS',set())):
        return 'air_cooler'
    return None
