# GovPress QC Ops Tools

- Repo root: `<repo-root>`
- gov-md-converter root: `<gov-md-root>`
- QC export root: `<repo-root>/exports/policy_briefing_qc`
- Wrapper CLI: `<repo-root>/scripts/openclaw_ops.py`
- Remote QC sample root: `<gov-md-root>/tests/manual_samples/storage_batch`
- Session state root: `<openclaw-state-root>/agents/govpress_qc_ops/state/telegram_qc_sessions`
- QC memory root: `<gov-md-root>/tests/manual_samples/qc_memory`
- Owner DM / fallback sender: `GOVPRESS_QC_DEFAULT_SENDER_ID`

Useful checks:

```bash
python3 <repo-root>/scripts/openclaw_ops.py qc-status --date latest
python3 <repo-root>/scripts/openclaw_ops.py qc-failures --date latest
python3 <repo-root>/scripts/openclaw_ops.py server-status
python3 <repo-root>/scripts/openclaw_ops.py \
  --remote-qc-root <gov-md-root>/tests/manual_samples/storage_batch \
  telegram-dispatch --chat-scope dm --message 'job 목록 보여줘'
```
