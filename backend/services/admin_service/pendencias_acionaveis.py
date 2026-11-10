"""Pendência só é do administrador quando alguma peça candidata já está aprovada.

Peça importada e ainda em revisão não recebe oferta; enquanto ela não for aprovada, a
pendência fica fora do painel (e volta sozinha quando a peça for aprovada).
"""
from collections import defaultdict

from models import ProdutoPendente
from models.modelos_pecas import MODELOS_PECAS

ABERTAS = ("pendente", "em_revisao")


def _referencias(candidatos):
    for candidato in candidatos or []:
        if candidato.get("conflitos"):
            continue
        categoria, _, identificador = str(candidato.get("peca", "")).partition(":")
        if identificador.isdecimal():
            yield categoria, int(identificador)


def ids_acionaveis(status, loja=None, categoria=None):
    consulta = ProdutoPendente.query.with_entities(ProdutoPendente.id, ProdutoPendente.candidatos)
    consulta = consulta.filter(ProdutoPendente.status == status)
    if loja is not None:
        consulta = consulta.filter(ProdutoPendente.loja == loja)
    if categoria is not None:
        consulta = consulta.filter(ProdutoPendente.categoria_sugerida == categoria)
    linhas = [(i, list(_referencias(c))) for i, c in consulta.order_by(ProdutoPendente.id).all()]
    pedidas = defaultdict(set)
    for _, referencias in linhas:
        for categoria_peca, identificador in referencias:
            pedidas[categoria_peca].add(identificador)
    aprovadas = set()
    for modelo in MODELOS_PECAS:
        ids = pedidas.get(modelo.__tablename__)
        if not ids:
            continue
        for lote in _lotes(sorted(ids)):
            encontrados = modelo.consulta_publicavel().filter(modelo.id.in_(lote)).with_entities(modelo.id).all()
            aprovadas.update((modelo.__tablename__, i) for (i,) in encontrados)
    return [i for i, referencias in linhas if any(r in aprovadas for r in referencias)]


def contar_acionaveis():
    contagens = {status: len(ids_acionaveis(status)) for status in ABERTAS}
    return {status: n for status, n in contagens.items() if n}


def _lotes(valores, tamanho=500):
    for inicio in range(0, len(valores), tamanho):
        yield valores[inicio:inicio + tamanho]
