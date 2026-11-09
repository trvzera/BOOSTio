from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
"""Recalcula apenas o indicador técnico das peças importadas, sem aprová-las."""
from collections import Counter
from models import db,ControleColeta
from services.peca_service.modelos_pecas import MODELOS_PECAS


class RepositorioReavaliacaoMontagem:
    def __init__(self):self.modelos={m.__tablename__:m for m in MODELOS_PECAS}

    def categorias(self):return list(self.modelos)

    def executar_lote(self,categoria,depois_id,limite,*,simular):
        try:
            db.session.rollback()
            if not ControleColeta.bloquear():raise ValueError('Prepare o catálogo antes de reavaliar')
            pecas=self.modelos[categoria].query.filter(self.modelos[categoria].id>depois_id).order_by(self.modelos[categoria].id).limit(limite).with_for_update().all()
            r=dict(lidas=len(pecas),ultimo_id=pecas[-1].id if pecas else depois_id,analisadas=0,minimos_atendidos=0,pendentes=0,indicadores_alterados=0,pendencias={})
            contagem=Counter()
            for p in pecas:
                if '_pc_part_dataset' not in (p.fontes_especificacoes or {}):continue
                faltantes=pendencias_para_montagem(p);apta=not faltantes
                r['analisadas']+=1;r['minimos_atendidos' if apta else 'pendentes']+=1
                contagem.update(faltantes)
                if p.ficha_montagem_validada is not apta:
                    r['indicadores_alterados']+=1;p.ficha_montagem_validada=apta
            r['pendencias']=dict(contagem)
            if simular:db.session.rollback()
            else:db.session.commit()
            return r
        except Exception:
            db.session.rollback();raise
