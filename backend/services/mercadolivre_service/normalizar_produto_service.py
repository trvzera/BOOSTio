"""Único adaptador de atributos/domínios Mercado Livre para o contrato comum."""
import re
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.normalizar_produto import atributos
from .especificacoes_complementares import complementar, tipo_refrigeracao

DOMINIOS = {
 'processador':'MLB-COMPUTER_PROCESSORS','placa_video':'MLB-GRAPHICS_CARDS','memoria_ram':'MLB-RAM_MEMORY_MODULES',
 'placa_mae':'MLB-COMPUTER_MOTHERBOARDS','ssd':'MLB-HARD_DRIVES_AND_SSDS','hd':'MLB-HARD_DRIVES_AND_SSDS',
 'mouse':'MLB-COMPUTER_MICE','fonte':'MLB-DESKTOP_COMPUTER_POWER_SUPPLIES',
 'monitor':'MLB-COMPUTER_MONITORS','fone':'MLB-HEADPHONES','teclado':'MLB-PC_KEYBOARDS',
 'gabinete':'MLB-DESKTOP_COMPUTER_CASES',
 'air_cooler':'MLB-DESKTOP_COMPUTER_COOLERS_AND_FANS','water_cooler':'MLB-DESKTOP_COMPUTER_COOLERS_AND_FANS',
 'fan':'MLB-DESKTOP_COMPUTER_COOLERS_AND_FANS',
 'adaptador_wifi':'MLB-NETWORK_CARDS','cabo_rede':'MLB-NETWORK_CABLES',
}
CAMPOS = {
 'soquete':('COMPATIBLE_SOCKETS',),'socket':('SOCKET',),'nucleo':('CPU_CORES_NUMBER',),'thread':('CPU_THREADS_NUMBER',),
 'clockbase':('MIN_CLOCK_FREQUENCY',),'clockmax':('MAX_CLOCK_FREQUENCY',),
 'memoria_gb':('MEMORY_SIZE',),'tipo_memoria':('GRAPHICS_MEMORY_TYPE','SUPPORTED_RAM_MEMORY_TYPE'),
 'capacidade_gb':('RAM_MEMORY_MODULE_TOTAL_CAPACITY','CAPACITY'), 'ddr':('RAM_MEMORY_MODULE_TYPE',),
 'frequencia_mhz':('RAM_MEMORY_MODULE_SPEED','TESTED_SPEED'),'latencia':('CAS_LATENCY','TESTED_LATENCY'),
 'quantidade_pentes':('RAM_MEMORY_MODULES',),'formato':('FORM_FACTOR','HARD_DRIVE_AND_SSD_FORM_FACTOR','RAM_MEMORY_FORMAT'),
 'tipo':('DRIVE_STORAGE_TYPE',),'interface':('INTERFACES',),'velocidade_rpm':('ROTATION_SPEED',),
 'memoria_cache_mb':('DATA_CACHE',),'potencia_w':('POWER_OUTPUT',),'dpi_max':('SENSOR_RESOLUTION',),
 'wifi':('WITH_WIFI',),'conexao':('CONNECTIVITY',),'chipset':('CHIPSET',),'iluminacao':('WITH_RGB_LIGHTING',),
}


class NormalizarProdutoService:
    def executar(self, produto, categoria=None):
        if not isinstance(produto,dict):raise ValueError('Produto do Mercado Livre inválido')
        a=atributos(produto);dominio=produto.get('domain_id')
        if categoria is None:
            candidatas=[k for k,v in DOMINIOS.items() if v==dominio]
            if len(candidatas)==1:categoria=candidatas[0]
        dominio_correto=categoria in DOMINIOS and dominio==DOMINIOS.get(categoria)
        if categoria == 'adaptador_wifi' and dominio == 'MLB-WIRELESS_ANTENNAS_AND_ADAPTERS':
            dominio_correto=True
        confirmado=dominio_correto
        tipo_cooler=tipo_refrigeracao(a) if categoria in ('air_cooler','water_cooler','fan') else None
        if categoria in ('air_cooler','water_cooler','fan'):
            confirmado=dominio_correto and tipo_cooler==categoria
        def valores(ids):return sorted(set().union(*(a.get(id,set()) for id in ids)))
        def unico(id):
            v=valores((id,));return v[0] if len(v)==1 else None
        def identificadores(ids):
            resultado = set()
            for atributo in produto.get('attributes', []):
                if not isinstance(atributo, dict) or atributo.get('id') not in ids:
                    continue
                estruturados = [v.get('name') for v in atributo.get('values', []) if isinstance(v, dict) and isinstance(v.get('name'), str)]
                textos = estruturados or [atributo.get('value_name')]
                for texto in textos:
                    if isinstance(texto, str) and texto.strip():
                        resultado.add(texto.strip())
            return sorted(resultado)
        specs={k:valores(ids) for k,ids in CAMPOS.items() if valores(ids)}
        if categoria=='memoria_ram':specs['formato_ram']=specs.pop('formato',[])
        if categoria in ('ssd','hd'):
            specs['tecnologia_armazenamento']=valores(('DRIVE_STORAGE_TYPE',))
        if categoria=='ssd':
            # SSD/SATA/NVMe são conceitos distintos. O tipo interno vem da interface explícita.
            interfaces=specs.get('interface',[])
            specs['tecnologia_armazenamento']=specs.pop('tipo',[])
            specs['tipo']=[v for v in interfaces if 'nvme' in v or 'sata' in v]
        complementar(produto,a,categoria,specs)
        return ProdutoNormalizado(loja='mercado_livre',id_externo=produto['id'] if isinstance(produto.get('id'),str) and re.fullmatch(r'MLB[0-9]+',produto['id']) else '',categoria=categoria,
            categoria_confirmada=confirmado,titulo=produto.get('name') or produto.get('title') or '',
            marca=unico('BRAND'),modelo=unico('MODEL'),
            modelos_alternativos=tuple(valores(('MODEL','LINE','DETAILED_MODEL','DETAILED_MODEL_NEW','EDITION','ALPHANUMERIC_MODEL','ALPHANUMERIC_MODELS','MPN','MANUFACTURER_PART_NUMBER','PART_NUMBER'))),
            especificacoes=specs,identificadores={'mpn':identificadores(('MPN','MANUFACTURER_PART_NUMBER','PART_NUMBER')),'gtin':identificadores(('GTIN','EAN','UPC'))},
            ativo=produto.get('status')=='active' if 'status' in produto else None,
            fonte=f"https://api.mercadolibre.com/products/{produto.get('id')}",
            contexto={'marcas_multiplas':len(a.get('BRAND',set()))>1,'oem':bool(a.get('IS_OEM',set()) & {'sim','yes','true'}),
                      'dominio_divergente':bool(dominio and categoria in DOMINIOS and not dominio_correto)
                          or bool(tipo_cooler and tipo_cooler!=categoria)})
