from io import BytesIO
import json
from urllib.error import HTTPError

import pytest

from scripts import check_daily_policy_briefing_cache as monitor


def test_daily_check_accepts_fresh_catalog_and_sends_api_key_only_in_header(monkeypatch):
    monkeypatch.setenv("GOVPRESS_API_KEY", "test-key")

    def response(request, timeout):
        assert request.get_header("X-api-key") == "test-key"
        assert "test-key" not in request.full_url
        assert timeout == 35
        return BytesIO(json.dumps({
            "date": "2026-09-24", "items": [{"news_item_id": "1"}],
            "last_refreshed_at": "2026-09-24T13:00:00+00:00", "served_stale": False,
        }).encode())

    monkeypatch.setattr(monitor, "urlopen", response)
    assert monitor.check_daily_catalog("2026-09-24") == 1


@pytest.mark.parametrize("payload", [
    {"date": "2026-09-24", "items": [], "last_refreshed_at": "x", "served_stale": True},
    {"date": "2026-09-23", "items": [], "last_refreshed_at": "x", "served_stale": False},
    {"date": "2026-09-24", "items": [], "last_refreshed_at": None, "served_stale": False},
])
def test_daily_check_rejects_stale_or_incomplete_catalog(monkeypatch, payload):
    monkeypatch.setenv("GOVPRESS_API_KEY", "test-key")
    monkeypatch.setattr(monitor, "urlopen", lambda *args, **kwargs: BytesIO(json.dumps(payload).encode()))
    with pytest.raises(RuntimeError):
        monitor.check_daily_catalog("2026-09-24")


def test_failed_refresh_sends_telegram_and_exits_nonzero(monkeypatch):
    monkeypatch.setattr(monitor, "check_daily_catalog", lambda date: (_ for _ in ()).throw(RuntimeError("HTTP 502")))
    sent = []
    monkeypatch.setattr(monitor, "send_telegram", lambda message: sent.append(message))
    assert monitor.main() == 1
    assert len(sent) == 1
    assert "HTTP 502" in sent[0]


def test_failed_refresh_reports_telegram_delivery_failure(monkeypatch):
    monkeypatch.setattr(monitor, "check_daily_catalog", lambda date: (_ for _ in ()).throw(RuntimeError("HTTP 502")))
    monkeypatch.setattr(monitor, "send_telegram", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("bot unavailable")))
    assert monitor.main() == 2


def test_upstream_http_error_keeps_status_without_exposing_key(monkeypatch):
    monkeypatch.setenv("GOVPRESS_API_KEY", "test-key")

    def failed(request, timeout):
        raise HTTPError(request.full_url, 502, "Bad Gateway", {}, BytesIO(b'{"detail":"upstream unavailable"}'))

    monkeypatch.setattr(monitor, "urlopen", failed)
    with pytest.raises(RuntimeError, match="HTTP 502: upstream unavailable") as result:
        monitor.check_daily_catalog("2026-09-24")
    assert "test-key" not in str(result.value)


def test_telegram_requires_confirmed_delivery(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat")
    monkeypatch.setattr(monitor, "urlopen", lambda *args, **kwargs: BytesIO(b'{"ok":true}'))
    monitor.send_telegram("test")
    monkeypatch.setattr(monitor, "urlopen", lambda *args, **kwargs: BytesIO(b'{"ok":false}'))
    with pytest.raises(RuntimeError, match="Telegram API did not confirm delivery"):
        monitor.send_telegram("test")
