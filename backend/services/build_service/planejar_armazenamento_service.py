"""Menor custo de capacidade entre um modelo SSD e um HD, até 64 de cada.

É uma estimativa de preço/capacidade; portas, baias e interfaces são validadas depois.
"""
from decimal import Decimal


class PlanejarArmazenamentoService:
    LIMITE_UNIDADES = 64

    @staticmethod
    def _fronteira(pecas):
        # Somente para estimar custo de capacidade, não para remover peças do catálogo.
        validas = [p for p in pecas if type(p.get('capacidade_gb')) is int and p['capacidade_gb'] > 0]
        validas.sort(key=lambda p: (Decimal(str(p['preco'])), -p['capacidade_gb'], str(p['id'])))
        fronteira, maior = [], 0
        for p in validas:
            if p['capacidade_gb'] > maior:
                fronteira.append(p)
                maior = p['capacidade_gb']
        return fronteira

    def executar(self, pools, minimo):
        grupos = {tipo: self._fronteira(pools.get(tipo, [])) for tipo in ('ssd', 'hd')}
        melhor = None

        def considerar(itens):
            nonlocal melhor
            custo = sum((Decimal(str(p['preco'])) * qtd for _, p, qtd in itens), Decimal(0))
            capacidade = sum(p['capacidade_gb'] * qtd for _, p, qtd in itens)
            chave = (custo, sum(qtd for _, _, qtd in itens), tuple((tipo, str(p['id']), qtd) for tipo, p, qtd in itens))
            if melhor is None or chave < melhor[0]:
                melhor = (chave, {'custo': float(custo), 'capacidade_total_gb': capacidade,
                                  'itens': [{'tipo': tipo, 'peca': p, 'quantidade': qtd} for tipo, p, qtd in itens]})

        for tipo, pecas in grupos.items():
            for p in pecas:
                qtd = (minimo + p['capacidade_gb'] - 1) // p['capacidade_gb']
                if 1 <= qtd <= self.LIMITE_UNIDADES:
                    considerar([(tipo, p, qtd)])
        for ssd in grupos['ssd']:
            max_ssds = min(self.LIMITE_UNIDADES, (minimo - 1) // ssd['capacidade_gb'])
            for hd in grupos['hd']:
                for qtd_ssd in range(1, max_ssds + 1):
                    restante = minimo - qtd_ssd * ssd['capacidade_gb']
                    qtd_hd = (restante + hd['capacidade_gb'] - 1) // hd['capacidade_gb']
                    if 1 <= qtd_hd <= self.LIMITE_UNIDADES:
                        considerar([('ssd', ssd, qtd_ssd), ('hd', hd, qtd_hd)])
        return melhor[1] if melhor else None
