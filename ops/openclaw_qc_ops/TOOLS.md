# GovPress QC Ops Tools

- Repo root: `/home/wavel/projects/GovPress_PDF_MD`
- gov-md-converter root: `/home/wavel/projects/gov-md-converter`
- QC export root: `/home/wavel/projects/GovPress_PDF_MD/exports/policy_briefing_qc`
- Wrapper CLI: `/home/wavel/projects/GovPress_PDF_MD/scripts/openclaw_ops.py`

Useful checks:

```bash
python3 /home/wavel/projects/GovPress_PDF_MD/scripts/openclaw_ops.py qc-status --date latest
python3 /home/wavel/projects/GovPress_PDF_MD/scripts/openclaw_ops.py qc-failures --date latest
python3 /home/wavel/projects/GovPress_PDF_MD/scripts/openclaw_ops.py server-status
```
