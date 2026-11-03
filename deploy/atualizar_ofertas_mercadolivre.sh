#!/usr/bin/env bash
# Simula por padrão. Não faz pull, build, migration, backup ou configuração automática.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f .env.production ]] || { echo 'Configure .env.production na VPS antes de executar.' >&2; exit 2; }
command -v docker >/dev/null || { echo 'Docker não encontrado.' >&2; exit 2; }
command -v flock >/dev/null || { echo 'Instale flock (util-linux) para impedir jobs simultâneos.' >&2; exit 2; }
exec 9>"${BOOSTIO_MERCADOLIVRE_LOCK:-${TMPDIR:-/tmp}/boostio-mercadolivre.lock}"
flock -n 9 || { echo 'Já existe uma coleta do Mercado Livre em execução neste host.' >&2; exit 75; }
compose=(docker compose --env-file .env.production)
"${compose[@]}" run --rm --no-deps -T api python -m flask --app app mercadolivre-validar >&2
"${compose[@]}" run --rm --no-deps -T api python -m flask --app app mercadolivre-ofertas-atualizar "$@"
