import math
from collections import Counter
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse

from models.modelos_pecas import MODELOS_PECAS
from .atualizar_imagem_peca_service import PASTA_COLETADOS
from services.preco_service.validar_link_service import ValidarLinkService


class AuditarCatalogoService:
    # Campos das conferências atuais e da ampliação da montagem (como formato da RAM).
    # Cobertura não é aprovação; parte dos campos depende da conexão/posição usada.
    CAMPOS_COMPATIBILIDADE = {
        "processador": ("soquete", "videointegrado", "cooler", "consumo_energia"),
        "placa_mae": ("socket", "tipo_memoria", "formato", "quantidade_slots_ram", "memoria_maxima_gb",
                      "quantidade_slots_m2", "quantidade_portas_sata", "slots_m2", "topologia_armazenamento_verificada",
                      "conectores_alimentacao", "conectores_alimentacao_completos", "consumo_energia"),
        "memoria_ram": ("ddr", "frequencia_mhz", "capacidade_gb", "quantidade_pentes", "latencia", "formato", "consumo_energia"),
        "placa_video": ("comprimento_mm", "altura_mm", "espessura_mm", "slots_ocupados", "consumo_energia",
                        "conectores_alimentacao", "conectores_alimentacao_completos", "cabos_pcie_independentes_minimos"),
        "fonte": ("potencia_w", "formato", "comprimento_mm", "conectores_alimentacao", "conectores_alimentacao_completos", "cabos_pcie_independentes"),
        "gabinete": ("formatos_placa_mae", "tamanho_max_gpu_mm", "tamanho_max_altura_gpu_mm", "tamanho_max_espessura_gpu_mm",
                     "slots_expansao", "tamanho_max_cooler_mm", "tamanho_max_fonte_mm", "formatos_fonte", "fans_inclusos",
                     "quantidade_max_fans", "posicoes_fans", "baias_25", "baias_35", "configuracoes_baias", "limites_radiador_mm"),
        "ssd": ("capacidade_gb", "interface", "formato", "formato_m2", "consumo_energia"),
        "hd": ("capacidade_gb", "interface", "formato", "consumo_energia"),
        "fan": ("tamanho_mm", "quantidade", "consumo_energia"),
        "air_cooler": ("compatibilidade", "altura_mm", "consumo_energia"),
        "water_cooler": ("compatibilidade", "tamanho_radiador_mm", "comprimento_radiador_mm", "largura_radiador_mm",
                         "espessura_radiador_mm", "espessura_fan_mm", "quantidade_fans", "tamanho_fan_mm", "consumo_energia"),
    }
    VERIFICACOES_FIXAS = (
        {"codigo": "suporte-cpu-bios", "titulo": "Suporte ao modelo da CPU e BIOS", "arquivo": "services/validacoes_service/avaliar_compatibilidade_service.py"},
        {"codigo": "ram-perfis", "titulo": "Perfis e estabilidade da RAM", "arquivo": "services/validacoes_service/avaliar_compatibilidade_service.py"},
        {"codigo": "radiador-posicao", "titulo": "Espessura e interferências do radiador", "arquivo": "services/validacoes_service/encaixe_fisico.py"},
        {"codigo": "gpu-interferencias", "titulo": "Espaço completo da GPU", "arquivo": "services/validacoes_service/encaixe_fisico.py"},
    )
    CAMPOS_TECNICOS = {
        "processador": ("soquete", "videointegrado", "cooler"),
        "placa_mae": ("socket", "tipo_memoria", "quantidade_slots_ram", "memoria_maxima_gb",
                      "quantidade_slots_m2", "quantidade_portas_sata"),
        "placa_video": ("comprimento_mm", "altura_mm", "espessura_mm", "conectores_energia"),
        "gabinete": ("comprimento_mm", "largura_mm", "altura_mm", "tamanho_max_gpu_mm",
                     "tamanho_max_cooler_mm", "tamanho_max_fonte_mm", "fans_inclusos",
                     "quantidade_max_fans", "posicoes_fans", "baias_25", "baias_35"),
        "fan": ("tamanho_mm", "quantidade", "espessura_mm", "conector_fan"),
        "air_cooler": ("compatibilidade", "altura_mm"),
        "water_cooler": ("compatibilidade", "comprimento_radiador_mm", "largura_radiador_mm",
                         "espessura_radiador_mm", "quantidade_fans", "tamanho_fan_mm"),
        "mouse": ("conexao", "dpi_max"), "teclado": ("conexao", "layout"),
        "fone": ("conexao", "microfone", "resposta_frequencia"),
        "monitor": ("conexao", "resolucao", "taxa_atualizacao_hz"),
        "memoria_ram": ("capacidade_gb", "ddr", "frequencia_mhz", "quantidade_pentes", "latencia", "formato"),
        "ssd": ("capacidade_gb", "interface", "formato", "formato_m2"),
        "hd": ("capacidade_gb", "interface", "formato"),
        "fonte": ("potencia_w", "formato", "comprimento_mm", "conectores_alimentacao"),
        "adaptador_wifi": ("interface", "padrao_wifi", "velocidade_mbps"),
        "cabo_rede": ("categoria_cabo", "comprimento_m", "conector"),
    }

    def executar(self, amostras=5, *, detalhar=False):
        if type(amostras) is not int or not 0 <= amostras <= 20:
            raise ValueError("Informe de 0 a 20 amostras por categoria")
        if type(detalhar) is not bool:
            raise ValueError("Informe detalhar como booleano")
        categorias = {}
        obrigatorias = {"processador", "placa_mae", "memoria_ram", "fonte", "gabinete"}
        for modelo in MODELOS_PECAS:
            categorias[modelo.__tablename__] = self._auditar_categoria(modelo, amostras, detalhar=detalhar)
        sem_oferta = [c for c in obrigatorias if not categorias.get(c, {}).get("disponiveisComPreco")]
        if not any(categorias.get(c, {}).get("disponiveisComPreco") for c in ("ssd", "hd")):
            sem_oferta.append("armazenamento")
        return {"somenteLeitura": True, "categorias": categorias,
                "verificacoesSemprePendentes": list(self.VERIFICACOES_FIXAS),
                "escopoTecnico": "Contagem de campos ausentes das conferências atuais e da ampliação da montagem, não certificação de compatibilidade. Campos condicionais dependem da build. Inclui todas as peças cadastradas, inclusive sem oferta/publicação. Ausência de campos monitorados não significa que todas as relações entre as peças foram implementadas.",
                "categoriasObrigatoriasSemOferta": sorted(sem_oferta),
                "temOfertasNasCategoriasObrigatorias": not sem_oferta,
                "aviso": "Oferta por categoria não garante uma combinação compatível ou dentro do orçamento. Fotos remotas, estoque e preços não foram consultados em tempo real."}

    def _auditar_categoria(self, modelo, amostras, *, detalhar=False):
        pecas = [p.to_catalogo() for p in modelo.mostrar_pecas()]
        contagens = Counter(p.get("part_number") for p in pecas if p.get("part_number"))
        pendencias, utilizaveis = [], 0
        tecnicas = []
        compatibilidade = []
        imagens = locais = medidas = 0
        genericas = []
        for p in pecas:
            if modelo.__tablename__ == "placa_video":
                from services.especificacoes_service.converter_referencias_gpu_service import ConverterReferenciasGpuService
                if ConverterReferenciasGpuService.generica(SimpleNamespace(fabricante=p.get("fabricante") or "",
                        modelo=p.get("modelo") or "", modelo_referencia=p.get("modelo_referencia"))):
                    genericas.append({"id": p["id"], "fabricante": p.get("fabricante"), "modelo": p.get("modelo")})
            ausentes = [campo for campo in self.CAMPOS_TECNICOS.get(modelo.__tablename__, ()) if self._ausente(p, campo)]
            campos_compatibilidade = [campo for campo in self.CAMPOS_COMPATIBILIDADE.get(modelo.__tablename__, ()) if self._ausente(p, campo)]
            if campos_compatibilidade:
                compatibilidade.append({"id": p["id"], "fabricante": p.get("fabricante"), "modelo": p.get("modelo"),
                                        "part_number": p.get("part_number"), "campos": campos_compatibilidade})
            if ausentes:
                tecnicas.append({"id": p["id"], "fabricante": p.get("fabricante"), "modelo": p.get("modelo"),
                                 "part_number": p.get("part_number"), "campos": ausentes})
            motivos = []
            preco = p.get("preco")
            valido = type(preco) in (int, float) and math.isfinite(preco) and preco > 0
            utilizaveis += bool(valido and p.get("esgotado") is False)
            if not valido:
                motivos.append("sem_preco_valido")
            if not p.get("preco_atualizado_em"):
                motivos.append("preco_sem_data")
            if p.get("esgotado") is True:
                motivos.append("indisponivel")
            elif p.get("esgotado") is not False:
                motivos.append("estoque_nao_confirmado")
            try:
                ValidarLinkService().executar(p.get("link"))
            except (ValueError, TypeError):
                motivos.append("link_nao_validado")
            if not p.get("part_number"):
                motivos.append("sem_part_number")
            elif contagens[p["part_number"]] > 1:
                motivos.append("part_number_duplicado")
            imagem, local = self._verificar_imagem(p.get("imagem"), motivos)
            imagens += imagem
            locais += local
            medidas += bool(p.get("fonte_medidas"))
            if motivos:
                pendencias.append({"id": p["id"], "part_number": p.get("part_number"), "motivos": motivos})
        return {
            "total": len(pecas), "disponiveisComPreco": utilizaveis, "comImagem": imagens,
            "imagensLocais": locais, "fichasFisicasRevisadas": medidas,
            "pendencias": dict(Counter(m for p in pendencias for m in p["motivos"])),
            "amostras": pendencias[:amostras],
            "camposTecnicosAusentes": dict(Counter(c for p in tecnicas for c in p["campos"])),
            "amostrasTecnicas": tecnicas[:amostras],
            "camposCompatibilidadeAusentes": dict(Counter(c for p in compatibilidade for c in p["campos"])),
            "pecasComDadosCompatibilidadeAusentes": len(compatibilidade),
            **({"quantidadeReferenciasGenericas": len(genericas), "referenciasGenericas": genericas if detalhar else genericas[:amostras]} if modelo.__tablename__ == "placa_video" else {}),
            **({"detalhesCompatibilidade": compatibilidade, "detalhesTecnicos": tecnicas} if detalhar else {}),
        }

    @staticmethod
    def _ausente(peca, campo):
        valor = peca.get(campo)
        if campo == "formato_m2":
            from services.validacoes_service.armazenamento import conexao_disco, formato_m2
            return formato_m2(peca) is None if conexao_disco(peca) in ("m2", "m2-sata") else False
        if campo == "slots_m2" and valor == [] and peca.get("quantidade_slots_m2") == 0:
            return False
        if campo == "conectores_alimentacao" and valor == {} and peca.get("conectores_alimentacao_completos") is True:
            return False
        if campo in ("topologia_armazenamento_verificada", "conectores_alimentacao_completos"):
            return valor is not True
        if isinstance(valor, float) and not math.isfinite(valor):
            return True
        return valor is None or valor == [] or valor == {} or isinstance(valor, str) and valor.strip().casefold() in ("", "n/a", "não informado", "desconhecido")

    @staticmethod
    def _verificar_imagem(imagem, motivos):
        imagens = locais = 0
        if imagem and isinstance(imagem, str):
            try:
                destino = urlparse(imagem)
            except ValueError:
                motivos.append("imagem_invalida")
                destino = None
            if destino is None:
                pass
            elif destino.scheme in ("http", "https") and destino.hostname:
                imagens += 1
            elif not destino.scheme:
                frontend = Path(__file__).resolve().parents[3] / "frontend"
                arquivo = (frontend / "pages" / imagem).resolve()
                raiz = frontend / "imgs"
                if imagem.startswith("../coletados/"):
                    raiz = PASTA_COLETADOS.resolve()
                    arquivo = (raiz / imagem.removeprefix("../coletados/")).resolve()
                if arquivo.is_relative_to(raiz) and arquivo.is_file():
                    imagens += 1
                    locais += 1
                else:
                    motivos.append("imagem_local_ausente")
            else:
                motivos.append("imagem_invalida")
        elif imagem:
            motivos.append("imagem_invalida")
        else:
            motivos.append("sem_imagem")
        return imagens, locais
