"""Anúncio de uma loja vinculado a uma peça; valores monetários em BRL."""
from . import db, ModeloBase


class Oferta(ModeloBase):
    __tablename__ = "oferta"

    # Peca é abstrato; o vínculo segue a referência usada por ConsultaPreco.
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    loja = db.Column(db.String(20), nullable=False)
    produto_id_loja = db.Column(db.String(80), nullable=False)
    # Vazio identifica venda direta. Em marketplace, informar o ID do vendedor.
    # Metadado: a identidade única do anúncio é loja + produto_id_loja.
    vendedor_id = db.Column(db.String(80), nullable=False, default="")
    vendedor_nome = db.Column(db.String(120), nullable=True)
    # Endereço original do anúncio para consultar preço e disponibilidade.
    url = db.Column(db.Text, nullable=False)
    # Link de divulgação; permanece None enquanto não houver afiliação configurada.
    url_afiliado = db.Column(db.Text, nullable=True, default=None)

    preco = db.Column(db.Numeric(14, 2), nullable=True)
    condicao_pagamento = db.Column(db.String(120), nullable=True)
    # NULL: disponibilidade ainda desconhecida; não assumir estoque sem coleta.
    esgotado = db.Column(db.Boolean, nullable=True)
    ativa = db.Column(db.Boolean, nullable=False, default=True)
    # UTC sem tzinfo, seguindo as datas de cotação do projeto.
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
    def aplicar_lote_mercado_livre(cls, peca, catalogo_id, assinatura, assinatura_catalogo, criterio, ofertas, agora, *, simular, confirmar=True, desativar_ausentes=True):
        """Uma transação por peça; nunca altera preço/estoque da peça da KaBuM."""
        from . import VinculoMercadoLivre, HistoricoOferta, ControleColeta
        from utils.identidade_peca import assinatura_peca
        propostas = []
        try:
            if not simular:
                if not ControleColeta.bloquear():
                    raise ValueError('Prepare o controle de coleta antes da importação')
            db.session.refresh(peca, with_for_update=not simular)
            if assinatura_peca(peca) != assinatura:
                raise ValueError('A identificação da peça mudou durante a consulta')
            vinculo = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id, bloquear=not simular)
            if vinculo and (vinculo.catalogo_id != catalogo_id or vinculo.assinatura_peca != assinatura or vinculo.assinatura_catalogo != assinatura_catalogo):
                raise ValueError('Vínculo existente divergente; revisão necessária')
            consulta_vinculo = VinculoMercadoLivre.query.filter_by(catalogo_id=catalogo_id)
            ocupante = (consulta_vinculo.populate_existing().with_for_update() if not simular else consulta_vinculo).first()
            if ocupante and (ocupante.tabela_peca, ocupante.peca_id) != (peca.__tablename__, peca.id):
                raise ValueError('Catálogo já associado a outra peça')
            consulta_ofertas = cls.query.filter_by(tabela_peca=peca.__tablename__, peca_id=peca.id, loja='mercado_livre')
            existentes = (consulta_ofertas.populate_existing().with_for_update() if not simular else consulta_ofertas).all()
            selecionadas = set()
            if not simular and vinculo is None:
                db.session.add(VinculoMercadoLivre(tabela_peca=peca.__tablename__, peca_id=peca.id,
                    catalogo_id=catalogo_id, assinatura_peca=assinatura, assinatura_catalogo=assinatura_catalogo, criterio=criterio))
            for dados in ofertas:
                anuncio, vendedor = dados['produto_id_loja'], dados['vendedor_id']
                identidade = (anuncio, vendedor)
                selecionadas.add(identidade)
                consulta_anuncio = cls.query.filter_by(loja='mercado_livre', produto_id_loja=anuncio)
                registro = (consulta_anuncio.populate_existing().with_for_update() if not simular else consulta_anuncio).first()
                if registro and registro.vendedor_id != vendedor:
                    raise ValueError('Vendedor do anúncio mudou; revisão necessária')
                if registro and (registro.tabela_peca, registro.peca_id) != (peca.__tablename__, peca.id):
                    raise ValueError('Anúncio já vinculado a outra peça')
                acao = 'criada' if registro is None else 'atualizada' if (
                    registro.preco != dados['preco'] or registro.esgotado != dados.get('esgotado') or not registro.ativa or registro.url != dados['url']) else 'inalterada'
                ultimo = HistoricoOferta.ultimo(registro.id, bloquear=not simular) if registro else None
                registrar_historico = ultimo is None or ultimo.preco != dados['preco'] or ultimo.esgotado != dados.get('esgotado') or ultimo.coletado_em.date() != agora.date()
                propostas.append({'anuncio': anuncio, 'vendedor': vendedor, 'preco': str(dados['preco']), 'acao': acao, 'historico': registrar_historico})
                if simular:
                    continue
                if registro is None:
                    registro = cls(tabela_peca=peca.__tablename__, peca_id=peca.id, loja='mercado_livre',
                                   produto_id_loja=anuncio, vendedor_id=vendedor, url=dados['url'])
                    db.session.add(registro)
                mudou = registro.preco != dados['preco']
                registro.preco = dados['preco']
                registro.url = dados['url']
                registro.esgotado = dados.get('esgotado')
                registro.ativa = True
                registro.consultado_em = agora
                if mudou:
                    registro.preco_atualizado_em = agora
                # url_afiliado e nome do vendedor cadastrados manualmente são preservados.
                db.session.flush()
                if registrar_historico:
                    db.session.add(HistoricoOferta(oferta_id=registro.id, preco=registro.preco, esgotado=dados.get('esgotado'), coletado_em=agora))
            # Fora das cinco selecionadas não significa esgotado; apenas sai da seleção ativa.
            for registro in existentes:
                if desativar_ausentes and registro.ativa and (registro.produto_id_loja, registro.vendedor_id) not in selecionadas:
                    propostas.append({'anuncio': registro.produto_id_loja, 'acao': 'desativada'})
                    if not simular:
                        registro.ativa = False
            if not simular and confirmar:
                db.session.commit()
            return propostas
        except Exception:
            if not simular:
                db.session.rollback()
            raise

    @classmethod
    def verificar_esquema_mercado_livre(cls):
        from sqlalchemy import inspect
        from . import VinculoMercadoLivre, HistoricoOferta, TokenIntegracao, ControleColeta
        inspetor = inspect(db.engine)
        for modelo in (cls, VinculoMercadoLivre, HistoricoOferta, TokenIntegracao, ControleColeta):
            if not inspetor.has_table(modelo.__tablename__):
                raise ValueError('Prepare as tabelas com integracoes-tokens-preparar e mercadolivre-ofertas-preparar')
            colunas = {c['name'] for c in inspetor.get_columns(modelo.__tablename__)}
            if colunas != {c.name for c in modelo.__table__.columns}:
                raise ValueError('Esquema de ofertas/tokens incompatível; revise as migrations')
        if db.session.get(ControleColeta, 1) is None:
            raise ValueError('Inicialize o controle com mercadolivre-ofertas-preparar')

    @classmethod
    def anexar_a_catalogo(cls, pecas):
        from sqlalchemy import inspect, tuple_, and_
        from . import VinculoMercadoLivre
        from utils.identidade_peca import assinatura_campos
        # Leitura opcional: catálogo anterior continua funcionando antes da migration.
        if not pecas or not all(inspect(db.engine).has_table(t) for t in (cls.__tablename__, VinculoMercadoLivre.__tablename__)):
            return pecas
        referencias = []
        for peca in pecas:
            tipo, identificador = str(peca.get('id', '')).rsplit(':', 1)
            referencias.append((tipo, int(identificador)))
        registros = db.session.query(cls, VinculoMercadoLivre).join(VinculoMercadoLivre, and_(
            VinculoMercadoLivre.tabela_peca == cls.tabela_peca, VinculoMercadoLivre.peca_id == cls.peca_id)).filter(cls.loja == 'mercado_livre', cls.ativa.is_(True),
            tuple_(cls.tabela_peca, cls.peca_id).in_(referencias)).order_by(cls.preco.asc(), cls.id.asc()).all()
        por_peca = {}
        fichas = dict(zip(referencias, pecas))
        for registro, vinculo in registros:
            ficha = fichas[(registro.tabela_peca, registro.peca_id)]
            assinatura = assinatura_campos(registro.tabela_peca, registro.peca_id,
                ficha.get('fabricante'), ficha.get('modelo'), ficha.get('part_number'))
            if vinculo.assinatura_peca != assinatura:
                continue
            dados = registro.para_exibicao()
            if dados is not None:
                por_peca.setdefault((registro.tabela_peca, registro.peca_id), []).append(dados)
        for peca, referencia in zip(pecas, referencias):
            peca['ofertas'] = [*peca.get('ofertas', []), *por_peca.get(referencia, [])]
        return pecas

    @classmethod
    def buscar_para_peca(cls, oferta_id, categoria, peca_id):
        return cls.query.filter_by(id=oferta_id, tabela_peca=categoria, peca_id=peca_id,
                                   loja='mercado_livre', ativa=True).first()

    def para_exibicao(self):
        from datetime import timezone
        from urllib.parse import urlsplit
        import re
        if self.preco is None or self.preco <= 0 or self.consultado_em is None:
            return None
        try:
            url = urlsplit(self.url)
            if (url.scheme != 'https' or url.hostname != 'produto.mercadolivre.com.br'
                or url.username or url.password or url.port not in (None, 443)):
                return None
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
                'url': url_compra, 'preco': float(self.preco), 'esgotado': self.esgotado,
                'atualizadoEm': self.consultado_em.replace(tzinfo=timezone.utc).isoformat(timespec='seconds')}
