from decimal import Decimal
from math import isfinite


class RequisitosArmazenamentoService:
    @staticmethod
    def validar_parametro(valor):
        if valor is None:
            return None
        if type(valor) is not int or not 1 <= valor <= 1000000:
            raise ValueError("O armazenamento mínimo deve ser um inteiro de 1 a 1.000.000 GB")
        return valor

    @classmethod
    def validar_build(cls, build, catalogo, minimo, proprias=None, detalhes_proprias=None):
        minimo = cls.validar_parametro(minimo)
        if minimo is None:
            return
        pecas = {(tipo, p['id']): p for tipo in ('ssd', 'hd') for p in catalogo.get(tipo, [])}
        total, desconhecido = Decimal(0), False
        for item in build['componentes']:
            if item['tipo'] not in ('ssd', 'hd'):
                continue
            peca = pecas.get((item['tipo'], item['id']), {})
            capacidade = cls._capacidade(peca.get('capacidade_gb'))
            if capacidade is None:
                desconhecido = True
            else:
                total += capacidade * item.get('quantidade', 1)
        for tipo in ('ssd', 'hd'):
            if tipo not in (proprias or {}):
                continue
            dados = (detalhes_proprias or {}).get(tipo, {}).get('especificacoes_confirmadas', {})
            capacidade = cls._capacidade(dados.get('capacidade_gb'))
            if capacidade is None:
                desconhecido = True
            else:
                total += capacidade
        if total >= minimo:
            return
        if desconhecido:
            raise ValueError(f"A configuração sugerida não permite confirmar o armazenamento mínimo de {minimo} GB: "
                             f"há peças sem capacidade cadastrada; total confirmado: {total:g} GB.")
        raise ValueError(f"A configuração sugerida não atende ao armazenamento mínimo: solicitado {minimo} GB, "
                         f"selecionado {total:g} GB. Selecione armazenamento suficiente respeitando o teto de gasto.")

    @staticmethod
    def _capacidade(valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float, Decimal)):
            return None
        if not isfinite(valor) or valor <= 0:
            return None
        return Decimal(str(valor))
