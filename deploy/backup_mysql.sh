#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
umask 077
destino="${BOOSTIO_BACKUP_DIR:?Defina BOOSTIO_BACKUP_DIR fora do projeto}"
mkdir -p "$destino"
arquivo="$destino/boostio-$(date -u +%Y%m%dT%H%M%SZ).sql.gz"
temporario="${arquivo}.tmp"
trap 'rm -f "$temporario"' EXIT

docker compose --env-file .env.production exec -T db sh -c \
  'exec mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --single-transaction --routines --triggers "$MYSQL_DATABASE"' \
  | gzip > "$temporario"
gzip -t "$temporario"
mv "$temporario" "$arquivo"
printf '%s\n' "$arquivo"
