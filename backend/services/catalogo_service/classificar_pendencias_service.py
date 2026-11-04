"""Classifica qualquer loja usando produtos normalizados e models compartilhados."""
from sqlalchemy.exc import SQLAlchemyError
from models import ProdutoPendente,IdentidadeFabricante
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_documento
from .produto_normalizado import ProdutoNormalizado
from .associacao_inteligente_service import AssociacaoInteligenteService


class ClassificarPendenciasService:
    def __init__(self,normalizador=None):
        self.normalizador=normalizador or self.normalizar_interno

    @staticmethod
    def normalizar_interno(pendencia):
        dados=pendencia.dados_originais.get('normalizado')
        if not isinstance(dados,dict):raise ValueError('A loja precisa de um adaptador para o formato comum')
        produto=ProdutoNormalizado(**dados)
        if produto.loja!=pendencia.loja:raise ValueError('Loja divergente')
        return (produto,)

    def executar(self,*,limite=20,depois_id=0,categoria=None,simular=True):
        if type(limite) is not int or not 1<=limite<=200:raise ValueError('Limite entre 1 e 200 pendências')
        modelos={m.__tablename__:m for m in MODELOS_PECAS};pools={}
        resumo=dict(simulacao=simular,confirmadas=0,ambiguas=0,rejeitadas=0,falhas=0,detalhes=[])
        for p in ProdutoPendente.listar_para_revisao(depois_id,limite,categoria):
            try:
                cat=p.categoria_sugerida
                if cat not in modelos:raise ValueError('Categoria precisa de revisão')
                if cat not in pools:
                    todos=modelos[cat].pool_para_matching(2001);pecas=todos[:2000]
                    pools[cat]=(pecas,IdentidadeFabricante.para_matching(pecas),len(todos)<=2000)
                pecas,ids,completo=pools[cat]
                decisoes=[AssociacaoInteligenteService().selecionar(pecas,produto,identidades=ids,completo=completo) for produto in self.normalizador(p)]
                if not decisoes:raise ValueError('Nenhum produto normalizado')
                decisao=min(decisoes,key=lambda d:d['percentual'])
                if len({d['peca'] for d in decisoes if d['classificacao']=='confirmada'})>1:
                    decisao={**decisao,'classificacao':'ambigua','percentual':80,'peca':None,'criterio':None,'motivo':'Título e ficha apontam para peças diferentes'}
                ProdutoPendente.registrar_matching(p.id,decisao,assinatura_documento(p.dados_originais),simular=simular)
                resumo[{'confirmada':'confirmadas','ambigua':'ambiguas','rejeitada':'rejeitadas'}[decisao['classificacao']]]+=1
                resumo['detalhes'].append(dict(pendencia_id=p.id,**decisao))
            except (ValueError,TypeError,SQLAlchemyError):
                resumo['falhas']+=1;resumo['detalhes'].append(dict(pendencia_id=p.id,erro='Falha de normalização ou classificação; revise adaptador e dados'))
        return resumo
