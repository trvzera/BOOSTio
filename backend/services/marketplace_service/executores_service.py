"""Adaptadores administrativos pequenos; matching e persistência continuam existentes."""
from services.mercadolivre_service.atualizar_ofertas_service import AtualizarOfertasMercadoLivreService
from .controle_requisicoes_service import controle_em_execucao


def atualizar_ofertas_mercado_livre(dados):
    permitidos = {'categoria', 'peca_id', 'simular', 'limite_ofertas'}
    if set(dados) - permitidos or not {'categoria', 'peca_id'} <= dados.keys():
        raise ValueError('Parâmetros de ofertas inválidos')
    resultado = AtualizarOfertasMercadoLivreService().executar(**dados, limite_pecas=1)
    controle = controle_em_execucao.get()
    if controle and controle.erro is not None:
        raise controle.erro
    if resultado.get('falhas') or resultado.get('interrompido'):
        raise ValueError('Atualização não concluída; confira esquema ou autorização')
    return resultado


def executores_disponiveis():
    from services.shopee_service.processar_ofertas_service import ProcessarOfertasShopeeService
    return {('mercado_livre', 'ofertas'): atualizar_ofertas_mercado_livre,
            ('shopee', 'ofertas'): lambda dados: ProcessarOfertasShopeeService().ofertas_peca(**dados),
            ('shopee', 'descoberta'): descobrir_shopee,
            ('shopee', 'importacao'): lambda dados: ProcessarOfertasShopeeService().importar_anuncio(**dados)}


def descobrir_shopee(dados):
    from .processar_fila_service import ProcessarFilaMarketplaceService
    from services.shopee_service.processar_ofertas_service import ProcessarOfertasShopeeService
    parametros = dict(dados)
    execucao = parametros.pop('execucao')
    paginas = parametros.pop('max_paginas')
    importar = parametros.pop('importar', False)
    novos = parametros.pop('permitir_novos', False)
    resultado = ProcessarOfertasShopeeService().descobrir_pagina(**parametros)
    fila = ProcessarFilaMarketplaceService(executores_disponiveis())
    if importar and not parametros['simular']:
        for anuncio in resultado['anuncios']:
            fila.enfileirar('shopee', 'importacao', dict(anuncio_id=anuncio,
                simular=False, permitir_novos=novos), execucao=execucao)
    if resultado['pagina']['hasNextPage'] and parametros['pagina'] < paginas:
        fila.enfileirar('shopee', 'descoberta', {**dados, 'pagina': parametros['pagina']+1}, execucao=execucao)
    return resultado
