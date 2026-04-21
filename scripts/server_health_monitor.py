from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.core.notify import send_telegram


STATE_VERSION = 1
MOBILE_CONSTANTS_PATH = PROJECT_ROOT / "mobile" / "src" / "constants.ts"
SEOUL_UTC_OFFSET = timedelta(hours=9)
QUIET_HOUR_START = 2
QUIET_HOUR_END = 8
DOWN_REMINDER_INTERVAL = timedelta(hours=1)


def utcnow_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_quiet_hours_seoul(checked_at: str) -> bool:
    checked = parse_iso_datetime(checked_at)
    if checked is None:
        return False
    seoul = checked.astimezone(UTC) + SEOUL_UTC_OFFSET
    return QUIET_HOUR_START <= seoul.hour < QUIET_HOUR_END


def should_repeat_down_alert(previous: dict[str, Any], *, checked_at: str) -> bool:
    if is_quiet_hours_seoul(checked_at):
        return False
    last_alert_at = parse_iso_datetime(str(previous.get("last_alert_at") or ""))
    checked = parse_iso_datetime(checked_at)
    if checked is None:
        return False
    if last_alert_at is None:
        return True
    return checked - last_alert_at >= DOWN_REMINDER_INTERVAL


def load_monitor_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": STATE_VERSION, "servers": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": STATE_VERSION, "servers": {}}
    if not isinstance(payload, dict):
        return {"version": STATE_VERSION, "servers": {}}
    servers = payload.get("servers")
    if not isinstance(servers, dict):
        servers = {}
    return {"version": STATE_VERSION, "servers": servers}


def save_monitor_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def seoul_today_iso() -> str:
    return (datetime.now(UTC) + SEOUL_UTC_OFFSET).date().isoformat()


def build_probe_request(url: str, *, api_key: str | None = None) -> tuple[str, Request]:
    if api_key:
        endpoint = (
            url.rstrip("/")
            + f"/v1/policy-briefings/today?date={seoul_today_iso()}"
        )
        request = Request(
            endpoint,
            headers={
                "User-Agent": "govpress-server-monitor/1.0",
                "Accept": "application/json",
                "X-API-Key": api_key,
            },
        )
        return endpoint, request

    endpoint = url.rstrip("/") + "/health"
    request = Request(endpoint, headers={"User-Agent": "govpress-server-monitor/1.0", "Accept": "application/json"})
    return endpoint, request


def fetch_health(url: str, *, timeout: float = 5.0, api_key: str | None = None) -> dict[str, Any]:
    endpoint, request = build_probe_request(url, api_key=api_key)
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "error": "",
                "endpoint": endpoint,
                "detail": f"HTTP {response.status}",
                "body": body[:200],
            }
    except HTTPError as exc:
        return {
            "ok": False,
            "status": exc.code,
            "error": f"HTTP {exc.code}",
            "endpoint": endpoint,
            "detail": f"HTTP {exc.code}",
            "body": "",
        }
    except URLError as exc:
        detail = str(exc.reason)
        return {
            "ok": False,
            "status": None,
            "error": detail,
            "endpoint": endpoint,
            "detail": detail,
            "body": "",
        }
    except Exception as exc:  # pragma: no cover
        detail = str(exc)
        return {
            "ok": False,
            "status": None,
            "error": detail,
            "endpoint": endpoint,
            "detail": detail,
            "body": "",
        }


def resolve_servers() -> list[dict[str, str]]:
    text = MOBILE_CONSTANTS_PATH.read_text(encoding="utf-8")
    presets = [
        {"key": match[0], "label": match[1], "url": match[2]}
        for match in re.findall(
            r'\{\s*key:\s*"([^"]+)",\s*label:\s*"([^"]+)",[^}]*url:\s*"([^"]+)"\s*\}',
            text,
        )
    ]
    if presets:
        return presets
    return [
        {"key": "serverH", "label": "서버H", "url": "https://api.govpress.cloud"},
        {"key": "serverW", "label": "서버W", "url": "https://api4.govpress.cloud"},
        {"key": "serverV", "label": "서버V", "url": "https://api2.govpress.cloud"},
    ]


def check_servers(*, timeout: float = 5.0, api_key: str | None = None) -> list[dict[str, Any]]:
    statuses = []
    for server in resolve_servers():
        statuses.append({**server, **fetch_health(server["url"], timeout=timeout, api_key=api_key)})
    return statuses


def evaluate_monitor(
    previous_state: dict[str, Any],
    statuses: list[dict[str, Any]],
    *,
    failure_threshold: int,
    checked_at: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    previous_servers = previous_state.get("servers", {})
    next_servers: dict[str, Any] = {}
    transitions: list[dict[str, Any]] = []

    for status in statuses:
        key = str(status["key"])
        previous = previous_servers.get(key, {})
        if not isinstance(previous, dict):
            previous = {}
        previous_status = str(previous.get("status") or "unknown")
        previous_failures = int(previous.get("consecutive_failures") or 0)

        if status["ok"]:
            current_status = "up"
            consecutive_failures = 0
            if previous_status in {"degraded", "down"}:
                transitions.append(
                    {
                        "server": key,
                        "label": status["label"],
                        "url": status["url"],
                        "type": "recovered",
                        "checked_at": checked_at,
                        "detail": f"HTTP {status['status']}",
                    }
                )
        else:
            consecutive_failures = previous_failures + 1
            if previous_status == "down":
                current_status = "down"
                if should_repeat_down_alert(previous, checked_at=checked_at):
                    transitions.append(
                        {
                            "server": key,
                            "label": status["label"],
                            "url": status["url"],
                            "type": "down_reminder",
                            "checked_at": checked_at,
                            "detail": status["detail"],
                            "status": status.get("status"),
                            "consecutive_failures": consecutive_failures,
                        }
                    )
            elif consecutive_failures >= failure_threshold:
                current_status = "down"
                transitions.append(
                    {
                        "server": key,
                        "label": status["label"],
                        "url": status["url"],
                        "type": "down",
                        "checked_at": checked_at,
                        "detail": status["detail"],
                        "status": status.get("status"),
                        "consecutive_failures": consecutive_failures,
                    }
                )
            else:
                current_status = "degraded"
                if previous_status != "degraded":
                    transitions.append(
                        {
                            "server": key,
                            "label": status["label"],
                            "url": status["url"],
                            "type": "degraded",
                            "checked_at": checked_at,
                            "detail": status["detail"],
                            "status": status.get("status"),
                            "consecutive_failures": consecutive_failures,
                        }
                    )

        transition_for_server = next((item for item in reversed(transitions) if item["server"] == key), None)
        next_servers[key] = {
            "status": current_status,
            "consecutive_failures": consecutive_failures,
            "last_status_code": status.get("status"),
            "last_error": "" if status["ok"] else status.get("detail", ""),
            "last_checked_at": checked_at,
            "last_transition_at": checked_at
            if current_status != previous_status
            else previous.get("last_transition_at"),
            "last_alert_at": checked_at
            if transition_for_server is not None
            else previous.get("last_alert_at"),
            "label": status["label"],
            "url": status["url"],
        }

    return {"version": STATE_VERSION, "updated_at": checked_at, "servers": next_servers}, transitions


def format_transition_message(transitions: list[dict[str, Any]]) -> str:
    lines = ["[Server Alert]"]
    for item in transitions:
        if item["type"] == "degraded":
            lines.append(
                f"DEGRADED {item['label']} ({item['server']})"
                f" - {item['detail']} - failures={item['consecutive_failures']}"
            )
        elif item["type"] == "down":
            lines.append(
                f"DOWN {item['label']} ({item['server']})"
                f" - {item['detail']} - failures={item['consecutive_failures']}"
            )
        elif item["type"] == "down_reminder":
            lines.append(
                f"DOWN {item['label']} ({item['server']})"
                f" - {item['detail']} - failures={item['consecutive_failures']} - reminder"
            )
        else:
            lines.append(f"RECOVERED {item['label']} ({item['server']}) - {item['detail']}")
        lines.append(f"url: {item['url']}")
        lines.append(f"time: {item['checked_at']}")
    return "\n".join(lines)


def summarise_statuses(statuses: list[dict[str, Any]], state: dict[str, Any]) -> list[str]:
    server_state = state.get("servers", {})
    lines = []
    for item in statuses:
        entry = server_state.get(item["key"], {})
        lines.append(
            f"- {item['label']} ({item['key']}): state={entry.get('status')} "
            f"http={item.get('status')} detail={item.get('detail')}"
        )
    return lines


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Monitor GovPress public server health and emit Telegram alerts")
    parser.add_argument("--state-path", required=True, help="Path to monitor state JSON")
    parser.add_argument("--failure-threshold", type=int, default=2, help="Consecutive failures required for a down alert")
    parser.add_argument("--timeout", type=float, default=5.0, help="Per-server health request timeout in seconds")
    parser.add_argument("--api-key", default="", help="Optional API key for authenticated policy probe")
    parser.add_argument("--send-telegram", action="store_true", help="Send Telegram when state transitions exist")
    parser.add_argument("--json", action="store_true", help="Print result JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    checked_at = utcnow_iso()
    state_path = Path(args.state_path)
    previous_state = load_monitor_state(state_path)
    statuses = check_servers(timeout=args.timeout, api_key=(args.api_key or "").strip() or None)
    next_state, transitions = evaluate_monitor(
        previous_state,
        statuses,
        failure_threshold=max(args.failure_threshold, 1),
        checked_at=checked_at,
    )
    save_monitor_state(state_path, next_state)

    message = format_transition_message(transitions) if transitions else ""
    if args.send_telegram and transitions:
        send_telegram(message)

    payload = {
        "checked_at": checked_at,
        "failure_threshold": max(args.failure_threshold, 1),
        "transitions": transitions,
        "transition_count": len(transitions),
        "message": message,
        "statuses": statuses,
        "state": next_state,
        "summary_lines": summarise_statuses(statuses, next_state),
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("\n".join(payload["summary_lines"]))
        if message:
            print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
