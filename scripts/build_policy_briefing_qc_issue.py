from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOV_MD_ROOT = (PROJECT_ROOT / ".." / "gov-md-converter").resolve()
if str(GOV_MD_ROOT) not in sys.path:
    sys.path.insert(0, str(GOV_MD_ROOT))


def _load_issue_module():
    from src.qc_issue import ISSUE_MARKER, build_issue_body, build_issue_payload, load_report

    return ISSUE_MARKER, build_issue_body, build_issue_payload, load_report


def build_issue_payload(*args, **kwargs):
    _, _, build_issue_payload_fn, _ = _load_issue_module()
    return build_issue_payload_fn(*args, **kwargs)


def build_issue_body(*args, **kwargs):
    _, build_issue_body_fn, _, _ = _load_issue_module()
    return build_issue_body_fn(*args, **kwargs)


def load_report(*args, **kwargs):
    _, _, _, load_report_fn = _load_issue_module()
    return load_report_fn(*args, **kwargs)


ISSUE_MARKER = "<!-- policy-briefing-qc-issue -->"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a GitHub issue payload from a policy briefing QC pipeline report")
    parser.add_argument("report", help="Path to the aggregated pipeline JSON report")
    parser.add_argument("--summary-markdown", help="Optional path to an existing Markdown summary")
    parser.add_argument("--output", help="Optional path to write the payload JSON")
    parser.add_argument("--json", action="store_true", help="Print the payload as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = load_report(args.report)
    summary_text = None
    if args.summary_markdown:
        summary_text = Path(args.summary_markdown).resolve().read_text(encoding="utf-8")
    payload = build_issue_payload(report, summary_markdown=summary_text)
    if args.output:
        Path(args.output).resolve().write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json or not args.output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
