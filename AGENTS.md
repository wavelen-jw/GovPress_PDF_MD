# GovPress_PDF_MD Agent Instructions

This file is the repo-local instruction document for Codex and other coding agents.
Read it before changing service, frontend, deployment, storage, or policy-briefing QC behavior.

## Remote Git Context

- Remote: `https://github.com/wavelen-jw/GovPress_PDF_MD.git`
- Default branch: `web`
- This repo is the product/service repo for the Readhim web app, API server, deployment, storage bridge, and policy-briefing QC orchestration.

## Cross-Repo Contract

- `GovPress_PDF_MD`: product service, UI, API, storage bridge, deployment, policy-briefing cache, export, and QC orchestration.
- `gov-md-converter`: canonical Markdown conversion engine and conversion quality rules.
- `GovPress-MCP`: long-term corpus ingestion, indexing, and MCP tools.
- Do not implement converter quality rules in this repo's package mirror or adapters. Fix conversion behavior in `gov-md-converter`, release/tag it there, then update this repo's dependency or packaged copy.
- Do not use MCP ingestion code as the service runtime path. Service APIs should remain optimized for on-demand user actions and policy-briefing browsing.
- Do not make bulk ingestion jobs call this service's public API endpoints. Bulk collection belongs in `GovPress-MCP` and should call upstream korea.kr/data.go.kr sources directly.

## Runtime Ownership

- Frontend app lives under `mobile/`.
- Server app lives under `server/app/`.
- Deployment and host-specific scripts live under `deploy/` and `.github/workflows/`.
- Operational scripts live under `scripts/`.
- Runtime storage under `storage/` and deployment data directories is operational state, not source-of-truth code.
- `packages/govpress-converter` is not the canonical converter implementation. Treat it as a packaged/runtime dependency artifact unless a task explicitly asks to update vendored package plumbing.

## Policy-Briefing Service Rules

- Policy-briefing list/detail/cache behavior is owned by `server/app/adapters/policy_briefing.py`, `server/app/api/policy_briefings.py`, and related storage/QC scripts.
- Recent-list and cache optimizations should avoid repeated upstream calls for dates that cannot change. Today may change during the day; past dates should be treated as stable once cached.
- API keys must come from environment variables or configured secrets only. Never log or commit service keys.
- User-facing failure messages must distinguish no HWPX attachment, upstream download failure, conversion failure, and missing job/detail state.

## QC And Deployment Rules

- QC sample generation/export can be orchestrated here, but converter fixes belong in `gov-md-converter`.
- Keep QC jobs on dedicated branches when doing converter-quality work. Do not mix unrelated frontend/deploy edits into QC branches.
- Converter releases are deployed through `deploy/converter.version`. The `Update Converter Version` workflow updates that file on `web` and then dispatches `vps.yml`; do not hand-edit server `.env` converter tags.
- For frontend changes, run `npm run typecheck` in `mobile/` when TypeScript or component code changes.
- For server changes, run the narrowest relevant Python tests or health checks available for the touched path.
- For deployment changes, verify the target workflow or script path and document the server target (`serverW`, `serverH`, etc.) in the commit/PR notes.

## Agent-Readable References

- `README.md`: product overview.
- `docs/serverw-split-edge-runbook.md`: serverW/split-edge operations.
- `docs/policy-briefing-qc-status-2026-04-12.md`: policy-briefing QC operations snapshot.
- `ops/openclaw_qc_ops/AGENTS.md`: OpenClaw QC ops only. Do not treat it as general service guidance.
