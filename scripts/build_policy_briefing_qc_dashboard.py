from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOV_MD_ROOT = (PROJECT_ROOT / ".." / "gov-md-converter").resolve()
if str(GOV_MD_ROOT) not in sys.path:
    sys.path.insert(0, str(GOV_MD_ROOT))

from src.qc_dashboard import build_dashboard_html, build_dashboard_payload, write_dashboard


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a static dashboard from policy briefing QC pipeline reports")
    parser.add_argument("--root", default="exports/policy_briefing_qc", help="Root directory containing dated pipeline reports")
    parser.add_argument("--output-html", default="exports/policy_briefing_qc/dashboard/index.html", help="Where to write the dashboard HTML")
    parser.add_argument("--output-json", default="exports/policy_briefing_qc/dashboard/dashboard.json", help="Where to write the dashboard JSON")
    parser.add_argument("--json", action="store_true", help="Print the aggregated payload as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = write_dashboard(args.root, output_html=args.output_html, output_json=args.output_json)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            "Dashboard summary: "
            f"runs={payload['run_count']} "
            f"latest_date={payload['latest_date']} "
            f"top_defects={len(payload['top_defects'])}"
        )
        print(f"Dashboard HTML written to {Path(args.output_html).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
