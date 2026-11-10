from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from models import db, Oferta, HistoricoOferta
from utils.medidas_fisicas import produto_kabum

LOJA = 'kabum'


def buscar_ativa(peca, *, bloquear=False):
    consulta = Oferta.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id, loja=LOJA, ativa=True)
    consulta = consulta.order_by(Oferta.id.desc())
    return (consulta.populate_existing().with_for_update() if bloquear else consulta).first()


def definir_link(peca, url):
    url = (url or '').strip() or None
    atual = buscar_ativa(peca, bloquear=True)
    if atual is not None and atual.url == url:
        return atual
    if atual is not None:
        atual.ativa = False
    if url is None:
        return None
    produto = produto_kabum(url)
    if produto is None:
        raise ValueError('Informe um link HTTPS de produto da KaBuM')
    existente = Oferta.query.filter_by(loja=LOJA, produto_id_loja=produto).with_for_update().first()
    if existente is not None:
        if (existente.tabela_peca, existente.peca_id) != (peca.__tablename__, peca.id):
            raise ValueError('Anúncio KaBuM já pertence a outra peça')
        existente.ativa, existente.url = True, url
        existente.preco, existente.esgotado = None, None
        existente.preco_atualizado_em = existente.consultado_em = None
        return existente
    oferta = Oferta(tabela_peca=peca.__tablename__, peca_id=peca.id, loja=LOJA, produto_id_loja=produto,
                    vendedor_id='', url=url, preco=None, esgotado=None)
    db.session.add(oferta)
    db.session.flush()
    return oferta


def gravar_cotacao_inicial(peca, url, preco, esgotado, atualizado_em):
    oferta = definir_link(peca, url)
    if oferta is None:
        return None
    oferta.preco = _decimal(preco) if preco else None
    oferta.esgotado = esgotado if oferta.preco is not None or esgotado else None
    oferta.preco_atualizado_em = atualizado_em if oferta.preco is not None else None
    oferta.consultado_em = oferta.preco_atualizado_em
    return oferta


def validar_cotacao(resultado):
    if type(resultado.get('esgotado')) is not bool:
        raise ValueError('Disponibilidade inválida na cotação')
    preco = resultado.get('preco')
    if preco is None:
        if not resultado['esgotado']:
            raise ValueError('Produto disponível sem preço na cotação')
        return {'preco': None, 'esgotado': True}
    if isinstance(preco, bool):
        raise ValueError('Preço inválido na cotação')
    try:
        preco = _decimal(preco)
    except ValueError:
        raise ValueError('Preço inválido na cotação') from None
    if not preco.is_finite() or not 0 < preco < Decimal('1000000000000'):
        raise ValueError('Preço inválido na cotação')
    return {'preco': preco, 'esgotado': resultado['esgotado']}


def aplicar_cotacao(oferta, resultado, instante):
    preco_alterado = False
    if resultado['preco'] is not None:
        novo = _decimal(resultado['preco'])
        if novo != oferta.preco:
            oferta.preco = novo
            oferta.preco_atualizado_em = instante
            preco_alterado = True
    estoque_alterado = oferta.esgotado != resultado['esgotado']
    if estoque_alterado:
        oferta.esgotado = resultado['esgotado']
    oferta.consultado_em = instante
    if oferta.preco is not None:
        _registrar_historico(oferta, instante)
    return {'preco_alterado': preco_alterado, 'estoque_alterado': estoque_alterado}


def _registrar_historico(oferta, instante):
    ultimo = HistoricoOferta.ultimo(oferta.id, bloquear=True)
    if (ultimo is None or ultimo.preco != oferta.preco or ultimo.esgotado != oferta.esgotado
            or ultimo.coletado_em.date() != instante.date()):
        db.session.add(HistoricoOferta(oferta_id=oferta.id, preco=oferta.preco,
                                       esgotado=oferta.esgotado, coletado_em=instante))


def _decimal(valor):
    try:
        return Decimal(str(valor)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        raise ValueError('Preço inválido') from None
