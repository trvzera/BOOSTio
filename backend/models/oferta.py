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
    # Não usar NULL na identidade: índices únicos permitem vários NULLs.
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
        db.UniqueConstraint("loja", "produto_id_loja", "vendedor_id", name="uq_oferta_loja_produto_vendedor"),
        db.CheckConstraint("peca_id > 0", name="ck_oferta_peca_positiva"),
        db.CheckConstraint("preco IS NULL OR preco > 0", name="ck_oferta_preco_positivo"),
        db.CheckConstraint("esgotado IS NULL OR esgotado = 1 OR preco IS NOT NULL", name="ck_oferta_disponivel_com_preco"),
        db.Index("ix_oferta_peca", "tabela_peca", "peca_id"),
        db.Index("ix_oferta_coleta", "loja", "ativa", "consultado_em"),
    )

    @classmethod
    def aplicar_lote_mercado_livre(cls, peca, catalogo_id, assinatura, assinatura_catalogo, criterio, ofertas, agora, *, simular):
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
                consulta_anuncio = cls.query.filter_by(loja='mercado_livre', produto_id_loja=anuncio, vendedor_id=vendedor)
                registro = (consulta_anuncio.populate_existing().with_for_update() if not simular else consulta_anuncio).first()
                if registro and (registro.tabela_peca, registro.peca_id) != (peca.__tablename__, peca.id):
                    raise ValueError('Anúncio já vinculado a outra peça')
                acao = 'criada' if registro is None else 'atualizada' if (
                    registro.preco != dados['preco'] or not registro.ativa or registro.url != dados['url']) else 'inalterada'
                ultimo = HistoricoOferta.ultimo(registro.id, bloquear=not simular) if registro else None
                registrar_historico = ultimo is None or ultimo.preco != dados['preco'] or ultimo.esgotado is not None or ultimo.coletado_em.date() != agora.date()
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
                registro.esgotado = None
                registro.ativa = True
                registro.consultado_em = agora
                if mudou:
                    registro.preco_atualizado_em = agora
                # url_afiliado e nome do vendedor cadastrados manualmente são preservados.
                db.session.flush()
                if registrar_historico:
                    db.session.add(HistoricoOferta(oferta_id=registro.id, preco=registro.preco, esgotado=None, coletado_em=agora))
            # Fora das cinco selecionadas não significa esgotado; apenas sai da seleção ativa.
            for registro in existentes:
                if registro.ativa and (registro.produto_id_loja, registro.vendedor_id) not in selecionadas:
                    propostas.append({'anuncio': registro.produto_id_loja, 'acao': 'desativada'})
                    if not simular:
                        registro.ativa = False
            if not simular:
                db.session.commit()
            return propostas
        except Exception:
            if not simular:
                db.session.rollback()
            raise
