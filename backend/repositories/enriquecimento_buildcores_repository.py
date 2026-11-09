from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
"""Acesso ao catálogo e atualizações condicionais, sem criar componentes/ofertas."""
from models import db, ControleColeta
from services.peca_service.modelos_pecas import MODELOS_PECAS
from utils.identidade_peca import assinatura_documento


class RepositorioEnriquecimentoBuildcores:
    def __init__(self):self.modelos={m.__tablename__:m for m in MODELOS_PECAS}

    def listar(self):
        saida=[]
        for cat,modelo in self.modelos.items():
            for p in modelo.query.yield_per(500):
                fontes=p.fontes_especificacoes or {}
                if '_pc_part_dataset' not in fontes:continue
                dados={c.name:getattr(p,c.name) for c in modelo.__table__.columns if c.name not in ('fontes_especificacoes','criado_em','atualizado_em')}
                saida.append(dict(id=p.id,categoria=cat,dados=dados,fontes=fontes,assinatura=assinatura_documento(dict(dados=dados,fontes=fontes))))
        db.session.rollback()
        return saida

    def aplicar_lote(self,propostas,*,simular):
        resultados=[]
        try:
            db.session.rollback()
            if not ControleColeta.bloquear():raise ValueError('Prepare o controle do catálogo')
            for proposta in propostas:
                p=self.modelos[proposta['categoria']].query.filter_by(id=proposta['id']).populate_existing().with_for_update().one()
                dados={c.name:getattr(p,c.name) for c in p.__table__.columns if c.name not in ('fontes_especificacoes','criado_em','atualizado_em')}
                atual=assinatura_documento(dict(dados=dados,fontes=p.fontes_especificacoes or {}))
                if atual!=proposta['assinatura']:
                    resultados.append(dict(peca=f"{proposta['categoria']}:{p.id}",acao='conflito_concorrencia'));continue
                fontes=dict(p.fontes_especificacoes or {})
                alterados=[]
                for campo,valor in proposta['alteracoes'].items():
                    if campo in {'id','fabricante','modelo','preco','esgotado','consumo_w','kabum_external','referencia_interna','status_validacao','validado_em','validacao_motivo','ficha_montagem_validada','fontes_especificacoes','criado_em','atualizado_em','preco_atualizado_em','imagem_url'} or campo.startswith('benchmark_'):
                        raise ValueError('Campo protegido no enriquecimento')
                    if getattr(p,campo) is not None:raise ValueError('Campo deixou de estar vazio')
                    setattr(p,campo,valor);fontes[campo]=proposta['fontes'][campo];alterados.append(campo)
                if alterados:
                    p.fontes_especificacoes=fontes
                    p.ficha_montagem_validada=not pendencias_para_montagem(p)
                    db.session.flush()
                resultados.append(dict(peca=f"{proposta['categoria']}:{p.id}",acao='proposta' if simular else 'atualizada' if alterados else 'inalterada',campos=alterados,
                  pendencias_montagem=pendencias_para_montagem(p)))
            if simular:db.session.rollback()
            else:db.session.commit()
            return resultados
        except Exception:
            db.session.rollback();raise
