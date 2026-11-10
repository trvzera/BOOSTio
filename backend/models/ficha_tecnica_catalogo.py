from sqlalchemy.orm import validates
from . import db, ModeloBase

ESTADOS_FICHA = ('descoberta','pendente_dados','em_revisao','validada','importada','rejeitada')
TRANSICOES = {
    'descoberta': {'pendente_dados','em_revisao','validada','rejeitada'},
    'pendente_dados': {'em_revisao','validada','rejeitada'},
    'em_revisao': {'pendente_dados','validada','rejeitada'},
    'validada': {'importada','pendente_dados','em_revisao','rejeitada'},
    'importada': {'em_revisao'},
    'rejeitada': {'em_revisao'},
}


class FichaTecnicaCatalogo(ModeloBase):
    __tablename__ = 'ficha_tecnica_catalogo'
    provedor = db.Column(db.String(60), nullable=False)
    id_externo = db.Column(db.String(120), nullable=False)
    categoria = db.Column(db.String(40), nullable=False)
    estado = db.Column(db.String(24), nullable=False, default='descoberta', server_default='descoberta')
    documento = db.Column(db.JSON, nullable=False)
    assinatura_documento = db.Column(db.String(64), nullable=False)
    campos_pendentes = db.Column(db.JSON, nullable=False, default=list)
    diagnostico = db.Column(db.JSON, nullable=False, default=dict)
    peca_id = db.Column(db.Integer, nullable=True)
    __table_args__ = (
        db.UniqueConstraint('provedor','id_externo',name='uq_ficha_tecnica_origem'),
        db.CheckConstraint("estado IN ('descoberta','pendente_dados','em_revisao','validada','importada','rejeitada')",name='ck_ficha_tecnica_estado'),
        db.Index('ix_ficha_tecnica_fila','estado','categoria','id'),
        db.Index('ix_ficha_tecnica_peca','categoria','peca_id'),
    )

    @validates('estado')
    def validar_estado(self, chave, valor):
        if valor not in ESTADOS_FICHA:raise ValueError('Estado de ficha inválido')
        return valor

    @classmethod
    def buscar_origem(cls, provedor, id_externo, *, bloquear=False):
        q=cls.query.filter_by(provedor=provedor,id_externo=id_externo)
        return (q.with_for_update() if bloquear else q).first()

    @classmethod
    def buscar(cls, identificador, *, bloquear=False):
        q=cls.query.filter_by(id=identificador)
        return (q.with_for_update() if bloquear else q).first()

    @classmethod
    def listar(cls, *, estado=None, depois_id=0, limite=50):
        if estado is not None and estado not in ESTADOS_FICHA:raise ValueError('Estado inválido')
        if type(limite) is not int or not 1<=limite<=200 or type(depois_id) is not int or depois_id<0:raise ValueError('Paginação inválida')
        q=cls.query.filter(cls.id>depois_id)
        if estado:q=q.filter_by(estado=estado)
        return q.order_by(cls.id).limit(limite).all()

    def transicionar(self, destino, *, motivo, responsavel, reabrir=False):
        if destino not in ESTADOS_FICHA:raise ValueError('Estado inválido')
        if destino==self.estado:return False
        if destino not in TRANSICOES[self.estado] or self.estado=='rejeitada' and not reabrir:
            raise ValueError('Transição não permitida; rejeições exigem reabertura explícita')
        if not isinstance(motivo,str) or not motivo.strip() or len(motivo)>1000:raise ValueError('Informe o motivo')
        if not isinstance(responsavel,str) or not responsavel.strip() or len(responsavel)>120:raise ValueError('Informe o responsável')
        db.session.add(RevisaoFichaTecnica(ficha_id=self.id,estado_anterior=self.estado,estado_novo=destino,
            motivo=motivo.strip(),responsavel=responsavel.strip(),assinatura_documento=self.assinatura_documento))
        self.estado=destino
        return True

    def resumo(self):
        return dict(id=self.id,provedor=self.provedor,id_externo=self.id_externo,categoria=self.categoria,
            estado=self.estado,peca_id=self.peca_id,campos_pendentes=self.campos_pendentes,diagnostico=self.diagnostico)


class RevisaoFichaTecnica(ModeloBase):
    __tablename__='revisao_ficha_tecnica'
    ficha_id=db.Column(db.Integer,db.ForeignKey('ficha_tecnica_catalogo.id'),nullable=False,index=True)
    estado_anterior=db.Column(db.String(24),nullable=False)
    estado_novo=db.Column(db.String(24),nullable=False)
    motivo=db.Column(db.Text,nullable=False)
    responsavel=db.Column(db.String(120),nullable=False)
    assinatura_documento=db.Column(db.String(64),nullable=False)
