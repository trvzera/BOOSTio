"""Atalhos para testar a geração sem passar pelo seletor."""
from services.build_service.gerar_candidata_service import gerar_candidata as _gerar_candidata
from services.build_service.pedido_build import montar_pedido


def pedido_teste(orcamento, percentual=0, proprias=None, detalhes=None, rede=None, *, utilidade=None,
                 cor="sem-preferencia", aparencia=None, armazenamento_minimo_gb=None, revisar_investimento=False):
    """Monta o dicionário do pedido direto, sem validar: os testes usam valores fora do formulário."""
    return montar_pedido(utilidade, orcamento, percentual, rede or {}, aparencia or {"cor": cor}, proprias or {},
                         revisar_investimento, armazenamento_minimo_gb=armazenamento_minimo_gb,
                         detalhes_proprias=detalhes or {})


def gerar_candidata(usuario_id, prompt, modelo, catalogo, orcamento, percentual, proprias, detalhes, rede,
                    tentativas_correcao=1, *, catalogo_reparo=None, plano_perifericos=None, **pedido):
    preparado = {"catalogo": catalogo, "catalogo_reparo": catalogo if catalogo_reparo is None else catalogo_reparo,
                 "prompt": prompt, "plano_perifericos": plano_perifericos}
    return _gerar_candidata(usuario_id, pedido_teste(orcamento, percentual, proprias, detalhes, rede, **pedido),
                            preparado, modelo, tentativas_correcao)
