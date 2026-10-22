from datetime import timezone

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
        """Serializa a escrita por usuário; nunca mantém lock durante a chamada à LLM."""
        try:
            # UPDATE também serializa no SQLite, onde SELECT FOR UPDATE não tem efeito.
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
    def criar_gerada_com_pecas_proprias(cls, usuario_id, dados, proprias, rede=None, percentual=0):
        componentes = {}
        for tipo, nome in proprias.items():
            if tipo not in MODELOS:
                continue
            item = {"proprio": nome, "quantidade": 1}
            componentes[tipo] = [item] if tipo in MULTIPLAS else item
        for item in dados["componentes"]:
            tipo = item["tipo"]
            componente = {"id": item["id"], "quantidade": item["quantidade"]}
            componentes[tipo] = [componente] if tipo in MULTIPLAS else componente
        estado = cls.validar_estado({
            "titulo": dados["nome"][:100], "descricao": dados["descricao"][:300],
            "orcamento": dados["orcamento"], "rede": rede or {},
            "incluirPerifericos": percentual > 0 or any(tipo in componentes for tipo in ("monitor", "teclado", "mouse", "fone")),
            "percentualPerifericos": percentual,
            "incluirRede": (rede or {}).get("tipo") in ("cabo", "wifi"),
            "pecasExtras": {tipo: nome for tipo, nome in proprias.items() if tipo not in MODELOS},
            "componentes": componentes,
        })
        return cls.criar_limitada(usuario_id, estado)

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
        if not identificador.startswith("s-") or not identificador[2:].isdigit():
            return None
        build = db.session.get(cls, int(identificador[2:]))
        return build if build is not None and build.estado.get("visibilidade") == "publico" else None

    @staticmethod
    def validar_estado(dados):
        if not isinstance(dados, dict):
            raise ValueError("Envie uma build válida")
        titulo = dados.get("titulo")
        if not isinstance(titulo, str) or not titulo.strip() or len(titulo) > 100:
            raise ValueError("Informe um nome de até 100 caracteres")
        descricao = dados.get("descricao", "")
        if not isinstance(descricao, str) or len(descricao) > 300:
            raise ValueError("Descrição inválida")
        if dados.get("visibilidade", "privado") not in ("privado", "publico"):
            raise ValueError("Visibilidade inválida")
        componentes = dados.get("componentes", {})
        if not isinstance(componentes, dict) or set(componentes) - set(MODELOS):
            raise ValueError("Categoria de peça inválida")
        limpos = {}
        for tipo, selecao in componentes.items():
            itens = selecao if isinstance(selecao, list) else [selecao]
            if not itens or len(itens) > (64 if tipo in MULTIPLAS else 1):
                raise ValueError("Quantidade de modelos inválida")
            tratados = []
            for item in itens:
                if not isinstance(item, dict):
                    raise ValueError("Componente inválido")
                quantidade = item.get("quantidade", 1)
                if type(quantidade) is not int or not 1 <= quantidade <= (64 if tipo in MULTIPLAS else 1):
                    raise ValueError("Quantidade inválida")
                if "id" in item:
                    try:
                        peca_id = int(str(item["id"]).split(":")[-1])
                    except ValueError:
                        raise ValueError("ID de peça inválido") from None
                    if MODELOS[tipo].buscar_por_id(peca_id) is None:
                        raise ValueError("Peça não encontrada no catálogo")
                    tratados.append({"id": peca_id, "quantidade": quantidade})
                elif isinstance(item.get("proprio"), str) and 0 < len(item["proprio"].strip()) <= 120:
                    tratados.append({"proprio": item["proprio"].strip(), "quantidade": quantidade})
                else:
                    raise ValueError("Componente inválido")
            limpos[tipo] = tratados if tipo in MULTIPLAS else tratados[0]
        orcamento = dados.get("orcamento")
        if orcamento is not None and (type(orcamento) not in (int, float) or not 0 <= orcamento <= 1000000):
            raise ValueError("Orçamento inválido")
        percentual = dados.get("percentualPerifericos", 0)
        if type(dados.get("substituirFansWaterCooler", False)) is not bool:
            raise ValueError("Opção de substituição das fans inválida")
        if type(percentual) is not int or not 0 <= percentual <= 99:
            raise ValueError("A porcentagem para periféricos deve ser de 0 a 99")
        pecas_extras = dados.get("pecasExtras", {})
        if not isinstance(pecas_extras, dict) or set(pecas_extras) - {"webcam", "microfone"}:
            raise ValueError("Peça própria extra inválida")
        if any(not isinstance(nome, str) or not nome.strip() or len(nome.strip()) > 120 for nome in pecas_extras.values()):
            raise ValueError("Modelo de peça própria extra inválido")
        return {
            "titulo": titulo.strip(), "descricao": descricao.strip(), "visibilidade": dados.get("visibilidade", "privado"),
            "travada": bool(dados.get("travada", False)), "orcamento": orcamento,
            "incluirPerifericos": bool(dados.get("incluirPerifericos", False)),
            "percentualPerifericos": percentual,
            "substituirFansWaterCooler": dados.get("substituirFansWaterCooler", False),
            "incluirRede": bool(dados.get("incluirRede", False)), "rede": dados.get("rede") or {},
            "pecasExtras": {tipo: nome.strip() for tipo, nome in pecas_extras.items()},
            "componentes": limpos,
        }

    def salvar_estado(self, dados):
        if self.estado.get("travada"):
            if dados != {"travada": False}:
                raise ValueError("Destranque a build para alterar")
            self.estado = {**self.estado, "travada": False}
            db.session.commit()
            return
        self.estado = {**self.validar_estado(dados), "setupAtual": bool(self.estado.get("setupAtual", False))}
        db.session.commit()

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
            "usuario_id": self.usuario_id, "criado_em": criado.isoformat(),
            "preco_total": round(sum(item["preco"] * item["quantidade"] for item in componentes), 2),
            "componentes": componentes, "estado": self.estado,
        }
