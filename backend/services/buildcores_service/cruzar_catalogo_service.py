"""Cruza uma revisão local verificada com o catálogo docyx já importado."""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import re
from sqlalchemy.exc import SQLAlchemyError
from repositories.enriquecimento_buildcores_repository import RepositorioEnriquecimentoBuildcores
from .normalizar_ficha_service import NormalizarFichaBuildcoresService, CATEGORIAS, fabricante
from .comparar_fichas_service import CompararFichasBuildcoresService


class CruzarCatalogoBuildcoresService:
    def __init__(self,repositorio=None):self.repositorio=repositorio or RepositorioEnriquecimentoBuildcores()

    def executar(self,pasta,*,simular=True,tamanho_lote=100,progresso=None):
        if type(simular) is not bool or type(tamanho_lote) is not int or not 1<=tamanho_lote<=1000:raise ValueError('Opções inválidas')
        pasta=Path(pasta);manifesto=json.loads((pasta/'manifesto.json').read_text())
        if not isinstance(manifesto,dict) or not isinstance(manifesto.get('arquivos'),dict) or manifesto.get('repositorio')!='https://github.com/buildcores/buildcores-open-db' or not isinstance(manifesto.get('commit'),str) or not re.fullmatch('[0-9a-f]{40}',manifesto['commit']):raise ValueError('Manifesto inválido')
        motor=CompararFichasBuildcoresService();indice=defaultdict(list);normalizador=NormalizarFichaBuildcoresService()
        resumo=dict(simulacao=simular,commit=manifesto['commit'],registros_fonte=0,invalidos_fonte=0,pecas_analisadas=0,sem_candidatos=0,
          conflitos=0,ambiguas=0,confirmadas=0,com_alteracoes=0,inalteradas=0,atualizadas=0,campos_preenchidos=0,
          com_mpn_unico=0,com_mpn_multiplo=0,falhas=0,interrompido=False,categorias={},campos={},detalhes=[])
        for arquivo,info in manifesto['arquivos'].items():
            partes=arquivo.split('/')
            if len(partes)!=3 or partes[0]!='open-db' or partes[1] not in {*CATEGORIAS,'Storage','CPUCooler'}:continue
            if not re.fullmatch('[0-9a-f-]{36}\\.json',partes[2]):raise ValueError('Nome de registro inválido')
            caminho=pasta/arquivo
            if caminho.stat().st_size>2000000:raise ValueError('Registro excessivo')
            corpo=caminho.read_bytes()
            if not isinstance(info,dict):raise ValueError('Metadados de registro inválidos')
            if hashlib.sha256(corpo).hexdigest()!=info.get('sha256'):raise ValueError('Snapshot diverge do manifesto: '+arquivo)
            bruto=json.loads(corpo)
            if not isinstance(bruto,dict):raise ValueError('Registro precisa ser objeto JSON')
            if bruto.get('opendb_id')!=partes[2][:-5]:raise ValueError('Identificador diverge do arquivo')
            origem=dict(url=f"https://github.com/buildcores/buildcores-open-db/blob/{manifesto['commit']}/{arquivo}",
              provedor='BuildCores OpenDB',commit=manifesto['commit'],id_externo=bruto['opendb_id'],sha256=info['sha256'])
            try:r=normalizador.executar(partes[1],bruto,origem)
            except (ValueError,TypeError,KeyError):resumo['invalidos_fonte']+=1;continue
            resumo['registros_fonte']+=1
            chave=motor.chave_remota(r)
            if chave:indice[(r['categoria'],r['fabricante'],chave)].append(r)
        pecas=self.repositorio.listar();propostas=[];relacoes=defaultdict(list)
        for p in pecas:
            resumo['pecas_analisadas']+=1
            cat=p['categoria'];dados=p['dados'];chave=motor.chave_local(p)
            candidatas=indice.get((cat,fabricante(dados['fabricante']),chave),[])
            avaliacoes=[(r,motor.avaliar(p,r)) for r in candidatas]
            validas=[(r,d) for r,d in avaliacoes if d['confirmada']]
            if len(validas)==1 and not any(not d['conflitos'] and not d['confirmada'] for _,d in avaliacoes):
                r,d=validas[0];relacoes[r['origem']['id_externo']].append((p,r,d))
            else:
                tipo='sem_candidatos' if not candidatas else 'conflitos' if all(d['conflitos'] for _,d in avaliacoes) else 'ambiguas'
                resumo[tipo]+=1
                resumo['detalhes'].append(dict(peca=f"{cat}:{p['id']}",acao=tipo,candidatos=[dict(id=r['origem']['id_externo'],**d) for r,d in avaliacoes]))
        for pares in relacoes.values():
            # Não usar a mesma ficha para dois registros locais potencialmente duplicados.
            if len(pares)>1:
                for p,r,d in pares:
                    resumo['ambiguas']+=1;resumo['detalhes'].append(dict(peca=f"{p['categoria']}:{p['id']}",acao='ambiguas',motivo='Ficha candidata a múltiplas peças locais'))
                continue
            p,r,d=pares[0];resumo['confirmadas']+=1
            alteracoes={k:v for k,v in r['dados'].items() if p['dados'].get(k) is None}
            if p['categoria']=='processador':
                # A base docyx não identifica Box/Tray. Cooler é atributo da
                # embalagem, portanto não pode ser transferido só pelo modelo.
                alteracoes.pop('cooler',None)
            fontes={k:r['fontes'][k] for k in alteracoes}
            # Vários MPNs podem representar regiões ou embalagens diferentes.
            if len(r['mpns'])==1:
                resumo['com_mpn_unico']+=1
                mpn=r['mpns'][0]
                # CPU sem identificação da embalagem: preencher fatos compartilhados,
                # mas não transformar o código de uma caixa em identidade de um tray.
                if p['categoria']!='processador' and p['dados'].get('part_number') is None and (len(mpn)>=8 or re.search('[-/]',mpn)):
                    alteracoes['part_number']=mpn;fontes['part_number']={**r['origem'],'campo':'identifiers.identifiers[type=mpn]'}
            elif len(r['mpns'])>1:resumo['com_mpn_multiplo']+=1
            if not alteracoes:resumo['inalteradas']+=1;continue
            resumo['com_alteracoes']+=1
            propostas.append(dict(id=p['id'],categoria=p['categoria'],assinatura=p['assinatura'],alteracoes=alteracoes,fontes=fontes))
        for inicio in range(0,len(propostas),tamanho_lote):
            lote=propostas[inicio:inicio+tamanho_lote]
            try:resultados=self.repositorio.aplicar_lote(lote,simular=simular)
            except (ValueError,SQLAlchemyError):
                resumo['falhas']+=len(lote);resumo['interrompido']=True;break
            for p,r in zip(lote,resultados):
                resumo['detalhes'].append(r)
                if r['acao']=='conflito_concorrencia':resumo['conflitos']+=1;continue
                if not simular:resumo['atualizadas']+=1
                resumo['campos_preenchidos']+=len(r['campos'])
                cat=resumo['categorias'].setdefault(p['categoria'],dict(pecas=0,campos=0,sem_pendencias_tecnicas=0))
                cat['pecas']+=1;cat['campos']+=len(r['campos']);cat['sem_pendencias_tecnicas']+=not r['pendencias_montagem']
                for campo in r['campos']:resumo['campos'][campo]=resumo['campos'].get(campo,0)+1
            if progresso:progresso(resumo)
        return resumo
