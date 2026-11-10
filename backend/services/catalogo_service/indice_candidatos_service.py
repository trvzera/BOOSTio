from collections import defaultdict
from types import SimpleNamespace
from copy import deepcopy

from .identidades_para_matching_service import IdentidadesParaMatchingService
from .associacao_inteligente_service import AssociacaoInteligenteService
from .comparar_nomes_service import marca
from .conferir_especificacoes_service import valores
from .normalizar_produto import codigo, gtin


class IndiceCandidatosService:
    def __init__(self, pecas, identidades=None, *, completo=True):
        self.pecas = list(pecas)
        self.comparaveis = []
        self.identidades = identidades or {}
        self.completo = completo
        self.por_marca = defaultdict(set)
        self.por_mpn = defaultdict(set)
        self.por_gtin = defaultdict(set)
        for posicao, peca in enumerate(self.pecas):
            tabela = getattr(peca, '__table__', None)
            dados = ({c.name:deepcopy(getattr(peca, c.name)) for c in tabela.columns
                      if c.name != 'fontes_especificacoes'}
                     if tabela is not None else deepcopy(vars(peca)))
            fonte_codigo = (getattr(peca, 'fontes_especificacoes', None) or {}).get('codigo_modelo_fabricante')
            dados['fontes_especificacoes'] = ({'codigo_modelo_fabricante':deepcopy(fonte_codigo)}
                                             if fonte_codigo else {})
            self.comparaveis.append(SimpleNamespace(**{**dados, '__tablename__':peca.__tablename__}))
            self.por_marca[marca(peca.fabricante)].add(posicao)
            identidade = self.identidades.get(peca.id, {})
            mpn = identidade.get('mpn', getattr(peca, 'part_number', None))
            if mpn:
                self.por_mpn[codigo(mpn)].add(posicao)
            ean = gtin(identidade.get('gtin', getattr(peca, 'gtin', None)))
            if ean:
                self.por_gtin[ean].add(posicao)

    @classmethod
    def carregar(cls, modelo):
        pecas = []
        identidades = {}
        lote = []
        for peca in modelo.iterar_para_matching():
            lote.append(peca)
            if len(lote) == 500:
                identidades.update(IdentidadesParaMatchingService().executar(lote))
                pecas.extend(lote)
                lote = []
        if lote:
            identidades.update(IdentidadesParaMatchingService().executar(lote))
            pecas.extend(lote)
        return cls(pecas, identidades)

    def _posicoes(self, produto):
        if not produto.marca:
            return range(len(self.pecas))
        posicoes = set(self.por_marca.get(marca(produto.marca), ()))
        for mpn in valores(produto.identificadores.get('mpn')):
            posicoes.update(self.por_mpn.get(codigo(mpn), ()))
        for valor in valores(produto.identificadores.get('gtin')):
            ean = gtin(valor)
            if ean:
                posicoes.update(self.por_gtin.get(ean, ()))
        return sorted(posicoes)

    def candidatos(self, produto):
        return [self.pecas[posicao] for posicao in self._posicoes(produto)]

    def avaliar(self, produto):
        candidatos = [self.comparaveis[posicao] for posicao in self._posicoes(produto)]
        decisao = AssociacaoInteligenteService().selecionar(
            candidatos, produto, identidades=self.identidades, completo=self.completo)
        return {**decisao, 'total_catalogo': len(self.pecas),
                'descartados_por_marca': len(self.pecas) - len(candidatos)}
