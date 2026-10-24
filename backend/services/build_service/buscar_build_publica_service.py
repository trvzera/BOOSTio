from copy import deepcopy

from models import BuildSalva
from models.build_salva import MODELOS
from .avaliar_compatibilidade_service import AvaliarCompatibilidadeService


class BuscarBuildPublicaService:
    def executar(self, identificador):
        build = BuildSalva.buscar_publica(identificador)
        if build is None:
            raise ValueError("Build não encontrada")
        dados = AvaliarCompatibilidadeService().para_resposta(build, incluir_links=True)
        dados.pop("usuario_id", None)
        dados["estado"] = {campo: deepcopy(build.estado[campo]) for campo in (
            "titulo", "descricao", "componentes", "incluirPerifericos", "incluirRede", "substituirFansWaterCooler"
        ) if campo in build.estado}
        dados["estado"].update(visibilidade="publico", travada=True)
        pecas = {}
        for tipo, selecao in build.estado.get("componentes", {}).items():
            for item in selecao if isinstance(selecao, list) else [selecao]:
                peca = MODELOS[tipo].buscar_por_id(item["id"]) if "id" in item else None
                if peca:
                    ficha = peca.to_catalogo()
                    pecas[ficha["id"]] = ficha
        dados["pecas"] = list(pecas.values())
        return dados
