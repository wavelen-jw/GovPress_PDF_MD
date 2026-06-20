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
HWP_QUEUE_GLOBAL="${HWP_QUEUE_GLOBAL:-data/fetch-log/hwp-queue.jsonl}"
HWP_QUEUE_OUTPUT="${HWP_QUEUE_OUTPUT:-}"
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

if [[ -n "$HWP_QUEUE_OUTPUT" && -f "$HWP_QUEUE_GLOBAL" ]]; then
  mkdir -p "$(dirname "$HWP_QUEUE_OUTPUT")"
  python3 - "$HWP_QUEUE_GLOBAL" "$HWP_QUEUE_OUTPUT" "$START_DATE" "$END_DATE" <<'PYFILTER'
import json
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
start = sys.argv[3]
end = sys.argv[4]
seen = set()
rows = []

with src.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        approve_date = str(item.get("approve_date") or "")
        if approve_date < start or approve_date > end:
            continue
        key = (item.get("news_item_id"), item.get("hwp_path"))
        if key in seen:
            continue
        seen.add(key)
        rows.append(item)

with dst.open("w", encoding="utf-8") as f:
    for item in rows:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"wrote_hwp_queue={dst} rows={len(rows)}")
PYFILTER
fi

scripts/derive-hot.sh
