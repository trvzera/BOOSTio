import json
import re
import hashlib
from services.especificacoes_service.buscar_ficha_kabum_service import _ScriptsJson
from services.catalogo_service.normalizar_produto import codigo, nome, gtin
from services.catalogo_service.conferir_especificacoes_service import valores


class PaginaTecnica(_ScriptsJson):
    def __init__(self):
        super().__init__()
        self.pares={}
        self.celula=None
        self.textos=[]
        self.chave=None

    def handle_starttag(self,tag,attrs):
        super().handle_starttag(tag,attrs)
        if tag in ('th','td','dt','dd'):
            self.celula=tag;self.textos=[]

    def handle_data(self,texto):
        super().handle_data(texto)
        if self.celula:self.textos.append(texto)

    def handle_endtag(self,tag):
        super().handle_endtag(tag)
        if tag!=self.celula:return
        texto=' '.join(' '.join(self.textos).split())
        if tag in ('th','dt'):self.chave=texto
        elif self.chave and texto:
            self.pares.setdefault(self.chave,set()).add(texto)
        self.celula=None


def produtos_json(dado,profundidade=0):
    if profundidade>20:return
    if isinstance(dado,list):
        for item in dado:yield from produtos_json(item,profundidade+1)
    elif isinstance(dado,dict):
        tipos=dado.get('@type',[])
        if tipos=='Product' or isinstance(tipos,list) and 'Product' in tipos:
            yield dado
        for chave in ('@graph','hasVariant','mainEntity'):
            yield from produtos_json(dado.get(chave),profundidade+1)


class NormalizarFichaFabricanteService:
    def executar(self,html,url,fabricante,produto):
        parser=PaginaTecnica();parser.feed(html)
        pares={k:next(iter(v)) for k,v in parser.pares.items() if len(v)==1}
        candidatos=[]
        procurados={codigo(v) for v in valores(produto.identificadores.get('mpn')) if isinstance(v,str)}
        if produto.modelo:procurados.add(codigo(produto.modelo))
        gtins={gtin(v) for v in valores(produto.identificadores.get('gtin')) if gtin(v)}
        for script in parser.scripts:
            try:dado=json.loads(script)
            except ValueError:continue
            for item in produtos_json(dado):
                sku=item.get('mpn') or item.get('sku')
                remotos={gtin(item.get(k)) for k in ('gtin8','gtin12','gtin13','gtin14') if gtin(item.get(k))}
                if sku and (codigo(sku) in procurados or gtins and gtins <= remotos):candidatos.append(item)
        if fabricante=='amd' and produto.categoria=='processador' and not candidatos:
            titulo=nome(produto.titulo)
            campo='Product ID Tray' if re.search(r'\b(oem|tray)\b',titulo) else 'Product ID Boxed' if re.search(r'\bbox(?:ed)?\b',titulo) else None
            if campo and pares.get(campo) and pares.get('Name','').startswith('AMD '):
                candidatos.append({'sku':pares[campo],'name':pares['Name'],'brand':'AMD'})
        unicos={json.dumps(v,sort_keys=True):v for v in candidatos}
        if len(unicos)!=1:
            raise ValueError('Identidade estruturada da ficha ausente ou ambígua')
        item=next(iter(unicos.values()))
        marca=item.get('brand')
        if isinstance(marca,dict):marca=marca.get('name')
        if not isinstance(marca,str) or not item.get('name'):
            raise ValueError('Ficha oficial sem fabricante e modelo confirmados')
        dados={'fabricante':marca,'modelo':item['name']}
        if fabricante=='corsair' and produto.categoria=='memoria_ram':
            tamanho=re.fullmatch(r'(\d+)\s*GB\s*\((\d+)\s*x\s*(\d+)\s*GB\)',pares.get('Memory Size',''),re.I)
            if tamanho and int(tamanho[1])==int(tamanho[2])*int(tamanho[3]):
                dados.update(capacidade_gb=int(tamanho[1]),quantidade_pentes=int(tamanho[2]))
            for origem,destino in {'Memory Type':'ddr','Package Memory Format':'formato','Tested Latency':'latencia'}.items():
                if pares.get(origem):dados[destino]=pares[origem]
            if pares.get('Lighting') in ('RGB','None'):
                dados['iluminacao']=pares['Lighting']=='RGB'
            velocidade=re.fullmatch(r'(\d+)\s*MHz',pares.get('Tested Speed',''),re.I)
            if velocidade:dados['frequencia_mhz']=int(velocidade[1])
        elif fabricante=='logitech' and produto.categoria=='mouse':
            for campo in item.get('additionalProperty',[]):
                if campo.get('name')=='Resolution':
                    m=re.fullmatch(r'(\d+)\s*DPI',str(campo.get('value','')),re.I)
                    if m:dados['dpi_max']=int(m[1])
                if campo.get('name')=='Connection Type':dados['conexao']=campo.get('value')
        elif fabricante=='amd' and produto.categoria=='processador':
            for origem,destino in {'CPU Socket':'soquete','# of CPU Cores':'nucleo','# of Threads':'thread','Base Clock':'clockbase','Max. Boost Clock':'clockmax','Default TDP':'consumo_energia'}.items():
                valor=pares.get(origem)
                if not valor:continue
                if destino=='soquete':dados[destino]=valor
                else:
                    m=re.fullmatch(r'(?:Up to )?(\d+(?:\.\d+)?)\s*(?:GHz|W)?',valor,re.I)
                    if m:dados[destino]=int(m[1]) if destino in ('nucleo','thread') else float(m[1])
            if pares.get('Graphics Model')=='Discrete Graphics Card Required':dados['videointegrado']=False
            if pares.get('Thermal Solution (PIB)')=='Not Included':dados['cooler']=False
        elif fabricante=='crucial' and produto.categoria=='ssd':
            for atributo in item.get('additionalProperty',[]):
                campo=atributo.get('name');valor=str(atributo.get('value',''))
                if campo=='Capacity':
                    m=re.fullmatch(r'(\d+)\s*GB',valor,re.I)
                    if m:dados['capacidade_gb']=int(m[1])
                if campo=='Interface':
                    dados['interface']=valor
                    if 'sata' in valor.lower():dados['tipo']='SATA'
        else:
            raise ValueError('Categoria ainda sem mapeamento nesse fabricante')
        sha=hashlib.sha256(html.encode()).hexdigest()
        fontes={k:dict(url=url,base=fabricante,sha256=sha) for k in [*dados,'mpn']}
        eans={gtin(item.get(k)) for k in ('gtin8','gtin12','gtin13','gtin14') if gtin(item.get(k))}
        return dict(dados=dados,identidade={'mpn':item.get('mpn') or item.get('sku'),'gtin':next(iter(eans)) if len(eans)==1 else None},
                    fontes=fontes,fonte_identidade=url,especificacoes_originais=pares,conflitos=[])
