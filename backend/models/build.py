from datetime import timezone

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
 
    @classmethod
    def criar_gerada(cls, usuario_id: int, dados: dict) -> "Build":
        componentes = dados["componentes"]
        por_tipo = {item["tipo"]: item for item in componentes}
        if len(por_tipo) != len(componentes):
            raise ValueError("A build contém categorias de peças repetidas")
        obrigatorias = ("processador", "placa_mae", "memoria_ram", "fonte", "gabinete")
        if any(tipo not in por_tipo for tipo in obrigatorias) or not ({"ssd", "hd"} & por_tipo.keys()):
            raise ValueError("A build gerada não contém todas as peças obrigatórias")
        if any(item["quantidade"] != 1 for tipo, item in por_tipo.items() if tipo not in cls.QUANTIDADES):
            raise ValueError("Quantidade inválida para uma peça da build")

        build = cls(usuario_id=usuario_id, nome=dados["nome"][:100])
        for tipo, item in por_tipo.items():
            setattr(build, f"{tipo}_id", item["id"])
            if tipo in cls.QUANTIDADES:
                setattr(build, cls.QUANTIDADES[tipo], item["quantidade"])
        db.session.add(build)
        db.session.commit()
        return build

    def to_dict(self, incluir_links: bool = False) -> dict:
        criado_em = self.criado_em
        if criado_em.tzinfo is None:
            criado_em = criado_em.replace(tzinfo=timezone.utc)
        componentes = [
            {
                "tipo": tipo,
                "id": peca.id,
                "nome": f"{peca.fabricante} {peca.modelo}",
                "preco": peca.preco,
                "quantidade": self.quantidade_de(tipo),
                **({
                    "fabricante": peca.fabricante,
                    "modelo": peca.modelo,
                    "link": peca.kabum_external,
                    "imagem": peca.imagem_url,
                    "esgotado": peca.esgotado,
                } if incluir_links else {}),
            }
            for tipo in self.CAMPOS_PECAS
            if (peca := getattr(self, tipo)) is not None
        ]
        return {
            "id": self.id,
            "nome": self.nome,
            "usuario_id": self.usuario_id,
            "criado_em": criado_em.isoformat(),
            "preco_total": round(sum(item["preco"] * item["quantidade"] for item in componentes), 2),
            "componentes": componentes,
        }

    @classmethod
    def listar_por_usuario(cls, usuario_id: int) -> list["Build"]:
        return cls.query.filter_by(usuario_id=usuario_id).order_by(cls.criado_em.desc()).all()

    @classmethod
    def buscar_por_id(cls, build_id: int) -> "Build | None":
        return db.session.get(cls, build_id)

    @classmethod
    def buscar_por_id_e_usuario(cls, build_id: int, usuario_id: int) -> "Build | None":
        return cls.query.filter_by(id=build_id, usuario_id=usuario_id).first()
