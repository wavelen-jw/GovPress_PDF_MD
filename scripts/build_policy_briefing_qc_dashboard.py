from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path


def _load_report(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid report JSON: {path}")
    return payload


def _collect_runs(root: Path) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []
    for path in sorted(root.glob("*/pipeline_report.json")):
        report = _load_report(path)
        report["report_path"] = str(path)
        runs.append(report)
    return runs


def _triage_entries(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if isinstance(entry, dict) and entry.get("command") == "triage":
            payload = entry.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("entries"), list):
                return [item for item in payload["entries"] if isinstance(item, dict)]
    return []


def _regression_entries(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if isinstance(entry, dict) and entry.get("command") == "regression":
            payload = entry.get("payload")
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
    return []


def _suggest_fix_entries(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if isinstance(entry, dict) and entry.get("command") == "suggest-fix":
            payload = entry.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("proposals"), list):
                return [item for item in payload["proposals"] if isinstance(item, dict)]
    return []


def build_dashboard_payload(root: str | Path) -> dict[str, object]:
    resolved_root = Path(root).resolve()
    runs = _collect_runs(resolved_root)
    defect_counter: Counter[str] = Counter()
    sample_counter: Counter[str] = Counter()
    timeline: list[dict[str, object]] = []

    for report in runs:
        summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        triage_entries = _triage_entries(report)
        regression_entries = _regression_entries(report)
        suggest_entries = _suggest_fix_entries(report)
        for entry in triage_entries:
            if entry.get("review_required"):
                sample_id = str(entry.get("sample_id", ""))
                if sample_id:
                    sample_counter[sample_id] += 1
        for entry in suggest_entries:
            defect_class = str(entry.get("defect_class", ""))
            if defect_class:
                defect_counter[defect_class] += 1
        timeline.append(
            {
                "date": report.get("date"),
                "exported_count": summary.get("exported_count", 0),
                "review_required_count": summary.get("review_required_count", 0),
                "proposal_count": summary.get("proposal_count", 0),
                "draft_count": summary.get("draft_count", 0),
                "regression_failed_count": sum(1 for item in regression_entries if item.get("passed") is False),
                "report_path": report.get("report_path"),
            }
        )

    latest = runs[-1] if runs else None
    latest_triage = _triage_entries(latest) if isinstance(latest, dict) else []
    latest_regression = _regression_entries(latest) if isinstance(latest, dict) else []
    latest_suggest = _suggest_fix_entries(latest) if isinstance(latest, dict) else []

    return {
        "root": str(resolved_root),
        "run_count": len(runs),
        "latest_date": latest.get("date") if isinstance(latest, dict) else None,
        "timeline": timeline,
        "top_defects": [{"defect_class": name, "count": count} for name, count in defect_counter.most_common(10)],
        "top_samples": [{"sample_id": name, "count": count} for name, count in sample_counter.most_common(10)],
        "latest": {
            "summary": latest.get("summary", {}) if isinstance(latest, dict) else {},
            "review_required": latest_triage,
            "regression_failures": [item for item in latest_regression if item.get("passed") is False],
            "proposals": latest_suggest,
        },
    }


def build_dashboard_html(payload: dict[str, object]) -> str:
    latest = payload.get("latest", {}) if isinstance(payload.get("latest"), dict) else {}
    latest_summary = latest.get("summary", {}) if isinstance(latest.get("summary"), dict) else {}
    latest_review = latest.get("review_required", []) if isinstance(latest.get("review_required"), list) else []
    latest_failures = latest.get("regression_failures", []) if isinstance(latest.get("regression_failures"), list) else []
    latest_proposals = latest.get("proposals", []) if isinstance(latest.get("proposals"), list) else []
    top_defects = payload.get("top_defects", []) if isinstance(payload.get("top_defects"), list) else []
    top_samples = payload.get("top_samples", []) if isinstance(payload.get("top_samples"), list) else []
    timeline = payload.get("timeline", []) if isinstance(payload.get("timeline"), list) else []

    def _metric(label: str, value: object) -> str:
        return f'<div class="metric"><div class="metric-label">{escape(label)}</div><div class="metric-value">{escape(str(value))}</div></div>'

    def _list(items: list[str]) -> str:
        if not items:
            return "<li>None</li>"
        return "".join(f"<li>{item}</li>" for item in items)

    review_items = [
        f"<code>{escape(str(item.get('sample_id', '')))}</code> risk={escape(str(item.get('risk_score', '-')))} status={escape(str(item.get('sample_status', '-')))}"
        for item in latest_review[:8]
    ]
    failure_items = [
        f"<code>{escape(str(item.get('sample_id', '')))}</code> findings={len(item.get('findings', [])) if isinstance(item.get('findings'), list) else 0}"
        for item in latest_failures[:8]
    ]
    proposal_items = [
        f"<code>{escape(str(item.get('defect_class', '')))}</code> files={escape(', '.join(str(path) for path in item.get('suggested_files', [])[:3]))}"
        for item in latest_proposals[:8]
    ]
    defect_rows = "".join(
        f"<tr><td><code>{escape(str(item.get('defect_class', '')))}</code></td><td>{escape(str(item.get('count', 0)))}</td></tr>"
        for item in top_defects
    )
    sample_rows = "".join(
        f"<tr><td><code>{escape(str(item.get('sample_id', '')))}</code></td><td>{escape(str(item.get('count', 0)))}</td></tr>"
        for item in top_samples
    )
    timeline_rows = "".join(
        "<tr>"
        f"<td>{escape(str(item.get('date', '')))}</td>"
        f"<td>{escape(str(item.get('exported_count', 0)))}</td>"
        f"<td>{escape(str(item.get('review_required_count', 0)))}</td>"
        f"<td>{escape(str(item.get('proposal_count', 0)))}</td>"
        f"<td>{escape(str(item.get('draft_count', 0)))}</td>"
        f"<td>{escape(str(item.get('regression_failed_count', 0)))}</td>"
        "</tr>"
        for item in timeline[-30:]
    )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Policy Briefing QC Dashboard</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --ink: #1f2a1f;
      --muted: #5d6559;
      --card: #fffdf7;
      --line: #d7cfbe;
      --accent: #1d6b57;
      --warn: #a24b2a;
      --soft: #e7dfcf;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: Georgia, 'Noto Serif KR', serif; background: linear-gradient(180deg, #f7f3ea 0%, #ece4d2 100%); color: var(--ink); }}
    .shell {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 48px; }}
    .hero {{ padding: 28px; background: radial-gradient(circle at top left, #fffef8 0%, #efe6d5 80%); border: 1px solid var(--line); border-radius: 24px; box-shadow: 0 16px 32px rgba(55, 44, 20, 0.08); }}
    h1, h2 {{ margin: 0 0 12px; }}
    p {{ color: var(--muted); }}
    .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; margin-top: 20px; }}
    .metric {{ background: var(--card); border: 1px solid var(--line); border-radius: 18px; padding: 16px; }}
    .metric-label {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.08em; color: var(--muted); }}
    .metric-value {{ font-size: 32px; margin-top: 10px; font-weight: bold; color: var(--accent); }}
    .grid {{ display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 18px; margin-top: 18px; }}
    .card {{ background: rgba(255,253,247,0.92); border: 1px solid var(--line); border-radius: 22px; padding: 20px; box-shadow: 0 12px 24px rgba(55, 44, 20, 0.06); }}
    .card h2 {{ font-size: 20px; }}
    ul {{ margin: 12px 0 0; padding-left: 18px; }}
    li {{ margin: 8px 0; line-height: 1.45; }}
    code {{ background: var(--soft); padding: 2px 6px; border-radius: 6px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 14px; }}
    th, td {{ border-bottom: 1px solid var(--line); padding: 10px 8px; text-align: left; vertical-align: top; }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; }}
    .full {{ margin-top: 18px; }}
    .note {{ margin-top: 10px; font-size: 13px; color: var(--muted); }}
    .warn {{ color: var(--warn); }}
    @media (max-width: 900px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <h1>Policy Briefing QC Dashboard</h1>
      <p>Latest run date: <strong>{escape(str(payload.get("latest_date") or "-"))}</strong></p>
      <div class="metrics">
        {_metric("Runs", payload.get("run_count", 0))}
        {_metric("Latest Exported", latest_summary.get("exported_count", 0))}
        {_metric("Review Required", latest_summary.get("review_required_count", 0))}
        {_metric("Proposals", latest_summary.get("proposal_count", 0))}
        {_metric("Drafts", latest_summary.get("draft_count", 0))}
      </div>
    </section>

    <div class="grid">
      <section class="card">
        <h2>Latest Review Queue</h2>
        <ul>{_list(review_items)}</ul>
      </section>
      <section class="card">
        <h2>Latest Regression Failures</h2>
        <ul>{_list(failure_items)}</ul>
      </section>
    </div>

    <div class="grid">
      <section class="card">
        <h2>Immediate Fix Targets</h2>
        <ul>{_list(proposal_items)}</ul>
      </section>
      <section class="card">
        <h2>Top Defect Classes</h2>
        <table>
          <thead><tr><th>Defect</th><th>Count</th></tr></thead>
          <tbody>{defect_rows or '<tr><td colspan="2">No data</td></tr>'}</tbody>
        </table>
      </section>
    </div>

    <section class="card full">
      <h2>Recurring Samples</h2>
      <table>
        <thead><tr><th>Sample</th><th>Count</th></tr></thead>
        <tbody>{sample_rows or '<tr><td colspan="2">No data</td></tr>'}</tbody>
      </table>
    </section>

    <section class="card full">
      <h2>Timeline</h2>
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Exported</th><th>Review Required</th><th>Proposals</th><th>Drafts</th><th>Regression Fails</th>
          </tr>
        </thead>
        <tbody>{timeline_rows or '<tr><td colspan="6">No runs yet</td></tr>'}</tbody>
      </table>
      <div class="note">This dashboard is generated from saved <code>pipeline_report.json</code> files under the export root.</div>
    </section>
  </div>
</body>
</html>
"""


def write_dashboard(root: str | Path, *, output_html: str | Path, output_json: str | Path | None = None) -> dict[str, object]:
    payload = build_dashboard_payload(root)
    html = build_dashboard_html(payload)
    html_path = Path(output_html).resolve()
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(html, encoding="utf-8")
    if output_json is not None:
        json_path = Path(output_json).resolve()
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


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
