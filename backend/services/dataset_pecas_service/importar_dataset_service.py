import hashlib
import json
from pathlib import Path
from sqlalchemy.exc import SQLAlchemyError
from services.dataset_pecas_service.gravar_dataset_pecas_service import GravarDatasetPecasService
from .normalizar_peca_service import ARQUIVOS, NormalizarPecaDatasetService


class ImportarDatasetService:
    def __init__(self, repositorio=None):self.repositorio=repositorio or GravarDatasetPecasService()

    def executar(self,pasta,*,simular=True,tamanho_lote=250,progresso=None):
        if type(simular) is not bool or type(tamanho_lote) is not int or not 1<=tamanho_lote<=1000:raise ValueError('Opções inválidas')
        pasta=Path(pasta);manifesto=json.loads((pasta/'manifesto.json').read_text())
        import re
        if not isinstance(manifesto,dict) or not isinstance(manifesto.get('arquivos'),dict):raise ValueError('Manifesto inválido')
        if manifesto.get('repositorio')!='https://github.com/docyx/pc-part-dataset' or not isinstance(manifesto.get('commit'),str) or not re.fullmatch('[0-9a-f]{40}',manifesto['commit']):raise ValueError('Manifesto de origem inválido')
        arquivos=[]
        for arquivo in ARQUIVOS:
            caminho=pasta/(arquivo+'.json')
            if not caminho.exists():continue
            if caminho.stat().st_size>32*1024*1024:raise ValueError('Arquivo excede 32 MiB')
            corpo=caminho.read_bytes();origem=manifesto['arquivos'].get(caminho.name,{})
            if not isinstance(origem,dict):raise ValueError('Metadados de arquivo inválidos')
            url=f"https://raw.githubusercontent.com/docyx/pc-part-dataset/{manifesto['commit']}/data/json/{caminho.name}"
            if hashlib.sha256(corpo).hexdigest()!=origem.get('sha256') or origem.get('url')!=url:raise ValueError('Arquivo diverge do manifesto: '+caminho.name)
            linhas=json.loads(corpo,parse_constant=lambda _: (_ for _ in ()).throw(ValueError('JSON não finito')))
            if not isinstance(linhas,list) or not all(isinstance(l,dict) for l in linhas):raise ValueError('Formato inválido: '+caminho.name)
            arquivos.append((arquivo,origem,len(linhas)))
        if not arquivos:raise ValueError('Nenhum arquivo de categoria suportada')
        resumo=dict(simulacao=simular,commit=manifesto['commit'],linhas=0,criadas=0,propostas=0,existentes=0,inalteradas=0,revisao=0,invalidas=0,duplicadas=0,falhas=0,interrompido=False,categorias={},detalhes=[])
        vistos=set();lote=[]
        def aplicar():
            if not lote:return
            try:resultados=self.repositorio.executar_lote(lote,simular=simular)
            except (SQLAlchemyError,ValueError):
                resumo.update(falhas=resumo['falhas']+len(lote),interrompido=True)
                raise
            for r in resultados:
                chave={'criada':'criadas','proposta':'propostas','existente':'existentes','inalterada':'inalteradas','revisao':'revisao','duplicada':'duplicadas'}[r['acao']]
                resumo[chave]+=1
                cat=resumo['categorias'].setdefault(r['categoria'],{})
                cat[chave]=cat.get(chave,0)+1
            lote.clear()
            if progresso:progresso(resumo)
        try:
            for arquivo,origem,total in arquivos:
                linhas=json.loads((pasta/(arquivo+'.json')).read_text())
                for pos,linha in enumerate(linhas,1):
                    resumo['linhas']+=1
                    try:r=NormalizarPecaDatasetService().executar(arquivo,linha,{**origem,'commit':manifesto['commit'],'arquivo':arquivo+'.json','linha':pos})
                    except (ValueError,TypeError,KeyError,IndexError) as erro:
                        resumo['invalidas']+=1
                        resumo['detalhes'].append(dict(arquivo=arquivo,linha=pos,motivo=str(erro)));continue
                    chave=(r['categoria'],r['identidade'])
                    if chave in vistos:resumo['duplicadas']+=1;continue
                    vistos.add(chave);lote.append(r)
                    if len(lote)>=tamanho_lote:aplicar()
                aplicar()
        except (SQLAlchemyError,ValueError):
            resumo['interrompido']=True
        return resumo
