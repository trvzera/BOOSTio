"""Lê apenas informações explícitas de uma ficha original da KaBuM."""
import re
from html.parser import HTMLParser
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.normalizar_produto import nome
from services.catalogo_service.conferir_especificacoes_service import extrair_titulo, converter


class _TextoFicha(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes = []
        self.ignorar = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.ignorar += 1
        if not self.ignorar and tag in ('br', 'p', 'li', 'div', 'tr', 'td'):
            self.partes.append('\n')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.ignorar = max(0, self.ignorar - 1)
        if not self.ignorar and tag in ('p', 'li', 'div', 'tr', 'td'):
            self.partes.append('\n')

    def handle_data(self, data):
        if not self.ignorar:
            self.partes.append(data)

    def linhas(self):
        return [s for p in ''.join(self.partes).splitlines()
                if (s := p.strip().lstrip('-•· ').strip())]


class NormalizarFichaKabumService:
    @staticmethod
    def _separar_memoria_gpu(specs):
        capacidades=[];tipos=list(specs.get('tipo_memoria', []))
        for valor in specs.get('memoria_gb', []):
            texto=nome(str(valor))
            tipos.extend(re.findall(r'\b(?:gddr\s*[567]x?|ddr\s*[345])\b',texto))
            ambiguo = (re.search(r'\bate\b|\bup to\b|compartilh|\b\d+\s*mb\b',texto)
                or re.search(r'\d+\s*(?:-|a)\s*\d+\s*gb',texto)
                or re.search(r'(?<!\w)[+-]\s*\d',texto)
                    and not re.fullmatch(r'gddr\s*[567]x?\s*-\s*\d+\s*gb',texto))
            if converter('memoria_gb',valor) is not None:
                capacidades.append(valor)
            elif not ambiguo:
                capacidades.extend(extrair_titulo('placa_video',texto).get('memoria_gb') or [valor])
            else:
                capacidades.append(valor)
        if capacidades:specs['memoria_gb']=sorted(set(capacidades))
        if tipos:specs['tipo_memoria']=sorted(set(tipos))

    CATEGORIAS = {
        'processador': r'processador', 'placa_mae': r'placas?[ -]?mae',
        'placa_video': r'placa de video', 'memoria_ram': r'memoria ram',
        'ssd': r'\bssd\b', 'hd': r'\bhd\b|disco rigido', 'fonte': r'fontes?',
        'mouse': r'\bmouse', 'monitor': r'monitores?', 'teclado': r'teclados?',
        'fone': r'headsets?|fones?', 'gabinete': r'gabinetes?',
        'air_cooler': r'air cooler', 'water_cooler': r'water cooler',
        'fan': r'/fan\b|ventoinha', 'adaptador_wifi': r'adaptador.*(?:wireless|wi.?fi)|placa de rede',
        'cabo_rede': r'cabo.*rede',
    }
    ROTULOS = {
        'capacidade_gb': {'capacidade', 'capacidades', 'capacidade total', 'armazenamento'},
        'frequencia_mhz': {'velocidade', 'velocidades', 'frequencia', 'frequencia de memoria'},
        'latencia': {'latencia', 'latencias', 'latencia cas'},
        'formato_ram': {'formato de memoria', 'tipo de modulo', 'formato'},
        'quantidade_pentes': {'quantidade de modulos', 'numero de modulos', 'modulos'},
        'conexao': {'conexao', 'conectividade', 'interface de conexao', 'conectores'},
        'dpi_max': {'dpi', 'dpi maximo', 'resolucao', 'resolucao do sensor'},
        'potencia_w': {'potencia', 'potencia nominal', 'potencia de saida'},
        'formato': {'fator de forma', 'formato', 'formato da fonte'},
        'interface': {'interface', 'interface de armazenamento'},
        'velocidade_rpm': {'velocidade de rotacao', 'rotacao', 'rpm'},
        'memoria_cache_mb': {'cache', 'memoria cache', 'tamanho do cache'},
        'compatibilidade': {'compatibilidade', 'soquetes suportados', 'soquetes', 'socket', 'suporte de soquete'},
        'formatos_placa_mae': {'placas mae suportadas', 'suporte a placa mae', 'placa mae', 'placas mae', 'compatibilidade de placa mae'},
        'tamanho_radiador_mm': {'tamanho do radiador', 'tamanho radiador'},
        'iluminacao': {'iluminacao', 'led', 'rgb'}, 'layout': {'layout', 'padrao do teclado'},
        'switch': {'switch', 'switches', 'tipo de switch'},
        'tipo_painel': {'painel', 'tipo de painel', 'tecnologia do painel'},
        'taxa_atualizacao_hz': {'taxa de atualizacao', 'frequencia de atualizacao'},
        'resolucao': {'resolucao maxima', 'resolucao nativa'},
        'tamanho_polegadas': {'tamanho da tela', 'tamanho em polegadas', 'polegadas'},
        'tipo_fone': {'tipo de fone', 'tipo de fone de ouvido'},
        'microfone': {'microfone', 'microfone integrado', 'com microfone', 'possui microfone'},
        'nucleo': {'nucleos', 'numero de nucleos', 'quantidade de nucleos'},
        'thread': {'threads', 'numero de threads'},
        'socket': {'soquete', 'socket', 'soquete de cpu'},
    }

    def executar(self, dados, categoria, *, codigo_esperado):
        if not isinstance(dados, dict) or str(dados.get('id')) != str(codigo_esperado) or not re.fullmatch(r'[1-9]\d*', str(codigo_esperado)):
            raise ValueError('Ficha não corresponde ao ID original da oferta')
        titulo = dados.get('title')
        fabricante = dados.get('manufacturer')
        if not isinstance(titulo, str) or not titulo.strip() or len(titulo) > 1000:
            raise ValueError('Título ausente ou inválido')
        if not isinstance(fabricante, dict) or not isinstance(fabricante.get('name'), str):
            raise ValueError('Fabricante não comprovado')
        categoria_fonte = nome(str(dados.get('category', '')))
        confirmado = categoria in self.CATEGORIAS and bool(re.search(self.CATEGORIAS[categoria], categoria_fonte))
        html = (dados.get('technicalInformation') or {}).get('text', '')
        if not isinstance(html, str) or len(html.encode()) > 2_000_000:
            raise ValueError('Ficha técnica inválida ou excessiva')
        parser = _TextoFicha(); parser.feed(html)
        linhas = parser.linhas()
        pares = {}
        rotulos_categoria = {
            'memoria_gb': {'memoria', 'memoria de video', 'tamanho da memoria', 'capacidade de memoria', 'quantidade de memoria'},
            'tipo_memoria': {'tipo de memoria', 'tipo memoria', 'tipo da memoria'},
        } if categoria == 'placa_video' else {}
        rotulos_validos = {'modelo', 'part number', 'mpn', 'tipo de conexao', 'conexoes'}
        rotulos_validos.update(set().union(*self.ROTULOS.values(), *rotulos_categoria.values()))
        for i, linha in enumerate(linhas):
            rotulo, sep, valor = linha.partition(':')
            chave = nome(rotulo).strip().rstrip('*')
            if not sep and chave not in rotulos_validos:
                continue
            if not valor.strip() and i + 1 < len(linhas) and ':' not in linhas[i + 1]:
                valor = linhas[i + 1]
            if valor.strip():
                pares.setdefault(chave, []).append(valor.strip())
        specs = extrair_titulo(categoria, titulo)
        for campo, aliases in {**self.ROTULOS, **rotulos_categoria}.items():
            encontrados = [v for k, vs in pares.items() if k in aliases for v in vs]
            if encontrados:
                anteriores = specs.get(campo, []) if campo in rotulos_categoria else []
                specs[campo] = sorted(set([*anteriores, *encontrados]))
        if categoria == 'monitor' and pares.get('resolucao'):
            specs['resolucao'] = pares['resolucao']
        if categoria == 'placa_video':
            self._separar_memoria_gpu(specs)
        if categoria == 'processador' and specs.get('socket'):
            specs['soquete'] = specs.pop('socket')
        if categoria in ('fone', 'mouse', 'teclado'):
            declaracoes = [*pares.get('tipo de conexao', []), *pares.get('conexoes', [])]
            if declaracoes:
                specs['conexao'] = [*specs.get('conexao', []), *declaracoes]
            if re.search(r'\bcom fio\b|\bc/fio\b', nome(titulo)):
                specs.setdefault('conexao', []).append('wired')
            if re.search(r'\bsem fio\b|\bwireless\b', nome(titulo)):
                specs.setdefault('conexao', []).append('wireless')
        if categoria == 'fone':
            if specs.get('tipo_fone'):
                specs['formato_fone'] = list(specs['tipo_fone'])
            if re.search(r'\bheadset\b', nome(titulo)):
                specs['tipo_fone'] = ['headset']
            for k in ('tipo de microfone', 'tipo do microfone', 'padrao polar do microfone',
                      'padrao de captacao do microfone', 'dimensoes do microfone', 'sensibilidade do microfone'):
                if pares.get(k) and any(nome(v) not in ('nao', 'sem', 'n/a', 'nao possui') for v in pares[k]):
                    specs.setdefault('microfone', []).append(True)
        if categoria == 'teclado':
            layouts = sorted(set(re.findall(r'\b(?:abnt\s*2|ansi|iso)\b', nome(titulo))))
            if layouts:
                specs['layout'] = layouts
            texto_titulo = nome(titulo)
            if not re.search(r'\bsemi[ -]?mecanico\b', texto_titulo) and re.search(r'\bmecanico\b', texto_titulo):
                specs['mecanico'] = [True]
            elif re.search(r'\bmembrana\b', texto_titulo):
                specs['mecanico'] = [False]
        texto = nome('\n'.join(linhas))
        if categoria == 'memoria_ram':
            formatos = set(re.findall(r'\b(?:u[ -]?dimm|so[ -]?dimm|lr[ -]?dimm|r[ -]?dimm|dimm)\b', texto))
            if formatos:
                specs['formato_ram'] = sorted(formatos)
            ddrs = set(re.findall(r'\bddr\s*[345]\b', texto))
            if ddrs:
                specs['ddr'] = sorted(ddrs)
        if categoria in ('air_cooler', 'water_cooler'):
            linhas_socket = [s for s in linhas if re.search(r'\b(?:lga\s*\d{3,5}|am[2345])\b', nome(s))]
            if linhas_socket:
                specs['compatibilidade'] = linhas_socket
        luz = specs.get('iluminacao')
        if luz:
            specs['iluminacao'] = [True if re.fullmatch(r'(?:a?rgb|led(?:s)?)', nome(v)) else v for v in luz]
        modelos = sorted(set(pares.get('modelo', [])))
        codigo_titulo = titulo.rsplit(' - ', 1)[-1].strip() if ' - ' in titulo else ''
        codigos_titulo = [codigo_titulo] if re.fullmatch(r'(?=.*\d)(?=.*[a-zA-Z])[a-zA-Z0-9]+(?:[-./][a-zA-Z0-9]+)*|\d{3}-\d{6,12}', codigo_titulo) else []
        mpns = sorted(set(pares.get('mpn', []) + pares.get('part number', [])))
        return ProdutoNormalizado(loja='kabum', id_externo=str(codigo_esperado), categoria=categoria,
            titulo=titulo, marca=fabricante['name'], modelo=modelos[0] if len(modelos) == 1 else None,
            modelos_alternativos=tuple(sorted(set(modelos + codigos_titulo))), especificacoes=specs, identificadores={'mpn': mpns},
            ativo=True, categoria_confirmada=confirmado,
            fonte=f'https://www.kabum.com.br/produto/{codigo_esperado}',
            contexto={'finalidade': 'especificacoes', 'rotulos_originais': pares, 'codigos_titulo': codigos_titulo})
