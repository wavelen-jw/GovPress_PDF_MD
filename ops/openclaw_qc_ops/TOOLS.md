# GovPress QC Ops Tools

- Repo root: `<repo-root>`
- gov-md-converter root: `<gov-md-root>`
- QC export root: `<repo-root>/exports/policy_briefing_qc`
- Wrapper CLI: `<repo-root>/scripts/openclaw_ops.py`
- Remote QC working root: `<gov-md-root>/tests/manual_samples/storage_batch`
- Curated QC root: `<gov-md-root>/tests/qc_samples`
- Session state root: `<openclaw-state-root>/agents/govpress_qc_ops/state/telegram_qc_sessions`
- QC memory root: `<gov-md-root>/tests/manual_samples/qc_memory`
- Owner DM / fallback sender: `GOVPRESS_QC_DEFAULT_SENDER_ID`

Root semantics:

- `tests/manual_samples/storage_batch` is the working area used by Telegram/Codex QC flows. Samples here are usually `scratch` and may be regenerated.
- `tests/qc_samples` is the authoritative curated corpus. Treat `golden_slices.json` under this root as the source of truth for promoted samples.
- Do not infer curated status from `manual_samples/storage_batch` alone. Some legacy samples may still carry curated-looking artifacts there.

Useful checks:

```bash
python3 <repo-root>/scripts/openclaw_ops.py qc-status --date latest
python3 <repo-root>/scripts/openclaw_ops.py qc-failures --date latest
python3 <repo-root>/scripts/openclaw_ops.py server-status
python3 <repo-root>/scripts/openclaw_ops.py \
  --remote-qc-root <gov-md-root>/tests/manual_samples/storage_batch \
  telegram-dispatch --chat-scope dm --message 'job 목록 보여줘'
```
