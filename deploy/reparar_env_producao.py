#!/usr/bin/env python3
"""Remove somente um diagnóstico conhecido inserido por engano no env da VPS."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import stat
import tempfile


DIAGNOSTICO = (
    'docker run --rm --network boostio_backend '
    '--env-file /opt/BOOSTio/.env.production -e APP_ENV=producao '
    '-w /app/backend boostio-catalogo:20261109 python -c '
    "'import os,json; print(json.dumps({k:bool(os.getenv(k,\"\").strip()) "
    'for k in ("SHOPEE_APP_ID","SHOPEE_APP_SECRET")}))\''
).encode('ascii')


def reparar(arquivo, *, aplicar=False, pasta_backup=None):
    arquivo = Path(arquivo)
    if arquivo.is_symlink() or not arquivo.is_file():
        raise ValueError('Informe um arquivo regular; links não serão substituídos.')
    atributos = arquivo.stat()
    original = arquivo.read_bytes()
    linhas = original.splitlines(keepends=True)
    remover = [i for i, linha in enumerate(linhas) if linha.rstrip(b'\r\n') == DIAGNOSTICO]
    resultado = dict(aplicado=False, linhas_removidas=[i + 1 for i in remover])
    if not remover or not aplicar:
        return resultado
    if pasta_backup is None:
        raise ValueError('Defina a pasta privada de backup antes de aplicar.')
    novo = b''.join(linha for i, linha in enumerate(linhas) if i not in remover)
    pasta_backup = Path(pasta_backup)
    pasta_backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    permissao = stat.S_IMODE(pasta_backup.stat().st_mode)
    if permissao & 0o077:
        raise ValueError('A pasta de backup precisa ser privada (permissão 700).')
    if arquivo.read_bytes() != original:
        raise ValueError('O arquivo foi alterado durante a conferência; repita a simulação.')
    data = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = pasta_backup / f'env-production-{data}.bak'
    descritor = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descritor, 'wb') as destino:
        destino.write(original)
        destino.flush()
        os.fsync(destino.fileno())
    descritor, temporario = tempfile.mkstemp(prefix='.env-reparo-', dir=arquivo.parent)
    try:
        with os.fdopen(descritor, 'wb') as destino:
            atual = os.fstat(destino.fileno())
            if (atual.st_uid, atual.st_gid) != (atributos.st_uid, atributos.st_gid):
                os.fchown(destino.fileno(), atributos.st_uid, atributos.st_gid)
            destino.write(novo)
            destino.flush()
            os.fsync(destino.fileno())
        if arquivo.read_bytes() != original:
            raise ValueError('O arquivo mudou; backup mantido, reparo não aplicado.')
        os.replace(temporario, arquivo)
    finally:
        if os.path.exists(temporario):
            os.unlink(temporario)
    return {**resultado, 'aplicado': True, 'backup': str(backup)}


def main():
    argumentos = argparse.ArgumentParser(description=__doc__)
    argumentos.add_argument('--arquivo', required=True, type=Path)
    argumentos.add_argument('--backup-dir', type=Path)
    argumentos.add_argument('--aplicar', action='store_true')
    opcoes = argumentos.parse_args()
    try:
        resultado = reparar(opcoes.arquivo, aplicar=opcoes.aplicar, pasta_backup=opcoes.backup_dir)
    except (ValueError, OSError):
        argumentos.exit(1, 'Reparo não concluído. Confira o arquivo e as permissões; nenhum segredo foi exibido.\n')
    print(json.dumps(resultado))


if __name__ == '__main__':
    main()
