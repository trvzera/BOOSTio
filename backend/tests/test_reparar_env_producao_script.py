import importlib.util
from pathlib import Path
import stat
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[2] / 'deploy' / 'reparar_env_producao.py'
spec = importlib.util.spec_from_file_location('reparar_env_producao', SCRIPT)
reparo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reparo)


def test_simular_e_aplicar_preservam_credenciais_e_formato(tmp_path):
    env = tmp_path / '.env.production'
    antes = b'MERCADO_LIVRE_CLIENT_SECRET="segredo-sintetico"\r\nINTEGRACOES_TOKEN_CHAVE=chave-sintetica\r\n'
    depois = b'SHOPEE_APP_SECRET="outro-segredo"\r\nICECAT_SENHA=senha-sintetica\r\n'
    original = antes + reparo.DIAGNOSTICO + b'\r\n' + depois
    env.write_bytes(original)
    backup = tmp_path / 'privado'
    assert reparo.reparar(env) == dict(aplicado=False, linhas_removidas=[3])
    assert env.read_bytes() == original
    assert not backup.exists()
    resultado = reparo.reparar(env, aplicar=True, pasta_backup=backup)
    assert resultado['aplicado'] is True
    assert env.read_bytes() == antes + depois
    assert Path(resultado['backup']).read_bytes() == original
    assert stat.S_IMODE(Path(resultado['backup']).stat().st_mode) == 0o600
    assert stat.S_IMODE(env.stat().st_mode) == 0o600
    assert reparo.reparar(env, aplicar=True, pasta_backup=backup)['aplicado'] is False
    assert len(list(backup.iterdir())) == 1


def test_nao_remove_comandos_ou_variaveis_parecidos(tmp_path):
    env = tmp_path / '.env.production'
    original = b'COMENTARIO=docker run --rm\n' + reparo.DIAGNOSTICO + b' MAIS_DADOS\n'
    env.write_bytes(original)
    assert reparo.reparar(env, aplicar=True)['aplicado'] is False
    assert env.read_bytes() == original


def test_recusa_backup_publico_sem_alterar_arquivo(tmp_path):
    env = tmp_path / '.env.production'
    env.write_bytes(reparo.DIAGNOSTICO + b'\n')
    backup = tmp_path / 'publico'
    backup.mkdir(mode=0o755)
    backup.chmod(0o755)
    with pytest.raises(ValueError):
        reparo.reparar(env, aplicar=True, pasta_backup=backup)
    assert env.read_bytes() == reparo.DIAGNOSTICO + b'\n'
    assert list(backup.iterdir()) == []


def test_cli_nao_mostra_segredos(tmp_path):
    env = tmp_path / '.env.production'
    env.write_bytes(b'ICECAT_SENHA=senha-sintetica\n' + reparo.DIAGNOSTICO + b'\n')
    r = subprocess.run([sys.executable, str(SCRIPT), '--arquivo', str(env)], capture_output=True, text=True, timeout=10)
    assert r.returncode == 0
    assert 'senha-sintetica' not in r.stdout + r.stderr
    assert 'ICECAT_SENHA' not in r.stdout + r.stderr
