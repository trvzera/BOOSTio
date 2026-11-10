"""Importa snapshots locais PassMark sem executar scraper nem criar peças."""
import csv
import hashlib
import io
import re
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from models import db, Processador, PlacaVideo

FONTE = "https://github.com/yassircherdouh/Algerian-Laptop-Market"
CONFIG = {
    "cpu": (Processador, {"cpumark": "benchmark_multi_core", "single_thread": "benchmark_single_thread"},
            "PassMark CPU Mark / Single Thread", {"name", "cpumark", "single_thread", "cores", "threads"}),
    "gpu": (PlacaVideo, {"g2d": "benchmark_g2d", "g3d": "benchmark_g3d"},
            "PassMark G2D / G3D", {"name", "g2d", "g3d"}),
}


def normalizar_nome(nome):
    nome = re.sub(r"[®™℠]|\((?:r|tm)\)", "", nome, flags=re.I).casefold()
    nome = re.sub(r"(?<=\w)[‐‑–—-](?=\w)", " ", nome)
    nome = re.sub(r"\b(i[3579])\s+(?=\d)", r"\1", nome)
    nome = re.sub(r"(?<=\d)\s+(ti|super|xt|xtx)\b", r"\1", nome)
    return " ".join(nome.split())


def pontuacao(valor):
    if valor is None or not valor.strip():
        return None
    valor = valor.strip()
    if not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d{1,2})?", valor):
        raise ValueError("pontuação inválida")
    try:
        numero = Decimal(valor.replace(",", ""))
    except InvalidOperation as erro:
        raise ValueError("pontuação inválida") from erro
    if not numero.is_finite() or numero <= 0 or numero >= Decimal("1000000000000"):
        raise ValueError("pontuação fora do intervalo")
    return numero


class ImportarBenchmarksService:
    def executar(self, cpu=None, gpu=None, simular=False, lote=100):
        if not cpu and not gpu:
            raise ValueError("Informe ao menos um CSV de CPU ou GPU")
        if type(lote) is not int or lote < 1:
            raise ValueError("O lote deve ser positivo")
        formatos = []
        for caminho in (cpu, gpu):
            if caminho:
                with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
                    campos = next(csv.reader(arquivo), [])
                formatos.append("id" in campos and "name" in campos)
        if any(formatos):
            if not all(formatos):
                raise ValueError("Não misture formatos de fontes diferentes na mesma importação")
            from .importar_referencias_passmark_service import ImportarReferenciasPassmarkService
            return ImportarReferenciasPassmarkService().executar(cpu, gpu, simular, lote)
        fontes = [(tipo, *self._ler(caminho, tipo)) for tipo, caminho in (("cpu", cpu), ("gpu", gpu)) if caminho]
        resumo = {"simulacao": simular, "atualizadas": 0, "propostas": 0, "inalteradas": 0,
                  "nao_encontradas": 0, "ambiguas": 0, "invalidas": 0, "duplicadas": 0,
                  "detalhes": [], "arquivos": {}}
        planos = []
        for tipo, linhas, sha in fontes:
            classe, metricas, teste, _ = CONFIG[tipo]
            resumo["arquivos"][tipo] = {"sha256": sha, "linhas": len(linhas)}
            exatos, normalizados = defaultdict(set), defaultdict(set)
            pecas = {p.id: p for p in classe.mostrar_pecas()}
            for p in pecas.values():
                for nome in (p.modelo, f"{p.fabricante} {p.modelo}"):
                    exatos[nome].add(p.id)
                    normalizados[normalizar_nome(nome)].add(p.id)
            grupos = defaultdict(list)
            for numero, linha in linhas:
                grupos[normalizar_nome(linha.get("name") or "")].append((numero, linha))
            candidatos = defaultdict(list)
            for chave, grupo in grupos.items():
                detalhe = {"tipo": tipo, "linhas": [n for n, _ in grupo], "nome": grupo[0][1].get("name")}
                try:
                    if not chave:
                        raise ValueError("nome ausente")
                    valores = []
                    for _, linha in grupo:
                        if len(linha["name"]) > 255 or any(ord(c) < 32 for c in linha["name"]):
                            raise ValueError("nome inválido")
                        dados = {destino: pontuacao(linha[origem]) for origem, destino in metricas.items()}
                        if all(v is None for v in dados.values()):
                            raise ValueError("sem pontuação")
                        valores.append(dados)
                except ValueError as erro:
                    resumo["invalidas"] += len(grupo)
                    resumo["detalhes"].append({**detalhe, "status": "invalida", "motivo": str(erro)})
                    continue
                if any(v != valores[0] for v in valores[1:]):
                    resumo["ambiguas"] += 1
                    resumo["detalhes"].append({**detalhe, "status": "ambigua", "motivo": "duplicatas conflitantes"})
                    continue
                resumo["duplicadas"] += len(grupo) - 1
                ids = set().union(*(exatos.get(linha["name"], set()) for _, linha in grupo))
                ids = ids or normalizados.get(chave, set())
                if len(ids) != 1:
                    status = "ambiguas" if ids else "nao_encontradas"
                    resumo[status] += 1
                    resumo["detalhes"].append({**detalhe, "status": status, "ids": sorted(ids)})
                    continue
                nome = min(linha["name"] for _, linha in grupo)
                dados = {k: v for k, v in valores[0].items() if v is not None}
                dados.update(benchmark_teste=teste, benchmark_versao=None, benchmark_nome_fonte=nome,
                             benchmark_fonte=f"{FONTE}/blob/main/data/{tipo}_passmark.csv", benchmark_referencia_em=None)
                candidatos[next(iter(ids))].append((dados, detalhe))
            for ident, entradas in candidatos.items():
                peca = pecas[ident]
                dados, detalhe = entradas[0]
                detalhe = {**detalhe, "id": ident}
                if len(entradas) > 1:
                    resumo["ambiguas"] += 1
                    resumo["detalhes"].append({**detalhe, "status": "ambigua", "motivo": "múltiplas linhas para a mesma peça"})
                    continue
                if len(set(metricas.values()) & dados.keys()) < len(metricas) and (
                    peca.benchmark_teste not in (None, teste) or peca.benchmark_versao is not None):
                    resumo["invalidas"] += 1
                    resumo["detalhes"].append({**detalhe, "status": "invalida", "motivo": "métricas parciais de teste diferente"})
                    continue
                alteracoes = {k: v for k, v in dados.items() if getattr(peca, k) != v}
                if not alteracoes:
                    resumo["inalteradas"] += 1
                    continue
                resumo["propostas"] += 1
                resumo["detalhes"].append({**detalhe, "status": "proposta", "alteracoes": {
                    k: {"antes": str(getattr(peca, k)) if getattr(peca, k) is not None else None,
                        "depois": str(v) if v is not None else None} for k, v in alteracoes.items()}})
                planos.append((classe, ident, alteracoes))
        if simular:
            return resumo
        return self._persistir(planos, resumo, lote)

    @staticmethod
    def _persistir(planos, resumo, lote):
        for inicio in range(0, len(planos), lote):
            batch = planos[inicio:inicio + lote]
            try:
                for classe, ident, dados in batch:
                    tabela = classe.__table__
                    db.session.execute(update(tabela).where(tabela.c.id == ident).values(
                        **dados, benchmark_atualizado_em=datetime.now(timezone.utc).replace(tzinfo=None),
                        atualizado_em=tabela.c.atualizado_em))
                db.session.commit()
                db.session.expire_all()
                resumo["atualizadas"] += len(batch)
                if "por_tipo" in resumo:
                    for classe, _, _ in batch:
                        tipo = "cpu" if classe is Processador else "gpu"
                        resumo["por_tipo"][tipo]["atualizadas"] += 1
            except SQLAlchemyError as erro:
                db.session.rollback()
                raise RuntimeError(f"Falha ao persistir lote; {resumo['atualizadas']} peças já confirmadas. "
                                   "Lote atual revertido; reexecute com os mesmos arquivos.") from erro
        return resumo

    def _ler(self, caminho, tipo):
        bruto = Path(caminho).read_bytes()
        try:
            leitor = csv.DictReader(io.StringIO(bruto.decode("utf-8-sig"), newline=""), strict=True)
            cabecalho = leitor.fieldnames
            if not cabecalho or len(cabecalho) != len(set(cabecalho)) or set(cabecalho) != CONFIG[tipo][3]:
                raise ValueError(f"Cabeçalho inesperado no CSV {tipo}: {cabecalho}")
            linhas = []
            for linha in leitor:
                if None in linha or any(v is None for v in linha.values()):
                    raise ValueError(f"Número de colunas inválido: {tipo}, linha {leitor.line_num}")
                linhas.append((leitor.line_num, linha))
            return linhas, hashlib.sha256(bruto).hexdigest()
        except (UnicodeError, csv.Error) as erro:
            raise ValueError(f"Formato inválido no CSV {tipo}: {erro}") from erro
