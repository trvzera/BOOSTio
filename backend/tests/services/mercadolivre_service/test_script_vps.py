import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.fixture
def projeto(tmp_path):
    raiz=tmp_path/'BOOSTio';(raiz/'deploy').mkdir(parents=True);(raiz/'bin').mkdir()
    origem=Path(__file__).resolve().parents[4]/'deploy/atualizar_ofertas_mercadolivre.sh'
    shutil.copyfile(origem,raiz/'deploy/atualizar_ofertas_mercadolivre.sh')
    (raiz/'.env.production').write_text('# fixture sem credenciais\n')
    docker=raiz/'bin/docker'
    docker.write_text('#!'+sys.executable+'\nimport os,sys,json\nwith open(os.environ["TEST_LOG"],"a") as f:f.write(json.dumps(sys.argv[1:])+"\\n")\nif "mercadolivre-validar" in sys.argv:sys.exit(int(os.environ.get("TEST_VALIDAR_EXIT","0")))\nprint("{}")\n')
    docker.chmod(0o755)
    flock=raiz/'bin/flock';flock.write_text('#!/bin/sh\nexit "${TEST_FLOCK_EXIT:-0}"\n');flock.chmod(0o755)
    env={**os.environ,'PATH':str(raiz/'bin')+os.pathsep+os.environ['PATH'],
         'TEST_LOG':str(raiz/'chamadas.jsonl'),'BOOSTIO_MERCADOLIVRE_LOCK':str(raiz/'teste.lock')}
    return raiz,env


def executar(projeto,*args):
    raiz,env=projeto
    resultado=subprocess.run(['bash',str(raiz/'deploy/atualizar_ofertas_mercadolivre.sh'),*args],env=env,text=True,capture_output=True)
    log=raiz/'chamadas.jsonl'
    return resultado,[json.loads(l) for l in log.read_text().splitlines()] if log.exists() else []


def test_script_valida_antes_e_simula_por_padrao(projeto):
    r,chamadas=executar(projeto,'--categoria','processador','--limite-pecas','5')
    assert r.returncode==0 and len(chamadas)==2
    assert chamadas[0][-1]=='mercadolivre-validar'
    assert 'mercadolivre-ofertas-atualizar' in chamadas[1] and '--aplicar' not in chamadas[1]
    assert chamadas[1][-4:]==['--categoria','processador','--limite-pecas','5']


def test_script_passa_aplicacao_somente_quando_explicita(projeto):
    r,c=executar(projeto,'--aplicar')
    assert r.returncode==0 and c[1][-1]=='--aplicar'


@pytest.mark.parametrize('variavel,codigo',[('TEST_VALIDAR_EXIT','1'),('TEST_FLOCK_EXIT','1')])
def test_script_nao_coleta_se_validacao_ou_lock_falha(projeto,variavel,codigo):
    projeto[1][variavel]=codigo
    r,c=executar(projeto,'--aplicar')
    assert r.returncode!=0
    assert not any('mercadolivre-ofertas-atualizar' in linha for linha in c)
