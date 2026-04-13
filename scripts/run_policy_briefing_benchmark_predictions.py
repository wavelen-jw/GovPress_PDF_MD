#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


GOVPRESS_CONVERTER_ROOT = Path("/home/wavel/gov-md-converter")
OPENDATALOADER_BENCH_ROOT = Path("/home/wavel/opendataloader-bench")
if str(GOVPRESS_CONVERTER_ROOT) not in sys.path:
    sys.path.insert(0, str(GOVPRESS_CONVERTER_ROOT))
if str(OPENDATALOADER_BENCH_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(OPENDATALOADER_BENCH_ROOT / "src"))

from govpress_converter import convert_hwpx
from pdf_parser_opendataloader import to_markdown as opendataloader_to_markdown


def write_summary(engine: str, version: str, count: int, elapsed: float, output_dir: Path) -> None:
    summary = {
        "engine_name": engine,
        "engine_version": version,
        "document_count": count,
        "total_elapsed": elapsed,
        "elapsed_per_doc": elapsed / count if count else 0,
        "date": time.strftime("%Y-%m-%d"),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2)
    )


def write_failures(engine: str, failures: list[dict], output_dir: Path) -> None:
    (output_dir / "failures.json").write_text(
        json.dumps({"engine_name": engine, "failures": failures}, ensure_ascii=False, indent=2)
    )


def run_readhim(hwpx_dir: Path, prediction_root: Path) -> None:
    markdown_dir = prediction_root / "readhim" / "markdown"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    docs = sorted(hwpx_dir.glob("*.hwpx"))
    start = time.time()
    failures: list[dict] = []
    success = 0
    for path in docs:
        try:
            markdown = convert_hwpx(path, table_mode="text")
            (markdown_dir / f"{path.stem}.md").write_text(markdown)
            success += 1
            print(f"readhim {path.stem}")
        except Exception as exc:  # pragma: no cover - batch failure logging
            failures.append({"document_id": path.stem, "error": repr(exc)})
            print(f"readhim_fail {path.stem} {exc}")
    write_summary("readhim", "0.1.0-hwpx", success, time.time() - start, markdown_dir.parent)
    write_failures("readhim", failures, markdown_dir.parent)


def run_opendataloader(pdf_dir: Path, prediction_root: Path) -> None:
    markdown_dir = prediction_root / "opendataloader" / "markdown"
    markdown_dir.mkdir(parents=True, exist_ok=True)
    docs = sorted(pdf_dir.glob("*.pdf"))
    start = time.time()
    failures: list[dict] = []
    success = 0
    for path in docs:
        try:
            opendataloader_to_markdown(None, path, markdown_dir)
            if (markdown_dir / f"{path.stem}.md").exists():
                success += 1
                print(f"opendataloader {path.stem}")
            else:
                failures.append({"document_id": path.stem, "error": "markdown output missing"})
                print(f"opendataloader_fail {path.stem} markdown output missing")
        except Exception as exc:  # pragma: no cover - batch failure logging
            failures.append({"document_id": path.stem, "error": repr(exc)})
            print(f"opendataloader_fail {path.stem} {exc}")
    write_summary("opendataloader", "custom-policy-briefing", success, time.time() - start, markdown_dir.parent)
    write_failures("opendataloader", failures, markdown_dir.parent)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--prediction-root", required=True)
    parser.add_argument(
        "--engine",
        choices=["readhim", "opendataloader", "all"],
        default="all",
    )
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    prediction_root = Path(args.prediction_root)
    if args.engine in {"readhim", "all"}:
        run_readhim(input_dir / "hwpxs", prediction_root)
    if args.engine in {"opendataloader", "all"}:
        run_opendataloader(input_dir / "pdfs", prediction_root)


if __name__ == "__main__":
    main()
