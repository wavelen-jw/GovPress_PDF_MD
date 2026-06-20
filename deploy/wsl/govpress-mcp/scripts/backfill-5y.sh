#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  echo "Usage: GPG_PASSPHRASE_FILE=~/.govpress-mcp-archive.pass $0 [START_MONTH] [END_MONTH]" >&2
  echo "Example: $0 2021-01 2021-01" >&2
  exit 2
}

START_MONTH="${1:-2021-01}"
END_MONTH="${2:-2026-06}"
MONTH_RE='^[0-9]{4}-[0-9]{2}$'
[[ "$START_MONTH" =~ $MONTH_RE ]] || usage
[[ "$END_MONTH" =~ $MONTH_RE ]] || usage

STATE_FILE="${STATE_FILE:-data/fetch-log/backfill-5y-state.jsonl}"
mkdir -p "$(dirname "$STATE_FILE")"

month_start() {
  date -d "$1-01" +%Y-%m-01
}

month_end() {
  date -d "$1-01 +1 month -1 day" +%Y-%m-%d
}

next_month() {
  date -d "$1-01 +1 month" +%Y-%m
}

log_event() {
  local month="$1"
  local stage="$2"
  local status="$3"
  printf '{"ts":"%s","month":"%s","stage":"%s","status":"%s"}\n' \
    "$(date -Iseconds)" "$month" "$stage" "$status" >> "$STATE_FILE"
}

current="$START_MONTH"
while [[ "$current" < "$(next_month "$END_MONTH")" ]]; do
  start_date="$(month_start "$current")"
  end_date="$(month_end "$current")"

  log_event "$current" capacity start
  scripts/check-capacity.sh
  log_event "$current" capacity ok

  log_event "$current" ingest start
  month_queue="data/fetch-log/hwp-queue-$current.jsonl"
  HWP_QUEUE_OUTPUT="$month_queue" scripts/ingest-recent.sh "$start_date" "$end_date"
  log_event "$current" ingest ok

  log_event "$current" hwp_queue start
  QUEUE="$month_queue" scripts/process-hwp-queue.sh
  log_event "$current" hwp_queue ok

  log_event "$current" archive start
  scripts/archive-month.sh "$current"
  log_event "$current" archive ok

  log_event "$current" prune start
  scripts/prune-raw-month.sh "$current"
  log_event "$current" prune ok

  current="$(next_month "$current")"
done
