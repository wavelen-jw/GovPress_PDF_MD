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
Copy `scripts/migrate-api-metadata.py` there and run a month in dry-run mode.
The month scope is driven by Markdown already present under `data/md/YYYY/MM`;
API-only items that have never been vectorized are not migration candidates.

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
- `rerender_reembed`: the Markdown frontmatter cannot be parsed safely;
  selectively reconvert and re-embed only these IDs.
- `deferred`: the API item or published Markdown is unavailable.

An API headline or agency that differs from the source document's H1 or press
label is recorded as `body_differences`. It is not a conversion failure: the
API owns catalog metadata while the HWPX body remains source document content.

After reviewing the manifest, add `--apply-metadata-only`. The tool creates an
online SQLite backup and a Qdrant collection snapshot first. It preserves the
candidate Markdown files in a tar snapshot, applies updates in small batches,
verifies exact body bytes, vector hashes, target rows, point counts, and
canonical Qdrant payloads, updates
`indexed_docs` to prevent unnecessary incremental embedding, and writes
`YYYY-MM-rerender-reembed.ids` for the selective conversion pipeline.
The recovery pointers are written with status `ready` before any metadata is
changed, then finalized as `completed` or `failed`.

Acceptance checks:

- API-backed departments must not remain `미상`.
- Frontmatter and SQLite must match the API title, department, approval time,
  and original URL.
- Qdrant department and approval-time payloads must match the API.
- `metadata_only` body and vector SHA-256 values must remain unchanged.
- A second run must classify the migrated item as `unchanged`.
- Reference document `156751988` must resolve to `행정안전부`.

### Whole-corpus metadata overwrite

Use the overwrite mode when an existing vector corpus was built before API
metadata became authoritative. It does not compare every current field and
does not reconvert or re-embed documents. It inventories local Markdown,
fetches each API date once into a resumable monthly cache, and classifies only
whether each document can be updated safely:

- `eligible`: API metadata and all three storage records exist.
- `vectorization_required`: Markdown and SQLite can receive API metadata, but
  no Qdrant point exists yet.
- `deferred`: the official API has no matching item.
- `invalid`: Markdown, SQLite, or Qdrant structure is incomplete.

Persistent API failures are cached as `failed_days`; unresolved documents in
those months use `api_metadata_unavailable_after_day_failure` instead of being
silently treated as ordinary API omissions. A failed day does not stop the
remaining corpus preflight.

Run preflight first:

```bash
docker compose run --rm \
  -e GOVPRESS_POLICY_BRIEFING_SERVICE_KEY \
  -v "$PWD/scripts:/work/scripts:ro" \
  mcp python /work/scripts/migrate-api-metadata.py \
  --overwrite-all 2014-01 2026-07 \
  --data-root /app/data \
  --db /app/data/govpress.db \
  --qdrant-url http://qdrant:6333 \
  --output-dir /app/data/fetch-log/metadata-migration/full-api-overwrite \
  --jobs 8 \
  --bulk-batch-size 250
```

Review `bulk-overwrite-manifest.jsonl`, then repeat the same command with
`--apply-overwrite`. The output directory is the resume checkpoint and must
not be reused for a different date or ID scope.

For a subset follow-up, pass `--api-cache-dir` pointing to the first run's
`api-cache`. A cached superset is reused when it already contains every
requested ID, avoiding repeated official API calls.

The apply run creates one SQLite backup and one Qdrant snapshot for the entire
scope. Markdown recovery stores only the original frontmatter plus body hashes,
not duplicate copies of every document. Markdown is rewritten with bounded
parallelism, SQLite is updated from one temporary staging table, and Qdrant
payloads are updated through batched point operations. Verification performs
one final Qdrant scan and checks all Markdown and SQLite metadata, body hashes,
target point counts, and a deterministic vector sample.

This path updates metadata only. Any `invalid` document that requires
reconversion or re-embedding must be handed to the improved vectorization
workflow in the server V task; this migration must not invoke an ad hoc
embedding path.

The preflight writes `server-v-vectorization.ids`, `invalid.ids`, and
`api-deferred.ids` automatically. For IDs with no Qdrant points, server V uses
`scripts/derive-targeted-pipeline.py` directly in sequential 250-document
batches (`TEI=64`, `inflight=4`, `prepare_workers=8`, `Qdrant=512`). Do not use
`finalize-archive-month.sh`, because its archive cleanup is unrelated to this
backfill. Before starting, the targeted pipeline must preserve the API-owned
Qdrant payload fields from Markdown frontmatter: `title`, `original_url`,
`metadata_source`, `metadata_schema_version`, `attachments`, and
`attachments_json`.
