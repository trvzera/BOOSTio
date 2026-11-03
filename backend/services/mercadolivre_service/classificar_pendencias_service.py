"""Aplica o comparador à fila sem criar peças ou publicar ofertas."""
from sqlalchemy.exc import SQLAlchemyError
from models import ProdutoPendente, IdentidadeFabricante
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_documento
from .comparar_produtos_service import CompararProdutosService


class ClassificarPendenciasService:
    def executar(self, *, limite=20, depois_id=0, simular=True):
        if type(limite) is not int or not 1 <= limite <= 200:
            raise ValueError('Limite entre 1 e 200 pendências')
        modelos = {c.__tablename__:c for c in MODELOS_PECAS}
        pools = {}
        resumo = dict(simulacao=simular, confirmadas=0, ambiguas=0, rejeitadas=0, falhas=0, detalhes=[])
        for pendencia in ProdutoPendente.listar_para_revisao(depois_id, limite):
            try:
                categoria = pendencia.categoria_sugerida
                if categoria not in modelos:
                    raise ValueError('Categoria requer revisão')
                if categoria not in pools:
                    pecas = modelos[categoria].pool_para_matching(2001)
                    pools[categoria] = (pecas[:2000], IdentidadeFabricante.para_matching(pecas[:2000]), len(pecas) <= 2000)
                pecas, identidades, completo = pools[categoria]
                bruto = pendencia.dados_originais
                produto = bruto.get('catalogo') or bruto.get('anuncio') or {}
                decisao = CompararProdutosService().selecionar(pecas, produto, identidades=identidades, completo=completo)
                # O título do anúncio pode divergir do catálogo: nunca ignorá-lo.
                anuncio = bruto.get('anuncio', {})
                if anuncio.get('title') and produto is not anuncio:
                    titulo = CompararProdutosService().selecionar(pecas, {**produto, 'name':anuncio['title']}, identidades=identidades, completo=completo)
                    if titulo['classificacao'] != 'confirmada' or titulo['peca'] != decisao['peca']:
                        decisao = titulo
                ProdutoPendente.registrar_matching(pendencia.id, decisao, assinatura_documento(bruto), simular=simular)
                resumo[{'confirmada':'confirmadas','ambigua':'ambiguas','rejeitada':'rejeitadas'}[decisao['classificacao']]] += 1
                resumo['detalhes'].append(dict(pendencia_id=pendencia.id, **decisao))
            except (ValueError, SQLAlchemyError):
                resumo['falhas'] += 1
                resumo['detalhes'].append(dict(pendencia_id=pendencia.id, erro='Falha de classificação; revise categoria, esquema e dados'))
        return resumo
