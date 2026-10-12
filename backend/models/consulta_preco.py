from sqlalchemy import func, update

from . import db, ModeloBase


class ConsultaPreco(ModeloBase):
    """Uma tentativa reservada antes da rede; falhas também contam no orçamento."""

    __tablename__ = "consulta_preco"
    tabela_peca = db.Column(db.String(40), nullable=False)
    peca_id = db.Column(db.Integer, nullable=False)
    url = db.Column(db.Text, nullable=False)
    dia = db.Column(db.String(10), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="reservada")
    erro = db.Column(db.String(300))

    @classmethod
    def ultimas_por_url(cls):
        return dict(db.session.query(cls.url, func.max(cls.id)).group_by(cls.url).all())

    @classmethod
    def consultadas_no_dia(cls, dia):
        return {
            (row.tabela_peca, row.peca_id, row.url)
            for row in cls.query.filter_by(dia=dia).all()
        }

    @classmethod
    def reservar(cls, tabela_peca, peca_id, url, dia):
        if not ControleColeta.bloquear():
            db.session.rollback()
            raise ValueError("Execute a migração de preços antes da atualização")
        existente = cls.query.filter_by(
            tabela_peca=tabela_peca, peca_id=peca_id, url=url, dia=dia,
        ).first()
        if existente:
            db.session.rollback()
            return None
        consulta = cls(
            tabela_peca=tabela_peca, peca_id=peca_id,
            url=url, dia=dia, status="reservada",
        )
        db.session.add(consulta)
        consulta.confirmar()
        return consulta

    def confirmar(self):
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    def ignorar(self):
        self.status = "ignorada"
        self.confirmar()


class ControleColeta(db.Model):
    """Linha única usada para serializar reservas concorrentes no banco."""

    __tablename__ = "controle_coleta"
    id = db.Column(db.Integer, primary_key=True)
    versao = db.Column(db.Integer, nullable=False, default=0)

    @classmethod
    def bloquear(cls):
        bloqueio = db.session.execute(
            update(cls).where(cls.id == 1).values(versao=cls.versao + 1)
        )
        return bool(bloqueio.rowcount)
