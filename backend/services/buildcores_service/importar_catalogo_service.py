"""Importação direta das fichas nativas, sem ofertas, preços ou novas aprovações."""

from decimal import Decimal,InvalidOperation
from sqlalchemy import Integer,Numeric,Float,Boolean,String
from sqlalchemy.exc import SQLAlchemyError
from repositories.importacao_buildcores_repository import RepositorioImportacaoBuildcores
from models.modelos_pecas import MODELOS_PECAS
from services.catalogo_service.normalizar_produto import codigo
from .ler_snapshot_service import LerSnapshotBuildcoresService


class ImportarCatalogoBuildcoresService:
    def __init__(self,repositorio=None):self.repositorio=repositorio or RepositorioImportacaoBuildcores()

    @staticmethod
    def preparar(r):
        r={**r,'dados':dict(r['dados'])}
        meta=r['bruto']['metadata'];fab=meta['manufacturer'].strip();nome=meta['name'].strip()
        modelo=nome[len(fab):].strip(' -') if nome.casefold().startswith(fab.casefold()+' ') else nome
        r.update(fabricante_original=fab,modelo=modelo)
        if not fab or not modelo:raise ValueError('Fabricante/modelo ausente')
        mpns=[v for v in r['mpns'] if (len(v)>=8 or '-' in v or '/' in v) and codigo(v)!=codigo(nome)]
        r['mpn_unico']=mpns[0] if len(r['mpns'])==1 and len(mpns)==1 else None
        classe=next(m for m in MODELOS_PECAS if m.__tablename__==r['categoria'])
        dados={**r['dados'],'fabricante':fab,'modelo':modelo}
        for c in classe.__table__.columns:
            if not c.nullable and c.name not in ('id','criado_em') and dados.get(c.name) is None:raise ValueError('Campo necessário ausente: '+c.name)
        for campo,v in dados.items():
            tipo=classe.__table__.c[campo].type
            if isinstance(tipo,Boolean):
                if type(v) is not bool:raise ValueError('Booleano inválido: '+campo)
            elif isinstance(tipo,(Integer,Numeric,Float)):
                try:
                    n=Decimal(str(v))
                    if isinstance(v,bool) or not n.is_finite() or n<0 or isinstance(tipo,Integer) and n!=int(n):raise ValueError('Número inválido: '+campo)
                except InvalidOperation:raise ValueError('Número inválido: '+campo) from None
            elif isinstance(tipo,String) and (not isinstance(v,str) or not v.strip() or tipo.length and len(v)>tipo.length):raise ValueError('Texto inválido: '+campo)
        return r

    def executar(self,pasta,*,simular=True,tamanho_lote=100,progresso=None):
        if type(simular) is not bool or type(tamanho_lote) is not int or not 1<=tamanho_lote<=1000:raise ValueError('Opções inválidas')
        snapshot=LerSnapshotBuildcoresService().executar(pasta)
        resumo=dict(simulacao=simular,commit=snapshot['commit'],fichas_lidas=len(snapshot['registros'])+len(snapshot['invalidos']),
          fora_escopo=snapshot['fora_escopo'],criadas=0,propostas=0,existentes=0,inalteradas=0,revisao=0,
          invalidas=len(snapshot['invalidos']),falhas=0,interrompido=False,novas_com_minimos=0,novas_pendentes=0,campos_completados=0,categorias={},pendencias={},detalhes=list(snapshot['invalidos']))
        registros=[]
        for r in snapshot['registros']:
            try:registros.append(self.preparar(r))
            except (ValueError,TypeError) as erro:
                resumo['invalidas']+=1;resumo['detalhes'].append(dict(id_externo=r['origem']['id_externo'],categoria=r['categoria'],acao='invalida',motivo=str(erro)))
        resultados_por_id={}
        fila=registros
        resumo.update(rodadas=0,estabilizada=False)
        for rodada in range(6):
            resumo['rodadas']=rodada+1;resolvidas=0
            for inicio in range(0,len(fila),tamanho_lote):
                lote=fila[inicio:inicio+tamanho_lote]
                try:resultados=self.repositorio.executar_lote(lote,simular=simular)
                except (ValueError,SQLAlchemyError):
                    resumo['falhas']+=len(lote);resumo['interrompido']=True;break
                for r in resultados:
                    ident=(r['categoria'],r['id_externo'])
                    anterior=resultados_por_id.get(ident)
                    if r['acao']!='revisao':resolvidas+=1
                    for valor,sinal in ((anterior,-1),(r,1)):
                        if valor is None:continue
                        chave={'criada':'criadas','proposta':'propostas','existente':'existentes','inalterada':'inalteradas','revisao':'revisao'}[valor['acao']]
                        resumo[chave]+=sinal
                        cat=resumo['categorias'].setdefault(valor['categoria'],{})
                        cat[chave]=cat.get(chave,0)+sinal
                        resumo['campos_completados']+=sinal*valor.get('campos',0)
                        if valor['acao'] in ('criada','proposta'):
                            tipo='novas_com_minimos' if valor['minimos_atendidos'] else 'novas_pendentes'
                            resumo[tipo]+=sinal;cat[tipo]=cat.get(tipo,0)+sinal
                            for campo in valor['pendencias']:resumo['pendencias'][campo]=resumo['pendencias'].get(campo,0)+sinal
                    resultados_por_id[ident]=r
                if progresso:progresso(resumo)
            if resumo['interrompido']:break
            pendentes=[r for r in registros if resultados_por_id.get((r['categoria'],r['origem']['id_externo']),{}).get('acao')=='revisao']
            if not pendentes or not resolvidas:
                resumo['estabilizada']=True;break
            fila=pendentes
        resumo['detalhes'].extend(resultados_por_id.values())
        return resumo
