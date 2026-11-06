"""Reavalia completude técnica, sem mudar status de identidade, oferta ou preço."""
from collections import Counter
from repositories.reavaliacao_montagem_repository import RepositorioReavaliacaoMontagem


class ReavaliarMontagemService:
    def __init__(self,repositorio=None):self.repositorio=repositorio or RepositorioReavaliacaoMontagem()

    def executar(self,*,simular=True,tamanho_lote=250):
        if type(simular) is not bool or type(tamanho_lote) is not int or not 1<=tamanho_lote<=1000:raise ValueError('Opções inválidas')
        r=dict(simulacao=simular,analisadas=0,minimos_atendidos=0,pendentes=0,indicadores_alterados=0,categorias={},pendencias={})
        total=Counter()
        for categoria in self.repositorio.categorias():
            depois=0;cat=Counter()
            while True:
                lote=self.repositorio.executar_lote(categoria,depois,tamanho_lote,simular=simular)
                for k in ('analisadas','minimos_atendidos','pendentes','indicadores_alterados'):r[k]+=lote[k];cat[k]+=lote[k]
                total.update(lote['pendencias'])
                if lote['lidas']<tamanho_lote:break
                depois=lote['ultimo_id']
            if cat['analisadas']:r['categorias'][categoria]=dict(cat)
        r['pendencias']=dict(total)
        return r
