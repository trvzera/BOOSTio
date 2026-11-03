"""Anúncios descobertos aguardando identificação; nunca entram no catálogo público."""
from . import db, ModeloBase


class ProdutoPendente(ModeloBase):
    __tablename__ = 'produto_pendente'

    loja = db.Column(db.String(20), nullable=False)
    produto_id_loja = db.Column(db.String(80), nullable=False)
    vendedor_id = db.Column(db.String(80), nullable=True)
    titulo = db.Column(db.String(255), nullable=False)
    url = db.Column(db.Text, nullable=False)
    categoria_sugerida = db.Column(db.String(40), nullable=True)
    dados_originais = db.Column(db.JSON, nullable=False)
    evidencias = db.Column(db.JSON, nullable=True)
    candidatos = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pendente', server_default='pendente')
    motivo = db.Column(db.Text, nullable=True)
    coletado_em = db.Column(db.DateTime, nullable=False)
    revisado_em = db.Column(db.DateTime, nullable=True)
    oferta_id = db.Column(db.Integer, db.ForeignKey('oferta.id', ondelete='SET NULL'), nullable=True)

    __table_args__ = (
        db.UniqueConstraint('loja', 'produto_id_loja', name='uq_pendente_loja_produto'),
        db.CheckConstraint("length(trim(loja)) > 0 AND length(trim(produto_id_loja)) > 0", name='ck_pendente_identidade'),
        db.CheckConstraint("status IN ('pendente','em_revisao','rejeitado','importado')", name='ck_pendente_status'),
        db.Index('ix_pendente_revisao', 'status', 'categoria_sugerida', 'id'),
        db.Index('ix_pendente_coleta', 'loja', 'coletado_em'),
    )

    @classmethod
    def buscar_por_id(cls, identificador):
        return db.session.get(cls, identificador)

    @classmethod
    def buscar_por_anuncio(cls, loja, produto_id_loja):
        return cls.query.filter_by(loja=loja, produto_id_loja=produto_id_loja).first()

    @classmethod
    def listar_para_revisao(cls, depois_id=0, limite=50):
        if type(limite) is not int or not 1 <= limite <= 200 or type(depois_id) is not int or depois_id < 0:
            raise ValueError('Paginação de pendências inválida')
        return (cls.query.filter(cls.id > depois_id, cls.status.in_(('pendente', 'em_revisao')))
                .order_by(cls.id).limit(limite).all())


    @classmethod
    def registrar_descobertos(cls, linhas, *, simular=True):
        """Transação por página. Nunca reabre pendência revisada ou altera oferta."""
        from . import Oferta
        contagens = {'novos': 0, 'ja_coletados': 0, 'ja_associados': 0}
        vistos = set()
        try:
            for dados in linhas:
                chave = (dados['loja'], dados['produto_id_loja'])
                if chave in vistos:
                    contagens['ja_coletados'] += 1
                    continue
                vistos.add(chave)
                if Oferta.query.filter_by(loja=chave[0], produto_id_loja=chave[1]).first():
                    contagens['ja_associados'] += 1
                elif cls.buscar_por_anuncio(*chave):
                    contagens['ja_coletados'] += 1
                elif simular:
                    contagens['novos'] += 1
                else:
                    db.session.add(cls(**dados))
                    db.session.flush()
                    contagens['novos'] += 1
            if not simular:
                db.session.commit()
            return contagens
        except Exception:
            db.session.rollback()
            raise


    @classmethod
    def registrar_matching(cls, identificador, decisao, assinatura_original, *, simular=True):
        from utils.identidade_peca import assinatura_documento
        try:
            registro = cls.query.filter_by(id=identificador).with_for_update().first()
            if registro is None or registro.status not in ('pendente', 'em_revisao'):
                raise ValueError('Pendência ausente ou já encerrada')
            if assinatura_documento(registro.dados_originais) != assinatura_original:
                raise ValueError('Anúncio mudou durante a análise')
            evidencias = {**(registro.evidencias or {}), 'matching': decisao}
            if not simular and registro.evidencias != evidencias:
                registro.evidencias = evidencias
                registro.candidatos = decisao['candidatos']
                registro.status = 'em_revisao'
                registro.motivo = 'Matching ' + decisao['classificacao']
                db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.rollback()


    @classmethod
    def registrar_enriquecimento(cls, identificador, resultado, assinatura_original, *, simular=True):
        import json
        from decimal import Decimal
        from utils.identidade_peca import assinatura_documento
        try:
            registro = cls.query.filter_by(id=identificador).with_for_update().first()
            if registro is None or registro.status not in ('pendente','em_revisao'):
                raise ValueError('Pendência ausente ou encerrada')
            if assinatura_documento(registro.dados_originais) != assinatura_original:
                raise ValueError('Anúncio mudou durante o enriquecimento')
            def serializar(valor):
                if isinstance(valor, Decimal):
                    return str(valor)
                raise ValueError('Tipo não suportado nas evidências')
            dados = json.loads(json.dumps(resultado, default=serializar, allow_nan=False))
            if not simular:
                registro.evidencias = {**(registro.evidencias or {}), 'enriquecimento':dados}
                registro.status = 'em_revisao'
                registro.motivo = 'Ficha completa aguardando importação' if dados['pronto'] else 'Ficha incompleta ou conflitante; revisar evidências'
                db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.rollback()


    @classmethod
    def registrar_falha_importacao(cls, identificador, *, simular):
        if simular:return
        try:
            registro=cls.query.filter_by(id=identificador).with_for_update().first()
            if registro is not None and registro.status in ('pendente','em_revisao'):
                registro.status='em_revisao'
                registro.motivo='Importação não confirmada; revisão necessária'
                registro.evidencias={**(registro.evidencias or {}),'ultima_importacao':{'resultado':'falha','origem':'mercado_livre'}}
                db.session.commit()
        except Exception:
            db.session.rollback()
            raise
