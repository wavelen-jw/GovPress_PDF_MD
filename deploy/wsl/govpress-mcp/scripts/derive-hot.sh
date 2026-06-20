#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

EXTRA=()
if [[ "${1:-}" == "--initial" ]]; then
  shift
elif [[ -f data/govpress.db ]]; then
  EXTRA=(--incremental)
fi

docker compose run --rm --no-deps mcp \
  python -m govpress_mcp.derive_hot \
  --data-root /app/data \
  --db /app/data/govpress.db \
  --qdrant-url http://qdrant:6333 \
  --tei-url http://tei:80 \
  "${EXTRA[@]}" \
  "$@"
