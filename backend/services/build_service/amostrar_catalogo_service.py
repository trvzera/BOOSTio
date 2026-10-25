from decimal import Decimal
from .preferencias_perifericos_service import PreferenciasPerifericosService
from .preferencias_cores_service import PreferenciasCoresService
from .preferencias_processador_service import PreferenciasProcessadorService


class AmostrarCatalogoService:
    """Preserva padrões incompatíveis e faixas de preço sem enviar o catálogo inteiro."""

    GRUPOS = {
        "processador": ("soquete",),
        "placa_mae": ("socket", "tipo_memoria"),
        "memoria_ram": ("ddr", "capacidade_gb", "quantidade_pentes"),
        "fan": ("tamanho_mm", "quantidade"),
        "fonte": ("formato",),
        "monitor": ("resolucao", "taxa_atualizacao_hz", "tipo_painel"),
        "teclado": ("layout", "mecanico", "switch"),
        "mouse": ("conexao",),
        "fone": ("conexao", "microfone"),
        "gabinete": ("formato", "painel_vidro", "fans_inclusos"),
    }

    def executar(self, tipo, pecas, limite=12, utilidade="", cor="sem-preferencia"):
        ordenadas = sorted(pecas, key=lambda p: (Decimal(str(p["preco"])), p["id"]))
        if len(ordenadas) <= limite:
            return ordenadas
        escolhidas = {ordenadas[0]["id"]: ordenadas[0], ordenadas[-1]["id"]: ordenadas[-1]}
        if tipo == "processador":
            for peca in PreferenciasProcessadorService.destaques(ordenadas, utilidade):
                if len(escolhidas) < max(2, limite - 4):
                    escolhidas[peca["id"]] = peca
        for peca in PreferenciasPerifericosService.destaques(tipo, ordenadas, utilidade):
            if len(escolhidas) < limite:
                escolhidas[peca["id"]] = peca
        campos = self.GRUPOS.get(tipo)
        if campos:
            grupos = {}
            primarios = {}
            for peca in ordenadas:
                chave = tuple(str(peca.get(campo, "")).upper().replace(" ", "") for campo in campos)
                grupos.setdefault(chave, peca)
                primarios.setdefault(chave[0], peca)
            # Guarda espaço para opções acima da entrada; preço não é nota de desempenho.
            for peca in [*primarios.values(), *grupos.values()]:
                if len(escolhidas) >= max(1, limite - 4):
                    break
                escolhidas[peca["id"]] = peca
        # Sem excluir padrões técnicos, a entrada econômica ou a faixa de investimento.
        for peca in PreferenciasCoresService.destaques(ordenadas, cor, campos or ()):
            if len(escolhidas) < limite:
                escolhidas[peca["id"]] = peca
        menor, maior = Decimal(str(ordenadas[0]["preco"])), Decimal(str(ordenadas[-1]["preco"]))
        vagas = limite - len(escolhidas)
        for indice in range(vagas):
            alvo = menor + (maior - menor) * (Decimal(indice) / (vagas - 1) if vagas > 1 else Decimal("0.5"))
            disponiveis = [p for p in ordenadas if p["id"] not in escolhidas]
            if not disponiveis or len(escolhidas) >= limite:
                break
            peca = min(disponiveis, key=lambda p: (abs(Decimal(str(p["preco"])) - alvo), p["preco"], p["id"]))
            escolhidas[peca["id"]] = peca
        return sorted(escolhidas.values(), key=lambda p: (p["preco"], p["id"]))
