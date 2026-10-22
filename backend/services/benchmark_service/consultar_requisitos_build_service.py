import re

from models import BuildSalva, MemoriaRAM
from .consultar_requisitos_service import ConsultarRequisitosService
from .fpshq_service import ErroBenchmark


class ConsultarRequisitosBuildService:
    """Compara a RAM persistida da própria conta, sem consultar o provedor de FPS."""

    def executar(self, dados, usuario_id):
        identificador = dados.get("build_id")
        if not isinstance(identificador, str) or not re.fullmatch(r"(?:s-)?[1-9][0-9]{0,17}", identificador):
            raise ValueError("Selecione uma build salva para verificar os requisitos.")
        build = BuildSalva.buscar(usuario_id, identificador)
        if build is None:
            raise ErroBenchmark("Build não encontrada na sua conta.", "build-nao-encontrada", 404)

        selecao = build.estado.get("componentes", {}).get("memoria_ram", [])
        itens = selecao if isinstance(selecao, list) else [selecao]
        capacidade, pentes, pendencias = 0, 0, []
        if not itens:
            pendencias.append("Adicione a memória RAM à build para confirmar a capacidade.")
        for item in itens:
            if not isinstance(item, dict) or type(item.get("quantidade", 1)) is not int or not 1 <= item.get("quantidade", 1) <= 64:
                pendencias.append("Há uma quantidade de RAM que precisa ser revisada.")
                continue
            identificacao = str(item.get("id", ""))
            if not re.fullmatch(r"(?:memoria_ram:)?[1-9][0-9]{0,17}", identificacao):
                pendencias.append("Uma memória própria ainda não tem modelo identificado no catálogo.")
                continue
            memoria = MemoriaRAM.buscar_por_id(int(identificacao.split(":")[-1]))
            if memoria is None or type(memoria.capacidade_gb) is not int or memoria.capacidade_gb <= 0:
                pendencias.append("Falta a capacidade confirmada de uma das memórias.")
                continue
            # capacidade_gb é a capacidade por item/kit, não por pente do kit.
            capacidade += memoria.capacidade_gb * item.get("quantidade", 1)
            if type(memoria.quantidade_pentes) is int and memoria.quantidade_pentes > 0:
                pentes += memoria.quantidade_pentes * item.get("quantidade", 1)
        if capacidade > 4096:
            pendencias.append("A capacidade está fora da faixa atendida por esta verificação.")
        completa = not pendencias and capacidade > 0
        resultado = ConsultarRequisitosService().executar({
            "game": dados.get("game"), "ram_gb": str(capacidade) if completa else None,
        }, usuario_id)
        resultado["buildId"] = identificador
        resultado["ram"].update({
            "fonte": "build_salva", "completa": completa,
            "conhecidaGb": capacidade, "pentesIdentificados": pentes,
            "pendencias": list(dict.fromkeys(pendencias)),
        })
        return resultado
