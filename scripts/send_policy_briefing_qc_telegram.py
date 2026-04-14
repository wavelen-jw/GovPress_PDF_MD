from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GOV_MD_ROOT = (PROJECT_ROOT / ".." / "gov-md-converter").resolve()
if str(GOV_MD_ROOT) not in sys.path:
    sys.path.insert(0, str(GOV_MD_ROOT))

from src.qc_telegram import build_telegram_message, load_json, send_telegram_message


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
