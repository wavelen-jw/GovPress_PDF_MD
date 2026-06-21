#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ -f hancom.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source hancom.env
  set +a
fi

ENV_FILE="${ENV_FILE:-$HOME/GovPress_PDF_MD/deploy/wsl/.env}"
QUEUE="${QUEUE:-data/fetch-log/hwp-queue.jsonl}"
STAMP="$(date +%Y%m%d-%H%M%S)"
CONVERTED_QUEUE="${CONVERTED_QUEUE:-data/fetch-log/hwp-queue-converted-${STAMP}.jsonl}"
LOG_JSON="${LOG_JSON:-data/fetch-log/hwp-to-hwpx-${STAMP}.jsonl}"
LIMIT="${1:-${LIMIT:-}}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing env file: $ENV_FILE" >&2
  exit 1
fi

scripts/fix-data-permissions.sh

LIMIT_ARG=()
if [[ -n "$LIMIT" ]]; then
  LIMIT_ARG=(--limit "$LIMIT")
fi

conversion_rc=0
scripts/hwp-to-hwpx.py \
  --data-root data \
  --queue "$QUEUE" \
  --output-queue "$CONVERTED_QUEUE" \
  --log-json "$LOG_JSON" \
  "${LIMIT_ARG[@]}" || conversion_rc=$?

if [[ ! -s "$CONVERTED_QUEUE" ]]; then
  echo "No converted HWPX entries to process: $CONVERTED_QUEUE" >&2
  exit "$conversion_rc"
fi

if [[ "$conversion_rc" -ne 0 ]]; then
  echo "Continuing with converted HWPX entries despite conversion failures: rc=$conversion_rc log=$LOG_JSON" >&2
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
  --from-hwp-queue "/app/$CONVERTED_QUEUE" \
  --data-root /app/data \
  --log-json "/app/data/fetch-log/hwp-reprocess-${STAMP}.jsonl"

scripts/derive-hot.sh
