import hashlib
import json
from pathlib import Path
import re
import tempfile
import zipfile
import requests


class BaixarSnapshotBuildcoresService:
    def executar(self,pasta,*,commit=None):
        pasta=Path(pasta);pasta.mkdir(parents=True,exist_ok=True)
        try:
            if commit is None:
                resposta=requests.get('https://api.github.com/repos/buildcores/buildcores-open-db/commits/main',timeout=(10,30),allow_redirects=False)
                try:
                    if resposta.status_code!=200:raise ValueError('GitHub recusou a consulta da revisão')
                    commit=resposta.json()['sha']
                finally:resposta.close()
            if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Revisão inválida')
            with tempfile.TemporaryFile() as arquivo:
                with requests.get(f'https://codeload.github.com/buildcores/buildcores-open-db/zip/{commit}',timeout=(10,120),stream=True,allow_redirects=False) as resposta:
                    if resposta.status_code!=200:raise ValueError('GitHub recusou o download')
                    tamanho=0
                    for bloco in resposta.iter_content(65536):
                        tamanho+=len(bloco)
                        if tamanho>128*1024*1024:raise ValueError('Download excede 128 MiB')
                        arquivo.write(bloco)
                arquivo.seek(0)
                with zipfile.ZipFile(arquivo) as zip:
                    if sum(i.file_size for i in zip.infolist())>512*1024*1024 or len(zip.infolist())>100000:raise ValueError('Snapshot excessivo')
                    manifesto={'repositorio':'https://github.com/buildcores/buildcores-open-db','commit':commit,'arquivos':{}}
                    with tempfile.TemporaryDirectory(dir=pasta,prefix='.snapshot-') as staging:
                        for item in zip.infolist():
                            nome='/'.join(item.filename.split('/')[1:]);partes=nome.split('/')
                            selecionado=(len(partes)==3 and partes[0]=='open-db' and partes[-1].endswith('.json')) or (len(partes)==2 and partes[0]=='schemas' and partes[-1].endswith('.json')) or nome in ('README.md','LICENSE.txt','NOTICE.md')
                            if not selecionado:continue
                            if any(p in ('..','') for p in partes) or item.file_size>2000000:raise ValueError('Registro inválido')
                            corpo=zip.read(item);destino=Path(staging)/nome;destino.parent.mkdir(parents=True,exist_ok=True);destino.write_bytes(corpo)
                            manifesto['arquivos'][nome]=dict(sha256=hashlib.sha256(corpo).hexdigest(),bytes=len(corpo))
                        if not manifesto['arquivos']:raise ValueError('Snapshot vazio')
                        import os
                        for nome in manifesto['arquivos']:
                            destino=pasta/nome;destino.parent.mkdir(parents=True,exist_ok=True);os.replace(Path(staging)/nome,destino)
                        temporario=pasta/'.manifesto.tmp';temporario.write_text(json.dumps(manifesto,indent=2));os.replace(temporario,pasta/'manifesto.json')
                    return dict(commit=commit,arquivos=len(manifesto['arquivos']))
        except requests.RequestException:raise ValueError('Falha de comunicação com GitHub') from None
