from .base import ModeloBase

# models/build.py
from models import db, ModeloBase


class Build(ModeloBase):
    __tablename__ = "build"
 
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
 
    placa_mae_id = db.Column(
        db.Integer, db.ForeignKey("placa_mae.id"), nullable=False
    )
    processador_id = db.Column(
        db.Integer, db.ForeignKey("processador.id"), nullable=False
    )
    memoria_ram_id = db.Column(
        db.Integer, db.ForeignKey("memoria_ram.id"), nullable=False
    )

    quantidade_ram = db.Column(db.Integer, nullable=False, default=1)
    fonte_id = db.Column(db.Integer, db.ForeignKey("fonte.id"), nullable=False)
    gabinete_id = db.Column(db.Integer, db.ForeignKey("gabinete.id"), nullable=False)

    placa_video_id = db.Column(
        db.Integer, db.ForeignKey("placa_video.id"), nullable=True
    )
 
    ssd_id = db.Column(db.Integer, db.ForeignKey("ssd.id"), nullable=True)
    quantidade_ssd = db.Column(db.Integer, nullable=False, default=0)
 
    hd_id = db.Column(db.Integer, db.ForeignKey("hd.id"), nullable=True)
    quantidade_hd = db.Column(db.Integer, nullable=False, default=0)
 
    air_cooler_id = db.Column(
        db.Integer, db.ForeignKey("air_cooler.id"), nullable=True
    )
    water_cooler_id = db.Column(
        db.Integer, db.ForeignKey("water_cooler.id"), nullable=True
    )
 
    fan_id = db.Column(db.Integer, db.ForeignKey("fan.id"), nullable=True)
    quantidade_fan = db.Column(db.Integer, nullable=False, default=0)
    monitor_id = db.Column(db.Integer, db.ForeignKey("monitor.id"), nullable=True)
    teclado_id = db.Column(db.Integer, db.ForeignKey("teclado.id"), nullable=True)
    mouse_id = db.Column(db.Integer, db.ForeignKey("mouse.id"), nullable=True)
    fone_id = db.Column(db.Integer, db.ForeignKey("fone.id"), nullable=True)

    usuario = db.relationship("Usuario", backref="builds")
    
    placa_mae = db.relationship("PlacaMae", backref="builds")
    processador = db.relationship("Processador", backref="builds")
    memoria_ram = db.relationship("MemoriaRam", backref="builds")
    fonte = db.relationship("Fonte", backref="builds")
    gabinete = db.relationship("Gabinete", backref="builds")
    placa_video = db.relationship("PlacaVideo", backref="builds")
 
    ssd = db.relationship("Ssd", backref="builds")
    hd = db.relationship("Hd", backref="builds")
 
    air_cooler = db.relationship("AirCooler", backref="builds")
    water_cooler = db.relationship("WaterCooler", backref="builds")
    fan = db.relationship("Fan", backref="builds")
 
    monitor = db.relationship("Monitor", backref="builds")
    teclado = db.relationship("Teclado", backref="builds")
    mouse = db.relationship("Mouse", backref="builds")
    fone = db.relationship("Fone", backref="builds")
 

    CAMPOS_PECAS = (
        "placa_mae",
        "processador",
        "memoria_ram",
        "fonte",
        "gabinete",
        "placa_video",
        "ssd",
        "hd",
        "air_cooler",
        "water_cooler",
        "fan",
        "monitor",
        "teclado",
        "mouse",
        "fone",
    )
 
    # Multiplicadores por peça — usados no preço total.
    QUANTIDADES = {
        "memoria_ram": "quantidade_ram",
        "ssd": "quantidade_ssd",
        "hd": "quantidade_hd",
        "fan": "quantidade_fan",
    }
 
    def quantidade_de(self, campo: str) -> int:
        """Quantas unidades desta peça a build tem."""
        atributo = self.QUANTIDADES.get(campo)
        if atributo is None:
            return 1 if getattr(self, f"{campo}_id") else 0
        return getattr(self, atributo) or 0
 
    def to_dict(self, incluir_pecas: bool = False) -> dict:
        dados = {
            "id": self.id,
            "nome": self.nome,
            "usuario_id": self.usuario_id,
            "criado_em": self.criado_em,
            "quantidade_ram": self.quantidade_ram,
            "quantidade_ssd": self.quantidade_ssd,
            "quantidade_hd": self.quantidade_hd,
            "quantidade_fan": self.quantidade_fan,
        }
 
        for campo in self.CAMPOS_PECAS:
            dados[f"{campo}_id"] = getattr(self, f"{campo}_id")
 
        # Só expande as peças quando pedido — expandir sempre gera N+1
        # se a query não tiver usado selectinload nas relationships.
        if incluir_pecas:
            dados["pecas"] = {
                campo: peca.to_dict()
                for campo in self.CAMPOS_PECAS
                if (peca := getattr(self, campo)) is not None
            }
 
        return dados
 


    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "usuario_id": self.usuario_id,
            "criado_em": self.criado_em
        }


    @staticmethod
    def listar_por_usuario(usuario_id: int) -> list["Build"]:
        return Build.query.filter_by(usuario_id=usuario_id).all()
    @staticmethod
    def buscar_por_id(id: int) -> "Build | None":
        return Build.query.get(id)

    @staticmethod
    def listar_por_usuario(usuario_id: int) -> list["Build"]:
        return Build.query.filter_by(usuario_id=usuario_id).all()