import re

from models import BuildSalva, MemoriaRAM, PlacaVideo, SSD, HD
from .consultar_requisitos_service import ConsultarRequisitosService
from .fpshq_service import ErroBenchmark


class ConsultarRequisitosBuildService:
    """Capacidades persistidas da própria conta; não certifica CPU/GPU nem prevê FPS."""

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
        self._capacidades_adicionais(resultado, build.estado.get("componentes", {}))
        return resultado

    @staticmethod
    def _identificar(componentes, tipo, modelo):
        selecao = componentes.get(tipo, [])
        itens = selecao if isinstance(selecao, list) else [selecao]
        pecas, completa = [], bool(itens)
        for item in itens:
            if not isinstance(item, dict) or type(item.get("quantidade", 1)) is not int or not 1 <= item.get("quantidade", 1) <= 64:
                completa = False
                continue
            identificador = str(item.get("id", ""))
            if not re.fullmatch(r"(?:" + tipo + r":)?[1-9][0-9]{0,17}", identificador):
                completa = False
                continue
            peca = modelo.buscar_por_id(int(identificador.split(":")[-1]))
            if peca is None:
                completa = False
            else:
                pecas.append(peca)
        return pecas, completa

    @classmethod
    def _capacidades_adicionais(cls, resultado, componentes):
        minimos = resultado["minimos"]
        gpu, completa = cls._identificar(componentes, "placa_video", PlacaVideo)
        vram = gpu[0].memoria_gb if completa and len(gpu) == 1 else None
        vram = vram if type(vram) is int and 0 < vram <= 1024 else None
        piso = minimos.get("vramGb")
        resultado["vram"] = {"dedicadaGb": vram, "minimaGb": piso,
                             "atendeCapacidadeMinima": vram >= piso if vram is not None and piso else None}

        discos, identificados = [], True
        for tipo, modelo in (("ssd", SSD), ("hd", HD)):
            pecas, completa = cls._identificar(componentes, tipo, modelo)
            if componentes.get(tipo) and not completa:
                identificados = False
            for peca in pecas:
                capacidade = peca.capacidade_gb
                if type(capacidade) is not int or not 0 < capacidade <= 1000000:
                    identificados = False
                else:
                    discos.append((tipo, capacidade))
        identificados = identificados and bool(discos)
        exige_ssd = minimos.get("exigeSsd") is True
        elegiveis = [gb for tipo, gb in discos if not exige_ssd or tipo == "ssd"]
        maior = max(elegiveis, default=0)
        minimo = minimos.get("armazenamentoGb")
        # Não somar discos: a instalação não cabe automaticamente em volumes separados.
        capacidade_minima = True if minimo and maior >= minimo else False if minimo and identificados else None
        resultado["armazenamento"] = {"maiorUnidadeElegivelGb": maior or None, "minimaGb": minimo,
                                      "exigeSsd": exige_ssd, "completo": identificados,
                                      "atendeCapacidadeMinima": capacidade_minima, "espacoLivreVerificado": False}
        impedimentos = []
        if resultado["ram"]["atendeMinimo"] is False:
            impedimentos.append("A RAM está abaixo do mínimo publicado.")
        if resultado["vram"]["atendeCapacidadeMinima"] is False:
            impedimentos.append("A VRAM dedicada está abaixo do mínimo publicado.")
        if capacidade_minima is False:
            impedimentos.append("Nenhuma unidade identificada atende à capacidade/tipo de armazenamento mínimo publicado.")
        resultado["impedimentosMinimos"] = impedimentos
