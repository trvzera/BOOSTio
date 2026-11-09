"""Adapta campos efetivamente presentes no snapshot OpenDB, sem valores presumidos."""
import re
from decimal import Decimal, InvalidOperation
from services.catalogo_service.comparar_nomes_service import marca
from services.catalogo_service.normalizar_produto import nome, gtin

CATEGORIAS={'CPU':'processador','GPU':'placa_video','Motherboard':'placa_mae','RAM':'memoria_ram',
 'PCCase':'gabinete','PSU':'fonte','Monitor':'monitor','Mouse':'mouse','Keyboard':'teclado',
 'Headphones':'fone','CaseFan':'fan','NetworkCard':'adaptador_wifi'}


def numero(v):
    if type(v) not in (int,float,Decimal):return None
    try:
        n=Decimal(str(v))
        return float(n) if n.is_finite() and n>0 else None
    except InvalidOperation:return None


def fabricante(v):
    s=marca(v or '')
    return {'hp hyperx':'hyperx','teamgroup':'teamgroup','team group':'teamgroup','be quiet!':'be quiet'}.get(s,s)


def cores(v):
    if not v:return ()
    if isinstance(v,str):v=v.split('/')
    aliases={'grey':'gray','cinza':'gray','preto':'black','branco':'white','vermelho':'red','azul':'blue','prata':'silver'}
    return tuple(sorted({aliases.get(nome(s),nome(s)) for s in v if isinstance(s,str) and s.strip()}))


class NormalizarFichaBuildcoresService:
    def executar(self, grupo, bruto, origem):
        meta=bruto.get('metadata') or {}
        if not isinstance(meta,dict) or not isinstance(meta.get('name'),str) or not isinstance(meta.get('manufacturer'),str):raise ValueError('Identidade ausente')
        cat=CATEGORIAS.get(grupo)
        if grupo=='NetworkCard' and not re.search(r'\b(?:wi[ -]?fi|wireless|802\.11)',meta['name'],re.I):
            raise ValueError('Placa de rede não comprovada como adaptador Wi-Fi')
        if grupo=='Storage':cat={'SSD':'ssd','HDD':'hd'}.get(bruto.get('storage_type',bruto.get('type')))
        if grupo=='CPUCooler' and type(bruto.get('water_cooled')) is bool:cat='water_cooler' if bruto['water_cooled'] else 'air_cooler'
        if not cat:raise ValueError('Categoria não comprovada')
        dados={};caminhos={}
        def ler(path):
            valor=bruto
            for k in path.split('.'):
                if not isinstance(valor,dict):return None
                valor=valor.get(k)
            return valor
        def campo(destino,path,tipo='texto'):
            v=ler(path)
            if tipo=='numero':v=numero(v)
            elif tipo=='bool':v=v if type(v) is bool else None
            else:v=v.strip() if isinstance(v,str) and v.strip() and nome(v) not in ('unknown','n/a','undefined') else None
            if v is not None:dados[destino]=v;caminhos[destino]=path
        mapa={
          'processador':{'soquete':'socket','nucleo':'cores.total','thread':'cores.threads','clockbase':'clocks.performance.base','clockmax':'clocks.performance.boost','consumo_energia':'specifications.tdp','cooler':'specifications.includesCooler'},
          'placa_video':{'memoria_gb':'memory','tipo_memoria':'memory_type','consumo_energia':'tdp','fabricante_chip':'chipset_manufacturer','modelo_referencia':'chipset'},
          'placa_mae':{'socket':'socket','formato':'form_factor','tipo_memoria':'memory.ram_type','memoria_maxima_gb':'memory.max','quantidade_slots_ram':'memory.slots','chipset':'chipset'},
          'memoria_ram':{'capacidade_gb':'capacity','quantidade_pentes':'modules.quantity','ddr':'ram_type','frequencia_mhz':'speed','latencia':'cas_latency'},
          'ssd':{'capacidade_gb':'capacity','interface':'interface','formato':'form_factor'},
          'hd':{'capacidade_gb':'capacity','interface':'interface','velocidade_rpm':'rpm','memoria_cache_mb':'cache'},
          'water_cooler':{'tamanho_radiador_mm':'radiator_size','quantidade_fans':'fan_quantity'},
          'air_cooler':{'dimensoes':'height'},
          'fan':{'tamanho_mm':'size','quantidade':'quantity'},
          'gabinete':{'formato':'form_factor','slots_expansao':'expansion_slots','tamanho_max_gpu_mm':'max_video_card_length','tamanho_max_cooler_mm':'max_cpu_cooler_height'},
          'fonte':{'potencia_w':'wattage','formato':'form_factor'},
          'monitor':{'tamanho_polegadas':'screen_size','taxa_atualizacao_hz':'refresh_rate','tipo_painel':'panel_type','tempo_resposta_ms':'response_time','conexao':'connectors'},
          'mouse':{'dpi_max':'max_dpi','sensor':'sensor','botoes':'buttons'},'teclado':{'layout':'layout','switch':'switch'},'fone':{'microfone':'has_microphone','tipo':'ear_cup_type'},'adaptador_wifi':{},
        }
        numericos={'nucleo','thread','clockbase','clockmax','consumo_energia','memoria_gb','memoria_maxima_gb','quantidade_slots_ram','capacidade_gb','quantidade_pentes','frequencia_mhz','latencia','velocidade_rpm','memoria_cache_mb','tamanho_radiador_mm','quantidade_fans','dimensoes','tamanho_mm','quantidade','slots_expansao','tamanho_max_gpu_mm','tamanho_max_cooler_mm','potencia_w','tamanho_polegadas','taxa_atualizacao_hz','tempo_resposta_ms','dpi_max','botoes'}
        for destino,path in mapa.get(cat,{}).items():campo(destino,path,'bool' if destino in ('cooler','microfone') else 'numero' if destino in numericos else 'texto')
        caminho_conexao={'mouse':'connectivity','teclado':'connectivity','fone':'connection_types'}.get(cat)
        if caminho_conexao:
            v=bruto.get(caminho_conexao)
            if isinstance(v,list) and v and all(isinstance(s,str) and s.strip() for s in v):
                dados['conexao']='; '.join(v);caminhos['conexao']=caminho_conexao
        if cat=='teclado' and nome(str(bruto.get('switch_type','')))=='membrane':
            dados['mecanico']=False;caminhos['mecanico']='switch_type'
        if cat=='processador':
            g=ler('specifications.integratedGraphics.model')
            if isinstance(g,str) and g.strip():
                dados['videointegrado']=nome(g) not in ('none','no','n/a')
                caminhos['videointegrado']='specifications.integratedGraphics.model'
                if dados['videointegrado']:dados['modelo_videointegrado']=g;caminhos['modelo_videointegrado']=caminhos['videointegrado']
        if cat=='memoria_ram':
            formato=bruto.get('form_factor')
            if isinstance(formato,str):
                m=re.search(r'(?<![a-z])(?:(?:so[- ]?|u|r|lr)?dimm)(?![a-z])',nome(formato))
                if m:dados['formato']=m[0].upper().replace(' ','-');caminhos['formato']='form_factor'
            if 'latencia' in dados:dados['latencia']=str(int(dados['latencia'])) if dados['latencia'].is_integer() else str(dados['latencia'])
        if cat in ('water_cooler','air_cooler') and isinstance(bruto.get('cpu_sockets'),list) and bruto['cpu_sockets']:
            dados['compatibilidade']=', '.join(str(v) for v in bruto['cpu_sockets']);caminhos['compatibilidade']='cpu_sockets'
        if cat=='ssd':
            if bruto.get('nvme') is True:dados['tipo']='NVMe';caminhos['tipo']='nvme'
            elif re.search(r'\bsata\b',str(bruto.get('interface','')),re.I):dados['tipo']='SATA';caminhos['tipo']='interface'
        if cat=='monitor':
            r=bruto.get('resolution') or {}
            if isinstance(r,dict) and numero(r.get('horizontalRes')) and numero(r.get('verticalRes')):
                dados['resolucao']=f"{r['horizontalRes']}x{r['verticalRes']}";caminhos['resolucao']='resolution'
        if cat=='gabinete' and isinstance(bruto.get('supported_motherboard_form_factors'),list) and bruto['supported_motherboard_form_factors']:
            dados['formatos_placa_mae']=', '.join(bruto['supported_motherboard_form_factors']);caminhos['formatos_placa_mae']='supported_motherboard_form_factors'
        # Nenhuma iluminação é inferida da ausência ou de uma lista vazia.
        if isinstance(bruto.get('lighting'),list) and bruto['lighting']:
            dados['iluminacao']=True;caminhos['iluminacao']='lighting'
        from services.peca_service.modelos_pecas import MODELOS_PECAS
        from sqlalchemy import Integer,String,Boolean
        modelo=next(m for m in MODELOS_PECAS if m.__tablename__==cat)
        for k,v in list(dados.items()):
            if k not in modelo.__table__.c:del dados[k];continue
            tipo=modelo.__table__.c[k].type
            if isinstance(tipo,Integer):
                if v!=int(v):del dados[k]
                else:dados[k]=int(v)
            elif isinstance(tipo,String):
                if not isinstance(v,str) or tipo.length and len(v)>tipo.length:del dados[k]
        ids=(bruto.get('identifiers') or {}).get('identifiers') or []
        mpns=set();gtins=set()
        for id in ids:
            if not isinstance(id,dict):continue
            valor=id.get('value')
            if id.get('type')=='mpn' and isinstance(valor,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9./_-]{2,99}',valor) and re.search('[0-9]',valor):mpns.add(valor)
            if id.get('type') in ('ean','gtin','upc') and gtin(valor):gtins.add(gtin(valor))
        # metadata.part_numbers não é identificador canônico e pode conter nomes.
        return dict(categoria=cat,fabricante=fabricante(meta['manufacturer']),nome=meta['name'],dados=dados,
          mpns=sorted(mpns),gtins=sorted(gtins),cores=cores(bruto.get('color') or meta.get('manufacturer_color')),
          bruto=bruto,origem=origem,fontes={k:{**origem,'campo':caminhos[k]} for k in dados})
