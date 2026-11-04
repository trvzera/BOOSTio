"""Ficha técnica extraída de atributos oficiais, mantendo lacunas explícitas."""
import re
from datetime import datetime, timezone
from dataclasses import asdict
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_catalogo
from services.catalogo_service.normalizar_produto import atributos, numero, gtin
from .comparar_produtos_service import CompararProdutosService, DOMINIOS
from .buscar_ofertas_mercado_livre_service import BuscarOfertasMercadoLivreService
from services.catalogo_service.consultar_benchmark_catalogo_service import ConsultarBenchmarkCatalogoService

# IDs efetivamente observados nas respostas oficiais preservadas.
ATRIBUTOS = {
 'processador': {'soquete':('COMPATIBLE_SOCKETS',None),'nucleo':('CPU_CORES_NUMBER','inteiro'),
    'thread':('CPU_THREADS_NUMBER','inteiro'),'clockbase':('MIN_CLOCK_FREQUENCY','ghz'),
    'clockmax':('MAX_CLOCK_FREQUENCY','ghz'),'consumo_energia':('TDP','w')},
 'placa_video': {'memoria_gb':('MEMORY_SIZE','gb'),'tipo_memoria':('GRAPHICS_MEMORY_TYPE',None),
    'consumo_energia':('TOTAL_GRAPHICS_POWER','w')},
 'memoria_ram': {'capacidade_gb':('RAM_MEMORY_MODULE_TOTAL_CAPACITY','gb'),
    'ddr':('RAM_MEMORY_MODULE_TYPE','ddr'),'formato':('RAM_MEMORY_FORMAT',None),'frequencia_mhz':('RAM_MEMORY_MODULE_SPEED','mhz')},
 'placa_mae': {'socket':('SOCKET',None),'tipo_memoria':('SUPPORTED_RAM_MEMORY_TYPE','ddr'),
    'quantidade_slots_ram':('RAM_MEMORY_SLOTS','inteiro'),'memoria_maxima_gb':('MAX_SUPPORTED_RAM_MEMORY_CAPACITY','gb')},
 'ssd': {'capacidade_gb':('CAPACITY','gb'),'interface':('INTERFACES',None),'tipo':('INTERFACES',None),
    'velocidade_leitura_mbps':('SSD_MAX_READ_SPEED','mbps'),'velocidade_gravacao_mbps':('SSD_MAX_WRITE_SPEED','mbps')},
 'hd': {'consumo_energia':('HARD_DRIVE_AND_SSD_POWER_CONSUMPTION','w'),'capacidade_gb':('CAPACITY','gb'),'interface':('INTERFACES',None),'velocidade_rpm':('ROTATION_SPEED','rpm')},
}
IGNORADOS = {'id','criado_em','atualizado_em','status_validacao'}


class EnriquecerProdutoService:
    def __init__(self, benchmarks=None, base_hardware=None):
        self.benchmarks = benchmarks or ConsultarBenchmarkCatalogoService()
        from services.catalogo_service.consultar_base_hardware_service import ConsultarBaseHardwareService
        self.base_hardware=base_hardware or ConsultarBaseHardwareService()

    def executar(self, categoria, produto, anuncio):
        modelos = {m.__tablename__:m for m in MODELOS_PECAS}
        if categoria not in modelos or not isinstance(produto,dict) or not isinstance(anuncio,dict):
            raise ValueError('Ficha ou categoria inválida')
        modelo = modelos[categoria]
        a = atributos(produto);dados = {};origens = {};conflitos = [];avisos = []
        def atribuir(campo, valor, origem):
            if valor is not None:
                dados[campo] = valor;origens[campo] = origem
        def unico(id):
            valores = a.get(id, set())
            return next(iter(valores)) if len(valores)==1 else None
        atribuir('fabricante',unico('BRAND'),'BRAND')
        atribuir('modelo',unico('MODEL'),'MODEL')
        for campo,(id,tipo) in ATRIBUTOS.get(categoria,{}).items():
            valor = unico(id)
            if valor is None:continue
            if tipo == 'ddr':
                m=re.fullmatch(r'ddr\s*([345])(?:\s+sdram)?',valor)
                valor='DDR'+m[1] if m else None
            elif tipo:
                valor=numero(valor,None if tipo=='inteiro' else tipo)
                if valor is not None:
                    if tipo in ('inteiro','gb','mhz','rpm','mbps'):
                        valor=int(valor) if valor==int(valor) and valor>0 else None
                    else:valor=float(valor) if valor>0 else None
            atribuir(campo,valor,id)
        if categoria=='processador':
            video=unico('GRAPHIC_PROCESSOR')
            if video in ('nao','no','não','sem video integrado'):
                atribuir('videointegrado',False,'GRAPHIC_PROCESSOR')
            elif video and video not in ('sim','yes'):
                atribuir('videointegrado',True,'GRAPHIC_PROCESSOR');atribuir('modelo_videointegrado',video,'GRAPHIC_PROCESSOR')
            avisos.append('TDP é potência nominal para planejamento; não mede consumo real')
        if categoria=='memoria_ram':
            modulos=unico('RAM_MEMORY_MODULES')
            if modulos:
                m=re.fullmatch(r'(\d+)\s*[x×]\s*(\d+)\s*gb',modulos)
                qtd=int(m[1]) if m else numero(modulos)
                if qtd is not None and qtd==int(qtd) and qtd>0:
                    atribuir('quantidade_pentes',int(qtd),'RAM_MEMORY_MODULES')
        try:atribuir('preco',float(BuscarOfertasMercadoLivreService._preco(anuncio.get('price'))),'anuncio.price')
        except ValueError:avisos.append('Preço ausente ou inválido')
        quantidade=anuncio.get('available_quantity')
        if type(quantidade) is int and quantidade>=0:
            atribuir('esgotado',quantidade==0,'anuncio.available_quantity')
        mpns = set().union(*(a.get(k,set()) for k in ('MPN','MANUFACTURER_PART_NUMBER','PART_NUMBER')))
        mpn=next(iter(mpns)) if len(mpns)==1 else None
        if mpn and not re.fullmatch(r'[a-z0-9][a-z0-9./_-]{2,254}',mpn):mpn=None
        gtins={gtin(v) for v in a.get('GTIN',set())};gtins.discard(None)
        identidade={'mpn':mpn,'gtin':next(iter(gtins)) if len(gtins)==1 else None}
        from services.catalogo_service.validar_ficha_tecnica_service import ValidarFichaTecnicaService
        from services.catalogo_service.consultar_base_hardware_service import ConsultarBaseHardwareService
        from .normalizar_produto_service import NormalizarProdutoService
        normalizado=NormalizarProdutoService().executar(produto,categoria)
        consulta=self.base_hardware.executar(normalizado)
        normalizado=consulta['produto']
        for campo,valor in consulta['dados'].items():
            if campo in modelo.__table__.columns and campo not in dados:dados[campo]=valor
        validacao=ValidarFichaTecnicaService().executar(categoria,dados,normalizado,identidade)
        conflitos+=validacao['conflitos'];pendentes=validacao['campos_pendentes']
        if anuncio.get('title'):
            from dataclasses import replace
            titulo=ValidarFichaTecnicaService().executar(categoria,dados,replace(normalizado,titulo=anuncio['title']),identidade)
            conflitos+=titulo['conflitos']
            if not titulo['pronto']:avisos.append('Título individual requer revisão')
        benchmark=self.benchmarks.executar(categoria,dados.get('fabricante',''),dados.get('modelo',''))
        pronto=not pendentes and not conflitos and validacao['pronto'] and 'Título individual requer revisão' not in avisos
        return dict(categoria=categoria,pronto=pronto,dados=dados,identidade=identidade,
            campos_pendentes=sorted(set(pendentes)),conflitos=sorted(set(conflitos)),avisos=avisos,
            fontes={**consulta['fontes'], **{k:dict(url=f"https://api.mercadolibre.com/products/{produto.get('id')}"+("/items" if v.startswith("anuncio.") else ""),atributo=v) for k,v in origens.items()}},
            benchmark=benchmark,normalizado=asdict(normalizado),loja='mercado_livre',fonte_identidade=normalizado.fonte,base_hardware=consulta['status'],assinatura_catalogo=assinatura_catalogo(produto),produto=produto,
            coletado_em=datetime.now(timezone.utc).isoformat())
