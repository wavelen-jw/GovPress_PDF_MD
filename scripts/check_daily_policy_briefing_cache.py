"""Refresh today's service catalog and alert if the daily refresh fails."""
from __future__ import annotations

from datetime import datetime
from html import escape
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

API_BASE_URL = "https://api4.govpress.cloud"


def send_telegram(message: str) -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Telegram bot token or chat ID is not configured")
    payload = json.dumps({"chat_id": chat_id, "text": message, "parse_mode": "HTML"}).encode()
    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        result = json.load(response)
    if result.get("ok") is not True:
        raise RuntimeError("Telegram API did not confirm delivery")


def check_daily_catalog(target_date: str, *, base_url: str = API_BASE_URL) -> int:
    api_key = os.environ.get("GOVPRESS_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GOVPRESS_API_KEY is not configured")
    parsed_url = urlsplit(base_url)
    if parsed_url.scheme != "https" and not (
        parsed_url.scheme == "http" and parsed_url.hostname in ("127.0.0.1", "localhost")
    ):
        raise ValueError("The policy briefing API URL must use HTTPS or a local SSH tunnel")
    url = f"{base_url.rstrip('/')}/v1/policy-briefings/today?{urlencode({'date': target_date})}"
    request = Request(url, headers={"X-API-Key": api_key, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=35) as response:
            payload = json.load(response)
    except HTTPError as exc:
        try:
            detail = json.load(exc).get("detail", "")
        except (ValueError, AttributeError):
            detail = ""
        raise RuntimeError(f"HTTP {exc.code}: {str(detail)[:160]}") from exc
    except URLError as exc:
        raise RuntimeError(f"API connection failed: {type(exc.reason).__name__}") from exc
    if not isinstance(payload, dict) or payload.get("date") != target_date:
        raise RuntimeError("API returned a different date or invalid catalog")
    if not isinstance(payload.get("items"), list) or not payload.get("last_refreshed_at"):
        raise RuntimeError("API returned an incomplete catalog")
    if payload.get("served_stale"):
        raise RuntimeError("API served stale catalog after upstream refresh failed")
    return len(payload["items"])


def main() -> int:
    target_date = datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    try:
        item_count = check_daily_catalog(
            target_date,
            base_url=os.environ.get("GOVPRESS_POLICY_BRIEFING_CHECK_URL", API_BASE_URL),
        )
    except Exception as exc:
        reason = f"{type(exc).__name__}: {exc}"
        run_url = ""
        if all(os.environ.get(key) for key in ("GITHUB_SERVER_URL", "GITHUB_REPOSITORY", "GITHUB_RUN_ID")):
            run_url = (f"\n실행: {os.environ['GITHUB_SERVER_URL']}/"
                       f"{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}")
        message = (f"<b>정책브리핑 일일 캐시 실패</b>\n"
                   f"날짜: {target_date}\n서버: api4.govpress.cloud\n"
                   f"원인: {escape(reason[:300])}{escape(run_url)}")
        try:
            send_telegram(message)
        except Exception as alert_exc:
            print(f"cache_check_failed; telegram_delivery_failed: {type(alert_exc).__name__}", file=sys.stderr)
            return 2
        print(f"cache_check_failed; telegram_sent; reason={reason}", file=sys.stderr)
        return 1
    print(f"date={target_date} cached_items={item_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
