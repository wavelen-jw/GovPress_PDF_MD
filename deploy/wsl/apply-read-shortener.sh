#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
ENV_PATH="$SCRIPT_DIR/.env"
COMPOSE_PATH="$SCRIPT_DIR/docker-compose.yourls.yml"
PORT="${GOVPRESS_READ_SHORTENER_PORT:-8091}"

if [[ ! -f "$ENV_PATH" ]]; then
  echo ".env not found at $ENV_PATH" >&2
  exit 1
fi

set -a
source "$ENV_PATH"
set +a

required_vars=(
  YOURLS_SITE
  YOURLS_USER
  YOURLS_PASSWORD
  YOURLS_DB_ROOT_PASSWORD
  YOURLS_DB_PASSWORD
)

for key in "${required_vars[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    echo "missing required env: $key" >&2
    exit 1
  fi
done

echo "== GovPress read shortener apply =="
echo "compose_file=$COMPOSE_PATH"
echo "site=$YOURLS_SITE"
echo "port=$PORT"

COMPOSE_FILE_OVERRIDE="$COMPOSE_PATH" "$SCRIPT_DIR/bin/compose.sh" up -d yourls-db yourls

echo "== Container status =="
COMPOSE_FILE_OVERRIDE="$COMPOSE_PATH" "$SCRIPT_DIR/bin/compose.sh" ps

echo "== Local checks =="
curl -I --max-time 10 "http://127.0.0.1:${PORT}/admin/" || true
echo
echo "Cloudflare public hostname target should be: http://127.0.0.1:${PORT}"
