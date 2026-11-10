"""Adaptador do JSON docyx; ausências e preços não são inferidos."""
import hashlib
import json
import math
import re

ARQUIVOS = {
    'cpu':'processador', 'motherboard':'placa_mae', 'memory':'memoria_ram',
    'internal-hard-drive':None, 'video-card':'placa_video', 'case':'gabinete',
    'power-supply':'fonte', 'monitor':'monitor', 'headphones':'fone',
    'keyboard':'teclado', 'mouse':'mouse', 'case-fan':'fan',
    'wireless-network-card':'adaptador_wifi', 'cpu-cooler':None,
}
MARCAS_COMPOSTAS = ('Western Digital','Cooler Master','be quiet!','Lian Li','HP HyperX',
    'Fractal Design','Silicon Power','Patriot Viper','Seasonic','PC Power & Cooling',
    'NZXT','Super Flower','Thermal Grizzly','Team Group','Antec','Asus','AMD','Intel')


def assinatura(valor):
    return hashlib.sha256(json.dumps(valor,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()


class NormalizarPecaDatasetService:
    def executar(self, arquivo, linha, origem):
        if arquivo not in ARQUIVOS or not isinstance(linha,dict):raise ValueError('Categoria ou linha inválida')
        titulo=linha.get('name')
        if not isinstance(titulo,str) or not titulo.strip():raise ValueError('Nome ausente')
        titulo=titulo.strip()
        fabricante=next((m for m in sorted(MARCAS_COMPOSTAS,key=len,reverse=True) if titulo.casefold().startswith(m.casefold()+' ')),titulo.split()[0])
        modelo=titulo[len(fabricante):].strip()
        if not modelo:raise ValueError('Nome sem modelo identificável')
        categoria=ARQUIVOS[arquivo]
        if arquivo=='internal-hard-drive':
            tipo=linha.get('type')
            categoria='ssd' if tipo=='SSD' else 'hd' if isinstance(tipo,(int,float)) and not isinstance(tipo,bool) and tipo>0 else None
        if arquivo=='cpu-cooler':
            tamanho=linha.get('size')
            # size é definido pela fonte como tamanho do radiador, não altura do cooler.
            categoria='water_cooler' if isinstance(tamanho,(int,float)) and tamanho>0 else 'air_cooler' if tamanho is None else None
        if categoria is None:raise ValueError('Tipo de componente não comprovado')
        dados={'fabricante':fabricante,'modelo':modelo}
        def por(campo,chave):
            v=linha.get(chave)
            if v is not None:dados[campo]=v
        for campo,chave in {
            'processador':{'nucleo':'core_count','clockbase':'core_clock','clockmax':'boost_clock','consumo_energia':'tdp'},
            'placa_mae':{'socket':'socket','formato':'form_factor','memoria_maxima_gb':'max_memory','quantidade_slots_ram':'memory_slots'},
            'placa_video':{'memoria_gb':'memory','modelo_referencia':'chipset'},
            'ssd':{'capacidade_gb':'capacity','interface':'interface','formato':'form_factor'},
            'hd':{'capacidade_gb':'capacity','interface':'interface','memoria_cache_mb':'cache','velocidade_rpm':'type'},
            'fonte':{'potencia_w':'wattage','formato':'type'},
            'gabinete':{'formato':'type','bays_disco':'internal_35_bays'},
            'mouse':{'dpi_max':'max_dpi','sensor':'tracking_method'},
            'monitor':{'tamanho_polegadas':'screen_size','taxa_atualizacao_hz':'refresh_rate','tipo_painel':'panel_type','tempo_resposta_ms':'response_time'},
            'fone':{'microfone':'microphone'},
            'teclado':{'switch':'switches'},
            'fan':{'tamanho_mm':'size'},
            'water_cooler':{'tamanho_radiador_mm':'size'},
            'adaptador_wifi':{'interface':'interface','padrao_wifi':'protocol'},
        }.get(categoria,{}).items():por(campo,chave)
        if categoria=='processador' and isinstance(linha.get('graphics'),str) and linha['graphics'].strip():
            dados.update(videointegrado=True,modelo_videointegrado=linha['graphics'])
        if categoria=='ssd':
            if type(dados.get('formato')) in (int,float):dados['formato']=str(dados['formato'])
            interface=str(linha.get('interface') or '')
            if 'sata' in interface.casefold():dados['tipo']='SATA'
            elif 'nvme' in interface.casefold():dados['tipo']='NVMe'
            # PCIe não comprova NVMe (existem SSDs PCIe AHCI).
        if categoria in ('ssd','hd'):
            # Muitos nomes da fonte omitem capacidade e interface, que distinguem SKUs.
            dados['modelo']+=' ['+' '.join(str(v) for v in (linha.get('capacity'), 'GB',linha.get('interface')) if v is not None)+']'
        if categoria=='memoria_ram':
            speed=linha.get('speed');modulos=linha.get('modules')
            if isinstance(speed,list) and len(speed)==2:
                if type(speed[0]) is int:dados['ddr']='DDR'+str(speed[0])
                dados['frequencia_mhz']=speed[1]
            if isinstance(modulos,list) and len(modulos)==2 and all(type(v) is int and v>0 for v in modulos):
                dados.update(quantidade_pentes=modulos[0],capacidade_gb=modulos[0]*modulos[1])
            if linha.get('cas_latency') is not None:dados['latencia']=str(linha['cas_latency'])
            detalhes=[dados.get('ddr'),str(dados.get('frequencia_mhz','')),f"{modulos[0]}x{modulos[1]}GB" if isinstance(modulos,list) and len(modulos)==2 else None,
                'CL'+str(linha['cas_latency']) if linha.get('cas_latency') is not None else None]
            dados['modelo']+=' ['+' '.join(str(v) for v in detalhes if v)+']'
        if categoria=='monitor' and isinstance(linha.get('resolution'),list) and len(linha['resolution'])==2:
            dados['resolucao']='x'.join(str(v) for v in linha['resolution'])
        if categoria in ('mouse','teclado') and isinstance(linha.get('connection_type'),str):
            dados['conexao']=linha['connection_type']
        if categoria=='fone':
            tipos={'Circumaural':'over-ear','Supra-aural':'on-ear','Earbud':'earbud','In Ear':'in-ear'}
            if linha.get('type') in tipos:dados['tipo']=tipos[linha['type']]
            if type(linha.get('wireless')) is bool:dados['conexao']='Wireless' if linha['wireless'] else 'Wired'
        # Quantidade só quando explicitamente identificada; ausência não significa 1.
        if categoria=='fan':
            m=re.search(r'\b(\d+)[ -]Pack\b',titulo,re.I)
            if m:dados['quantidade']=int(m[1])
        cor=linha.get('color')
        if isinstance(cor,str) and cor.strip():dados['modelo']+=' ['+cor.strip()+']'
        bruto={k:v for k,v in linha.items() if k not in ('price','price_per_gb')}
        from models.modelos_pecas import MODELOS_PECAS
        classe=next(m for m in MODELOS_PECAS if m.__tablename__==categoria)
        ausentes=[c.name for c in classe.__table__.columns if not c.nullable
            and c.name not in ('id','criado_em') and dados.get(c.name) is None]
        if ausentes:raise ValueError('Campos necessários ausentes: '+', '.join(ausentes))
        from sqlalchemy import Boolean,Integer,Numeric,Float,String
        for campo,valor in dados.items():
            tipo=classe.__table__.c[campo].type
            if isinstance(tipo,Boolean):
                if type(valor) is not bool:raise ValueError('Booleano inválido: '+campo)
            elif isinstance(tipo,(Integer,Numeric,Float)):
                if type(valor) not in (int,float) or not math.isfinite(valor) or valor<0 or isinstance(tipo,Integer) and valor!=int(valor):raise ValueError('Número inválido: '+campo)
            elif isinstance(tipo,String):
                if not isinstance(valor,str) or not valor.strip() or tipo.length and len(valor)>tipo.length:raise ValueError('Texto inválido: '+campo)
        return dict(categoria=categoria,dados=dados,titulo=titulo,
            identidade=assinatura({'categoria':categoria,'dados':bruto}),bruto=bruto,origem=origem)
