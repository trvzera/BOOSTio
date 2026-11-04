import re
from decimal import Decimal
from .normalizar_produto import nome, numero
from utils.sockets import normalizar_socket
from .normalizar_especificacoes import converter_adicional, agregar, CONJUNTOS

ESSENCIAIS={
 'processador':('soquete','nucleo','thread'),
 'placa_video':('memoria_gb','tipo_memoria'),
 'memoria_ram':('capacidade_gb','ddr','frequencia_mhz','quantidade_pentes','latencia','formato_ram'),
 'placa_mae':('socket','tipo_memoria','formato'),
 'ssd':('capacidade_gb','tipo','interface'),
 'hd':('capacidade_gb','interface','velocidade_rpm'),
 'fonte':('potencia_w','formato'),
 'mouse':('dpi_max','conexao'),
 'monitor':('tamanho_polegadas','resolucao','taxa_atualizacao_hz','tipo_painel','conexao'),
 'fone':('tipo_fone','microfone','conexao'),
 'teclado':('layout','mecanico','conexao'),
 'fan':('tamanho_mm','quantidade','iluminacao'),
 'gabinete':('formatos_placa_mae',),
 'air_cooler':('compatibilidade','iluminacao'),
 'water_cooler':('compatibilidade','tamanho_radiador_mm','iluminacao'),
 'adaptador_wifi':('interface','padrao_wifi','velocidade_mbps','bluetooth'),
 'cabo_rede':('categoria_cabo','comprimento_m','conector'),
}
OPCIONAIS={
 'memoria_ram':('iluminacao',),
 'placa_mae':('chipset',), 'ssd':('formato',), 'hd':('memoria_cache_mb',),
 'gabinete':('tamanho_max_gpu_mm','tamanho_max_cooler_mm'),
 'teclado':('switch',),
}


def valores(valor):
    return valor if isinstance(valor,(list,tuple,set)) else [] if valor is None else [valor]


def converter(campo, valor):
    if valor is None:return None
    adicional = converter_adicional(campo, valor)
    if adicional is not NotImplemented:
        return adicional
    s=nome(str(valor))
    if campo in ('soquete','socket'):return normalizar_socket(s)
    if campo in ('ddr','tipo_memoria'):
        m=re.fullmatch(r'((?:g)?ddr)\s*([34567])(?:\s*(x|sdram))?',s)
        return m[1]+m[2]+('x' if m[3]=='x' else '') if m else None
    if campo in ('capacidade_gb','memoria_gb'):return numero(s,'gb')
    if campo in ('frequencia_mhz','clockbase','clockmax'):
        n=numero(s,'mhz')
        if n is None:
            n=numero(s,'ghz')
            if n is not None:n*=1000
        if n is None:return None
        # Campos de clock de CPU são armazenados em GHz no projeto.
        if campo in ('clockbase','clockmax'):
            return n/1000 if re.search(r'(?:ghz|mhz)',s) else numero(s)
        return n
    if campo=='latencia':
        m=re.fullmatch(r'(?:cl\s*)?(\d+)',s);return int(m[1]) if m else None
    if campo=='quantidade_pentes':
        m=re.fullmatch(r'(\d+)\s*[x×]\s*\d+\s*gb',s)
        return int(m[1]) if m else numero(s)
    if campo in ('nucleo','thread'):return numero(s)
    if campo in ('potencia_w','velocidade_rpm','dpi_max','memoria_cache_mb'):
        return numero(s,{'potencia_w':'w','velocidade_rpm':'rpm','dpi_max':'dpi','memoria_cache_mb':'mb'}[campo])
    if campo=='iluminacao':
        if type(valor) is bool:return valor
        return True if s in ('sim','yes','true','1') else False if s in ('nao','não','no','false','0') else None
    if campo=='tipo':
        return 'nvme' if 'nvme' in s else 'sata' if 'sata' in s else None
    if campo=='interface':
        s=s.replace('pci express','pcie').replace('pci-e','pcie')
        s=re.sub(r'\bsata\s*(iii|3)(?:\.0)?\b','sata3',s)
        return re.sub(r'[^a-z0-9./+]','',s) if s else None
    if campo=='formato_ram':
        s=s.replace('-','').replace(' ','')
        return {'udimm':'dimm'}.get(s,s) if s in ('dimm','udimm','sodimm','rdimm','lrdimm') else None
    if campo=='formato':
        s=s.replace('\"','').replace('″','').strip()
        return {'microatx':'matx','micro-atx':'matx','mini-itx':'itx','miniitx':'itx'}.get(s.replace(' ',''),s.replace(' ',''))
    return re.sub(r'\s+','',s) or None


def extrair_titulo(categoria,titulo):
    texto=nome(titulo);dados={}
    def unico(campo, padrao, montar=lambda m:m[0]):
        achados={montar(m) for m in re.findall(padrao,texto)}
        if achados:dados[campo]=sorted(achados)
    if categoria in ('memoria_ram','placa_video','ssd','hd'):
        kit=re.search(r'\b(\d+)\s*[x×]\s*(\d+)\s*gb',texto)
        if categoria=='memoria_ram' and kit:
            dados['quantidade_pentes']=[kit[1]];dados['capacidade_gb']=[str(int(kit[1])*int(kit[2]))+' gb']
        else:unico('memoria_gb' if categoria=='placa_video' else 'capacidade_gb',r'\b(\d+(?:[.,]\d+)?)\s*(gb|tb)\b',lambda m:''.join(m))
    if categoria=='memoria_ram':
        unico('formato_ram',r'\b(so[ -]?dimm|dimm)\b',lambda m:m)
        unico('ddr',r'\b(ddr\s*[345])\b',lambda m:m)
        unico('frequencia_mhz',r'\b(\d+)\s*(mhz)\b',lambda m:''.join(m))
        unico('latencia',r'\b(cl\s*\d+)\b',lambda m:m)
    if categoria in ('processador','placa_mae'):
        unico('soquete' if categoria=='processador' else 'socket',r'\b(am[45]|(?:fc)?lga[ -]?\d{3,5})\b',lambda m:m)
    if categoria=='processador':
        unico('nucleo',r'\b(\d+)\s*(?:nucleos?|cores?)\b',lambda m:m)
        unico('thread',r'\b(\d+)\s*threads?\b',lambda m:m)
    if categoria in ('placa_mae','fonte'):
        unico('formato',r'\b(micro[ -]?atx|m[ -]?atx|atx|mini[ -]?itx|itx)\b',lambda m:m)
    if categoria=='placa_mae':unico('tipo_memoria',r'\b(ddr\s*[345])\b',lambda m:m)
    if categoria=='placa_video':unico('tipo_memoria',r'\b(gddr\s*[567]x?)\b',lambda m:m)
    if categoria=='ssd':
        unico('tipo',r'\b(nvme|sata)\b',lambda m:m)
    if categoria=='fonte':unico('potencia_w',r'\b(\d+)\s*(w)\b',lambda m:''.join(m))
    return dados


class ConferirEspecificacoesService:
    def executar(self, peca, produto):
        campos=ESSENCIAIS.get(peca.__tablename__,())
        if peca.__tablename__ == 'teclado' and getattr(peca, 'mecanico', False) is True:
            campos = (*campos, 'switch')
        dados=dict(produto.especificacoes);titulo=extrair_titulo(peca.__tablename__,produto.titulo)
        conflitos=[];ausentes=[];conferidos=[]
        for campo in dict.fromkeys((*campos,*OPCIONAIS.get(peca.__tablename__,()))):
            valor_local=getattr(peca, {'tipo_fone':'tipo','categoria_cabo':'categoria'}.get(campo,campo),None)
            if campo=='formato_ram':
                valor_local=getattr(peca,'formato',None) or valor_local
                if valor_local is None:
                    t=nome(peca.modelo)
                    valor_local='sodimm' if re.search(r'so.?dimm|notebook|laptop',t) else 'dimm' if re.search(r'\bdimm\b|desktop',t) else None
            local=converter(campo,valor_local)
            bruto=valores(dados.get(campo)) or valores(titulo.get(campo))
            observados={converter(campo,v) for v in bruto}
            if campo in CONJUNTOS:
                agregado = agregar(observados)
                observados = {agregado}
            if not bruto or local is None or None in observados:
                if campo in campos:ausentes.append(campo)
                continue
            if campo in ('compatibilidade', 'conexao') and len(observados) == 1:
                remoto = next(iter(observados))
                if set(local.split('|')) <= set(remoto.split('|')):
                    conferidos.append(campo)
                    continue
                if campo == 'conexao' and ('wireless' in remoto or 'usb' in remoto) and any(
                        v.startswith(('bluetooth', 'usb')) for v in local.split('|')):
                    if campo in campos:ausentes.append(campo)
                    continue
            if campo=='interface' and any(v in ('sata','pcie','nvme') and str(local).startswith(v) for v in observados):
                if campo in campos:ausentes.append(campo)
                continue
            if campo=='interface' and len(observados)==1:
                r=next(iter(observados))
                if str(local).startswith('pcie') and str(r).startswith('pcie') and 'x' not in str(local) and str(r).startswith(str(local)+'x'):
                    conferidos.append(campo);continue
            if campo=='formato' and local=='m.2' and len(observados)==1 and next(iter(observados)).startswith('m.2'):
                conferidos.append(campo);continue
            if observados!={local}:conflitos.append('especificacao_divergente:'+campo)
            else:conferidos.append(campo)
            if campo in titulo:
                ts={converter(campo,v) for v in valores(titulo[campo])}
                if None not in ts and ts!={local}:conflitos.append('titulo_divergente:'+campo)
        return dict(conferidos=conferidos,ausentes=ausentes,conflitos=conflitos,
                    completa=bool(campos) and not ausentes and not conflitos,
                    pontos=round(40*sum(c in conferidos for c in campos)/len(campos),2) if campos else 0)
