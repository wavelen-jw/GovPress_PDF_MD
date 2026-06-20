# GovPress MCP recovery

Recovered on 2026-06-19 from live Docker container metadata after the WSL reset.

Current operating layout:
- Hot data stays on WSL ext4: `~/projects/govpress-mcp/data`.
- D: is used only for encrypted cold archives: `/mnt/d/govpress-mcp-archives`.
- Raw HWPX/PDF files must not be copied to D: in unpacked form.
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
- Rebuild initial hot index: `scripts/derive-hot.sh --initial`
- Incremental hot index only: `scripts/derive-hot.sh`
- Create encrypted cold archive on D: `scripts/archive-cold.sh`

Notes:
- The upstream API returned HTTP 500 for 2026-06-01 during backfill; retry that date separately later.
- `govpress-mcp-converter:latest` currently lacks a `git` binary. `scripts/ingest-recent.sh` installs a temporary in-container git shim for frontmatter metadata only.
- Do not delete the external Redis volume unless it has been intentionally replaced.
