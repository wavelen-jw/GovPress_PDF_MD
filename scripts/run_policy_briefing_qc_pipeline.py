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

from server.app.adapters.policy_briefing import PolicyBriefingCatalog, PolicyBriefingClient
from server.app.adapters.policy_briefing_qc import run_policy_briefing_qc_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export policy briefings and run the gov-md-converter QC pipeline")
    parser.add_argument("--date", default=date.today().isoformat(), help="Target date in YYYY-MM-DD format")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Where to export raw files and reports")
    parser.add_argument("--news-item-id", action="append", help="Specific news_item_id to include. Repeat to include multiple ids.")
    parser.add_argument("--limit", type=int, help="Maximum number of items to export after filtering")
    parser.add_argument("--cached-only", action="store_true", help="Use cached catalog items without forcing refresh")
    parser.add_argument("--no-pdf", action="store_true", help="Skip primary PDF download even when available")
    parser.add_argument("--gov-md-converter-root", default=str(DEFAULT_GOV_MD_ROOT), help="Path to the private gov-md-converter repository")
    parser.add_argument(
        "--qc-root",
        default=str(DEFAULT_GOV_MD_ROOT / "tests" / "manual_samples" / "policy_briefings"),
        help="QC sample root inside gov-md-converter",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold sample directories")
    parser.add_argument("--no-autofill", action="store_true", help="Skip starter assertions and golden candidate generation")
    parser.add_argument("--sample-status", default="scratch", help="Sample status to use for scaffolded QC samples")
    parser.add_argument("--output", help="Optional path to write the aggregated pipeline report JSON")
    parser.add_argument("--json", action="store_true", help="Print the full pipeline report as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_date = date.fromisoformat(args.date)
    report_output = (
        Path(args.output).resolve()
        if args.output
        else (Path(args.output_root).resolve() / target_date.isoformat() / "pipeline_report.json")
    )
    storage_root = Path(os.environ.get("GOVPRESS_STORAGE_ROOT", PROJECT_ROOT / "storage"))
    client = PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY"))
    if not client.configured:
        raise SystemExit("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY is not configured")

    catalog = PolicyBriefingCatalog(client=client, cache_path=storage_root / "policy_briefing_catalog.json")
    report = run_policy_briefing_qc_pipeline(
        client=client,
        catalog=catalog,
        target_date=target_date,
        output_root=args.output_root,
        gov_md_converter_root=args.gov_md_converter_root,
        qc_root=args.qc_root,
        news_item_ids=args.news_item_id,
        limit=args.limit,
        include_pdf=not args.no_pdf,
        ensure_fresh=not args.cached_only,
        autofill=not args.no_autofill,
        force=args.force,
        sample_status=args.sample_status,
    )
    if report["export"]["missing_news_item_ids"]:
        raise SystemExit(f"Missing requested news_item_ids: {', '.join(report['export']['missing_news_item_ids'])}")

    report_output.parent.mkdir(parents=True, exist_ok=True)
    report_output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        summary = report["summary"]
        print(
            "Policy briefing QC pipeline summary: "
            f"date={report['date']} "
            f"exported={summary['exported_count']} "
            f"scaffolded={summary['scaffolded_count']} "
            f"review_required={summary['review_required_count']} "
            f"proposals={summary['proposal_count']} "
            f"drafts={summary['draft_count']}"
        )
        print(f"Export root: {report['export']['output_root']}")
        print(f"Reports dir: {report['reports_dir']}")
        print(f"Pipeline report written to {report_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
