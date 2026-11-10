from datetime import timezone
import re

from . import db, ModeloBase
from .build import Build
from .usuario import Usuario
from sqlalchemy import update
from . import Processador, PlacaMae, PlacaVideo, MemoriaRAM, SSD, HD, Fonte, Gabinete
from . import WaterCooler, AirCooler, Fan, Fone, Teclado, Mouse, Monitor
from . import PlacaRede, CaboRede


MODELOS = {modelo.__tablename__: modelo for modelo in (
    Processador, PlacaMae, PlacaVideo, MemoriaRAM, SSD, HD, Fonte, Gabinete,
    WaterCooler, AirCooler, Fan, Fone, Teclado, Mouse, Monitor, PlacaRede, CaboRede,
)}
MULTIPLAS = {"memoria_ram", "ssd", "hd", "fan"}


class LimiteBuildsError(ValueError):
    def __init__(self):
        super().__init__("Você atingiu o limite de três builds. Exclua uma para liberar espaço.")


class EmailNaoVerificadoError(PermissionError):
    def __init__(self):
        super().__init__("Verifique seu e-mail nas configurações do perfil antes de criar uma build.")


class BuildSalva(ModeloBase):
    __tablename__ = "build_salva"

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuario.id"), nullable=False)
    build_original_id = db.Column(db.Integer, db.ForeignKey("build.id"), unique=True)
    estado = db.Column(db.JSON, nullable=False)
    LIMITE = 3

    @classmethod
    def verificar_espaco(cls, usuario_id):
        usuario = db.session.get(Usuario, usuario_id)
        if usuario is None:
            raise ValueError("Usuário não encontrado")
        if not usuario.verificado:
            raise EmailNaoVerificadoError()
        cls.migrar_geradas(usuario_id)
        if cls.query.filter_by(usuario_id=usuario_id).count() >= cls.LIMITE:
            raise LimiteBuildsError()

    @classmethod
    def criar_limitada(cls, usuario_id, estado, gerada=None):
        try:
            resultado = db.session.execute(update(Usuario).where(Usuario.id == usuario_id).values(id=Usuario.id))
            if resultado.rowcount != 1:
                raise ValueError("Usuário não encontrado")
            if not db.session.get(Usuario, usuario_id).verificado:
                raise EmailNaoVerificadoError()
            cls.migrar_geradas(usuario_id, confirmar=False)
            if cls.query.filter_by(usuario_id=usuario_id).count() >= cls.LIMITE:
                raise LimiteBuildsError()
            original = Build.criar_gerada(usuario_id, gerada, confirmar=False) if gerada else None
            build = cls(usuario_id=usuario_id, estado=estado, build_original_id=original.id if original else None)
            db.session.add(build)
            db.session.commit()
            return build
        except Exception:
            db.session.rollback()
            raise


    @classmethod
    def migrar_geradas(cls, usuario_id, confirmar=True):
        originais = Build.listar_por_usuario(usuario_id)
        existentes = {item.build_original_id for item in cls.query.filter_by(usuario_id=usuario_id).all()}
        for original in originais:
            if original.id in existentes:
                continue
            estado = {
                "titulo": original.nome, "descricao": "", "visibilidade": "privado",
                "travada": False, "orcamento": None,
                "componentes": {}
            }
            for tipo in original.CAMPOS_PECAS:
                peca = getattr(original, tipo)
                if peca is None:
                    continue
                item = {"id": peca.id, "quantidade": original.quantidade_de(tipo)}
                estado["componentes"][tipo] = [item] if tipo in MULTIPLAS else item
            estado["incluirPerifericos"] = any(tipo in estado["componentes"] for tipo in ("monitor", "teclado", "mouse", "fone"))
            db.session.add(cls(usuario_id=usuario_id, build_original_id=original.id, estado=estado))
        db.session.flush()
        if confirmar:
            db.session.commit()

    @classmethod
    def listar_por_usuario(cls, usuario_id):
        cls.migrar_geradas(usuario_id)
        return cls.query.filter_by(usuario_id=usuario_id).order_by(cls.criado_em.desc()).all()

    @classmethod
    def buscar(cls, usuario_id, identificador):
        cls.migrar_geradas(usuario_id)
        if str(identificador).startswith("s-"):
            numero = str(identificador)[2:]
            return cls.query.filter_by(id=int(numero), usuario_id=usuario_id).first() if numero.isdigit() else None
        return cls.query.filter_by(build_original_id=int(identificador), usuario_id=usuario_id).first() if str(identificador).isdigit() else None

    @classmethod
    def buscar_publica(cls, identificador):
        if not isinstance(identificador, str) or not re.fullmatch(r"s-[1-9][0-9]{0,17}", identificador):
            return None
        build = db.session.get(cls, int(identificador[2:]))
        return build if build is not None and build.estado.get("visibilidade") == "publico" else None


    @classmethod
    def definir_setup_atual(cls, usuario_id, identificador):
        selecionada = cls.buscar(usuario_id, identificador)
        if selecionada is None:
            raise ValueError("Build não encontrada")
        novo_valor = not selecionada.estado.get("setupAtual", False)
        for build in cls.query.filter_by(usuario_id=usuario_id).all():
            build.estado = {**build.estado, "setupAtual": novo_valor and build.id == selecionada.id}
        db.session.commit()

    def excluir_com_original(self):
        original = None
        if self.build_original_id is not None:
            original = Build.buscar_por_id_e_usuario(self.build_original_id, self.usuario_id)
        db.session.delete(self)
        db.session.flush()
        if original is not None:
            db.session.delete(original)
        db.session.commit()

    def to_dict(self, incluir_links=False):
        criado = self.criado_em
        if criado.tzinfo is None:
            criado = criado.replace(tzinfo=timezone.utc)
        criador = db.session.get(Usuario, self.usuario_id)
        nome_criador = (criador.nome if criador.ativo else "Conta desativada") if criador else "Autor não informado"
        componentes = []
        for tipo, selecao in self.estado.get("componentes", {}).items():
            for item in (selecao if isinstance(selecao, list) else [selecao]):
                peca = MODELOS[tipo].buscar_por_id(item["id"]) if "id" in item else None
                componentes.append({
                    "tipo": tipo, "id": peca.id if peca else None,
                    "nome": f"{peca.fabricante} {peca.modelo}" if peca else item["proprio"],
                    "preco": peca.preco if peca else 0, "quantidade": item["quantidade"],
                    **({"fabricante": peca.fabricante if peca else "", "modelo": peca.modelo if peca else item["proprio"],
                        "link": peca.kabum_external if peca else None, "imagem": peca.imagem_url if peca else None,
                        "esgotado": peca.esgotado if peca else False} if incluir_links else {}),
                })
        return {
            "id": f"s-{self.id}", "nome": self.estado["titulo"], "descricao": self.estado.get("descricao", ""),
            "criador": {"nome": nome_criador},
            "usuario_id": self.usuario_id, "criado_em": criado.isoformat(),
            "preco_total": round(sum(item["preco"] * item["quantidade"] for item in componentes), 2),
            "componentes": componentes, "estado": self.estado,
        }

    def gravar_estado(self, estado):
        self.estado = estado
        db.session.commit()
