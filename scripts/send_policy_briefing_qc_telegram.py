from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request


def load_json(path: str | Path) -> dict[str, object]:
    payload = json.loads(Path(path).resolve().read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object")
    return payload


def _collect_triage_entries(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if isinstance(entry, dict) and entry.get("command") == "triage":
            payload = entry.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("entries"), list):
                return [item for item in payload["entries"] if isinstance(item, dict)]
    return []


def _collect_suggest_fix_proposals(report: dict[str, object]) -> list[dict[str, object]]:
    for entry in report.get("qc_commands", []):
        if isinstance(entry, dict) and entry.get("command") == "suggest-fix":
            payload = entry.get("payload")
            if isinstance(payload, dict) and isinstance(payload.get("proposals"), list):
                return [item for item in payload["proposals"] if isinstance(item, dict)]
    return []


def build_telegram_message(
    report: dict[str, object],
    *,
    dashboard_url: str | None = None,
    issue_url: str | None = None,
) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    triage_entries = [item for item in _collect_triage_entries(report) if item.get("review_required")][:3]
    proposals = _collect_suggest_fix_proposals(report)[:3]
    lines = [
        f"[Policy Briefing QC] {report.get('date')}",
        f"- exported: {summary.get('exported_count', 0)}",
        f"- review_required: {summary.get('review_required_count', 0)}",
        f"- proposals: {summary.get('proposal_count', 0)}",
        f"- drafts: {summary.get('draft_count', 0)}",
    ]
    if triage_entries:
        lines.append("- top samples:")
        for entry in triage_entries:
            lines.append(
                f"  • {entry.get('sample_id')} (risk={entry.get('risk_score', '-')}, status={entry.get('sample_status', '-')})"
            )
    if proposals:
        lines.append("- top fix targets:")
        for entry in proposals:
            files = ", ".join(str(path) for path in entry.get("suggested_files", [])[:2]) or "-"
            lines.append(f"  • {entry.get('defect_class')}: {files}")
    if dashboard_url:
        lines.append(f"- dashboard: {dashboard_url}")
    if issue_url:
        lines.append(f"- issue: {issue_url}")
    return "\n".join(lines)


def send_telegram_message(
    *,
    bot_token: str,
    chat_id: str,
    text: str,
) -> dict[str, object]:
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read().decode("utf-8")
    parsed = json.loads(data)
    if not isinstance(parsed, dict):
        raise ValueError("Unexpected Telegram response")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send a policy briefing QC summary to Telegram")
    parser.add_argument("report", help="Path to pipeline_report.json")
    parser.add_argument("--dashboard-url", help="Optional dashboard URL to include")
    parser.add_argument("--issue-url", help="Optional issue URL to include")
    parser.add_argument("--bot-token", help="Telegram bot token. Defaults to TELEGRAM_BOT_TOKEN")
    parser.add_argument("--chat-id", help="Telegram chat id. Defaults to TELEGRAM_CHAT_ID")
    parser.add_argument("--print-only", action="store_true", help="Print the message instead of sending it")
    parser.add_argument("--json", action="store_true", help="Print the send result as JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = load_json(args.report)
    text = build_telegram_message(report, dashboard_url=args.dashboard_url, issue_url=args.issue_url)
    if args.print_only:
        print(text)
        return 0

    bot_token = args.bot_token or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = args.chat_id or os.environ.get("TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        raise SystemExit("Telegram bot token/chat id is not configured")
    payload = send_telegram_message(bot_token=bot_token, chat_id=chat_id, text=text)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("Telegram notification sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
