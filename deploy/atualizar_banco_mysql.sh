#!/usr/bin/env bash
# Rodar no checkout atualizado da VPS. Não remove volumes, importa seeds ou restaura dados.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${BOOSTIO_BACKUP_DIR:?Defina BOOSTIO_BACKUP_DIR fora do projeto}"
compose=(docker compose --env-file .env.production)
if [[ "${1:-}" != "--aplicar" ]]; then
  if [[ $# -ne 0 ]]; then echo 'Uso: bash deploy/atualizar_banco_mysql.sh [--aplicar]' >&2; exit 2; fi
  "${compose[@]}" build api
  "${compose[@]}" run --rm --no-deps api python -m flask --app app banco-atualizar-mysql
  exit
fi
[[ $# -eq 1 ]] || exit 2
"${compose[@]}" build api
# Falhar antes da indisponibilidade se o esquema não for compatível.
"${compose[@]}" run --rm --no-deps api python -m flask --app app banco-atualizar-mysql
trap '"${compose[@]}" stop web api || true; echo "Atualização interrompida; API e web permanecem paradas. Confira o backup e o esquema antes de reiniciar. Não restaure automaticamente sobre dados novos." >&2' ERR
"${compose[@]}" stop web api
# Pare também cron/jobs externos que gravam antes de executar esta rotina.
bash deploy/backup_mysql.sh
"${compose[@]}" run --rm --no-deps api python -m flask --app app banco-atualizar-mysql --aplicar
"${compose[@]}" up -d --no-deps --wait api
"${compose[@]}" up -d --no-deps web
trap - ERR
echo 'Migração concluída; API saudável e web iniciada. Confira login e builds existentes.'
