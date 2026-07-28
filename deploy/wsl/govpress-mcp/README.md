# GovPress MCP recovery

Recovered on 2026-06-19 from live Docker container metadata after the WSL reset.

Current operating layout:
- Hot data stays on WSL ext4: `~/projects/govpress-mcp/data`.
- D: is used only for compressed cold archives: `/mnt/d/govpress-mcp-archives`.
- Raw HWP/HWPX/PDF files must not be copied to D: in unpacked form. Use monthly `.tar.gz` archives plus `.sha256` manifests.
- Use `ARCHIVE_ENCRYPT=1` only when an encrypted `.tar.gz.gpg` archive is specifically required.
- TEI runs on GPU with `ghcr.io/huggingface/text-embeddings-inference:cuda-latest` and `gpus: all`.
- MCP HTTP is bound to W-local localhost only: `127.0.0.1:8000`.

Recovered data status:
- Original Qdrant and Redis data were not recoverable after the WSL reset.
- Backfill on 2026-06-20 created 402 markdown docs covering 2026-06-02..2026-06-20.
- Hot index currently has 402 docs and 1158 Qdrant chunks.

Operations:

Hancom HWP SDK queue processing:
- The Hancom HWP SDK is Windows-only. The WSL bridge calls Windows Python through `scripts/hancom-hwp2hwpx-windows.sh`.
- Copy `scripts/hancom.env.example` to `hancom.env` and set `HANCOM_SDK_DIR` to the directory containing `hwpsdk.py` and `SHDKFunctionExport.dll`, or the SDK root containing `Bin/`.
- `HANCOM_HWP2HWPX_CMD=scripts/hancom-hwp2hwpx-windows.sh` is the default bridge command for Windows SDK usage.
- Process queued HWP files: `scripts/process-hwp-queue.sh [LIMIT]`
- The process is: fix `data/` permissions -> convert `raw/.../*.hwp` to adjacent `*.hwpx` -> run MCP `bulk_ingest --from-hwp-queue` -> run hot index.
- If WSL interop does not expose `cmd.exe`, set `CMD_EXE=/mnt/c/Windows/System32/cmd.exe` or enable WSL interop.
- Start services: `docker compose up -d`
- Check services: `docker compose ps`
- Ingest and incrementally index: `scripts/ingest-recent.sh YYYY-MM-DD [YYYY-MM-DD] [LIMIT]`
- Monthly backfill writes month-scoped HWP queues such as `data/fetch-log/hwp-queue-2021-02.jsonl`; avoid processing the global `hwp-queue.jsonl` for long backfills.
- Rebuild initial hot index: `scripts/derive-hot.sh --initial`
- Incremental hot index only: `scripts/derive-hot.sh`
- Create monthly compressed archive on D: `scripts/archive-month.sh YYYY-MM`
- Create legacy encrypted monthly archive if needed: `ARCHIVE_ENCRYPT=1 GPG_PASSPHRASE_FILE=~/.govpress-mcp-archive.pass scripts/archive-month.sh YYYY-MM`

Storage policy:
- Do not use GitHub as the raw archive store. Five years of raw attachments are too large/noisy for normal Git operations and will make clone/fetch/CI expensive.
- Keep GitHub for code, manifests, and small operational metadata. Keep raw public files in compressed monthly archives on D: or, later, object storage/S3-compatible storage if D: becomes insufficient.

Notes:
- The upstream API returned HTTP 500 for 2026-06-01 during backfill; retry that date separately later.
- `govpress-mcp-converter:latest` currently lacks a `git` binary. `scripts/ingest-recent.sh` installs a temporary in-container git shim for frontmatter metadata only.
- Do not delete the external Redis volume unless it has been intentionally replaced.

## Official API metadata reconciliation

Policy briefing API values are authoritative for `news_item_id`, `title`,
`department`, `approve_date`, `original_url`, and all attachments. Published
documents record `metadata_source=policy-briefing-api` and
`metadata_schema_version=1`. HWPX body metadata such as embargo time, contacts,
and page counts remains document content and does not replace API metadata.

The live vector workspace is `/home/wavel/projects/govpress-mcp` on serverW.
Copy `scripts/migrate-api-metadata.py` there and run a month in dry-run mode:

```bash
set -a
. /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/.env
set +a
cd /home/wavel/projects/govpress-mcp
docker compose run --rm \
  -e GOVPRESS_POLICY_BRIEFING_SERVICE_KEY \
  -v "$PWD/scripts:/work/scripts:ro" \
  mcp python /work/scripts/migrate-api-metadata.py 2026 03 \
  --data-root /app/data \
  --db /app/data/govpress.db \
  --qdrant-url http://qdrant:6333
```

The manifest is written under
`data/fetch-log/metadata-migration/YYYY-MM.jsonl`.

- `unchanged`: all stores already use the API values.
- `metadata_only`: patch frontmatter, SQLite, and Qdrant payload without TEI.
- `rerender_reembed`: the H1 or explicit agency press label conflicts with the
  API; selectively reconvert and re-embed only these IDs.
- `deferred`: the API item or published Markdown is unavailable.

After reviewing the manifest, add `--apply-metadata-only`. The tool creates an
online SQLite backup and a Qdrant collection snapshot first. It preserves the
Markdown body, verifies target rows and point counts, updates
`indexed_docs` to prevent unnecessary incremental embedding, and writes
`YYYY-MM-rerender-reembed.ids` for the selective conversion pipeline.

Acceptance checks:

- API-backed departments must not remain `미상`.
- Frontmatter and SQLite must match the API title, department, approval time,
  and original URL.
- Qdrant department and approval-time payloads must match the API.
- `metadata_only` body and vector SHA-256 values must remain unchanged.
- A second run must classify the migrated item as `unchanged`.
- Reference document `156751988` must resolve to `행정안전부`.
