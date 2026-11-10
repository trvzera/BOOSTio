"""Enriquece peças a partir do anúncio de origem, com arquivo reproduzível."""
import json
from pathlib import Path
from dataclasses import replace
from sqlalchemy.exc import SQLAlchemyError
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService
from .normalizar_ficha_kabum_service import NormalizarFichaKabumService


class PreencherFichasOriginaisService:
    def executar(self, pasta, *, simular=True, categoria=None):
        pasta = Path(pasta)
        if not pasta.is_dir():
            raise ValueError('Pasta de fichas inexistente')
        modelos = [m for m in MODELOS_PECAS if categoria is None or m.__tablename__ == categoria]
        if not modelos:
            raise ValueError('Categoria inválida')
        resumo = dict(simulacao=simular, examinadas=0, propostas=0, atualizadas=0,
                      inalteradas=0, sem_ficha=0, sem_correspondencia=0, revisao=0, falhas=0, detalhes=[])
        from models import Oferta
        for modelo in modelos:
            depois = 0
            while True:
                lote = modelo.lote_para_identificadores(depois, 100)
                if not lote:
                    break
                for peca in lote:
                    depois = peca.id
                    from utils.medidas_fisicas import produto_kabum
                    externo = produto_kabum(peca.kabum_external)
                    if externo is None:
                        resumo['sem_ficha'] += 1
                        continue
                    arquivo = pasta / f'kabum-{externo}.json'
                    if not arquivo.is_file():
                        resumo['sem_ficha'] += 1
                        continue
                    resumo['examinadas'] += 1
                    try:
                        if arquivo.stat().st_size > 4_000_000:
                            raise ValueError('Arquivo excessivo')
                        dados = json.loads(arquivo.read_text())
                        dto = NormalizarFichaKabumService().executar(dados, modelo.__tablename__, codigo_esperado=externo)
                        dto = replace(dto, contexto={**dto.contexto, 'origem_peca':f'{modelo.__tablename__}:{peca.id}'})
                        if not Oferta.corresponde_origem(peca, 'kabum', externo):
                            resultado = dict(status='revisao', motivo='Oferta original não comprovada; prepare os identificadores')
                        else:
                            resultado = EnriquecerPecaExistenteService().executar(peca, dto, simular=simular)
                        k = {'proposta':'propostas','atualizada':'atualizadas','inalterada':'inalteradas'}.get(resultado['status'], resultado['status'])
                        resumo[k] += 1
                        resumo['detalhes'].append({'peca':f'{modelo.__tablename__}:{peca.id}', **resultado})
                    except (ValueError, TypeError, OSError, SQLAlchemyError):
                        from models import db
                        db.session.rollback()
                        resumo['falhas'] += 1
                        resumo['detalhes'].append(dict(peca=f'{modelo.__tablename__}:{peca.id}', status='falha', motivo='Ficha inválida ou falha ao persistir; nenhum campo desta peça foi confirmado'))
        return resumo
