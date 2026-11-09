#!/usr/bin/env bash
# Rodar no checkout atualizado da VPS. Copia link, preço e estoque da KaBuM das peças para a tabela oferta.
# Não apaga colunas nem dados: as colunas antigas continuam como cópia de segurança.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${BOOSTIO_BACKUP_DIR:?Defina BOOSTIO_BACKUP_DIR fora do projeto}"
compose=(docker compose --env-file .env.production)
comando=(python -m flask --app app ofertas-kabum-migrar)
if [[ "${1:-}" != "--aplicar" ]]; then
  if [[ $# -ne 0 ]]; then echo 'Uso: bash deploy/migrar_ofertas_kabum.sh [--aplicar]' >&2; exit 2; fi
  "${compose[@]}" build api
  "${compose[@]}" run --rm --no-deps api "${comando[@]}"   # simulação: só conta
  exit
fi
[[ $# -eq 1 ]] || exit 2
"${compose[@]}" build api
"${compose[@]}" run --rm --no-deps api "${comando[@]}"
trap '"${compose[@]}" stop web api || true; echo "Migração interrompida; API e web permanecem paradas. Confira o backup e o banco antes de reiniciar. Não restaure automaticamente sobre dados novos." >&2' ERR
# Sem as ofertas, as peças ficam sem preço: a API para antes e só volta depois da cópia.
"${compose[@]}" stop web api
# Pare também cron/jobs externos que gravam (precos-atualizar, ofertas, worker) antes de executar.
bash deploy/backup_mysql.sh
"${compose[@]}" run --rm --no-deps api "${comando[@]}" --aplicar
"${compose[@]}" run --rm --no-deps api "${comando[@]}"   # repetir não deve criar nada
"${compose[@]}" up -d --no-deps --wait api
"${compose[@]}" up -d --no-deps web
trap - ERR
echo 'Ofertas da KaBuM migradas; API saudável e web iniciada. Confira o catálogo e as builds geradas.'
