"""Auditoria somente leitura: não consulta lojas, prepara banco nem executa seed."""
import math
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from .modelos_pecas import MODELOS_PECAS
from .atualizar_imagem_peca_service import PASTA_COLETADOS
from services.preco_service.validar_link_service import ValidarLinkService


class AuditarCatalogoService:
    def executar(self, amostras=5):
        if type(amostras) is not int or not 0 <= amostras <= 20:
            raise ValueError("Informe de 0 a 20 amostras por categoria")
        categorias = {}
        obrigatorias = {"processador", "placa_mae", "memoria_ram", "fonte", "gabinete"}
        for modelo in MODELOS_PECAS:
            pecas = [p.to_catalogo() for p in modelo.mostrar_pecas()]
            contagens = Counter(p.get("part_number") for p in pecas if p.get("part_number"))
            pendencias, utilizaveis = [], 0
            imagens = locais = medidas = 0
            for p in pecas:
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
                imagem = p.get("imagem")
                if imagem and isinstance(imagem, str):
                    try:
                        destino = urlparse(imagem)
                    except ValueError:
                        motivos.append("imagem_invalida")
                        destino = None
                    if destino is None:
                        pass
                    elif destino.scheme in ("http", "https") and destino.hostname:
                        imagens += 1  # URL presente; disponibilidade remota não foi consultada.
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
                medidas += bool(p.get("fonte_medidas"))
                if motivos:
                    pendencias.append({"id": p["id"], "part_number": p.get("part_number"), "motivos": motivos})
            categorias[modelo.__tablename__] = {
                "total": len(pecas), "disponiveisComPreco": utilizaveis, "comImagem": imagens,
                "imagensLocais": locais, "fichasFisicasRevisadas": medidas,
                "pendencias": dict(Counter(m for p in pendencias for m in p["motivos"])),
                "amostras": pendencias[:amostras],
            }
        sem_oferta = [c for c in obrigatorias if not categorias.get(c, {}).get("disponiveisComPreco")]
        if not any(categorias.get(c, {}).get("disponiveisComPreco") for c in ("ssd", "hd")):
            sem_oferta.append("armazenamento")
        return {"somenteLeitura": True, "categorias": categorias,
                "categoriasObrigatoriasSemOferta": sorted(sem_oferta),
                "temOfertasNasCategoriasObrigatorias": not sem_oferta,
                "aviso": "Oferta por categoria não garante uma combinação compatível ou dentro do orçamento. Fotos remotas, estoque e preços não foram consultados em tempo real."}
