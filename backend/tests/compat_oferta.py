"""Só para testes: permite montar peças com preco/esgotado/kabum_external e grava a oferta da KaBuM.

Em produção esses campos não existem na peça; os testes antigos os usam para preparar cenários.
Cada atribuição vira uma gravação na tabela oferta quando a sessão faz flush.
"""
import zlib
from datetime import datetime, timezone

from sqlalchemy import event, insert, select, update
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified, set_committed_value

from models import Peca, Oferta
from models.medidas_fisicas import produto_kabum

CAMPOS = Peca.CAMPOS_DA_OFERTA
_original_setattr = Peca.__setattr__
_instalado = False


def _init(alvo, args, kwargs):
    pendentes = {c: kwargs.pop(c) for c in CAMPOS if c in kwargs}
    if pendentes:
        alvo.__dict__['_legado_oferta'] = pendentes
        for campo, valor in pendentes.items():
            set_committed_value(alvo, campo, valor)


def _setattr(self, nome, valor):
    if nome in CAMPOS:
        self.__dict__.setdefault('_legado_oferta', {})[nome] = valor
        set_committed_value(self, nome, valor)
        if self.__dict__.get('_sa_instance_state') is not None and self.id is not None:
            try:
                flag_modified(self, 'fabricante')
            except Exception:
                pass
        return
    _original_setattr(self, nome, valor)


def _sintetico(tabela, peca_id):
    return str(zlib.crc32(tabela.encode()) % 900 + 100) + f'{peca_id:07d}'


def _gravar(session, peca):
    pendentes = peca.__dict__.pop('_legado_oferta', None)
    if not pendentes:
        return
    conexao = session.connection()
    tabela = Oferta.__table__
    atual = conexao.execute(select(tabela).where(
        tabela.c.tabela_peca == peca.__tablename__, tabela.c.peca_id == peca.id,
        tabela.c.loja == 'kabum', tabela.c.ativa.is_(True)).order_by(tabela.c.id.desc())).mappings().first()
    campos = {}
    if 'kabum_external' in pendentes:
        url = pendentes['kabum_external'] or ''
        produto = produto_kabum(url) or _sintetico(peca.__tablename__, peca.id)
        campos.update(url=url, produto_id_loja=produto)
    if 'preco' in pendentes:
        preco = pendentes['preco']
        campos['preco'] = preco if preco and preco > 0 else None
    if 'esgotado' in pendentes:
        campos['esgotado'] = pendentes['esgotado']
    if 'preco_atualizado_em' in pendentes:
        campos['preco_atualizado_em'] = pendentes['preco_atualizado_em']
        campos['consultado_em'] = pendentes['preco_atualizado_em']
    if atual is None:
        campos.setdefault('url', '')
        campos.setdefault('produto_id_loja', _sintetico(peca.__tablename__, peca.id))
        campos.setdefault('esgotado', False)
        if campos.get('preco') is None and campos['esgotado'] is False:
            campos['esgotado'] = None
        if campos.get('preco') is not None and 'preco_atualizado_em' not in pendentes:
            campos['preco_atualizado_em'] = None
        conexao.execute(insert(tabela).values(tabela_peca=peca.__tablename__, peca_id=peca.id,
                                              loja='kabum', vendedor_id='', ativa=True, **campos))
    else:
        if campos.get('preco') is None and 'preco' in campos and atual['esgotado'] is False and 'esgotado' not in campos:
            campos['esgotado'] = None
        if campos.get('preco', atual['preco']) is None and campos.get('esgotado', atual['esgotado']) is False:
            campos['esgotado'] = None
        conexao.execute(update(tabela).where(tabela.c.id == atual['id']).values(**campos))
    session.info.setdefault('legado_expirar', []).append(peca)


def _depois_do_flush(session, contexto):
    for objeto in list(session.new) + list(session.dirty):
        if isinstance(objeto, Peca) and objeto.__dict__.get('_legado_oferta'):
            _gravar(session, objeto)


def _expirar(session, contexto):
    for peca in session.info.pop('legado_expirar', []):
        session.expire(peca, list(CAMPOS))


def instalar():
    global _instalado
    if _instalado:
        return
    event.listen(Peca, 'init', _init, propagate=True)
    Peca.__setattr__ = _setattr
    event.listen(Session, 'after_flush', _depois_do_flush)
    event.listen(Session, 'after_flush_postexec', _expirar)
    _instalado = True
