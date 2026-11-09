from repositories.identificadores_peca_repository import separar_identificadores
"""Coordena lotes; persistência e migração de cada peça ficam nos models."""
from sqlalchemy.exc import SQLAlchemyError
from models import Oferta
from services.peca_service.modelos_pecas import MODELOS_PECAS


class SepararIdentificadoresService:
    def executar(self, *, simular=True, limite_lote=100):
        if type(limite_lote) is not int or not 1 <= limite_lote <= 500:
            raise ValueError('Lote deve ter entre 1 e 500 peças')
        resumo = dict(simulacao=simular, examinadas=0, alteradas=0, inalteradas=0,
                      ofertas_criadas=0, revisao=0, falhas=0, detalhes=[])
        ambiguos = Oferta.identidades_kabum_ambiguas()
        for modelo in MODELOS_PECAS:
            depois = 0
            while True:
                lote = modelo.lote_para_identificadores(depois, limite_lote)
                if not lote:
                    break
                for peca in lote:
                    depois = peca.id
                    try:
                        r = separar_identificadores(peca, simular=simular, ids_ambiguos=ambiguos)
                        resumo['examinadas'] += 1
                        resumo['alteradas' if r['alterada'] else 'inalteradas'] += 1
                        resumo['ofertas_criadas'] += r['oferta'] == 'criada'
                        resumo['revisao'] += r['oferta'] == 'revisao'
                        resumo['detalhes'].append(r)
                    except (ValueError, SQLAlchemyError):
                        resumo['falhas'] += 1
                        raise ValueError('Separação interrompida; confira esquema e referências antes de repetir') from None
        return resumo
