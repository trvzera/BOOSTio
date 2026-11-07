"""Preço, disponibilidade e link da peça são lidos da melhor oferta ativa; nada disso é gravado na peça.

A melhor oferta é a mais barata entre as ativas, preferindo as disponíveis, depois as de estoque
desconhecido e por último as esgotadas. Ofertas do Mercado Livre e da Shopee só são
gravadas pela associação revisada, que as desativa quando a identidade deixa de valer.
"""
from sqlalchemy import Float, case, cast, select
from sqlalchemy.orm import column_property

from . import Peca, Oferta


def _da_melhor_oferta(modelo, coluna, *, so_kabum=False):
    filtros = [Oferta.tabela_peca == modelo.__tablename__, Oferta.peca_id == modelo.id, Oferta.ativa.is_(True)]
    if so_kabum:
        filtros += [Oferta.loja == 'kabum', Oferta.url != '']
    # Disponível, depois estoque desconhecido, depois esgotado; dentro de cada grupo, o mais barato.
    disponibilidade = case((Oferta.esgotado.is_(False), 0), (Oferta.esgotado.is_(None), 1), else_=2)
    ordem = (disponibilidade, Oferta.preco.is_(None), Oferta.preco, Oferta.id)
    return (select(coluna).where(*filtros).order_by(*ordem).limit(1)
            .correlate(modelo).scalar_subquery())


def instalar_precos_derivados():
    for modelo in _modelos(Peca):
        modelo.preco = column_property(cast(_da_melhor_oferta(modelo, Oferta.preco), Float), deferred=False)
        modelo.esgotado = column_property(_da_melhor_oferta(modelo, Oferta.esgotado), deferred=False)
        modelo.preco_atualizado_em = column_property(_da_melhor_oferta(modelo, Oferta.preco_atualizado_em))
        modelo.kabum_external = column_property(_da_melhor_oferta(modelo, Oferta.url, so_kabum=True))


def _modelos(base):
    for filho in base.__subclasses__():
        if getattr(filho, '__tablename__', None):
            yield filho
        yield from _modelos(filho)
