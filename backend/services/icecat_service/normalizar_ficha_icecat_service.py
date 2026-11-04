"""Converte somente campos estruturados da ficha inglesa, com evidência por campo."""
import hashlib
import re
from defusedxml.ElementTree import fromstring
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError
from services.catalogo_service.normalizar_produto import nome, numero, gtin

# Nomes da taxonomia inglesa da ficha XML. Rótulos desconhecidos ficam pendentes.
CATEGORIAS = {
    'processador': {'processors'}, 'placa_video': {'graphics cards'},
    'memoria_ram': {'memory modules'}, 'placa_mae': {'motherboards'},
    'ssd': {'internal solid state drives'}, 'hd': {'internal hard drives'},
    'fonte': {'power supply units'}, 'gabinete': {'computer cases'},
    'mouse': {'mice'}, 'teclado': {'keyboards'}, 'monitor': {'computer monitors'},
    'fone': {'headphones & headsets'}, 'cabo_rede': {'networking cables'},
    'adaptador_wifi': {'network cards'},
    'air_cooler': {'computer cooling systems'}, 'water_cooler': {'computer cooling systems'},
    'fan': {'computer cooling systems'},
}
CAMPOS = {
    'processador': {
        'Processor socket': ('soquete', None), 'Processor cores': ('nucleo', 'int'),
        'Processor threads': ('thread', 'int'), 'Processor base frequency': ('clockbase', 'ghz'),
        'Processor boost frequency': ('clockmax', 'ghz'),
        'Thermal Design Power (TDP)': ('consumo_energia', 'w'),
        'On-board graphics card': ('videointegrado', 'bool'),
        'On-board graphics card model': ('modelo_videointegrado', None),
        'Cooler included': ('cooler', 'bool'),
    },
    'memoria_ram': {
        'Internal memory': ('capacidade_gb', 'gb'), 'Internal memory type': ('ddr', None),
        'Memory clock speed': ('frequencia_mhz', 'mhz'), 'Bus clock rate': ('frequencia_mhz', 'mhz'), 'Memory form factor': ('formato', None),
        'CAS latency': ('latencia', None), 'Memory layout (modules x size)': ('quantidade_pentes', 'modulos'),
    },
    'placa_video': {
        'Discrete graphics card memory': ('memoria_gb', 'gb'), 'Graphics card memory type': ('tipo_memoria', None),
    },
    'placa_mae': {
        'Processor socket': ('socket', None), 'Supported memory types': ('tipo_memoria', None),
        'Motherboard form factor': ('formato', None), 'Motherboard chipset': ('chipset', None),
        'Number of memory slots': ('quantidade_slots_ram', 'int'), 'Maximum internal memory': ('memoria_maxima_gb', 'gb'),
    },
    'ssd': {
        'SSD capacity': ('capacidade_gb', 'gb'), 'Interface': ('interface', None),
        'SSD form factor': ('formato', None), 'Read speed': ('velocidade_leitura_mbps', 'mbps'),
        'Write speed': ('velocidade_gravacao_mbps', 'mbps'), 'NVMe': ('tipo', 'nvme'),
    },
    'hd': {
        'HDD capacity': ('capacidade_gb', 'gb'), 'Interface': ('interface', None),
        'HDD speed': ('velocidade_rpm', 'rpm'), 'Storage drive buffer size': ('memoria_cache_mb', 'mb'),
    },
    'fonte': {'Total power': ('potencia_w', 'w'), 'Power supply unit (PSU) form factor': ('formato', None)},
    'gabinete': {'Supported motherboard form factors': ('formatos_placa_mae', 'lista')},
    'mouse': {'Movement resolution': ('dpi_max', 'dpi'), 'Device interface': ('conexao', None)},
    'teclado': {'Keyboard layout': ('layout', None), 'Keyboard key switch': ('mecanico', 'switch'), 'Device interface': ('conexao', None)},
    'monitor': {'Display diagonal': ('tamanho_polegadas', 'inch'), 'Display resolution': ('resolucao', None),
                'Maximum refresh rate': ('taxa_atualizacao_hz', 'hz'), 'Panel type': ('tipo_painel', None)},
    'fone': {'Product type': ('tipo', None), 'Microphone type': ('microfone', 'microfone')},
    'cabo_rede': {'Cable standard': ('categoria', None), 'Cable length': ('comprimento_m', 'm')},
    'adaptador_wifi': {'Host interface': ('interface', None), 'Wi-Fi standards': ('padrao_wifi', None),
                       'Maximum data transfer rate': ('velocidade_mbps', 'mbps')},
}


def converter(valor, tipo):
    if tipo is None:
        return valor.strip() or None
    texto = nome(valor)
    if tipo in ('bool', 'nvme'):
        if texto in ('y', 'yes', 'true'):
            return 'NVMe' if tipo == 'nvme' else True
        return False if tipo == 'bool' and texto in ('n', 'no', 'false') else None
    if tipo == 'switch':
        return True if texto == 'mechanical' else False if texto == 'membrane' else None
    if tipo == 'microfone':
        return False if texto == 'not available' else True if texto in ('boom', 'built-in', 'in-line') else None
    if tipo == 'lista':
        return ', '.join(v.strip() for v in valor.split(',') if v.strip())
    if tipo == 'modulos':
        m = re.fullmatch(r'(\d+)\s*x\s*\d+(?:\.\d+)?\s*(?:gb|mb)?', texto)
        return int(m[1]) if m else None
    if tipo == 'inch':
        m = re.fullmatch(r'(\d+(?:\.\d+)?)\s*(?:inch|"|in)', texto)
        return float(m[1]) if m else None
    texto = texto.replace('mb/s', 'mbps').replace('mbit/s', 'mbps')
    n = numero(texto, None if tipo == 'int' else tipo)
    if n is None and tipo == 'ghz':
        n = numero(texto, 'mhz')
        if n is not None:
            n /= 1000
    if n is None or n <= 0:
        return None
    if tipo in ('int', 'gb', 'mhz', 'rpm', 'mbps', 'mb', 'dpi', 'hz'):
        return int(n) if n == int(n) else None
    return float(n)


class NormalizarFichaIcecatService:
    def executar(self, corpo, referencia, categoria):
        if len(corpo) > 2_000_000:
            raise ValueError('Ficha Icecat excede 2 MB')
        try:
            raiz = fromstring(corpo)
        except (DefusedXmlException, ParseError):
            raise ValueError('XML Icecat inválido ou inseguro') from None
        produto = raiz.find('Product')
        if produto is None or produto.get('ID') != referencia['id']:
            raise ValueError('Ficha Icecat diverge do ID consultado')
        cat = produto.find('Category')
        cat_nome = cat.find('Name') if cat is not None else None
        if cat is None or cat.get('ID') != referencia['categoria'] or cat_nome is None or nome(cat_nome.get('Value')) not in CATEGORIAS.get(categoria, set()):
            raise ValueError('Categoria Icecat incompatível com o anúncio')
        fornecedor = produto.find('Supplier')
        fabricante = fornecedor.get('Name') if fornecedor is not None else None
        modelo = produto.get('Name')
        mpn = produto.get('Prod_id')
        if not fabricante or not modelo or not mpn:
            raise ValueError('Ficha Icecat sem identidade suficiente')
        url = f"https://data.icecat.biz/export/freexml/EN/{referencia['id']}.xml"
        sha = hashlib.sha256(corpo).hexdigest()
        dados = dict(fabricante=fabricante, modelo=modelo)
        fontes = {c:dict(url=url, base='Icecat', sha256=sha, atualizado_na_origem=referencia['atualizado'])
                  for c in ('fabricante', 'modelo', 'mpn')}
        conflitos = []
        for atributo in produto.findall('ProductFeature'):
            rotulo = atributo.find('./Feature/Name')
            if rotulo is None:
                continue
            mapeamento = CAMPOS.get(categoria, {}).get(rotulo.get('Value'))
            if mapeamento is None:
                continue
            campo, tipo = mapeamento
            apresentado = atributo.get('Presentation_Value', '')
            if categoria == 'memoria_ram' and campo == 'capacidade_gb' and re.fullmatch(r'\d+ MB', apresentado):
                mb = int(apresentado.split()[0])
                valor = mb // 1024 if mb > 0 and mb % 1024 == 0 else None
            else:
                valor = converter(apresentado, tipo)
            if valor is None:
                continue
            if campo in dados and dados[campo] != valor:
                conflitos.append('icecat_campo_contraditorio:' + campo)
                continue
            dados[campo] = valor
            fontes[campo] = dict(url=url, base='Icecat', sha256=sha, atributo=rotulo.get('Value'),
                                 feature_id=atributo.get('Feature_ID'), atualizado_na_origem=referencia['atualizado'])
        if categoria == 'ssd' and 'tipo' not in dados and 'sata' in nome(dados.get('interface')):
            dados['tipo'] = 'SATA'
            fontes['tipo'] = fontes['interface']
        # As categorias de refrigeração compartilham taxonomia: requerem validação
        # adicional para separar ventoinha, air cooler e water cooler.
        if categoria in ('fan', 'air_cooler', 'water_cooler'):
            conflitos.append('icecat_subtipo_refrigeracao_nao_confirmado')
        eans = {gtin(e.get('EAN')) for e in produto.findall('EANCode') if e.get('IsApproved')=='1' and gtin(e.get('EAN'))}
        return dict(dados=dados, fontes=fontes, conflitos=conflitos,
                    identidade={'mpn':mpn, 'gtin':next(iter(eans)) if len(eans)==1 else None},
                    gtins=sorted(eans), fonte_identidade=url, referencia_icecat=referencia['id'])
