from copy import deepcopy
from decimal import Decimal

from .amostra_inteligente_service import AmostraInteligenteService
from .custos_build_service import resumo_custos

numero = AmostraInteligenteService.numero


class MelhorarInvestimentoBuildService:
    """Sobe de nível as peças principais quando a build válida deixa muito do teto do PC sem uso."""

    ORDEM = ('placa_video', 'processador', 'memoria_ram', 'ssd')
    PARTICIPACAO_MAXIMA = {'placa_video': Decimal('.45'), 'processador': Decimal('.40'),
                           'memoria_ram': Decimal('.25'), 'ssd': Decimal('.15')}
    BENCHMARKS = {'placa_video': 'benchmark_g3d', 'processador': 'benchmark_multi_core'}
    DESEMPATE = {'memoria_ram': 'frequencia_mhz', 'ssd': 'velocidade_leitura_mbps'}
    LIMIAR = Decimal('0.75')
    MAX_VALIDACOES = 40

    def executar(self, build, catalogo, teto_pc, proprias, validar):
        """Devolve (build melhorada, trocas) ou None quando não há melhoria possível."""
        teto_pc = Decimal(str(teto_pc))
        gasto = self.gasto(build, catalogo)
        if gasto is None or gasto >= teto_pc * self.LIMIAR:
            return None
        atual, trocas, validacoes, melhorou = build, [], 0, True
        while melhorou and validacoes < self.MAX_VALIDACOES:
            melhorou = False
            for tipo in self.ORDEM:
                item = next((i for i in atual['componentes'] if i['tipo'] == tipo), None)
                if item is None or tipo in proprias:
                    continue
                for nova in self._candidatas(item, tipo, atual, catalogo, teto_pc):
                    if validacoes >= self.MAX_VALIDACOES:
                        break
                    validacoes += 1
                    tentativa = deepcopy(atual)
                    next(i for i in tentativa['componentes'] if i['tipo'] == tipo)['id'] = nova['id']
                    try:
                        validada = validar(tentativa)
                    except ValueError:
                        continue
                    novo_gasto = self.gasto(validada, catalogo)
                    if novo_gasto is None or novo_gasto > teto_pc:
                        continue
                    trocas.append({'tipo': tipo, 'id_anterior': item['id'], 'id_novo': nova['id']})
                    atual, melhorou = validada, True
                    break
        return (atual, trocas) if trocas else None

    @staticmethod
    def gasto(build, catalogo):
        resumo = resumo_custos(build, catalogo)
        if len(resumo['itens']) != len(build['componentes']):
            return None
        return Decimal(str(resumo['pc']))

    def _candidatas(self, item, tipo, build, catalogo, teto_pc):
        pecas = catalogo.get(tipo, [])
        original = next((p for p in pecas if p['id'] == item['id']), None)
        quantidade = item.get('quantidade', 1)
        if original is None:
            return []
        subtotal = Decimal(str(original['preco'])) * quantidade
        sobra = teto_pc - self.gasto(build, catalogo) + subtotal
        limite = min(sobra, teto_pc * self.PARTICIPACAO_MAXIMA[tipo])
        candidatas = [p for p in pecas if p['id'] != item['id'] and p.get('esgotado') is not True
                      and numero(p.get('preco')) and Decimal(str(p['preco'])) * quantidade <= limite
                      and Decimal(str(p['preco'])) > Decimal(str(original['preco'])) and self._melhor(original, p, tipo)]
        return sorted(candidatas, key=lambda p: (-Decimal(str(p['preco'])), str(p['id'])))

    def _melhor(self, original, nova, tipo):
        if tipo in self.BENCHMARKS:
            antes, depois = numero(original.get(self.BENCHMARKS[tipo])), numero(nova.get(self.BENCHMARKS[tipo]))
            return antes is not None and depois is not None and depois > antes
        capacidade_antes, capacidade_depois = original.get('capacidade_gb'), nova.get('capacidade_gb')
        if type(capacidade_antes) is not int or type(capacidade_depois) is not int or capacidade_depois < capacidade_antes:
            return False
        if capacidade_depois > capacidade_antes:
            return True
        antes, depois = numero(original.get(self.DESEMPATE[tipo])), numero(nova.get(self.DESEMPATE[tipo]))
        return antes is not None and depois is not None and depois > antes
