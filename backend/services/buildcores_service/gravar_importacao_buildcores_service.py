from services.catalogo_service.pendencias_montagem_service import pendencias_para_montagem
"""Importação transacional do OpenDB; consultas e deduplicação ficam no repositório."""
from collections import defaultdict


from difflib import SequenceMatcher
import re
from sqlalchemy import null
from models import db,ControleColeta
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.normalizar_produto import nome,codigo
from services.buildcores_service.normalizar_ficha_service import fabricante
from services.buildcores_service.comparar_fichas_service import CompararFichasBuildcoresService,chave_modelo,equivalente


class GravarImportacaoBuildcoresService:
    def __init__(self):
        self.modelos={m.__tablename__:m for m in MODELOS_PECAS}
        self.indice=None;self.versao=None;self.motor=CompararFichasBuildcoresService()

    def _carregar(self):
        self.indice=defaultdict(set);self.origens=defaultdict(set);self.mpns=defaultdict(set);self.tokens=defaultdict(set);self.registros={};self.guarda=defaultdict(set);self.codigos_nome=defaultdict(set);self.gpus=defaultdict(set);self.chaves=defaultdict(set)
        for cat,m in self.modelos.items():
            for p in m.iterar_todas():self._indexar(self._dados(p,cat))

    @staticmethod
    def _dados(p,cat):
        return dict(id=p.id,categoria=cat,dados={c.name:getattr(p,c.name) for c in p.__table__.columns if c.name not in ('fontes_especificacoes','criado_em','atualizado_em')},fontes=p.fontes_especificacoes or {})

    @staticmethod
    def _origem(p):return p['fontes'].get('_pc_part_dataset') or p['fontes'].get('_buildcores_importacao') or {}

    def _chave(self,p):
        origem=self._origem(p)
        from services.buildcores_service.normalizar_ficha_service import cores
        raw=origem.get('dados_originais',{})
        titulo=origem.get('nome_original') or p['dados']['modelo']
        return chave_modelo(p['categoria'],titulo,fabricante(p['dados']['fabricante']),cores(raw.get('color')))

    def _indexar(self,p):
        cat=p['categoria'];ident=(cat,p['id']);self.registros[ident]=p
        chave=self._chave(p);marca=fabricante(p['dados']['fabricante'])
        self.indice[(cat,marca,chave)].add(ident)
        base=p['dados']['fabricante']+' '+p['dados']['modelo']
        chave_base=chave_modelo(cat,base,marca)
        self.chaves[ident].update((chave,chave_base))
        self.guarda[(cat,marca,self._chave_guarda(cat,base,marca))].add(ident)
        for token in re.findall(r'[a-z0-9][a-z0-9/_.-]{5,99}',nome(base)):
            if re.search('[a-z]',token) and re.search('[0-9]',token):
                self.codigos_nome[(cat,marca,codigo(token))].add(ident)
                if len(token)>=8:self.codigos_nome[(cat,'*',codigo(token))].add(ident)
        titulo=self._origem(p).get('nome_original') or p['dados']['modelo']
        self.guarda[(cat,marca,self._chave_guarda(cat,titulo,marca))].add(ident)
        for token in re.findall(r'[a-z0-9][a-z0-9/_.-]{5,99}',nome(titulo)):
            if re.search('[a-z]',token) and re.search('[0-9]',token):
                self.codigos_nome[(cat,marca,codigo(token))].add(ident)
                if len(token)>=8:self.codigos_nome[(cat,'*',codigo(token))].add(ident)
        if cat=='placa_video':
            raw=self._origem(p).get('dados_originais',{})
            chave_gpu=self._guarda_gpu(titulo,raw.get('chipset') or p['dados'].get('modelo_referencia'),marca)
            if chave_gpu:self.gpus[(marca,chave_gpu)].add(ident)
        for alias in self.chaves[ident]:
            for token in alias.split('|'):
                if len(token)>=3 and re.search(r'\d',token):self.tokens[(cat,marca,token)].add(ident)
        mpn=p['dados'].get('part_number')
        if mpn:self.mpns[(cat,codigo(mpn))].add(ident)
        propria=p['fontes'].get('_buildcores_importacao',{})
        if propria.get('id_externo'):self.origens[(cat,propria['id_externo'])].add(ident)
        for id_externo in propria.get('origens',{}):self.origens[(cat,id_externo)].add(ident)
        for v in p['fontes'].values():
            if isinstance(v,dict) and v.get('provedor')=='BuildCores OpenDB' and v.get('id_externo'):
                self.origens[(cat,v['id_externo'])].add(ident)

    def executar_lote(self,registros,*,simular=True):
        try:
            db.session.rollback()
            if not ControleColeta.bloquear():raise ValueError('Prepare o controle do catálogo')
            versao=db.session.get(ControleColeta,1,populate_existing=True).versao
            if self.indice is None or not simular and self.versao!=versao-1:self._carregar()
            resultados=[self._processar(r,simular) for r in registros]
            if simular:db.session.rollback()
            else:db.session.commit();self.versao=versao
            return resultados
        except Exception:
            db.session.rollback();self.indice=None;self.versao=None
            raise

    def _proximos(self,r,chave):
        cat=r['categoria'];marca=r['fabricante'];proximos=set()
        aliases=[r['nome'],*r['mpns'],*(r['bruto'].get('metadata',{}).get('part_numbers') or [])]
        for alias in aliases:
            if not isinstance(alias,str):continue
            proximos.update(self.guarda.get((cat,marca,self._chave_guarda(cat,alias,marca)),set()))
            proximos.update(self.codigos_nome.get((cat,marca,codigo(alias)),set()))
            if len(alias)>=8:proximos.update(self.codigos_nome.get((cat,'*',codigo(alias)),set()))
        if cat=='placa_video':
            proximos.update(self.gpus.get((marca,self._guarda_gpu(r['nome'],r['bruto'].get('chipset'),marca)),set()))
        if proximos:return proximos
        grupos=[self.tokens[(r['categoria'],r['fabricante'],t)] for t in chave.split('|') if len(t)>=3 and re.search(r'\d',t)]
        grupos=[g for g in grupos if g]
        if not grupos:return set()
        candidatos=set().union(*grupos)
        comparador=SequenceMatcher(None,'',chave)
        for ident in sorted(candidatos):
            for alias in self.chaves[ident]:
                if not alias or 2*min(len(alias),len(chave))/(len(alias)+len(chave))<.92:continue
                comparador.set_seq1(alias)
                if comparador.quick_ratio()>=.92 and comparador.ratio()>=.92:return {ident}
        return set()

    @staticmethod
    def _chave_guarda(cat,titulo,marca):
        s=nome(titulo)
        s=re.split(r'\bwith\b',s,maxsplit=1)[0]
        s=re.sub(r'\b\d+(?:[.,]\d+)?[- ]inch\b',' ',s)
        s=re.sub(r'\bddr\s*[1-5]\s*[- ]\s*\d{3,5}\b',' ',s)
        s=re.sub(r'\b\d+(?:[.,]\d+)?\s*["″]|\b\d{3,4}p\b|\b[248]k\b',' ',s)
        s=re.sub(r'\b(?:black|white|gray|grey|silver|gold|red|blue|green|pink|orange|purple|brown)\b',' ',s)
        s=re.sub(r'\b(?:micro|mini|mid|full|atx|matx|itx|eatx|tower|chassis|tempered|glass|monitor|curved|ips|va|tn|oled|qled|gddr\s*[3-7]x?|rgb|argb|oem|tray|boxed|box|lga\s*\d+(?:-\d+)?)\b',' ',s)
        if 'threadripper' in s:s=re.sub(r'\bryzen\b',' ',s)
        return chave_modelo(cat,s,marca)

    @classmethod
    def _guarda_gpu(cls,titulo,chip,marca):
        from services.catalogo_service.normalizar_produto import variante
        v=variante('placa_video',chip or '')
        if not v:return None
        s=nome(titulo)
        s=s.replace(nome(chip),' ')
        s=re.sub(r'\b(?:geforce|radeon|nvidia|amd|gaming)\b',' ',s)
        return v+'::'+cls._chave_guarda('placa_video',s,marca)

    def _avaliar(self,p,r,forte):
        if forte:
            conflitos=[]
            from services.buildcores_service.normalizar_ficha_service import cores
            anteriores=self._origem(p).get('dados_originais',{})
            cor_anterior=cores(anteriores.get('color'))
            if cor_anterior and r['cores'] and cor_anterior!=r['cores']:conflitos.append('cor')
            if r['categoria']=='placa_video':
                for antigo,novo in (('core_clock','core_base_clock'),('boost_clock','core_boost_clock')):
                    v=anteriores.get(novo,anteriores.get(antigo))
                    if v is not None and r['bruto'].get(novo) is not None and equivalente('placa_video',novo,v,r['bruto'][novo]) is False:conflitos.append(novo)
            for campo,v in r['dados'].items():
                if p['dados'].get(campo) is not None and equivalente(r['categoria'],campo,p['dados'][campo],v) is False:conflitos.append(campo)
            return not conflitos and fabricante(p['dados']['fabricante'])==r['fabricante']
        if '_buildcores_importacao' in p['fontes']:return False
        return self.motor.avaliar(p,r)['confirmada']

    def _processar(self,r,simular):
        cat=r['categoria'];origem=r['origem'];m=self.modelos[cat]
        fontes_existentes=self.origens.get((cat,origem['id_externo']),set())
        if len(fontes_existentes)==1:
            p=self.registros[next(iter(fontes_existentes))]
            anterior=p['fontes'].get('_buildcores_importacao',{})
            fonte_anterior=anterior if anterior.get('id_externo')==origem['id_externo'] else anterior.get('origens',{}).get(origem['id_externo'],{})
            if fonte_anterior.get('sha256')==origem['sha256']:
                return dict(acao='inalterada',categoria=cat,id_externo=origem['id_externo'])
            if fonte_anterior:
                return dict(acao='revisao',categoria=cat,id_externo=origem['id_externo'],motivo='A ficha da origem mudou; não substituir automaticamente')
        fortes=set(fontes_existentes)
        for mpn in r['mpns']:fortes.update(self.mpns.get((cat,codigo(mpn)),set()))
        chave=self.motor.chave_remota(r)
        candidatos=fortes or self.indice.get((cat,r['fabricante'],chave),set())
        if candidatos:
            validos=[i for i in candidatos if self._avaliar(self.registros[i],r,bool(fortes))]
            if len(validos)!=1 or len(candidatos)!=1:
                return dict(acao='revisao',categoria=cat,id_externo=origem['id_externo'],motivo='Identidade/modelo existente ambíguo ou conflitante')
            ident=validos[0];p=self.registros[ident]
            alteracoes={k:v for k,v in r['dados'].items() if p['dados'].get(k) is None}
            if cat=='processador':alteracoes.pop('cooler',None)
            evidencia=dict(p['fontes'].get('_buildcores_importacao') or self._evidencia(r))
            evidencia['origens']={**evidencia.get('origens',{}),origem['id_externo']:origem}
            novas_fontes={**p['fontes'],**{k:r['fontes'][k] for k in alteracoes},'_buildcores_importacao':evidencia}
            if not simular:
                atual=db.session.get(m,p['id'])
                for k,v in alteracoes.items():setattr(atual,k,v)
                atual.fontes_especificacoes=novas_fontes
                atual.ficha_montagem_validada=not pendencias_para_montagem(atual)
                db.session.flush()
            p['dados'].update(alteracoes);p['fontes']=novas_fontes;self._indexar(p)
            return dict(acao='existente',categoria=cat,id_externo=origem['id_externo'],campos=len(alteracoes))
        if self._proximos(r,chave):
            return dict(acao='revisao',categoria=cat,id_externo=origem['id_externo'],motivo='Nome próximo de peça existente; revisar antes de cadastrar')
        valores={**r['dados'],'fabricante':r['fabricante_original'],'modelo':r['modelo'],
          'part_number':r.get('mpn_unico') or null(),
          'referencia_interna':'BUILDCORES:'+origem['id_externo'],
          'status_validacao':'em_revisao','ficha_montagem_validada':False,
          'validacao_motivo':'Ficha BuildCores importada; identidade e compatibilidade final dependem de validação',
          'fontes_especificacoes':{**r['fontes'],'_buildcores_importacao':self._evidencia(r)}}
        for c in m.__table__.columns:
            if c.nullable and c.default is not None and c.name not in valores:valores[c.name]=null()
        if simular:
            limpos={k:v for k,v in valores.items() if k in r['dados'] or k in ('fabricante','modelo','referencia_interna','status_validacao')}
            for c in m.__table__.columns:limpos.setdefault(c.name,None)
            limpos['part_number']=r.get('mpn_unico')
            objeto=m(**limpos);objeto.id=-(len(self.registros)+1)
        else:
            objeto=m(**valores);db.session.add(objeto);db.session.flush();db.session.refresh(objeto)
        objeto.ficha_montagem_validada=not pendencias_para_montagem(objeto)
        p=self._dados(objeto,cat);p['fontes']=valores['fontes_especificacoes'];self._indexar(p)
        return dict(acao='proposta' if simular else 'criada',categoria=cat,id_externo=origem['id_externo'],minimos_atendidos=objeto.ficha_montagem_validada,pendencias=pendencias_para_montagem(objeto))

    @staticmethod
    def _evidencia(r):
        return {**r['origem'],'nome_original':r['nome'],'mpns':r['mpns'],'gtins':r['gtins'],'dados_originais':r['bruto']}
