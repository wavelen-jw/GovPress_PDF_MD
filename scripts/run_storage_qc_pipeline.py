from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
DEFAULT_GOV_MD_ROOT = Path(os.environ.get("GOV_MD_CONVERTER_ROOT", PROJECT_ROOT.parent / "gov-md-converter")).resolve()
DEFAULT_OUTPUT_ROOT = DEFAULT_GOV_MD_ROOT / "exports" / "policy_briefing_qc"

from server.app.adapters.policy_briefing_qc import run_storage_backed_qc_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the GovPress QC pipeline against deploy storage originals/results/golden")
    parser.add_argument("--date", default=date.today().isoformat(), help="Target report date in YYYY-MM-DD format")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Where to write pipeline artifacts")
    parser.add_argument("--gov-md-converter-root", default=str(DEFAULT_GOV_MD_ROOT), help="Path to the private gov-md-converter repository")
    parser.add_argument(
        "--qc-root",
        default=str(DEFAULT_GOV_MD_ROOT / "tests" / "manual_samples" / "storage_batch"),
        help="QC sample root inside gov-md-converter",
    )
    parser.add_argument(
        "--storage-root",
        default="deploy/wsl/data/storage",
        help="Storage root containing originals/results/golden",
    )
    parser.add_argument("--limit", type=int, help="Maximum number of storage corpus items to scaffold")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold sample directories")
    parser.add_argument("--no-autofill", action="store_true", help="Skip starter assertions and golden candidate generation")
    parser.add_argument("--output", help="Optional explicit path for pipeline_report.json")
    parser.add_argument("--json", action="store_true", help="Print the full pipeline report as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_date = date.fromisoformat(args.date)
    output_root = Path(args.output_root).resolve()
    report_output = (
        Path(args.output).resolve()
        if args.output
        else output_root / target_date.isoformat() / "pipeline_report.json"
    )
    report = run_storage_backed_qc_pipeline(
        target_date=target_date,
        output_root=output_root,
        gov_md_converter_root=args.gov_md_converter_root,
        qc_root=args.qc_root,
        storage_root=args.storage_root,
        limit=args.limit,
        autofill=not args.no_autofill,
        force=args.force,
    )

    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        summary = report["summary"]
        print(
            "Storage-backed QC pipeline summary: "
            f"date={report['date']} "
            f"exported={summary['exported_count']} "
            f"scaffolded={summary['scaffolded_count']} "
            f"review_required={summary['review_required_count']} "
            f"proposals={summary['proposal_count']} "
            f"drafts={summary['draft_count']}"
        )
        print(f"Reports dir: {report['reports_dir']}")
        print(f"Pipeline report written to {report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
