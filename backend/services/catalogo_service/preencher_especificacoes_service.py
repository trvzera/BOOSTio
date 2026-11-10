"""Preenche lacunas comprovadas nas peças existentes, independente da loja."""
from sqlalchemy.exc import SQLAlchemyError
from models import ProdutoPendente
from models.modelos_pecas import MODELOS_PECAS
from .classificar_pendencias_service import ClassificarPendenciasService
from .enriquecer_peca_existente_service import EnriquecerPecaExistenteService
from .indice_candidatos_service import IndiceCandidatosService


class PreencherEspecificacoesService:
    def __init__(self, normalizador=None):
        self.normalizar = normalizador or ClassificarPendenciasService.normalizar_interno

    def executar(self, *, limite=100, depois_id=0, categoria=None, simular=True):
        if type(limite) is not int or not 1 <= limite <= 200:
            raise ValueError('Limite entre 1 e 200 anúncios')
        if type(depois_id) is not int or depois_id < 0:
            raise ValueError('Cursor inválido')
        modelos = {m.__tablename__: m for m in MODELOS_PECAS}
        resumo = dict(simulacao=simular, propostas=0, atualizadas=0, inalteradas=0,
                      revisao=0, sem_correspondencia=0, falhas=0, ultima_pendencia_id=depois_id, detalhes=[])
        motor = EnriquecerPecaExistenteService()
        for pendencia in ProdutoPendente.listar_para_revisao(depois_id, limite, categoria):
            identificador = pendencia.id
            try:
                modelo = modelos.get(pendencia.categoria_sugerida)
                if modelo is None:
                    raise ValueError('Categoria desconhecida')
                indice = IndiceCandidatosService.carregar(modelo)
                produtos = tuple(self.normalizar(pendencia))
                pecas = {p.id:p for produto in produtos for p in indice.candidatos(produto)}
                candidatos = []
                for peca in pecas.values():
                    propostas = [motor.preparar(peca, produto) for produto in produtos]
                    if propostas and all(p['status'] in ('proposta', 'inalterada') for p in propostas):
                        candidatos.append((peca, propostas))
                if len(candidatos) > 1:
                    resultado = dict(status='revisao', motivo='Código e ficha correspondem a mais de uma peça')
                elif not candidatos:
                    resultado = dict(status='sem_correspondencia', motivo='Sem identidade e ficha suficientes para preencher')
                else:
                    peca, propostas = candidatos[0]
                    if any(p.get('dados') != propostas[0].get('dados') for p in propostas):
                        resultado = dict(status='revisao', motivo='Título e ficha divergem')
                    else:
                        resultado = motor.executar(peca, produtos[0], simular=simular)
                contador = {'proposta':'propostas','atualizada':'atualizadas','inalterada':'inalteradas'}.get(resultado['status'], resultado['status'])
                resumo[contador] += 1
                resumo['detalhes'].append(dict(pendencia_id=identificador, **resultado))
            except (ValueError, TypeError, SQLAlchemyError):
                from models import db
                db.session.rollback()
                resumo['falhas'] += 1
                resumo['detalhes'].append(dict(pendencia_id=identificador, status='falha', motivo='Falha ao validar ou persistir especificações; confira o esquema e a ficha'))
            resumo['ultima_pendencia_id'] = identificador
        return resumo
