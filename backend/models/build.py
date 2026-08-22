from .base import ModeloBase

# models/build.py
from models import db, ModeloBase


class Build(ModeloBase):
    __tablename__ = "build"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    nome = db.Column(db.String(100), nullable=False)

    usuario = db.relationship('Usuario', backref='builds')

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "usuario_id": self.usuario_id,
            "criado_em": self.criado_em
        }

    @staticmethod
    def buscar_por_id(id: int) -> "Build | None":
        return Build.query.get(id)

    @staticmethod
    def listar_por_usuario(usuario_id: int) -> list["Build"]:
        return Build.query.filter_by(usuario_id=usuario_id).all()