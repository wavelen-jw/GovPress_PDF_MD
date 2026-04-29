#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


TOP_IDS = [
    "156759031",
    "156754934",
    "156756008",
    "156757632",
    "156757541",
    "156448349",
    "156757495",
    "156757844",
    "156755997",
    "156757801",
]

DEFAULT_CONVERTER_ROOT = Path("/home/wavel/projects/gov-md-converter")
DEFAULT_OUTPUT_ROOT = Path("artifacts/hardest_policy_briefings")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate conversion outputs for the hardest policy briefing page.")
    parser.add_argument("--converter-root", type=Path, default=DEFAULT_CONVERTER_ROOT)
    parser.add_argument("--qc-root", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument(
        "--engine",
        choices=["readhim", "kordoc", "opendataloader", "docling", "all"],
        default="all",
    )
    return parser.parse_args()


def find_samples(qc_root: Path) -> dict[str, Path]:
    samples: dict[str, Path] = {}
    for news_id in TOP_IDS:
        matches = sorted(qc_root.glob(f"*_{news_id}"))
        if not matches:
            raise FileNotFoundError(f"Missing QC sample for news id {news_id} under {qc_root}")
        samples[news_id] = matches[0]
    return samples


def write_status(output_root: Path, engine: str, statuses: list[dict]) -> None:
    target = output_root / "outputs" / engine
    target.mkdir(parents=True, exist_ok=True)
    payload = {
        "engine": engine,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "documents": statuses,
    }
    (target / "status.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def copy_readhim(samples: dict[str, Path], output_root: Path) -> None:
    statuses: list[dict] = []
    target = output_root / "outputs" / "readhim"
    target.mkdir(parents=True, exist_ok=True)
    for news_id, sample in samples.items():
        source = sample / "rendered.md"
        if not source.exists():
            statuses.append({"news_id": news_id, "status": "failed", "error": "rendered.md missing"})
            continue
        shutil.copyfile(source, target / f"{news_id}.md")
        statuses.append({"news_id": news_id, "status": "available"})
    write_status(output_root, "readhim", statuses)


def run_kordoc(samples: dict[str, Path], output_root: Path) -> None:
    statuses: list[dict] = []
    target = output_root / "outputs" / "kordoc"
    target.mkdir(parents=True, exist_ok=True)
    cached_cli = Path("/home/wavel/.npm/_npx/5ea84d466de2b626/node_modules/kordoc/dist/cli.js")
    command_prefix = ["node", str(cached_cli)] if cached_cli.exists() else ["npx", "kordoc"]
    for news_id, sample in samples.items():
        source = sample / "source.hwpx"
        if not source.exists():
            statuses.append({"news_id": news_id, "status": "missing_input", "error": "source.hwpx missing"})
            continue
        output = target / f"{news_id}.md"
        try:
            subprocess.run([*command_prefix, str(source), "-o", str(output), "--silent"], check=True)
        except Exception as exc:
            statuses.append({"news_id": news_id, "status": "failed", "error": str(exc)})
            continue
        statuses.append({"news_id": news_id, "status": "available" if output.exists() else "failed"})
    write_status(output_root, "kordoc", statuses)


def run_opendataloader(samples: dict[str, Path], output_root: Path) -> None:
    statuses: list[dict] = []
    target = output_root / "outputs" / "opendataloader"
    target.mkdir(parents=True, exist_ok=True)
    bench_root = Path("/home/wavel/opendataloader-bench")
    if str(bench_root / "src") not in sys.path:
        sys.path.insert(0, str(bench_root / "src"))
    venv_site = Path("/home/wavel/projects/gov-md-converter/.venv/lib/python3.12/site-packages")
    if venv_site.exists() and str(venv_site) not in sys.path:
        sys.path.insert(0, str(venv_site))
    try:
        from pdf_parser_opendataloader import to_markdown as opendataloader_to_markdown

        def convert_pdf(source: Path, out_dir: Path) -> None:
            opendataloader_to_markdown(None, source, out_dir)

    except Exception as exc:
        try:
            from opendataloader_pdf import convert as opendataloader_convert

            def convert_pdf(source: Path, out_dir: Path) -> None:
                opendataloader_convert(str(source), output_dir=str(out_dir), format="markdown", quiet=True)

        except Exception:
            statuses = [{"news_id": news_id, "status": "missing_tool", "error": str(exc)} for news_id in samples]
            write_status(output_root, "opendataloader", statuses)
            return
    for news_id, sample in samples.items():
        source = sample / "source.pdf"
        if not source.exists():
            statuses.append({"news_id": news_id, "status": "missing_input", "error": "source.pdf missing"})
            continue
        before = {path.resolve() for path in target.glob("*.md")}
        try:
            convert_pdf(source, target)
        except Exception as exc:
            statuses.append({"news_id": news_id, "status": "failed", "error": str(exc)})
            continue
        final = target / f"{news_id}.md"
        generated = target / f"{source.stem}.md"
        if generated.exists() and generated != final:
            generated.replace(final)
        if not final.exists():
            after = sorted((path for path in target.glob("*.md") if path.resolve() not in before), key=lambda path: path.stat().st_mtime, reverse=True)
            if after:
                after[0].replace(final)
        statuses.append({"news_id": news_id, "status": "available" if final.exists() else "failed"})
    write_status(output_root, "opendataloader", statuses)


def run_docling(samples: dict[str, Path], output_root: Path) -> None:
    statuses: list[dict] = []
    target = output_root / "outputs" / "docling"
    target.mkdir(parents=True, exist_ok=True)
    docling = shutil.which("docling")
    if not docling:
        statuses = [{"news_id": news_id, "status": "missing_tool", "error": "docling command not found"} for news_id in samples]
        write_status(output_root, "docling", statuses)
        return
    for news_id, sample in samples.items():
        source = sample / "source.pdf"
        if not source.exists():
            statuses.append({"news_id": news_id, "status": "missing_input", "error": "source.pdf missing"})
            continue
        work_dir = target / f".{news_id}"
        work_dir.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run([docling, str(source), "--to", "md", "--output", str(work_dir)], check=True)
        except Exception as exc:
            statuses.append({"news_id": news_id, "status": "failed", "error": str(exc)})
            continue
        candidates = sorted(work_dir.glob("*.md"))
        if candidates:
            shutil.copyfile(candidates[0], target / f"{news_id}.md")
            statuses.append({"news_id": news_id, "status": "available"})
        else:
            statuses.append({"news_id": news_id, "status": "failed", "error": "markdown output missing"})
    write_status(output_root, "docling", statuses)


def main() -> int:
    args = parse_args()
    converter_root = args.converter_root.resolve()
    qc_root = args.qc_root.resolve() if args.qc_root else converter_root / "tests" / "qc_samples_qc_v2"
    output_root = args.output_root.resolve()
    samples = find_samples(qc_root)

    if args.engine in {"readhim", "all"}:
        copy_readhim(samples, output_root)
    if args.engine in {"kordoc", "all"}:
        run_kordoc(samples, output_root)
    if args.engine in {"opendataloader", "all"}:
        run_opendataloader(samples, output_root)
    if args.engine in {"docling", "all"}:
        run_docling(samples, output_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
