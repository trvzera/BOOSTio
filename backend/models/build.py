from models import db, ModeloBase


class Build(ModeloBase):
    """Tabela antiga das builds geradas. Só é lida para migrar e excluir; builds novas ficam em build_salva."""
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
    adaptador_wifi_id = db.Column(db.Integer, db.ForeignKey("adaptador_wifi.id"), nullable=True)
    cabo_rede_id = db.Column(db.Integer, db.ForeignKey("cabo_rede.id"), nullable=True)

    usuario = db.relationship("Usuario", backref="builds")
    
    placa_mae = db.relationship("PlacaMae", backref="builds")
    processador = db.relationship("Processador", backref="builds")
    memoria_ram = db.relationship("MemoriaRAM", backref="builds")
    fonte = db.relationship("Fonte", backref="builds")
    gabinete = db.relationship("Gabinete", backref="builds")
    placa_video = db.relationship("PlacaVideo", backref="builds")
 
    ssd = db.relationship("SSD", backref="builds")
    hd = db.relationship("HD", backref="builds")
 
    air_cooler = db.relationship("AirCooler", backref="builds")
    water_cooler = db.relationship("WaterCooler", backref="builds")
    fan = db.relationship("Fan", backref="builds")
 
    monitor = db.relationship("Monitor", backref="builds")
    teclado = db.relationship("Teclado", backref="builds")
    mouse = db.relationship("Mouse", backref="builds")
    fone = db.relationship("Fone", backref="builds")
    adaptador_wifi = db.relationship("PlacaRede", backref="builds")
    cabo_rede = db.relationship("CaboRede", backref="builds")
 

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
        "adaptador_wifi",
        "cabo_rede",
    )
 
    QUANTIDADES = {
        "memoria_ram": "quantidade_ram",
        "ssd": "quantidade_ssd",
        "hd": "quantidade_hd",
        "fan": "quantidade_fan",
    }
 
    def quantidade_de(self, campo: str) -> int:
        atributo = self.QUANTIDADES.get(campo)
        if atributo is None:
            return 1 if getattr(self, f"{campo}_id") else 0
        return getattr(self, atributo) or 0
 
    @classmethod
    def buscar_por_id_e_usuario(cls, build_id: int, usuario_id: int) -> "Build | None":
        return cls.query.filter_by(id=build_id, usuario_id=usuario_id).first()
