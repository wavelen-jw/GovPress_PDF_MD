from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOV_MD_ROOT = (PROJECT_ROOT / ".." / "gov-md-converter").resolve()
if str(GOV_MD_ROOT) not in sys.path:
    sys.path.insert(0, str(GOV_MD_ROOT))

from src.qc_report import build_markdown_summary, evaluate_report, load_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a policy briefing QC pipeline report for CI/cron usage")
    parser.add_argument("report", help="Path to the aggregated pipeline JSON report")
    parser.add_argument("--summary-markdown", help="Optional path to write a Markdown summary")
    parser.add_argument("--allow-review-required", action="store_true", help="Do not fail when review_required_count > 0")
    parser.add_argument("--allow-regression-failures", action="store_true", help="Do not fail when regression payload contains failures")
    parser.add_argument("--allow-command-errors", action="store_true", help="Do not fail when a QC command returns non-zero")
    parser.add_argument("--json", action="store_true", help="Print the evaluation result as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = load_report(args.report)
    markdown = build_markdown_summary(report)
    if args.summary_markdown:
        Path(args.summary_markdown).resolve().write_text(markdown, encoding="utf-8")

    exit_code, reasons = evaluate_report(
        report,
        fail_on_review_required=not args.allow_review_required,
        fail_on_regression=not args.allow_regression_failures,
        fail_on_command_error=not args.allow_command_errors,
    )
    payload = {
        "ok": exit_code == 0,
        "reasons": reasons,
        "summary_markdown": str(Path(args.summary_markdown).resolve()) if args.summary_markdown else None,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        status = "PASS" if exit_code == 0 else "FAIL"
        print(f"QC evaluation {status}")
        if reasons:
            print("Reasons: " + ", ".join(reasons))
        if args.summary_markdown:
            print(f"Summary markdown written to {Path(args.summary_markdown).resolve()}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
