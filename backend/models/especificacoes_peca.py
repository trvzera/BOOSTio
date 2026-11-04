"""Persistência atômica das lacunas, com origem por campo e controle de concorrência."""
from datetime import datetime, timezone
from . import db
from .identificadores_peca import _vinculos, reassinar_vinculos
from utils.identidade_peca import assinatura_peca, assinatura_tecnica
from utils.codigos_peca import codigo_interno


def preencher_especificacoes(peca, proposta, assinatura, *, simular=True):
    from services.catalogo_service.enriquecer_peca_existente_service import EnriquecerPecaExistenteService
    from services.catalogo_service.conferir_especificacoes_service import ESSENCIAIS, OPCIONAIS
    try:
        db.session.refresh(peca, with_for_update=True)
        if assinatura_peca(peca) != assinatura or assinatura_tecnica(peca) != proposta['assinatura_tecnica']:
            raise ValueError('Peça mudou durante a consulta; repita a validação')
        if codigo_interno(peca.part_number):
            raise ValueError('Execute catalogo-identificadores-separar antes do enriquecimento')
        if proposta.get('criterio') == 'anuncio_original_e_especificacoes_compativeis':
            from .oferta import Oferta
            origem = proposta.get('origem') or {}
            if not Oferta.corresponde_origem(peca, origem.get('loja'), origem.get('id_externo'), bloquear=True):
                raise ValueError('Oferta original mudou; repita a validação')
        vinculos, anterior = _vinculos(peca), peca.part_number
        fontes = dict(peca.fontes_especificacoes or {})
        agora = datetime.now(timezone.utc).isoformat()
        dados = proposta['dados']
        permitidos = {EnriquecerPecaExistenteService.ALIASES.get(c, c) for c in (
            *ESSENCIAIS.get(peca.__tablename__, ()), *OPCIONAIS.get(peca.__tablename__, ()))} | {'part_number', 'codigo_modelo_fabricante'}
        for campo, valor in dados.items():
            if campo not in permitidos or campo in EnriquecerPecaExistenteService.CAMPOS_PROTEGIDOS - {'part_number'} or campo not in peca.__table__.columns:
                raise ValueError('Campo protegido ou desconhecido')
            if not EnriquecerPecaExistenteService.ausente(getattr(peca,campo)):
                raise ValueError('Campo já preenchido; não sobrescrever')
            if campo in fontes and fontes[campo].get('valor') != valor:
                raise ValueError('Fonte anterior diverge; revisão necessária')
            setattr(peca,campo,valor)
            fontes[campo] = {**proposta['fontes'][campo], 'valor':valor, 'codigo':proposta['codigo'],
                'consultado_em':agora, 'sha256_especificacoes':proposta['sha256'], 'criterio':proposta['criterio']}
        peca.fontes_especificacoes = fontes
        for campo in dados:
            fontes[campo]['assinatura_peca'] = assinatura_peca(peca)
        reassinar_vinculos(peca,vinculos,assinatura,anterior,campos_preenchidos=dados)
        if simular:
            db.session.rollback()
        else:
            db.session.commit()
        return dict(status='proposta' if simular else 'atualizada',peca=f'{peca.__tablename__}:{peca.id}',
                    dados=dados,fontes=proposta['fontes'],codigo=proposta['codigo'])
    except Exception:
        db.session.rollback()
        raise
