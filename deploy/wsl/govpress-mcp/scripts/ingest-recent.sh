#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  echo "Usage: $0 START_DATE [END_DATE] [LIMIT]" >&2
  echo "Example: $0 2026-06-19 2026-06-20 50" >&2
  exit 2
}

START_DATE="${1:-}"
END_DATE="${2:-$START_DATE}"
LIMIT="${3:-}"
DATE_RE='^[0-9]{4}-[0-9]{2}-[0-9]{2}$'

[[ -n "$START_DATE" ]] || usage
[[ "$START_DATE" =~ $DATE_RE ]] || usage
[[ "$END_DATE" =~ $DATE_RE ]] || usage
if [[ -n "$LIMIT" && ! "$LIMIT" =~ ^[0-9]+$ ]]; then
  usage
fi

ENV_FILE="${ENV_FILE:-$HOME/GovPress_PDF_MD/deploy/wsl/.env}"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

mkdir -p data/fetch-log
STAMP="$(date +%Y%m%d-%H%M%S)"
LIMIT_ARG=()
if [[ -n "$LIMIT" ]]; then
  LIMIT_ARG=(--limit "$LIMIT")
fi

docker compose run --rm --no-deps \
  --env-from-file "$ENV_FILE" \
  --entrypoint sh \
  mcp -lc '
    mkdir -p /tmp/fakebin
    printf "%s\n" "#!/bin/sh" "printf \"%s\\n\" \"\${GOVPRESS_CONVERTER_COMMIT:-unknown}\"" > /tmp/fakebin/git
    chmod +x /tmp/fakebin/git
    PATH=/tmp/fakebin:$PATH exec python -m govpress_mcp.bulk_ingest "$@"
  ' sh \
  --start-date "$START_DATE" \
  --end-date "$END_DATE" \
  --data-root /app/data \
  "${LIMIT_ARG[@]}" \
  --log-json "/app/data/fetch-log/bulk-ingest-${STAMP}.jsonl"

scripts/derive-hot.sh
