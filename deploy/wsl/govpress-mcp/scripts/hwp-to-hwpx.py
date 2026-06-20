#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert GovPress HWP queue files to HWPX using Hancom SDK.")
    parser.add_argument("--data-root", default="data")
    parser.add_argument("--queue", default="data/fetch-log/hwp-queue.jsonl")
    parser.add_argument("--output-queue", default=None)
    parser.add_argument("--log-json", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--workers", type=int, default=int(os.environ.get("HWP_CONVERT_WORKERS", "1")))
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--cmd",
        default=os.environ.get("HANCOM_HWP2HWPX_CMD") or os.environ.get("HWP2HWPX_CMD"),
        help=(
            "Hancom SDK command. Use {input} and {output} placeholders when needed. "
            "If placeholders are omitted, input and output paths are appended."
        ),
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def append_jsonl(path: Path | None, row: dict[str, object], lock: threading.Lock | None = None) -> None:
    if path is None:
        return
    if lock is None:
        lock = threading.Lock()
    with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_queue(path: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(
            {
                "news_item_id": str(row["news_item_id"]),
                "approve_date": str(row["approve_date"]),
                "reason": str(row["reason"]),
                "hwp_path": str(row["hwp_path"]),
            }
        )
    return rows



def decode_output(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    for encoding in ("utf-8", "cp949", "euc-kr"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("utf-8", errors="replace")

def build_command(template: str, input_path: Path, output_path: Path) -> list[str]:
    if "{input}" in template or "{output}" in template:
        rendered = template.format(input=str(input_path), output=str(output_path))
        return shlex.split(rendered)
    return [*shlex.split(template), str(input_path), str(output_path)]



def convert_one(
    row: dict[str, str],
    *,
    data_root: Path,
    cmd_template: str,
    force: bool,
    dry_run: bool,
    log_path: Path | None,
    log_lock: threading.Lock,
) -> tuple[str, dict[str, str] | None]:
    hwp_rel = Path(row["hwp_path"])
    hwp_path = data_root / hwp_rel
    hwpx_path = hwp_path.with_suffix(".hwpx")
    event = {
        "timestamp": now_iso(),
        "news_item_id": row["news_item_id"],
        "hwp_path": str(hwp_rel),
        "hwpx_path": str(hwpx_path.relative_to(data_root)),
    }

    if hwpx_path.exists() and not force:
        append_jsonl(log_path, {**event, "status": "exists"}, log_lock)
        return "exists", row
    if not hwp_path.exists():
        append_jsonl(log_path, {**event, "status": "missing_hwp"}, log_lock)
        return "missing", None
    if dry_run:
        append_jsonl(log_path, {**event, "status": "dry_run", "cmd": cmd_template}, log_lock)
        return "dry_run", None

    hwpx_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = hwpx_path.with_suffix(hwpx_path.suffix + f".tmp.{os.getpid()}.{threading.get_ident()}")
    tmp_path.unlink(missing_ok=True)
    cmd = build_command(cmd_template, hwp_path, tmp_path)
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=False, timeout=180)
    except Exception as exc:
        append_jsonl(log_path, {**event, "status": "failed", "error": f"{type(exc).__name__}: {exc}"}, log_lock)
        return "failed", None
    if not tmp_path.exists() or tmp_path.stat().st_size == 0:
        detail = (decode_output(result.stderr) or decode_output(result.stdout)).strip()
        append_jsonl(
            log_path,
            {
                **event,
                "status": "failed",
                "returncode": result.returncode,
                "detail": detail[-1000:],
            },
            log_lock,
        )
        tmp_path.unlink(missing_ok=True)
        return "failed", None
    tmp_path.replace(hwpx_path)
    append_jsonl(log_path, {**event, "status": "converted", "bytes": hwpx_path.stat().st_size}, log_lock)
    return "converted", row


def main() -> int:
    args = parse_args()
    data_root = Path(args.data_root)
    queue_path = Path(args.queue)
    log_path = Path(args.log_json) if args.log_json else None
    output_queue = Path(args.output_queue) if args.output_queue else data_root / "fetch-log" / "hwp-queue-converted.jsonl"

    if not args.cmd:
        print(
            "Missing Hancom SDK command. Set HANCOM_HWP2HWPX_CMD or pass --cmd.\n"
            "Example with placeholders: HANCOM_HWP2HWPX_CMD='/opt/hancom/bin/hwp2hwpx --input {input} --output {output}'",
            file=sys.stderr,
        )
        return 2
    if not queue_path.exists():
        print(f"Missing queue: {queue_path}", file=sys.stderr)
        return 1

    rows = load_queue(queue_path)
    if args.limit is not None:
        rows = rows[: args.limit]
    if args.workers < 1:
        print("--workers must be >= 1", file=sys.stderr)
        return 2

    output_queue.parent.mkdir(parents=True, exist_ok=True)
    successes: list[dict[str, str]] = []
    stats = {"converted": 0, "exists": 0, "missing": 0, "failed": 0, "dry_run": 0}
    log_lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        results = executor.map(
            lambda row: convert_one(
                row,
                data_root=data_root,
                cmd_template=args.cmd,
                force=args.force,
                dry_run=args.dry_run,
                log_path=log_path,
                log_lock=log_lock,
            ),
            rows,
        )
        for status, row in results:
            stats[status] += 1
            if row is not None:
                successes.append(row)

    with output_queue.open("w", encoding="utf-8") as handle:
        for row in successes:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(
        " ".join(
            [
                f"converted={stats['converted']}",
                f"exists={stats['exists']}",
                f"missing={stats['missing']}",
                f"failed={stats['failed']}",
                f"dry_run={stats['dry_run']}",
                f"output_queue={output_queue}",
            ]
        )
    )
    return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
