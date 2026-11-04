"""Ligação do adaptador Mercado Livre com a classificação compartilhada."""
from dataclasses import replace
from services.catalogo_service.classificar_pendencias_service import ClassificarPendenciasService as ClassificarCatalogoService
from .normalizar_produto_service import NormalizarProdutoService


class ClassificarPendenciasService(ClassificarCatalogoService):
    def __init__(self):super().__init__(normalizador=self.normalizar)

    @staticmethod
    def normalizar(pendencia):
        if pendencia.loja!='mercado_livre':return ClassificarCatalogoService.normalizar_interno(pendencia)
        bruto=pendencia.dados_originais
        produto=(pendencia.evidencias or {}).get('enriquecimento',{}).get('produto') or bruto.get('catalogo') or bruto.get('anuncio') or {}
        ficha=(pendencia.evidencias or {}).get('enriquecimento',{})
        from services.catalogo_service.produto_normalizado import ProdutoNormalizado
        p=ProdutoNormalizado(**ficha['normalizado']) if ficha.get('normalizado') else NormalizarProdutoService().executar(produto,pendencia.categoria_sugerida)
        titulo=(bruto.get('anuncio') or {}).get('title')
        return (p,replace(p,titulo=titulo)) if titulo else (p,)
