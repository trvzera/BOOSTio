"""Backup deve preservar o stdin da rotina que o chamou e falhar sem publicar dump."""
import gzip
import os
from pathlib import Path
import subprocess

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / 'deploy' / 'backup_mysql.sh'


@pytest.mark.parametrize('falhar', [False, True])
def test_backup_nao_consumir_comandos_do_terminal(tmp_path, falhar):
    executaveis = tmp_path / 'bin'
    executaveis.mkdir()
    docker = executaveis / 'docker'
    docker.write_text(
        '#!/bin/sh\n'
        'cat >/dev/null\n'
        'if [ "$BOOSTIO_TEST_BACKUP_FAIL" = 1 ]; then exit 1; fi\n'
        "printf '%s\\n' '-- dump de teste'\n"
    )
    docker.chmod(0o700)
    destino = tmp_path / 'backups'
    ambiente = {
        **os.environ,
        'PATH': f'{executaveis}{os.pathsep}{os.environ["PATH"]}',
        'BOOSTIO_BACKUP_DIR': str(destino),
        'BOOSTIO_TEST_BACKUP_FAIL': str(int(falhar)),
    }
    resultado = subprocess.run(
        ['bash'],
        input=f'bash "{SCRIPT}"\nretorno=$?\nprintf "RETORNO=%s\\n" "$retorno"\n',
        text=True, capture_output=True, env=ambiente, timeout=10,
    )
    assert resultado.returncode == 0
    assert f'RETORNO={int(falhar)}' in resultado.stdout
    arquivos = list(destino.iterdir())
    if falhar:
        assert arquivos == []
    else:
        assert len(arquivos) == 1
        assert arquivos[0].suffix == '.gz'
        assert gzip.decompress(arquivos[0].read_bytes()) == b'-- dump de teste\n'
