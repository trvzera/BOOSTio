"""Único adaptador de atributos/domínios Mercado Livre para o contrato comum."""
import re
from services.catalogo_service.produto_normalizado import ProdutoNormalizado
from services.catalogo_service.normalizar_produto import atributos

DOMINIOS = {
 'processador':'MLB-COMPUTER_PROCESSORS','placa_video':'MLB-GRAPHICS_CARDS','memoria_ram':'MLB-RAM_MEMORY_MODULES',
 'placa_mae':'MLB-COMPUTER_MOTHERBOARDS','ssd':'MLB-HARD_DRIVES_AND_SSDS','hd':'MLB-HARD_DRIVES_AND_SSDS',
 'mouse':'MLB-COMPUTER_MICE','fonte':'MLB-DESKTOP_COMPUTER_POWER_SUPPLIES',
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
        confirmado=categoria in DOMINIOS and dominio==DOMINIOS.get(categoria)
        def valores(ids):return sorted(set().union(*(a.get(id,set()) for id in ids)))
        def unico(id):
            v=valores((id,));return v[0] if len(v)==1 else None
        specs={k:valores(ids) for k,ids in CAMPOS.items() if valores(ids)}
        if categoria=='memoria_ram':specs['formato_ram']=specs.pop('formato',[])
        if categoria in ('ssd','hd'):
            specs['tecnologia_armazenamento']=valores(('DRIVE_STORAGE_TYPE',))
        if categoria=='ssd':
            # SSD/SATA/NVMe são conceitos distintos. O tipo interno vem da interface explícita.
            interfaces=specs.get('interface',[])
            specs['tecnologia_armazenamento']=specs.pop('tipo',[])
            specs['tipo']=[v for v in interfaces if 'nvme' in v or 'sata' in v]
        return ProdutoNormalizado(loja='mercado_livre',id_externo=produto['id'] if isinstance(produto.get('id'),str) and re.fullmatch(r'MLB[0-9]+',produto['id']) else '',categoria=categoria,
            categoria_confirmada=confirmado,titulo=produto.get('name') or produto.get('title') or '',
            marca=unico('BRAND'),modelo=unico('MODEL'),
            modelos_alternativos=tuple(valores(('MODEL','LINE','DETAILED_MODEL','DETAILED_MODEL_NEW','EDITION','ALPHANUMERIC_MODEL'))),
            especificacoes=specs,identificadores={'mpn':valores(('MPN','MANUFACTURER_PART_NUMBER','PART_NUMBER')),'gtin':valores(('GTIN','EAN','UPC'))},
            ativo=produto.get('status')=='active' if 'status' in produto else None,
            fonte=f"https://api.mercadolibre.com/products/{produto.get('id')}",
            contexto={'marcas_multiplas':len(a.get('BRAND',set()))>1,'oem':bool(a.get('IS_OEM',set()) & {'sim','yes','true'}),
                      'dominio_divergente':bool(dominio and categoria in DOMINIOS and not confirmado)})
