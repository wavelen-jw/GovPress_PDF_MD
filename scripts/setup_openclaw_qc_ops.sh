#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWNER_CHAT_ID="${OWNER_CHAT_ID:-6475698942}"
JOB_NAME="${JOB_NAME:-govpress-qc-digest}"
CRON_EXPR="${CRON_EXPR:-20 13 * * *}"
TZ_NAME="${TZ_NAME:-Asia/Seoul}"
AGENT_NAME="${AGENT_NAME:-govpress_qc_ops}"
AGENT_MODEL="${AGENT_MODEL:-gemma4/gemma-4-26B-A4B-it-UD-IQ4_NL.gguf}"
EXPORT_ROOT="${GOVPRESS_QC_EXPORT_ROOT:-$REPO_ROOT/exports/policy_briefing_qc}"
GOV_MD_ROOT="${GOV_MD_CONVERTER_ROOT:-$REPO_ROOT/../gov-md-converter}"
QC_ROOT="${GOVPRESS_QC_ROOT:-$GOV_MD_ROOT/tests/manual_samples/policy_briefings}"
WRAPPER="$REPO_ROOT/scripts/openclaw_ops.py"
AGENT_WORKSPACE="${AGENT_WORKSPACE:-$REPO_ROOT/ops/openclaw_qc_ops}"

if ! command -v openclaw >/dev/null 2>&1; then
  echo "openclaw CLI not found"
  exit 1
fi

if [ ! -f "$WRAPPER" ]; then
  echo "wrapper script missing: $WRAPPER"
  exit 1
fi

if [ ! -d "$AGENT_WORKSPACE" ]; then
  echo "agent workspace missing: $AGENT_WORKSPACE"
  exit 1
fi

if [ ! -d "$HOME/.openclaw/agents/$AGENT_NAME" ]; then
  openclaw agents add "$AGENT_NAME" \
    --workspace "$AGENT_WORKSPACE" \
    --model "$AGENT_MODEL" \
    --non-interactive
  echo "Added OpenClaw agent: $AGENT_NAME"
else
  echo "OpenClaw agent already exists: $AGENT_NAME"
fi

if ! openclaw cron list --json | python3 - "$JOB_NAME" <<'PY'
import json, sys
name = sys.argv[1]
raw = sys.stdin.read()
start = raw.find("{")
if start == -1:
    raise SystemExit(1)
payload = json.loads(raw[start:])
jobs = payload.get("jobs", [])
matches = [job for job in jobs if job.get("name") == name]
print("present" if matches else "missing")
sys.exit(0 if matches else 1)
PY
then
  openclaw cron add \
    --name "$JOB_NAME" \
    --description "GovPress QC daily digest via /qc today" \
    --cron "$CRON_EXPR" \
    --tz "$TZ_NAME" \
    --agent "$AGENT_NAME" \
    --message "/qc today" \
    --channel telegram \
    --to "$OWNER_CHAT_ID" \
    --announce \
    --session isolated \
    --light-context \
    --thinking low \
    --timeout-seconds 180 \
    --best-effort-deliver
  echo "Added OpenClaw cron job: $JOB_NAME"
else
  echo "OpenClaw cron job already exists: $JOB_NAME"
fi

cat <<EOF
OpenClaw GovPress QC setup
- repo_root: $REPO_ROOT
- agent_name: $AGENT_NAME
- agent_workspace: $AGENT_WORKSPACE
- export_root: $EXPORT_ROOT
- gov_md_root: $GOV_MD_ROOT
- qc_root: $QC_ROOT
- wrapper: $WRAPPER

Test commands:
  python3 "$WRAPPER" qc-status --date latest
  python3 "$WRAPPER" server-status
  python3 "$WRAPPER" telegram-dispatch --chat-scope dm --message "/qc today"
  openclaw agent --agent "$AGENT_NAME" --message "/qc today" --json
EOF
