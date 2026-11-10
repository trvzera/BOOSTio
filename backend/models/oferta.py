"""Anúncio de uma loja vinculado a uma peça; valores monetários em BRL."""
from . import db, ModeloBase
from utils.medidas_fisicas import produto_kabum
from .modelos_pecas import MODELOS_PECAS
from utils.url_shopee import validar_url_shopee


class Oferta(ModeloBase):
    __tablename__ = "oferta"

    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    loja = db.Column(db.String(20), nullable=False)
    produto_id_loja = db.Column(db.String(80), nullable=False)
    vendedor_id = db.Column(db.String(80), nullable=False, default="")
    vendedor_nome = db.Column(db.String(120), nullable=True)
    url = db.Column(db.Text, nullable=False)
    url_afiliado = db.Column(db.Text, nullable=True, default=None)

    preco = db.Column(db.Numeric(14, 2), nullable=True)
    condicao_pagamento = db.Column(db.String(120), nullable=True)
    esgotado = db.Column(db.Boolean, nullable=True)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    preco_atualizado_em = db.Column(db.DateTime, nullable=True)
    consultado_em = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("loja", "produto_id_loja", name="uq_oferta_loja_produto"),
        db.CheckConstraint("peca_id > 0", name="ck_oferta_peca_positiva"),
        db.CheckConstraint("preco IS NULL OR preco > 0", name="ck_oferta_preco_positivo"),
        db.CheckConstraint("esgotado IS NULL OR esgotado = 1 OR preco IS NOT NULL", name="ck_oferta_disponivel_com_preco"),
        db.Index("ix_oferta_publicacao", "tabela_peca", "peca_id", "ativa", "preco"),
        db.Index("ix_oferta_peca", "tabela_peca", "peca_id"),
        db.Index("ix_oferta_coleta", "loja", "ativa", "consultado_em"),
    )

    @classmethod
    def buscar_por_anuncio(cls, loja, produto_id_loja, *, bloquear=False, recarregar=False):
        consulta = cls.query.filter_by(loja=loja, produto_id_loja=produto_id_loja)
        if recarregar:
            consulta = consulta.populate_existing()
        return (consulta.with_for_update() if bloquear else consulta).first()

    @classmethod
    def buscar_unica_por_anuncio(cls, loja, produto_id_loja):
        return cls.query.filter_by(loja=loja, produto_id_loja=produto_id_loja).one()

    @classmethod
    def listar_da_peca(cls, peca, loja, *, apenas_ativas=False, bloquear=False, recarregar=False):
        consulta = cls.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id, loja=loja)
        if apenas_ativas:
            consulta = consulta.filter_by(ativa=True)
        if recarregar:
            consulta = consulta.populate_existing()
        return (consulta.with_for_update() if bloquear else consulta).all()

    @classmethod
    def corresponde_origem(cls, peca, loja, identificador, *, bloquear=False):
        consulta = cls.query.filter_by(loja=loja, produto_id_loja=identificador)
        registro = (consulta.with_for_update() if bloquear else consulta).first()
        return bool(registro and (registro.tabela_peca, registro.peca_id) == (peca.__tablename__, peca.id))

    @classmethod
    def identidades_kabum_ambiguas(cls):
        from sqlalchemy import inspect
        from collections import defaultdict
        import re
        encontrados = defaultdict(set)
        inspetor = inspect(db.engine)
        if not inspetor.has_table(cls.__tablename__) or not set(cls.__table__.columns.keys()) <= {
                c['name'] for c in inspetor.get_columns(cls.__tablename__)}:
            raise ValueError('Prepare as tabelas com catalogo-preparar antes de separar identificadores')
        for modelo in MODELOS_PECAS:
            if not inspetor.has_table(modelo.__tablename__):
                continue
            for ident, link, referencia, numero in modelo.query.with_entities(
                    modelo.id, modelo.kabum_external, modelo.referencia_interna, modelo.part_number).all():
                legado = re.fullmatch(r'KABUM-([1-9][0-9]*)', referencia or numero or '', re.I)
                codigo = produto_kabum(link) or (legado[1] if legado else None)
                if codigo:
                    encontrados[codigo].add((modelo.__tablename__, ident))
        return {codigo for codigo, pecas in encontrados.items() if len(pecas) > 1}

    @classmethod
    def registrar_identidade_kabum(cls, peca, *, simular=False, ids_ambiguos=None):
        """Registra o ID real do anúncio. Não inventa cotação nem estoque da seed."""
        import re
        referencia = peca.referencia_interna or peca.part_number or ''
        legado = re.fullmatch(r'KABUM-([1-9][0-9]*)', referencia, re.I)
        identificador = produto_kabum(peca.kabum_external)
        if legado and identificador and legado[1] != identificador:
            raise ValueError('ID KaBuM diverge do link; exige revisão')
        identificador = identificador or (legado[1] if legado else None)
        if identificador is None:
            return 'sem_anuncio'
        atual = cls.query.filter_by(loja='kabum', produto_id_loja=identificador).with_for_update().first()
        if atual:
            if (atual.tabela_peca, atual.peca_id) != (peca.__tablename__, peca.id):
                raise ValueError('Anúncio KaBuM já pertence a outra peça')
            return 'inalterada'
        if ids_ambiguos is not None and identificador in ids_ambiguos:
            raise ValueError('Mais de uma peça referencia o mesmo anúncio KaBuM; revisar duplicidade')
        if simular:
            return 'criada'
        cls_url = peca.kabum_external if produto_kabum(peca.kabum_external) else f'https://www.kabum.com.br/produto/{identificador}'
        db.session.add(cls(tabela_peca=peca.__tablename__, peca_id=peca.id, loja='kabum',
            produto_id_loja=identificador, vendedor_id='', url=cls_url,
            preco=None, esgotado=None, preco_atualizado_em=None, consultado_em=None))
        db.session.flush()
        return 'criada'


    @classmethod
    def verificar_esquema_mercado_livre(cls):
        from sqlalchemy import inspect
        from . import VinculoMercadoLivre, HistoricoOferta, TokenIntegracao, ControleColeta
        inspetor = inspect(db.engine)
        for modelo in (cls, VinculoMercadoLivre, HistoricoOferta, TokenIntegracao, ControleColeta):
            if not inspetor.has_table(modelo.__tablename__):
                raise ValueError('Prepare as tabelas com integracoes-tokens-preparar e mercadolivre-ofertas-preparar')
            colunas = {c['name'] for c in inspetor.get_columns(modelo.__tablename__)}
            if modelo is VinculoMercadoLivre and colunas == {c.name for c in modelo.__table__.columns} - {'especificacoes_revisadas'}:
                raise ValueError('Execute mercadolivre-vinculos-preparar antes de coletar ofertas')
            if colunas != {c.name for c in modelo.__table__.columns}:
                raise ValueError('Esquema de ofertas/tokens incompatível; revise as migrations')
        if db.session.get(ControleColeta, 1) is None:
            raise ValueError('Inicialize o controle com mercadolivre-ofertas-preparar')

    @classmethod
    def anexar_a_catalogo(cls, pecas):
        from sqlalchemy import inspect, tuple_, and_
        from . import VinculoMercadoLivre
        from utils.identidade_peca import assinatura_campos
        if not pecas or not inspect(db.engine).has_table(cls.__tablename__):
            return pecas
        referencias = []
        for peca in pecas:
            tipo, identificador = str(peca.get('id', '')).rsplit(':', 1)
            referencias.append((tipo, int(identificador)))
            peca.setdefault('ofertas', [])
        cls._anexar_kabum(pecas, referencias)
        if not inspect(db.engine).has_table(VinculoMercadoLivre.__tablename__) or not VinculoMercadoLivre.tabela_preparada():
            return pecas
        registros = db.session.query(cls, VinculoMercadoLivre).join(VinculoMercadoLivre, and_(
            VinculoMercadoLivre.tabela_peca == cls.tabela_peca, VinculoMercadoLivre.peca_id == cls.peca_id)).filter(cls.loja == 'mercado_livre', cls.ativa.is_(True),
            tuple_(cls.tabela_peca, cls.peca_id).in_(referencias)).order_by(cls.preco.asc(), cls.id.asc()).all()
        por_peca = {}
        fichas = dict(zip(referencias, pecas))
        for registro, vinculo in registros:
            ficha = fichas[(registro.tabela_peca, registro.peca_id)]
            assinatura = assinatura_campos(registro.tabela_peca, registro.peca_id,
                ficha.get('fabricante'), ficha.get('modelo'), ficha.get('part_number'))
            from types import SimpleNamespace
            if vinculo.assinatura_peca != assinatura or not vinculo.especificacoes_compativeis(SimpleNamespace(**ficha)):
                continue
            dados = registro.para_exibicao()
            if dados is not None:
                por_peca.setdefault((registro.tabela_peca, registro.peca_id), []).append(dados)
        for peca, referencia in zip(pecas, referencias):
            peca['ofertas'] = [*peca.get('ofertas', []), *por_peca.get(referencia, [])]
        cls._anexar_shopee(fichas, referencias)
        return pecas

    @classmethod
    def _anexar_shopee(cls, fichas, referencias):
        from sqlalchemy import tuple_
        from . import ProdutoPendente
        ofertas = cls.query.filter(cls.loja == 'shopee', cls.ativa.is_(True),
                tuple_(cls.tabela_peca, cls.peca_id).in_(referencias)).order_by(cls.preco, cls.id).all()
        ids_por_tabela = {}
        for oferta in ofertas:
            ids_por_tabela.setdefault(oferta.tabela_peca, set()).add(oferta.peca_id)
        modelos = {m.__tablename__: m for m in MODELOS_PECAS}
        pecas = {(tabela, peca.id): peca for tabela, ids in ids_por_tabela.items() if tabela in modelos
                 for peca in modelos[tabela].listar_por_ids(ids)}
        pendencias = ProdutoPendente.mapear_por_anuncios('shopee', {o.produto_id_loja for o in ofertas})
        for oferta in ofertas:
            peca = pecas.get((oferta.tabela_peca, oferta.peca_id))
            pendencia = pendencias.get(oferta.produto_id_loja)
            dados = oferta.para_exibicao()
            if peca and pendencia and dados and oferta.shopee_validada(peca, pendencia):
                fichas[(oferta.tabela_peca, oferta.peca_id)]['ofertas'].append(dados)

    @classmethod
    def _anexar_kabum(cls, pecas, referencias):
        from sqlalchemy import tuple_
        fichas = dict(zip(referencias, pecas))
        for oferta in cls.query.filter(cls.loja == 'kabum', cls.ativa.is_(True),
                tuple_(cls.tabela_peca, cls.peca_id).in_(referencias)).order_by(cls.id).all():
            dados = oferta.para_exibicao()
            if dados is not None:
                fichas[(oferta.tabela_peca, oferta.peca_id)]['ofertas'].append(dados)

    @classmethod
    def buscar_para_peca(cls, oferta_id, categoria, peca_id):
        return cls.query.filter_by(id=oferta_id, tabela_peca=categoria, peca_id=peca_id,
                                   ativa=True).filter(cls.loja.in_(('mercado_livre', 'shopee'))).first()

    def shopee_validada(self, peca, pendencia=None):
        from . import ProdutoPendente
        from utils.identidade_peca import assinatura_peca, assinatura_tecnica
        p = pendencia or ProdutoPendente.buscar_por_anuncio('shopee', self.produto_id_loja)
        prova = (p.evidencias or {}).get('vinculo', {}) if p else {}
        return bool(p and p.status == 'importado' and p.oferta_id == self.id
                    and prova.get('assinatura_peca') == assinatura_peca(peca)
                    and prova.get('assinatura_tecnica') == assinatura_tecnica(peca))

    def para_exibicao(self):
        from datetime import timezone
        from urllib.parse import urlsplit
        import re
        coleta = self.preco_atualizado_em if self.loja == 'kabum' else self.consultado_em
        if self.preco is None or self.preco <= 0 or coleta is None:
            return None
        try:
            url = urlsplit(self.url)
            if self.loja == 'kabum':
                if produto_kabum(self.url) != self.produto_id_loja:
                    return None
                url_compra = self.url
            elif self.loja == 'shopee':
                if (not validar_url_shopee(self.url) or
                        url.path != '/product/' + self.produto_id_loja.replace(':', '/')):
                    return None
                url_compra = self.url_afiliado if validar_url_shopee(self.url_afiliado, afiliado=True) else self.url
            elif (url.scheme != 'https' or url.hostname != 'produto.mercadolivre.com.br'
                or url.username or url.password or url.port not in (None, 443)):
                return None
            else:
                codigo = re.match(r'^/MLB-(\d+)(?:-|/|$)', url.path)
                if not codigo or 'MLB' + codigo[1] != self.produto_id_loja:
                    return None
                afiliado = urlsplit(self.url_afiliado or '')
                url_compra = self.url
                if (afiliado.scheme == 'https' and afiliado.hostname in
                    {'mercadolivre.com.br', 'www.mercadolivre.com.br', 'produto.mercadolivre.com.br'}
                    and not afiliado.username and not afiliado.password and afiliado.port in (None, 443)):
                    url_compra = self.url_afiliado
        except ValueError:
            return None
        return {'id': self.id, 'loja': self.loja, 'produto_id_loja': self.produto_id_loja,
                'vendedor_id': self.vendedor_id, 'vendedor_nome': self.vendedor_nome,
                'url': url_compra, 'preco': float(self.preco),
                'esgotado': bool(self.esgotado) if self.loja == 'kabum' else self.esgotado,
                'atualizadoEm': coleta.replace(tzinfo=timezone.utc).isoformat(timespec='seconds')}
