"""Baixa arquivos de uma revisão fixa; nunca executa o scraper da fonte."""
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
import requests
from .normalizar_peca_service import ARQUIVOS


class BaixarDatasetService:
    def __init__(self,session=None):self.session=session or requests.Session()

    def _ler(self,url):
        try:
            with self.session.get(url,timeout=(10,60),stream=True,allow_redirects=False) as resposta:
                if resposta.status_code!=200:raise ValueError('Download recusado pela fonte: HTTP '+str(resposta.status_code))
                corpo=bytearray()
                for bloco in resposta.iter_content(65536):
                    corpo.extend(bloco)
                    if len(corpo)>32*1024*1024:raise ValueError('Arquivo excede 32 MiB')
                return bytes(corpo)
        except requests.RequestException:raise ValueError('Falha de rede ao baixar dataset') from None

    def executar(self,destino,*,commit=None):
        if commit is None:
            commit=json.loads(self._ler('https://api.github.com/repos/docyx/pc-part-dataset/commits/main'))['sha']
        if not isinstance(commit,str) or not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Informe o SHA completo da revisão')
        destino=Path(destino);destino.mkdir(parents=True,exist_ok=True)
        manifesto={'repositorio':'https://github.com/docyx/pc-part-dataset','commit':commit,'arquivos':{}}
        with tempfile.TemporaryDirectory(dir=destino,prefix='.download-') as pasta:
            for arquivo in [*(a+'.json' for a in ARQUIVOS),'API.md','README.md','LICENSE']:
                caminho='data/json/'+arquivo if arquivo.endswith('.json') else arquivo
                url=f'https://raw.githubusercontent.com/docyx/pc-part-dataset/{commit}/{caminho}'
                corpo=self._ler(url)
                if arquivo.endswith('.json'):
                    dados=json.loads(corpo)
                    if not isinstance(dados,list) or not all(isinstance(v,dict) for v in dados):raise ValueError('Formato inesperado: '+arquivo)
                (Path(pasta)/arquivo).write_bytes(corpo)
                manifesto['arquivos'][arquivo]=dict(url=url,sha256=hashlib.sha256(corpo).hexdigest(),bytes=len(corpo))
            (Path(pasta)/'manifesto.json').write_text(json.dumps(manifesto,ensure_ascii=False,indent=2))
            # Manifesto por último: se houver interrupção, os hashes recusam um snapshot misto.
            for arquivo in [*manifesto['arquivos'],'manifesto.json']:os.replace(Path(pasta)/arquivo,destino/arquivo)
        return manifesto
