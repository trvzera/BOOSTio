from decimal import Decimal
from math import isfinite

from utils.sockets import normalizar_socket
from .preferencias_cores_service import PreferenciasCoresService


class AmostraInteligenteService:
    METRICAS = {'processador': ('benchmark_multi_core', 'benchmark_single_thread'),
                'placa_video': ('benchmark_g3d', 'benchmark_g2d')}
    RECURSOS = {
        'processador': ('soquete', 'videointegrado', 'cooler', 'nucleo', 'thread'),
        'placa_video': ('gpu_chip', 'memoria_gb', 'tipo_memoria', 'interface_memoria'),
    }
    EXTRAS = {
        'processador': ('modelo_videointegrado', 'modelo_cooler', 'tipos_memoria_cpu', 'memoria_maxima_cpu_gb'),
        'placa_video': ('conectores_energia', 'comprimento_mm', 'altura_mm', 'slots_ocupados'),
    }

    @staticmethod
    def numero(valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)) or not isfinite(valor):
            return None
        return Decimal(str(valor))

    @classmethod
    def chave_equivalencia(cls, peca, tipo, cor):
        campos = cls.RECURSOS[tipo]
        if any(peca.get(c) is None for c in campos):
            return None
        socket = normalizar_socket(peca.get('soquete')) if tipo == 'processador' else None
        if tipo == 'processador' and (not socket or
            (peca.get('videointegrado') and not peca.get('modelo_videointegrado')) or
            (peca.get('cooler') and not peca.get('modelo_cooler'))):
            return None
        if not peca.get('benchmark_teste'):
            return None
        valores = tuple(str(peca.get(c)) for c in (*campos, *cls.EXTRAS[tipo]))
        cores = tuple(sorted(PreferenciasCoresService.identificar(peca)[0])) if cor != 'sem-preferencia' else ()
        return (socket, *valores, peca.get('benchmark_teste'), peca.get('benchmark_versao'), cores)

    @classmethod
    def domina(cls, melhor, pior, tipo):
        maior = cls.METRICAS[tipo]
        maiores = [(cls.numero(melhor.get(c)), cls.numero(pior.get(c))) for c in maior]
        menores = [(cls.numero(melhor.get(c)), cls.numero(pior.get(c))) for c in ('preco', 'consumo_energia')]
        if any(a is None or b is None for a, b in maiores + menores):
            return False
        if any(a <= 0 or b <= 0 for a, b in maiores) or any(a <= 0 or b <= 0 for a, b in menores):
            return False
        return (all(a >= b for a, b in maiores) and all(a <= b for a, b in menores)
                and (any(a > b for a, b in maiores) or any(a < b for a, b in menores)))

    def pareto(self, pecas, tipo, cor='sem-preferencia'):
        grupos, mantidas = {}, []
        for peca in pecas:
            chave = self.chave_equivalencia(peca, tipo, cor)
            if chave is None:
                mantidas.append(peca)
            else:
                grupos.setdefault(chave, []).append(peca)
        removidas = []
        for grupo in grupos.values():
            for peca in grupo:
                if any(p['id'] != peca['id'] and self.domina(p, peca, tipo) for p in grupo):
                    removidas.append(peca['id'])
                else:
                    mantidas.append(peca)
        return mantidas, sorted(removidas)

    @classmethod
    def ranking(cls, pecas, tipo, prioridade):
        campo = cls.METRICAS[tipo][0]
        medidas, sem_medida = [], []
        for p in pecas:
            pontos = cls.numero(p.get(campo))
            (medidas if pontos is not None and pontos > 0 else sem_medida).append(p)
        def chave(p):
            pontos = cls.numero(p[campo])
            preco = cls.numero(p['preco'])
            criterio = pontos / preco if prioridade == 'custo_beneficio' else pontos
            return (-criterio, preco, int(str(p['id']).split(':')[-1]))
        return sorted(medidas, key=chave) + sorted(sem_medida, key=lambda p: (
            cls.numero(p['preco']), int(str(p['id']).split(':')[-1])))

    @staticmethod
    def faixa(preco, teto):
        proporcao = Decimal(str(preco)) / Decimal(str(teto))
        return 'entrada' if proporcao <= Decimal('0.4') else 'intermediaria' if proporcao <= Decimal('0.7') else 'superior'

    def executar(self, pecas, tipo, prioridade, teto, limite=12, cor='sem-preferencia'):
        pecas, removidas = self.pareto(pecas, tipo, cor)
        principal = self.ranking(pecas, tipo, prioridade)
        secundario = self.ranking(pecas, tipo, 'desempenho' if prioridade == 'custo_beneficio' else 'custo_beneficio')
        escolhidas = {}
        def incluir(p):
            if len(escolhidas) < limite:
                escolhidas.setdefault(p['id'], p)
        if principal:
            incluir(principal[0])
        if tipo == 'processador':
            grupos = {}
            for p in principal:
                socket = normalizar_socket(p.get('soquete'))
                if socket:
                    grupos.setdefault((socket, p.get("videointegrado")), p)
            for p in grupos.values():
                incluir(p)
        for faixa in ('entrada', 'intermediaria', 'superior'):
            p = next((p for p in principal if self.faixa(p['preco'], teto) == faixa), None)
            if p:
                incluir(p)
        if cor != 'sem-preferencia':
            p = next((p for p in principal if PreferenciasCoresService.prioridade(p, cor) <= 1), None)
            if p:
                incluir(p)
        for a, b in zip(principal, secundario):
            incluir(a)
            incluir(b)
        amostra = self.ranking(list(escolhidas.values()), tipo, prioridade)
        return amostra, {'dominadas': removidas, 'elegiveis': len(pecas),
                         'plataformas_elegiveis': sorted({s for p in pecas if (s := normalizar_socket(p.get('soquete')))}),
                         'plataformas_representadas': sorted({s for p in amostra if (s := normalizar_socket(p.get('soquete')))}),
                         'faixas': {f: sum(self.faixa(p['preco'], teto) == f for p in amostra)
                                    for f in ('entrada', 'intermediaria', 'superior')}}
