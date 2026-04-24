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
from server.app.adapters.policy_briefing_qc import export_policy_briefings_for_qc, run_gov_md_scaffold


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export policy briefing HWPX/PDF files for gov-md-converter QC")
    parser.add_argument("--date", default=date.today().isoformat(), help="Target date in YYYY-MM-DD format")
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT), help="Where to export raw files")
    parser.add_argument(
        "--news-item-id",
        action="append",
        help="Specific news_item_id to export. Repeat to export multiple ids.",
    )
    parser.add_argument("--limit", type=int, help="Maximum number of items to export after filtering")
    parser.add_argument("--cached-only", action="store_true", help="Use cached catalog items without forcing refresh")
    parser.add_argument("--no-pdf", action="store_true", help="Skip primary PDF download even when available")
    parser.add_argument("--json", action="store_true", help="Print the full export report as JSON")
    parser.add_argument(
        "--gov-md-converter-root",
        default=str(DEFAULT_GOV_MD_ROOT),
        help="Optional path to the private gov-md-converter repository",
    )
    parser.add_argument(
        "--qc-root",
        default=str(DEFAULT_GOV_MD_ROOT / "tests" / "qc_samples"),
        help="QC sample root inside gov-md-converter. Required with --gov-md-converter-root",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite existing scaffold sample directories")
    parser.add_argument("--no-autofill", action="store_true", help="Skip starter assertions and golden candidate generation")
    parser.add_argument("--sample-status", default="scratch", help="Sample status to use for scaffolded QC samples")
    parser.add_argument("--output", help="Optional path to write the report JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    target_date = date.fromisoformat(args.date)
    storage_root = Path(os.environ.get("GOVPRESS_STORAGE_ROOT", PROJECT_ROOT / "storage"))
    client = PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY"))
    if not client.configured:
        raise SystemExit("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY is not configured")

    catalog = PolicyBriefingCatalog(client=client, cache_path=storage_root / "policy_briefing_catalog.json")
    report = export_policy_briefings_for_qc(
        client=client,
        catalog=catalog,
        target_date=target_date,
        output_root=args.output_root,
        news_item_ids=args.news_item_id,
        limit=args.limit,
        include_pdf=not args.no_pdf,
        ensure_fresh=not args.cached_only,
        scaffold_runner=run_gov_md_scaffold,
        gov_md_converter_root=args.gov_md_converter_root,
        qc_root=args.qc_root,
        autofill=not args.no_autofill,
        force=args.force,
        sample_status=args.sample_status,
    )
    if report["missing_news_item_ids"]:
        raise SystemExit(f"Missing requested news_item_ids: {', '.join(report['missing_news_item_ids'])}")

    if args.output:
        Path(args.output).resolve().write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            "Policy briefing QC export summary: "
            f"date={report['date']} "
            f"exported={report['exported_count']} "
            f"scaffolded={report['scaffolded_count']}"
        )
        print(f"Export root: {report['output_root']}")
        if args.output:
            print(f"Report written to {Path(args.output).resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
