from models import VinculoMercadoLivre


def catalogo_que_ocupa_a_peca(pendencia, peca):
    catalogo_da_pendencia = ((pendencia.dados_originais or {}).get("catalogo") or {}).get("id")
    if peca is None or not catalogo_da_pendencia:
        return None
    vinculo = VinculoMercadoLivre.buscar(peca.__tablename__, peca.id)
    return vinculo.catalogo_id if vinculo and vinculo.catalogo_id != catalogo_da_pendencia else None
