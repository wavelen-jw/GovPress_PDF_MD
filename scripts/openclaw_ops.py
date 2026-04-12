from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.build_policy_briefing_qc_dashboard import build_dashboard_payload
from scripts.build_policy_briefing_qc_issue import build_issue_payload, load_report as load_issue_report
from scripts.evaluate_policy_briefing_qc_report import build_markdown_summary


DEFAULT_EXPORT_ROOT = Path(
    __import__("os").environ.get("GOVPRESS_QC_EXPORT_ROOT", PROJECT_ROOT / "exports" / "policy_briefing_qc")
).resolve()
DEFAULT_GOV_MD_ROOT = Path(
    __import__("os").environ.get("GOV_MD_CONVERTER_ROOT", PROJECT_ROOT.parent / "gov-md-converter")
).resolve()
DEFAULT_QC_ROOT = Path(
    __import__("os").environ.get("GOVPRESS_QC_ROOT", DEFAULT_GOV_MD_ROOT / "tests" / "manual_samples" / "policy_briefings")
).resolve()
MOBILE_CONSTANTS_PATH = PROJECT_ROOT / "mobile" / "src" / "constants.ts"
DEFAULT_DASHBOARD_PATH = "/v1/policy-briefings/qc/dashboard"


@dataclass(frozen=True)
class ServerPreset:
    key: str
    label: str
    url: str


def _valid_date(value: str) -> str:
    if value == "latest":
        return value
    date.fromisoformat(value)
    return value


def _valid_sample_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise argparse.ArgumentTypeError("sample_id must match [A-Za-z0-9._-]+")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _report_dates(root: Path) -> list[str]:
    dates = [path.parent.name for path in root.glob("*/pipeline_report.json") if path.parent.is_dir()]
    return sorted({item for item in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", item)})


def resolve_report_path(export_root: Path, requested_date: str) -> Path:
    dates = _report_dates(export_root)
    if not dates:
        raise FileNotFoundError(f"No pipeline_report.json found under {export_root}")
    target_date = dates[-1] if requested_date == "latest" else requested_date
    report_path = export_root / target_date / "pipeline_report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"Pipeline report not found: {report_path}")
    return report_path


def _find_qc_command(report: dict[str, Any], command: str) -> dict[str, Any] | None:
    for entry in report.get("qc_commands", []):
        if isinstance(entry, dict) and entry.get("command") == command:
            return entry
    return None


def _triage_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    entry = _find_qc_command(report, "triage")
    payload = entry.get("payload") if isinstance(entry, dict) else None
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def _regression_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    entry = _find_qc_command(report, "regression")
    payload = entry.get("payload") if isinstance(entry, dict) else None
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _proposal_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    entry = _find_qc_command(report, "suggest-fix")
    payload = entry.get("payload") if isinstance(entry, dict) else None
    proposals = payload.get("proposals") if isinstance(payload, dict) else None
    if not isinstance(proposals, list):
        return []
    return [item for item in proposals if isinstance(item, dict)]


def parse_server_presets(constants_path: Path = MOBILE_CONSTANTS_PATH) -> tuple[list[ServerPreset], str]:
    text = constants_path.read_text(encoding="utf-8")
    presets = [
        ServerPreset(key=match[0], label=match[1], url=match[2])
        for match in re.findall(
            r'\{\s*key:\s*"([^"]+)",\s*label:\s*"([^"]+)",[^}]*url:\s*"([^"]+)"\s*\}',
            text,
        )
    ]
    primary_match = re.search(r'PRIMARY_SERVER_KEY\s*=\s*"([^"]+)"', text)
    primary_key = primary_match.group(1) if primary_match else (presets[0].key if presets else "serverW")
    if not presets:
        presets = [
            ServerPreset(key="serverW", label="서버W", url="https://api4.govpress.cloud"),
            ServerPreset(key="serverH", label="서버H", url="https://api.govpress.cloud"),
            ServerPreset(key="serverV", label="서버V", url="https://api2.govpress.cloud"),
        ]
    return presets, primary_key


def _fetch_health(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    endpoint = url.rstrip("/") + "/health"
    try:
        with urlopen(endpoint, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {"ok": 200 <= response.status < 300, "status": response.status, "endpoint": endpoint, "body": body[:200]}
    except URLError as exc:
        return {"ok": False, "status": None, "endpoint": endpoint, "error": str(exc.reason)}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "status": None, "endpoint": endpoint, "error": str(exc)}


def build_server_status(*, dashboard_path: str = DEFAULT_DASHBOARD_PATH) -> dict[str, Any]:
    presets, primary_key = parse_server_presets()
    statuses = []
    for preset in presets:
        health = _fetch_health(preset.url)
        statuses.append(
            {
                "key": preset.key,
                "label": preset.label,
                "url": preset.url,
                "dashboard_url": preset.url.rstrip("/") + dashboard_path,
                **health,
            }
        )
    primary = next((item for item in statuses if item["key"] == primary_key), statuses[0])
    healthy_urls = [item["url"] for item in statuses if item["ok"]]
    fallback_candidates = [item["url"] for item in statuses if item["url"] != primary["url"] and item["ok"]]
    return {
        "primary_key": primary_key,
        "primary_url": primary["url"],
        "primary_healthy": primary["ok"],
        "fallback_candidates": fallback_candidates,
        "status": statuses,
        "mismatch": (not primary["ok"] and bool(fallback_candidates)),
        "recommended_url": primary["url"] if primary["ok"] else (fallback_candidates[0] if fallback_candidates else None),
        "healthy_urls": healthy_urls,
    }


def _shorten(value: Any, *, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def qc_status(export_root: Path, requested_date: str, *, dashboard_url: str | None = None) -> dict[str, Any]:
    report_path = resolve_report_path(export_root, requested_date)
    report = load_issue_report(report_path)
    payload = build_dashboard_payload(export_root)
    latest = payload.get("latest", {}) if isinstance(payload.get("latest"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return {
        "command": "qc-status",
        "date": report.get("date"),
        "report_path": str(report_path),
        "summary": summary,
        "top_defects": payload.get("top_defects", []),
        "top_samples": payload.get("top_samples", []),
        "latest_review_required": latest.get("review_required", []),
        "latest_regression_failures": latest.get("regression_failures", []),
        "dashboard_url": dashboard_url,
    }


def qc_failures(export_root: Path, requested_date: str) -> dict[str, Any]:
    report_path = resolve_report_path(export_root, requested_date)
    report = load_issue_report(report_path)
    triage_entries = [item for item in _triage_entries(report) if item.get("review_required") is True]
    regression_failures = [item for item in _regression_entries(report) if item.get("passed") is False]
    proposals = _proposal_entries(report)
    return {
        "command": "qc-failures",
        "date": report.get("date"),
        "report_path": str(report_path),
        "review_required": triage_entries,
        "regression_failures": regression_failures,
        "proposals": proposals,
    }


def qc_issue(export_root: Path, requested_date: str) -> dict[str, Any]:
    report_path = resolve_report_path(export_root, requested_date)
    report = load_issue_report(report_path)
    summary_path = report_path.with_name("qc_summary.md")
    summary_markdown = summary_path.read_text(encoding="utf-8") if summary_path.exists() else build_markdown_summary(report)
    payload = build_issue_payload(report, summary_markdown=summary_markdown)
    issue_path = report_path.with_name("issue_payload.json")
    return {
        "command": "qc-issue",
        "date": report.get("date"),
        "report_path": str(report_path),
        "issue_path": str(issue_path),
        "title": payload["title"],
        "body_preview": _shorten(payload["body"], limit=700),
    }


def _run_subprocess(command: list[str], *, cwd: Path) -> dict[str, Any]:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "command": command,
    }


def qc_rerun(target_date: str, *, output_root: Path, gov_md_root: Path, qc_root: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_policy_briefing_qc_pipeline.py"),
        "--date",
        target_date,
        "--output-root",
        str(output_root),
        "--gov-md-converter-root",
        str(gov_md_root),
        "--qc-root",
        str(qc_root),
        "--json",
    ]
    result = _run_subprocess(command, cwd=PROJECT_ROOT)
    payload = json.loads(result["stdout"]) if result["stdout"] else {}
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    return {
        "command": "qc-rerun",
        "date": target_date,
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "summary": summary,
        "report_path": str(output_root / target_date / "pipeline_report.json"),
    }


def qc_promote(sample_id: str, *, qc_root: Path, gov_md_root: Path) -> dict[str, Any]:
    sample_dir = qc_root / sample_id
    if not sample_dir.exists():
        raise FileNotFoundError(f"QC sample directory not found: {sample_dir}")
    command = [
        sys.executable,
        str(gov_md_root / "scripts" / "run_hwpx_qc.py"),
        "promote-sample",
        str(sample_dir),
        "--sample-status",
        "curated",
    ]
    result = _run_subprocess(command, cwd=gov_md_root)
    return {
        "command": "qc-promote",
        "sample_id": sample_id,
        "sample_dir": str(sample_dir),
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


def server_failover_check() -> dict[str, Any]:
    status = build_server_status()
    if status["primary_healthy"]:
        message = f"Primary server {status['primary_key']} is healthy"
    elif status["recommended_url"]:
        message = f"Primary server {status['primary_key']} is unhealthy; recommend {status['recommended_url']}"
    else:
        message = f"Primary server {status['primary_key']} is unhealthy and no healthy fallback is available"
    return {
        "command": "server-failover-check",
        **status,
        "action_required": bool(status["mismatch"]),
        "message": message,
    }


def parse_telegram_command(message: str) -> tuple[str, list[str]]:
    tokens = message.strip().split()
    if not tokens:
        raise ValueError("Empty message")
    if tokens[:2] == ["/qc", "today"]:
        return "qc-status", ["latest"]
    if tokens[:2] == ["/qc", "failures"]:
        return "qc-failures", ["latest"]
    if tokens[:2] == ["/qc", "issue"]:
        return "qc-issue", ["latest"]
    if len(tokens) == 3 and tokens[:2] == ["/qc", "rerun"]:
        _valid_date(tokens[2])
        return "qc-rerun", [tokens[2]]
    if len(tokens) == 4 and tokens[:2] == ["/qc", "promote"]:
        _valid_date(tokens[2])
        _valid_sample_id(tokens[3])
        return "qc-promote", [tokens[2], tokens[3]]
    if tokens[:2] == ["/server", "status"]:
        return "server-status", []
    if tokens[:2] == ["/server", "failover-check"]:
        return "server-failover-check", []
    raise ValueError("Unsupported command. Use /qc today|rerun|failures|issue|promote or /server status|failover-check")


def dispatch_telegram_message(message: str, *, chat_scope: str, export_root: Path, gov_md_root: Path, qc_root: Path) -> dict[str, Any]:
    if chat_scope != "dm":
        return {
            "command": "telegram-dispatch",
            "ok": False,
            "message": "GovPress QC commands are allowed only in direct Telegram DMs.",
        }
    command, args = parse_telegram_command(message)
    if command == "qc-status":
        server_status = build_server_status()
        dashboard_url = next(
            (item["dashboard_url"] for item in server_status["status"] if item["key"] == server_status["primary_key"]),
            None,
        )
        payload = qc_status(export_root, args[0], dashboard_url=dashboard_url)
    elif command == "qc-failures":
        payload = qc_failures(export_root, args[0])
    elif command == "qc-issue":
        payload = qc_issue(export_root, args[0])
    elif command == "qc-rerun":
        payload = qc_rerun(args[0], output_root=export_root, gov_md_root=gov_md_root, qc_root=qc_root)
    elif command == "qc-promote":
        payload = qc_promote(args[1], qc_root=qc_root, gov_md_root=gov_md_root)
    elif command == "server-status":
        payload = {"command": "server-status", **build_server_status()}
    elif command == "server-failover-check":
        payload = server_failover_check()
    else:  # pragma: no cover
        raise ValueError(f"Unsupported command: {command}")
    payload["ok"] = True
    return payload


def format_human(payload: dict[str, Any]) -> str:
    command = payload.get("command")
    if command == "qc-status":
        summary = payload.get("summary", {})
        top_defects = payload.get("top_defects", [])
        top_samples = payload.get("top_samples", [])
        regression_failures = payload.get("latest_regression_failures", [])
        lines = [
            f"[QC] {payload.get('date')}",
            f"exported={summary.get('exported_count', 0)} review_required={summary.get('review_required_count', 0)} regression_failures={len(regression_failures)} proposals={summary.get('proposal_count', 0)} drafts={summary.get('draft_count', 0)}",
            f"report={payload.get('report_path')}",
        ]
        if payload.get("dashboard_url"):
            lines.append(f"dashboard={payload['dashboard_url']}")
        if not regression_failures and summary.get("review_required_count", 0):
            lines.append("note=review_required counts scratch samples pending human review, not current conversion failures")
        if top_defects:
            defect = top_defects[0]
            lines.append(f"top_defect={defect.get('defect_class')} ({defect.get('count')})")
        if top_samples:
            sample = top_samples[0]
            lines.append(f"top_sample={sample.get('sample_id')} ({sample.get('count')})")
        return "\n".join(lines)
    if command == "qc-failures":
        review_required = payload.get("review_required", [])
        regression_failures = payload.get("regression_failures", [])
        proposals = payload.get("proposals", [])
        lines = [
            f"[QC Failures] {payload.get('date')}",
            f"review_required={len(review_required)} regression_failures={len(regression_failures)} proposals={len(proposals)}",
            f"report={payload.get('report_path')}",
        ]
        if not regression_failures:
            lines.append("note=no current regression failures; remaining review queue is scratch-sample review")
        if review_required:
            sample = review_required[0]
            lines.append(f"first_review_sample={sample.get('sample_id')} risk={sample.get('risk_score')}")
        if proposals:
            proposal = proposals[0]
            first_file = (proposal.get("suggested_files") or ["-"])[0]
            lines.append(f"first_fix_target={proposal.get('defect_class')} file={first_file}")
        return "\n".join(lines)
    if command == "qc-issue":
        return "\n".join(
            [
                f"[QC Issue] {payload.get('date')}",
                f"title={payload.get('title')}",
                f"issue_payload={payload.get('issue_path')}",
                payload.get("body_preview", ""),
            ]
        ).strip()
    if command == "qc-rerun":
        summary = payload.get("summary", {})
        status = "ok" if payload.get("returncode") == 0 else "failed"
        return "\n".join(
            [
                f"[QC Rerun] {payload.get('date')} status={status}",
                f"exported={summary.get('exported_count', 0)} review_required={summary.get('review_required_count', 0)} proposals={summary.get('proposal_count', 0)} drafts={summary.get('draft_count', 0)}",
                f"report={payload.get('report_path')}",
                _shorten(payload.get("stderr") or payload.get("stdout"), limit=500),
            ]
        ).strip()
    if command == "qc-promote":
        status = "ok" if payload.get("returncode") == 0 else "failed"
        return "\n".join(
            [
                f"[QC Promote] sample={payload.get('sample_id')} status={status}",
                f"sample_dir={payload.get('sample_dir')}",
                _shorten(payload.get("stderr") or payload.get("stdout"), limit=500),
            ]
        ).strip()
    if command in {"server-status", "server-failover-check"}:
        lines = [
            f"[Server Status] primary={payload.get('primary_key')} healthy={payload.get('primary_healthy')}",
            f"recommended={payload.get('recommended_url')}",
        ]
        for item in payload.get("status", [])[:3]:
            lines.append(f"{item.get('key')} status={item.get('status')} ok={item.get('ok')} url={item.get('url')}")
        if payload.get("message"):
            lines.append(payload["message"])
        return "\n".join(lines)
    if command == "telegram-dispatch" and payload.get("ok") is False:
        return str(payload.get("message"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw wrapper for GovPress QC and server health operations")
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT))
    parser.add_argument("--gov-md-root", default=str(DEFAULT_GOV_MD_ROOT))
    parser.add_argument("--qc-root", default=str(DEFAULT_QC_ROOT))
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    status_parser = subparsers.add_parser("qc-status")
    status_parser.add_argument("--date", default="latest", type=_valid_date)
    status_parser.add_argument("--dashboard-url")

    failures_parser = subparsers.add_parser("qc-failures")
    failures_parser.add_argument("--date", default="latest", type=_valid_date)

    issue_parser = subparsers.add_parser("qc-issue")
    issue_parser.add_argument("--date", default="latest", type=_valid_date)

    rerun_parser = subparsers.add_parser("qc-rerun")
    rerun_parser.add_argument("--date", required=True, type=_valid_date)

    promote_parser = subparsers.add_parser("qc-promote")
    promote_parser.add_argument("--date", required=True, type=_valid_date)
    promote_parser.add_argument("--sample-id", required=True, type=_valid_sample_id)

    subparsers.add_parser("server-status")
    subparsers.add_parser("server-failover-check")

    dispatch_parser = subparsers.add_parser("telegram-dispatch")
    dispatch_parser.add_argument("--message", required=True)
    dispatch_parser.add_argument("--chat-scope", default="dm", choices=["dm", "group"])

    return parser


def main() -> int:
    args = build_parser().parse_args()
    export_root = Path(args.export_root).resolve()
    gov_md_root = Path(args.gov_md_root).resolve()
    qc_root = Path(args.qc_root).resolve()
    try:
        if args.subcommand == "qc-status":
            payload = qc_status(export_root, args.date, dashboard_url=args.dashboard_url)
        elif args.subcommand == "qc-failures":
            payload = qc_failures(export_root, args.date)
        elif args.subcommand == "qc-issue":
            payload = qc_issue(export_root, args.date)
        elif args.subcommand == "qc-rerun":
            payload = qc_rerun(args.date, output_root=export_root, gov_md_root=gov_md_root, qc_root=qc_root)
        elif args.subcommand == "qc-promote":
            payload = qc_promote(args.sample_id, qc_root=qc_root, gov_md_root=gov_md_root)
            payload["date"] = args.date
        elif args.subcommand == "server-status":
            payload = {"command": "server-status", **build_server_status()}
        elif args.subcommand == "server-failover-check":
            payload = server_failover_check()
        elif args.subcommand == "telegram-dispatch":
            payload = dispatch_telegram_message(
                args.message,
                chat_scope=args.chat_scope,
                export_root=export_root,
                gov_md_root=gov_md_root,
                qc_root=qc_root,
            )
        else:  # pragma: no cover
            raise AssertionError(f"Unhandled subcommand {args.subcommand}")
    except Exception as exc:
        payload = {"command": args.subcommand, "ok": False, "message": str(exc)}
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["message"])
        return 1

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(format_human(payload))
    if payload.get("returncode") not in (None, 0):
        return int(payload["returncode"])
    if payload.get("ok") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
