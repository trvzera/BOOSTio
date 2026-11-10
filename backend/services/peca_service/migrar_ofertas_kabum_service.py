"""Copia preço, estoque e link da KaBuM das tabelas de peças para a tabela oferta.

As colunas antigas não são alteradas nem apagadas: ficam como cópia de segurança até a fase 2.
Repetir o comando não duplica ofertas nem sobrescreve cotações mais novas já gravadas na oferta.
"""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import inspect, text

from models import db, Oferta, HistoricoOferta
from utils.medidas_fisicas import produto_kabum
from models.modelos_pecas import MODELOS_PECAS

COLUNAS_ANTIGAS = {'kabum_external', 'preco', 'esgotado', 'preco_atualizado_em'}


class MigrarOfertasKabumService:
    def executar(self, *, simular=True):
        if not simular:
            for modelo in (Oferta, HistoricoOferta):
                modelo.__table__.create(db.engine, checkfirst=True)
        resumo = {'simulacao': simular, 'criadas': 0, 'atualizadas': 0, 'inalteradas': 0,
                  'sem_link': 0, 'link_invalido': 0, 'conflitos': [], 'historicos': 0}
        inspetor = inspect(db.engine)
        # Verificado uma vez, fora da transação: consultar o esquema no meio dela pode descartá-la.
        self.historico_antigo = inspetor.has_table('historico_preco')
        if not simular and db.engine.dialect.name == 'mysql':
            self._tornar_colunas_antigas_opcionais(inspetor)
        tabelas = [m.__tablename__ for m in MODELOS_PECAS if inspetor.has_table(m.__tablename__)
                   and COLUNAS_ANTIGAS <= {c['name'] for c in inspetor.get_columns(m.__tablename__)}]
        for tabela in tabelas:
            nome = db.engine.dialect.identifier_preparer.quote(tabela)
            for linha in db.session.execute(text(
                    f'SELECT id, kabum_external, preco, esgotado, preco_atualizado_em FROM {nome}')).mappings().all():
                self._migrar_peca(tabela, linha, resumo, simular)
        if simular:
            db.session.rollback()
        else:
            db.session.commit()
        return resumo

    @staticmethod
    def comandos_colunas_opcionais(dialeto, tabela, colunas):
        """ALTER TABLE para as colunas antigas ainda NOT NULL: peças novas não as preenchem mais."""
        nome = dialeto.identifier_preparer.quote(tabela)
        return [f'ALTER TABLE {nome} MODIFY {dialeto.identifier_preparer.quote(c["name"])} {c["type"].compile(dialect=dialeto)} NULL'
                for c in colunas if c['name'] in COLUNAS_ANTIGAS and not c['nullable']]

    def _tornar_colunas_antigas_opcionais(self, inspetor):
        for modelo in MODELOS_PECAS:
            if not inspetor.has_table(modelo.__tablename__):
                continue
            for comando in self.comandos_colunas_opcionais(
                    db.engine.dialect, modelo.__tablename__, inspetor.get_columns(modelo.__tablename__)):
                db.session.execute(text(comando))

    def _migrar_peca(self, tabela, linha, resumo, simular):
        url = (linha['kabum_external'] or '').strip()
        if not url:
            resumo['sem_link'] += 1
            return
        produto = produto_kabum(url)
        if produto is None:
            resumo['link_invalido'] += 1
            return
        preco = _preco(linha['preco'])
        esgotado = None if linha['esgotado'] is None else bool(linha['esgotado'])
        if preco is None and esgotado is False:
            esgotado = None
        atualizado = _data(linha['preco_atualizado_em']) if preco is not None else None
        oferta = Oferta.buscar_por_anuncio('kabum', produto)
        if oferta is not None and (oferta.tabela_peca, oferta.peca_id) != (tabela, linha['id']):
            resumo['conflitos'].append(f'{tabela}:{linha["id"]} -> anúncio {produto} pertence a {oferta.tabela_peca}:{oferta.peca_id}')
            return
        if oferta is None:
            resumo['criadas'] += 1
            if not simular:
                oferta = Oferta(tabela_peca=tabela, peca_id=linha['id'], loja='kabum',
                                produto_id_loja=produto, vendedor_id='', url=url, preco=preco,
                                esgotado=esgotado, preco_atualizado_em=atualizado, consultado_em=atualizado)
                db.session.add(oferta)
                db.session.flush()
        elif oferta.preco is None and preco is not None:
            resumo['atualizadas'] += 1
            if not simular:
                oferta.preco, oferta.esgotado = preco, esgotado
                oferta.preco_atualizado_em = oferta.consultado_em = atualizado
                oferta.ativa = True
        else:
            resumo['inalteradas'] += 1
        if not simular and oferta is not None:
            resumo['historicos'] += self._copiar_historico(tabela, linha['id'], produto, oferta)

    def _copiar_historico(self, tabela, peca_id, produto, oferta):
        if not self.historico_antigo:
            return 0
        copiados = 0
        for obs in db.session.execute(text(
                'SELECT preco, esgotado, coletado_em FROM historico_preco WHERE tabela_peca=:t AND peca_id=:p '
                "AND loja='kabum' AND produto_id_loja=:a AND preco IS NOT NULL ORDER BY coletado_em, id"),
                {'t': tabela, 'p': peca_id, 'a': produto}).mappings():
            coletado = _data(obs['coletado_em'])
            if not HistoricoOferta.existe_coleta(oferta.id, coletado):
                db.session.add(HistoricoOferta(oferta_id=oferta.id, preco=_preco(obs['preco']),
                                               esgotado=None if obs['esgotado'] is None else bool(obs['esgotado']),
                                               coletado_em=coletado))
                copiados += 1
        return copiados


def _preco(valor):
    try:
        preco = Decimal(str(valor)).quantize(Decimal('0.01')) if valor is not None else None
    except InvalidOperation:
        return None
    return preco if preco is not None and preco > 0 else None


def _data(valor):
    if isinstance(valor, datetime) or valor is None:
        return valor
    return datetime.fromisoformat(str(valor))
