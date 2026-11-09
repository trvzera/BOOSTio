"""Consulta somente snapshots locais já suportados; nunca estima pontuações."""
from pathlib import Path
from services.benchmark_service.importar_referencias_passmark_service import ImportarReferenciasPassmarkService
from services.benchmark_service.importar_benchmarks_service import normalizar_nome, CONFIG


class ConsultarBenchmarkCatalogoService:
    def __init__(self, cpu=None, gpu=None):
        self.caminhos = {'processador':cpu, 'placa_video':gpu}
        self.cache = {}

    def executar(self, categoria, fabricante, modelo):
        caminho = self.caminhos.get(categoria)
        if not caminho:
            return {'status':'nao_configurado', 'dados':{}}
        tipo = 'cpu' if categoria == 'processador' else 'gpu'
        if tipo not in self.cache:
            if Path(caminho).stat().st_size > 32_000_000:
                raise ValueError('Snapshot de benchmark excede 32 MB')
            self.cache[tipo] = ImportarReferenciasPassmarkService()._ler(caminho, tipo)
        ids, nomes, fonte = self.cache[tipo]
        encontrados = set()
        for texto in (modelo, f'{fabricante} {modelo}'):
            encontrados |= nomes.get(normalizar_nome(texto), set())
        if len(encontrados) != 1:
            return {'status':'ambigua' if encontrados else 'nao_encontrado','dados':{}}
        grupo = ids[next(iter(encontrados))]
        r = grupo[0]
        if any(x['erro'] or x['nome'] != r['nome'] or x['valores'] != r['valores'] for x in grupo):
            return {'status':'invalido','dados':{}}
        dados = {k:str(v) for k,v in r['valores'].items() if v is not None}
        dados.update(benchmark_teste=CONFIG[tipo][2],benchmark_versao=None,benchmark_nome_fonte=r['nome'],
                     benchmark_fonte=fonte['fonte'],benchmark_referencia_em=None)
        return {'status':'encontrado','dados':dados,'sha256':fonte['sha256'],
                'escopo':'modelo_cpu' if tipo=='cpu' else 'referencia_chip_gpu'}
