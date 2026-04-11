#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

DATE_ARG="${1:-${TARGET_DATE:-$(date -u +%F)}}"
OUTPUT_ROOT="${OUTPUT_ROOT:-exports/policy_briefing_qc}"
QC_ROOT="${QC_ROOT:-tests/manual_samples/policy_briefings}"
GOV_MD_CONVERTER_ROOT="${GOV_MD_CONVERTER_ROOT:-../gov-md-converter}"
EXPORT_LIMIT="${EXPORT_LIMIT:-5}"

REPORT_PATH="$OUTPUT_ROOT/$DATE_ARG/pipeline_report.json"
SUMMARY_PATH="$OUTPUT_ROOT/$DATE_ARG/qc_summary.md"
DASHBOARD_HTML="${DASHBOARD_HTML:-$OUTPUT_ROOT/dashboard/index.html}"
DASHBOARD_JSON="${DASHBOARD_JSON:-$OUTPUT_ROOT/dashboard/dashboard.json}"
TELEGRAM_DASHBOARD_URL="${TELEGRAM_DASHBOARD_URL:-}"
TELEGRAM_ISSUE_URL="${TELEGRAM_ISSUE_URL:-}"

python3 scripts/run_policy_briefing_qc_pipeline.py \
  --date "$DATE_ARG" \
  --output-root "$OUTPUT_ROOT" \
  --limit "$EXPORT_LIMIT" \
  --gov-md-converter-root "$GOV_MD_CONVERTER_ROOT" \
  --qc-root "$QC_ROOT"

python3 scripts/evaluate_policy_briefing_qc_report.py \
  "$REPORT_PATH" \
  --summary-markdown "$SUMMARY_PATH"

python3 scripts/build_policy_briefing_qc_dashboard.py \
  --root "$OUTPUT_ROOT" \
  --output-html "$DASHBOARD_HTML" \
  --output-json "$DASHBOARD_JSON"

if [ -n "${TELEGRAM_BOT_TOKEN:-}" ] && [ -n "${TELEGRAM_CHAT_ID:-}" ]; then
  TELEGRAM_ARGS=()
  if [ -n "$TELEGRAM_DASHBOARD_URL" ]; then
    TELEGRAM_ARGS+=(--dashboard-url "$TELEGRAM_DASHBOARD_URL")
  fi
  if [ -n "$TELEGRAM_ISSUE_URL" ]; then
    TELEGRAM_ARGS+=(--issue-url "$TELEGRAM_ISSUE_URL")
  fi
  python3 scripts/send_policy_briefing_qc_telegram.py "$REPORT_PATH" "${TELEGRAM_ARGS[@]}"
fi
