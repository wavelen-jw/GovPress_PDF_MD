from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_report(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).resolve().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Pipeline report must be a JSON object")
    return payload


def build_markdown_summary(report: dict[str, object]) -> str:
    export = report.get("export") if isinstance(report.get("export"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    qc_commands = report.get("qc_commands") if isinstance(report.get("qc_commands"), list) else []

    lines = [
        "# Policy Briefing QC Summary",
        "",
        f"- date: `{report.get('date')}`",
        f"- exported: `{summary.get('exported_count')}`",
        f"- scaffolded: `{summary.get('scaffolded_count')}`",
        f"- review_required: `{summary.get('review_required_count')}`",
        f"- proposals: `{summary.get('proposal_count')}`",
        f"- drafts: `{summary.get('draft_count')}`",
        "",
    ]
    missing = export.get("missing_news_item_ids")
    if isinstance(missing, list) and missing:
        lines.extend(
            [
                "## Missing Requested Items",
                "",
                *[f"- `{item_id}`" for item_id in missing],
                "",
            ]
        )

    if isinstance(qc_commands, list) and qc_commands:
        lines.extend(["## QC Commands", ""])
        for entry in qc_commands:
            if not isinstance(entry, dict):
                continue
            command = entry.get("command")
            returncode = entry.get("returncode")
            output_path = entry.get("output_path")
            lines.append(f"- `{command}` returncode=`{returncode}` output=`{output_path}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def evaluate_report(
    report: dict[str, object],
    *,
    fail_on_review_required: bool = True,
    fail_on_regression: bool = True,
    fail_on_command_error: bool = True,
) -> tuple[int, list[str]]:
    reasons: list[str] = []
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    qc_commands = report.get("qc_commands") if isinstance(report.get("qc_commands"), list) else []

    review_required_count = summary.get("review_required_count")
    if fail_on_review_required and isinstance(review_required_count, int) and review_required_count > 0:
        reasons.append(f"review_required_count={review_required_count}")

    for entry in qc_commands:
        if not isinstance(entry, dict):
            continue
        command = str(entry.get("command"))
        returncode = entry.get("returncode")
        if fail_on_command_error and isinstance(returncode, int) and returncode != 0:
            reasons.append(f"{command}_returncode={returncode}")
        if fail_on_regression and command == "regression":
            payload = entry.get("payload")
            if isinstance(payload, list):
                failed = sum(
                    1
                    for item in payload
                    if isinstance(item, dict) and item.get("passed") is False
                )
                if failed > 0:
                    reasons.append(f"regression_failed_samples={failed}")

    return (1 if reasons else 0, reasons)


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
