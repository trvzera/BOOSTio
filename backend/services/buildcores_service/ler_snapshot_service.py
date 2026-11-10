import hashlib
import json
from pathlib import Path
import re
from .normalizar_ficha_service import NormalizarFichaBuildcoresService,CATEGORIAS


class LerSnapshotBuildcoresService:
    def executar(self,pasta):
        pasta=Path(pasta)
        manifesto=json.loads((pasta/'manifesto.json').read_text())
        if not isinstance(manifesto,dict) or not isinstance(manifesto.get('arquivos'),dict) or manifesto.get('repositorio')!='https://github.com/buildcores/buildcores-open-db' or not isinstance(manifesto.get('commit'),str) or not re.fullmatch('[0-9a-f]{40}',manifesto['commit']):
            raise ValueError('Manifesto inválido')
        registros=[];invalidos=[];fora_escopo=0
        for arquivo,info in sorted(manifesto['arquivos'].items()):
            partes=arquivo.split('/')
            if len(partes)!=3 or partes[0]!='open-db':continue
            if partes[1] not in {*CATEGORIAS,'Storage','CPUCooler'}:fora_escopo+=1;continue
            if not re.fullmatch(r'[0-9a-f-]{36}\.json',partes[2]) or not isinstance(info,dict):raise ValueError('Registro inválido')
            caminho=pasta/arquivo
            if caminho.stat().st_size>2000000:raise ValueError('Registro excessivo')
            corpo=caminho.read_bytes()
            if hashlib.sha256(corpo).hexdigest()!=info.get('sha256'):raise ValueError('Snapshot diverge do manifesto: '+arquivo)
            bruto=json.loads(corpo)
            if not isinstance(bruto,dict) or bruto.get('opendb_id')!=partes[2][:-5]:raise ValueError('Identificador diverge do arquivo')
            origem=dict(url=f"https://github.com/buildcores/buildcores-open-db/blob/{manifesto['commit']}/{arquivo}",provedor='BuildCores OpenDB',commit=manifesto['commit'],id_externo=bruto['opendb_id'],sha256=info['sha256'])
            try:r=NormalizarFichaBuildcoresService().executar(partes[1],bruto,origem)
            except (ValueError,TypeError,KeyError) as erro:
                invalidos.append(dict(arquivo=arquivo,motivo=str(erro)));continue
            registros.append(r)
        if not registros:raise ValueError('Snapshot sem registros válidos nas categorias suportadas')
        return dict(commit=manifesto['commit'],registros=registros,invalidos=invalidos,fora_escopo=fora_escopo)
