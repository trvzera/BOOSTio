from copy import deepcopy
from models import db, FichaTecnicaCatalogo
from repositories.catalogo_tecnico_repository import RepositorioCatalogoTecnico
from .importar_base_tecnica_service import ImportarBaseTecnicaService


class RevisarFichaService:
    def executar(self,identificador,acao,*,responsavel,motivo,simular=True):
        if not isinstance(responsavel,str) or not responsavel.strip() or len(responsavel)>120:raise ValueError('Informe o responsável')
        if not isinstance(motivo,str) or not motivo.strip() or len(motivo)>1000:raise ValueError('Informe o motivo')
        if acao not in ('aprovar','rejeitar','reabrir'):raise ValueError('Ação inválida')
        repo=RepositorioCatalogoTecnico()
        if acao=='aprovar':
            ficha=FichaTecnicaCatalogo.buscar(identificador)
            if ficha is None:raise ValueError('Ficha não encontrada')
            if ficha.estado=='rejeitada':raise ValueError('Reabra explicitamente a ficha antes de aprovar')
            documento=deepcopy(ficha.documento);assinatura=ficha.assinatura_documento
            db.session.rollback()
            # O importador relê e valida a origem sob a mesma trava global.
            return ImportarBaseTecnicaService(repo).processar(documento,simular=simular,responsavel=responsavel,assinatura_esperada=assinatura)
        with repo.transacao(simular=simular):
            ficha=FichaTecnicaCatalogo.buscar(identificador,bloquear=True)
            if ficha is None:raise ValueError('Ficha não encontrada')
            if acao=='reabrir' and ficha.estado!='rejeitada':raise ValueError('Somente fichas rejeitadas exigem reabertura')
            if acao=='rejeitar' and ficha.estado=='importada':raise ValueError('Ficha já importada: revise a peça antes de despublicar')
            ficha.transicionar('rejeitada' if acao=='rejeitar' else 'em_revisao',motivo=motivo,responsavel=responsavel,reabrir=acao=='reabrir')
            return dict(simulacao=simular,**ficha.resumo())
