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
        from utils.identidade_peca import assinatura_catalogo
        cache_valido = (ficha.get('normalizado')
            and ficha.get('normalizacao_versao') == NormalizarProdutoService.VERSAO
            and ficha.get('assinatura_catalogo') == assinatura_catalogo(produto))
        if cache_valido:
            p = ProdutoNormalizado(**ficha['normalizado'])
        else:
            p = NormalizarProdutoService().executar(produto,pendencia.categoria_sugerida)
            if ficha.get('normalizado'):
                from services.catalogo_service.consultar_base_hardware_service import ConsultarBaseHardwareService
                p = ConsultarBaseHardwareService().executar(p)['produto']
        titulo=(bruto.get('anuncio') or {}).get('title')
        return (p,replace(p,titulo=titulo)) if titulo and titulo != p.titulo else (p,)
