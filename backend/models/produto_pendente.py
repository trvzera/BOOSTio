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
    def buscar_por_id_com_trava(cls, identificador):
        return cls.query.filter_by(id=identificador).populate_existing().with_for_update().first()

    @classmethod
    def mapear_por_anuncios(cls, loja, produtos_id_loja):
        """Pendências de vários anúncios de uma loja em uma consulta: {produto_id_loja: pendência}."""
        if not produtos_id_loja:
            return {}
        pendencias = cls.query.filter(cls.loja == loja, cls.produto_id_loja.in_(list(produtos_id_loja))).all()
        return {p.produto_id_loja: p for p in pendencias}

    @classmethod
    def buscar_por_anuncio(cls, loja, produto_id_loja):
        return cls.query.filter_by(loja=loja, produto_id_loja=produto_id_loja).first()

    @classmethod
    def listar_para_revisao(cls, depois_id=0, limite=50, categoria=None):
        if type(limite) is not int or not 1 <= limite <= 200 or type(depois_id) is not int or depois_id < 0:
            raise ValueError('Paginação de pendências inválida')
        consulta=cls.query.filter(cls.id > depois_id, cls.status.in_(('pendente','em_revisao')))
        if categoria is not None:consulta=consulta.filter(cls.categoria_sugerida==categoria)
        return consulta.order_by(cls.id).limit(limite).all()


    @classmethod
    def listar_ids_e_candidatos(cls, *, status, loja=None, categoria=None):
        consulta = cls.query.with_entities(cls.id, cls.candidatos).filter(cls.status == status)
        if loja is not None:
            consulta = consulta.filter(cls.loja == loja)
        if categoria is not None:
            consulta = consulta.filter(cls.categoria_sugerida == categoria)
        return consulta.order_by(cls.id).all()

    @classmethod
    def listar_para_admin(cls, *, status, loja=None, categoria=None, depois_id=0, limite=20, ids=None):
        """Página de pendências em ordem estável; devolve também o total do filtro."""
        consulta = cls.query.filter(cls.status == status)
        if loja is not None:
            consulta = consulta.filter(cls.loja == loja)
        if categoria is not None:
            consulta = consulta.filter(cls.categoria_sugerida == categoria)
        if ids is not None:
            if not ids:
                return [], 0
            consulta = consulta.filter(cls.id.in_(ids))
        total = consulta.count()
        return consulta.filter(cls.id > depois_id).order_by(cls.id).limit(limite).all(), total

    @classmethod
    def contar_por_status(cls):
        from sqlalchemy import func
        return dict(db.session.query(cls.status, func.count(cls.id)).group_by(cls.status).all())

    @classmethod
    def registrar_sugestao_ia(cls, identificador, sugestao):
        """Guarda a recomendação da IA; é só informação, nunca decide nem muda o status."""
        try:
            registro = cls.query.filter_by(id=identificador).with_for_update().first()
            if registro is None or registro.status not in ('pendente', 'em_revisao'):
                raise ValueError('Pendência ausente ou já encerrada')
            registro.evidencias = {**(registro.evidencias or {}), 'sugestao_ia': sugestao}
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def descartar_candidato(cls, identificador, peca, revisao):
        """Tira uma peça da lista de candidatas; um novo matching não a recoloca."""
        try:
            registro = cls.query.filter_by(id=identificador).with_for_update().first()
            if registro is None:
                raise LookupError('Pendência não encontrada')
            if registro.status not in ('pendente', 'em_revisao'):
                raise ValueError('Esta pendência já foi decidida')
            restantes = [c for c in registro.candidatos or [] if c.get('peca') != peca]
            if len(restantes) == len(registro.candidatos or []):
                raise ValueError('Esta peça não é candidata desta pendência')
            registro.candidatos = restantes
            registro.evidencias = {**(registro.evidencias or {}),
                                   'descartados': [*(registro.evidencias or {}).get('descartados', []), {'peca': peca, **revisao}]}
            db.session.commit()
            return registro
        except Exception:
            db.session.rollback()
            raise

    @classmethod
    def rejeitar(cls, identificador, motivo, revisao):
        """Encerra uma pendência aberta; nunca reabre uma já importada ou rejeitada."""
        from datetime import datetime, timezone
        try:
            registro = cls.query.filter_by(id=identificador).with_for_update().first()
            if registro is None:
                raise LookupError('Pendência não encontrada')
            if registro.status not in ('pendente', 'em_revisao'):
                raise ValueError('Esta pendência já foi decidida')
            registro.status = 'rejeitado'
            registro.motivo = motivo
            registro.revisado_em = datetime.now(timezone.utc).replace(tzinfo=None)
            registro.evidencias = {**(registro.evidencias or {}), 'revisao_manual': revisao}
            db.session.commit()
            return registro
        except Exception:
            db.session.rollback()
            raise

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
                descartados = {d.get('peca') for d in (registro.evidencias or {}).get('descartados', [])}
                registro.candidatos = [c for c in decisao['candidatos'] if c.get('peca') not in descartados]
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
