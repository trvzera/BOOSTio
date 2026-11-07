"""Formato de uma pendência para o painel de administração; não decide nada."""
from services.peca_service.modelos_pecas import MODELOS_PECAS


def apresentar_pendencia(pendencia, *, detalhado=False):
    candidatos = pendencia.candidatos or []
    dados = {
        "id": pendencia.id,
        "loja": pendencia.loja,
        "produto_id_loja": pendencia.produto_id_loja,
        "titulo": pendencia.titulo,
        "url": pendencia.url,
        "categoria": pendencia.categoria_sugerida,
        "status": pendencia.status,
        "motivo": pendencia.motivo,
        "preco": _preco(pendencia),
        "coletado_em": pendencia.coletado_em.isoformat() if pendencia.coletado_em else None,
        "total_candidatos": len(candidatos),
        "sugestao_ia": _sugestao(pendencia, detalhado),
    }
    if detalhado:
        dados["candidatos"] = [_candidato(c) for c in candidatos]
        dados["decisao"] = (pendencia.evidencias or {}).get("revisao_manual")
    return dados


def _sugestao(pendencia, detalhado):
    sugestao = (pendencia.evidencias or {}).get("sugestao_ia")
    if not isinstance(sugestao, dict):
        return None
    resumo = {"peca": sugestao.get("peca"), "confianca": sugestao.get("confianca")}
    if detalhado:
        resumo["justificativa"] = sugestao.get("justificativa")
    return resumo


def preco_do_anuncio(pendencia):
    return _preco(pendencia)


def _preco(pendencia):
    anuncio = (pendencia.dados_originais or {}).get("anuncio") or {}
    minimo = _numero(anuncio.get("priceMin", anuncio.get("price")))
    maximo = _numero(anuncio.get("priceMax", anuncio.get("price")))
    return None if minimo is None else {"minimo": minimo, "maximo": maximo if maximo is not None else minimo}


def _numero(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


_FICHA = (("capacidade_gb", "{} GB"), ("tipo", "{}"), ("interface", "{}"), ("formato", "{}"),
          ("velocidade_leitura_mbps", "leitura {} MB/s"), ("velocidade_gravacao_mbps", "gravação {} MB/s"))


def resumir_ficha(peca):
    """Resumo do que a peça já tem na ficha; o que falta simplesmente não aparece."""
    return [texto.format(getattr(peca, campo)) for campo, texto in _FICHA
            if peca is not None and getattr(peca, campo, None) not in (None, "")]


def _candidato(candidato):
    referencia = str(candidato.get("peca", ""))
    categoria, _, identificador = referencia.partition(":")
    modelo = next((m for m in MODELOS_PECAS if m.__tablename__ == categoria), None)
    peca = modelo.buscar_por_id(int(identificador)) if modelo and identificador.isdecimal() else None
    return {
        "peca": referencia,
        "percentual": candidato.get("percentual"),
        "conflitos": candidato.get("conflitos", []),
        "pendencias": candidato.get("pendencias", []),
        "fabricante": peca.fabricante if peca else None,
        "modelo": peca.modelo if peca else None,
        "part_number": peca.part_number if peca else None,
        "ficha": resumir_ficha(peca),
    }
