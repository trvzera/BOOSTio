from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
"""Persistência do catálogo em lotes protegidos pelo bloqueio já existente."""
from collections import defaultdict
from sqlalchemy import null
from models import db, ControleColeta
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.normalizar_produto import nome


class GravarDatasetPecasService:
    def __init__(self):
        self.modelos={m.__tablename__:m for m in MODELOS_PECAS}
        self.indice=None;self.versao=None

    def _carregar(self):
        self.indice=defaultdict(list);self.origens={};self.virtuais={}
        for categoria,modelo in self.modelos.items():
            for p in modelo.iterar_todas():
                fonte=(p.fontes_especificacoes or {}).get('_pc_part_dataset',{})
                if fonte.get('identidade'):self.origens[(categoria,fonte['identidade'])]=p.id
                self.indice[(categoria,nome(p.fabricante+' '+p.modelo))].append(p.id)

    def executar_lote(self,registros,*,simular):
        resultados=[]
        try:
            db.session.rollback()
            if not ControleColeta.bloquear():raise ValueError('Prepare o catálogo antes de importar')
            versao=db.session.get(ControleColeta,1,populate_existing=True).versao
            if self.indice is None or not simular and self.versao!=versao-1:self._carregar()
            for r in registros:resultados.append(self._processar(r,simular))
            if simular:
                db.session.rollback()
            else:
                db.session.commit();self.versao=versao
            return resultados
        except Exception:
            db.session.rollback();self.indice=None;self.versao=None
            raise

    def _processar(self,r,simular):
        cat=r['categoria'];modelo=self.modelos[cat];dados=r['dados']
        if (cat,r['identidade']) in self.origens:return dict(acao='inalterada',categoria=cat)
        chave=(cat,nome(dados['fabricante']+' '+dados['modelo']))
        base=(cat,nome(r['titulo']))
        ids=set(self.indice.get(chave,[]) + self.indice.get(base,[]))
        if ids:
            # Uma identidade comercial já presente nunca gera outra peça automaticamente.
            # Mesmo nome com variantes/especificações desconhecidas exige revisão.
            # A projeção em nossas colunas não distingue todos os SKUs (por exemplo,
            # clocks de fábrica da GPU). Sem a mesma identidade de origem, não fundir.
            return dict(acao='revisao',categoria=cat,motivo='Nome existente com variantes ou especificações não comprovadas',ids=sorted(ids))
        valores={**dados,'part_number':null(),
            'status_validacao':'em_revisao','ficha_montagem_validada':False,
            'validacao_motivo':'Catálogo de terceiros sem MPN/GTIN estruturado; completar e validar antes de publicar'}
        for coluna in modelo.__table__.columns:
            if coluna.nullable and coluna.default is not None and coluna.name not in valores:
                valores[coluna.name]=null()
        evidencia=dict(**r['origem'],identidade=r['identidade'],nome_original=r['titulo'],dados_originais=r['bruto'])
        valores['fontes_especificacoes']={k:dict(url=r['origem']['url'],arquivo_sha256=r['origem']['sha256'],campo=k)
            for k in dados}
        valores['fontes_especificacoes']['_pc_part_dataset']=evidencia
        if simular:
            from types import SimpleNamespace
            p=SimpleNamespace(id=-(len(self.virtuais)+1),**dados)
            self.virtuais[p.id]=p
        else:
            p=modelo(**valores);db.session.add(p);db.session.flush()
            p.ficha_montagem_validada=not pendencias_para_montagem(p)
        self.origens[(cat,r['identidade'])]=p.id
        self.indice[chave].append(p.id)
        return dict(acao='proposta' if simular else 'criada',categoria=cat)
