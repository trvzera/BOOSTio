"""Identidades revisadas (MPN e GTIN) das peças, para o matching de ofertas."""
from sqlalchemy import inspect

from models import db, IdentidadeFabricante
from services.catalogo_service.normalizar_produto import gtin, codigo
from utils.identidade_peca import assinatura_peca, assinatura_tecnica


class IdentidadesParaMatchingService:
    def executar(self, pecas):
        if not pecas:return {}
        tabela=pecas[0].__tablename__;locais={p.id:p for p in pecas}
        registros=[]
        if inspect(db.session.connection()).has_table(IdentidadeFabricante.__tablename__):
            registros=IdentidadeFabricante.listar_das_pecas(tabela,locais)
        resultado={r.peca_id:{'mpn':r.mpn,'gtin':r.gtin} for r in registros
            if r.assinatura_peca==assinatura_peca(locais[r.peca_id]) and IdentidadeFabricante.conferem(locais[r.peca_id],r.especificacoes)}
        for p in pecas:
            prova=(p.fontes_especificacoes or {}).get('_identidade_tecnica',{})
            if (not prova or not p.publicavel or prova.get('assinatura_peca')!=assinatura_peca(p)
                    or prova.get('assinatura_tecnica')!=assinatura_tecnica(p)):continue
            mpn=p.part_number or prova.get('mpn');ean=prova.get('gtin')
            if ean is not None and gtin(ean) is None:continue
            anterior=resultado.get(p.id,{})
            if any(anterior.get(k) and v and codigo(anterior[k])!=codigo(v) for k,v in [('mpn',mpn),('gtin',ean)]):continue
            resultado[p.id]={'mpn':anterior.get('mpn') or mpn,'gtin':anterior.get('gtin') or ean}
        return resultado
