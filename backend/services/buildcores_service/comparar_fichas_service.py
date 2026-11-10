"""Correspondência exata por modelo com verificação independente das variantes."""
import re
from decimal import Decimal, InvalidOperation
from services.catalogo_service.normalizar_produto import nome, codigo
from services.catalogo_service.comparar_nomes_service import cpu
from services.catalogo_service.conferir_especificacoes_service import converter
from .normalizar_ficha_service import fabricante, cores


def chave_modelo(categoria,texto,marca,cor=()):
    s=nome(texto)
    if categoria=='processador':
        c=cpu(s)
        if c:return repr(c)
    for b in sorted({marca, 'hp hyperx' if marca=='hyperx' else marca},key=len,reverse=True):
        s=re.sub(r'(?<!\w)'+re.escape(b)+r'(?!\w)',' ',s)
    for c in cor:
        s=re.sub(r'(?<!\w)'+re.escape(c)+r'(?!\w)',' ',s)
    s=re.sub(r'\b\d+\s*[x×]\s*\d+\s*gb\b',' ',s)
    s=re.sub(r'\b\d+(?:[.,]\d+)?\s*(?:ghz|mhz|hz|gb|tb|w|mm|inch(?:es)?)\b',' ',s)
    s=re.sub(r'\b\d+\s*[- ]?cores?\b|\b\d+\s*[x×]\s*\d+\b',' ',s)
    if categoria=='memoria_ram':
        s=re.sub(r'\bddr\s*[1-5](?:-\d+)?\b|\bcl\s*\d+\b|\b(?:288|260|240|204)-pin\b|\b(?:so-?)?dimm\b',' ',s)
    s=re.sub(r'\b(?:motherboard|processor|graphics card|video card|memory|kit|internal|desktop)\b',' ',s)
    return '|'.join(sorted(re.findall(r'[a-z0-9]+',s)))


def equivalente(cat,campo,a,b):
    if a is None or b is None:return None
    if type(a) is bool or type(b) is bool:return type(a) is type(b) and a==b
    if isinstance(a,(int,float,Decimal)) and isinstance(b,(int,float,Decimal)):
        try:return Decimal(str(a))==Decimal(str(b))
        except InvalidOperation:return False
    if isinstance(a,str) and isinstance(b,str) and nome(a)==nome(b):return True
    chave='formato_ram' if cat=='memoria_ram' and campo=='formato' else campo
    x,y=converter(chave,a),converter(chave,b)
    return x is not None and y is not None and x==y


class CompararFichasBuildcoresService:
    def chave_local(self,p):
        origem=p['fontes'].get('_pc_part_dataset',{})
        raw=origem.get('dados_originais',{})
        titulo=origem.get('nome_original') or p['dados']['modelo']
        return chave_modelo(p['categoria'],titulo,fabricante(p['dados']['fabricante']),cores(raw.get('color')))

    def chave_remota(self,r):
        return chave_modelo(r['categoria'],r['nome'],r['fabricante'],r['cores'])

    def avaliar(self,p,r):
        cat=p['categoria'];local=p['dados'];raw=p['fontes'].get('_pc_part_dataset',{}).get('dados_originais',{})
        conflitos=[];ausentes=[];conferidos=[]
        if fabricante(local['fabricante'])!=r['fabricante']:conflitos.append('fabricante_divergente')
        if self.chave_local(p)!=self.chave_remota(r):conflitos.append('modelo_divergente')
        lc=cores(raw.get('color'))
        if lc and lc!=r['cores']:ausentes.append('cor_nao_comprovada')
        for campo,v in r['dados'].items():
            atual=local.get(campo)
            if atual is None:continue
            if equivalente(cat,campo,atual,v) is False:conflitos.append('campo_divergente:'+campo)
            elif equivalente(cat,campo,atual,v) is True:conferidos.append(campo)
        pares={'placa_video':{'core_clock':'core_base_clock','boost_clock':'core_boost_clock','length':'length'},
          'fonte':{'modular':'modular'},'fan':{'pwm':'pwm'}}.get(cat,{})
        for a,b in pares.items():
            if raw.get(a) is not None:
                if r['bruto'].get(b) is None:ausentes.append('especificacao_nao_comprovada:'+a)
                elif equivalente(cat,a,raw[a],r['bruto'][b]) is False:conflitos.append('variante_divergente:'+a)
        requisitos={'processador':('nucleo','clockbase','clockmax'),
          'placa_video':('memoria_gb',),'memoria_ram':('capacidade_gb','ddr','frequencia_mhz','quantidade_pentes','latencia'),
          'placa_mae':('socket','formato'),'ssd':('capacidade_gb','interface'),'hd':('capacidade_gb','interface'),
          'fonte':('potencia_w',),'monitor':('tamanho_polegadas','resolucao','taxa_atualizacao_hz'),
          'mouse':('dpi_max',),'fan':('tamanho_mm',),'gabinete':('formato',),
          'water_cooler':('tamanho_radiador_mm',)}.get(cat,())
        if not requisitos:ausentes.append('criterio_categoria_nao_homologado')
        ausentes.extend('especificacao_identidade:'+k for k in requisitos if k not in conferidos)
        if local.get('part_number') and r['mpns'] and codigo(local['part_number']) not in {codigo(v) for v in r['mpns']}:conflitos.append('mpn_divergente')
        return dict(confirmada=not conflitos and not ausentes,conflitos=sorted(set(conflitos)),pendencias=sorted(set(ausentes)),conferidos=conferidos)
