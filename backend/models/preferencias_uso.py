from . import db


class PreferenciasUso(db.Model):
    __tablename__ = "preferencias_uso"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), primary_key=True)
    nivel_hardware = db.Column(db.String(16), nullable=True)
    tutorial = db.Column(db.String(16), nullable=False, default="nao-oferecido")
    versao_tutorial = db.Column(db.Integer, nullable=False, default=1)

    def to_dict(self):
        return {"nivel_hardware": self.nivel_hardware, "tutorial": self.tutorial,
                "versao_tutorial": self.versao_tutorial}
