#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
exec 9>"${TMPDIR:-/tmp}/boostio-precos.lock"
flock -n 9 || exit 0

docker compose --env-file .env.production run --rm --no-deps api \
  python -m flask --app app precos-atualizar --intervalo 1
