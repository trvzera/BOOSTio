import hashlib,json,re
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlsplit
from .comparar_nomes_service import CompararNomesService, marca as normalizar_marca
from .associacao_inteligente_service import AssociacaoInteligenteService
from .conferir_especificacoes_service import ConferirEspecificacoesService

BASE=Path(__file__).resolve().parents[2]/'data/hardware/pc-builder-parts.json'
GRUPOS={'processador':'cpu','placa_video':'gpu','placa_mae':'motherboard','memoria_ram':'ram','ssd':'storage','fonte':'psu','gabinete':'case'}
CAMPOS={'cores':'nucleo','threads':'thread','socket':'soquete','boost_ghz':'clockmax','vram_gb':'memoria_gb',
 'ram_type':'ddr','capacity_gb':'capacidade_gb','cas_latency':'latencia','interface':'interface',
 'form_factor':'formato','wattage_w':'potencia_w','chipset':'chipset','ram_slots':'quantidade_slots_ram',
 'ram_max_gb':'memoria_maxima_gb','m2_slots':'quantidade_slots_m2','read_mbps':'velocidade_leitura_mbps',
 'write_mbps':'velocidade_gravacao_mbps','max_gpu_length_mm':'tamanho_max_gpu_mm','max_cpu_cooler_mm':'tamanho_max_cooler_mm'}


class ConsultarBaseHardwareService:
    def __init__(self,caminho=BASE):self.caminho=Path(caminho);self.base=None;self.cache={}

    def _ler(self):
        if self.base is not None:return
        bruto=self.caminho.read_bytes()
        if len(bruto)>8_000_000:raise ValueError('Base de hardware excede 8 MB')
        self.base=json.loads(bruto);self.sha=hashlib.sha256(bruto).hexdigest()
        if self.base.get('_meta',{}).get('license')!='CC BY 4.0':raise ValueError('Licença inesperada na base técnica')
        self.atribuicao=self.base['_meta']['attribution_required']
        self.por_marca = {}
        for grupo in set(GRUPOS.values()):
            for linha in self.base.get(grupo, []):
                chave = (grupo, normalizar_marca(linha['vendor']))
                self.por_marca.setdefault(chave, []).append(linha)

    def executar(self,produto):
        self._ler()
        chave=json.dumps(asdict(produto),sort_keys=True,default=str)
        if chave in self.cache:return self.cache[chave]
        candidatos=[]
        grupo = GRUPOS.get(produto.categoria, '')
        linhas = self.por_marca.get((grupo, normalizar_marca(produto.marca)), []) if produto.marca else self.base.get(grupo, [])
        for row in linhas:
            fonte=row.get('source');u=urlsplit(fonte or '')
            if u.scheme!='https' or not u.hostname or u.username or u.password:continue
            try:
                if date.fromisoformat(row['last_verified'])>date.today():continue
            except (ValueError,KeyError):continue
            dados={destino:row[origem] for origem,destino in CAMPOS.items() if origem in row}
            if produto.categoria=='placa_mae':
                if 'soquete' in dados:dados['socket']=dados.pop('soquete')
                if 'ddr' in dados:dados['tipo_memoria']=dados.pop('ddr')
            if produto.categoria=='memoria_ram':
                m=re.fullmatch(r'(\d+)x\d+GB',row.get('kit',''),re.I)
                if m:dados['quantidade_pentes']=int(m[1])
            local=SimpleNamespace(__tablename__=produto.categoria,fabricante=row['vendor'],modelo=row['model'],**dados)
            marca=AssociacaoInteligenteService().comparar_marca(local,produto)
            nomes=CompararNomesService().executar(local,produto)
            specs=ConferirEspecificacoesService().executar(local,produto)
            if marca['conflitos'] or not marca['pontos'] or not nomes['exato'] or specs['conflitos']:continue
            candidatos.append((row,dados))
        if len(candidatos)!=1:
            resultado=dict(status='ambigua' if candidatos else 'nao_encontrada',produto=produto,dados={},fontes={})
        else:
            row,dados=candidatos[0];specs=dict(produto.especificacoes)
            preenchidos={k:v for k,v in dados.items() if not specs.get(k)}
            specs.update(preenchidos)
            resultado=dict(status='encontrada',produto=replace(produto,especificacoes=specs),dados=preenchidos,
                fontes={k:dict(url=row['source'],base='TechFuelHQ',licenca='CC BY 4.0',sha256=self.sha,
                              referencia=row['id'],referencia_em=row['last_verified'],atribuicao=self.atribuicao) for k in preenchidos})
        if len(self.cache) >= 256:
            self.cache.pop(next(iter(self.cache)))
        self.cache[chave]=resultado
        return resultado
