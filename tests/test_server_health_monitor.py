from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.server_health_monitor import (
    evaluate_monitor,
    format_transition_message,
    load_monitor_state,
    save_monitor_state,
)


class ServerHealthMonitorTests(unittest.TestCase):
    def _status(
        self,
        key: str,
        *,
        ok: bool,
        status: int | None,
        detail: str,
        label: str | None = None,
        url: str | None = None,
    ) -> dict[str, object]:
        return {
            "key": key,
            "label": label or key,
            "url": url or f"https://{key}.example.test",
            "ok": ok,
            "status": status,
            "detail": detail,
            "error": "" if ok else detail,
            "endpoint": f"https://{key}.example.test/health",
            "body": "",
        }

    def test_all_servers_healthy_from_clean_state_updates_without_alert(self) -> None:
        statuses = [
            self._status("serverH", ok=True, status=200, detail="HTTP 200"),
            self._status("serverW", ok=True, status=200, detail="HTTP 200"),
        ]
        state, transitions = evaluate_monitor({}, statuses, failure_threshold=2, checked_at="2026-04-14T00:00:00Z")
        self.assertEqual(transitions, [])
        self.assertEqual(state["servers"]["serverH"]["status"], "up")
        self.assertEqual(state["servers"]["serverW"]["consecutive_failures"], 0)

    def test_first_failure_emits_degraded_alert_before_threshold(self) -> None:
        previous_state = {
            "servers": {
                "serverH": {
                    "status": "up",
                    "consecutive_failures": 0,
                    "last_transition_at": "2026-04-14T00:00:00Z",
                }
            }
        }
        state, transitions = evaluate_monitor(
            previous_state,
            [self._status("serverH", ok=False, status=502, detail="HTTP 502")],
            failure_threshold=2,
            checked_at="2026-04-14T00:05:00Z",
        )
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["type"], "degraded")
        self.assertEqual(state["servers"]["serverH"]["status"], "degraded")
        self.assertEqual(state["servers"]["serverH"]["consecutive_failures"], 1)

    def test_second_consecutive_failure_emits_single_down_alert(self) -> None:
        previous_state = {
            "servers": {
                "serverH": {
                    "status": "degraded",
                    "consecutive_failures": 1,
                    "last_transition_at": "2026-04-14T00:00:00Z",
                }
            }
        }
        state, transitions = evaluate_monitor(
            previous_state,
            [self._status("serverH", ok=False, status=502, detail="HTTP 502", label="서버H")],
            failure_threshold=2,
            checked_at="2026-04-14T00:10:00Z",
        )
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["type"], "down")
        self.assertEqual(state["servers"]["serverH"]["status"], "down")
        self.assertEqual(state["servers"]["serverH"]["consecutive_failures"], 2)

    def test_down_server_does_not_repeat_alert_until_recovery(self) -> None:
        previous_state = {
            "servers": {
                "serverH": {
                    "status": "down",
                    "consecutive_failures": 2,
                    "last_transition_at": "2026-04-14T00:10:00Z",
                }
            }
        }
        state, transitions = evaluate_monitor(
            previous_state,
            [self._status("serverH", ok=False, status=None, detail="timed out")],
            failure_threshold=2,
            checked_at="2026-04-14T00:15:00Z",
        )
        self.assertEqual(transitions, [])
        self.assertEqual(state["servers"]["serverH"]["status"], "down")
        self.assertEqual(state["servers"]["serverH"]["consecutive_failures"], 3)

    def test_recovery_emits_single_recovered_alert(self) -> None:
        previous_state = {
            "servers": {
                "serverH": {
                    "status": "down",
                    "consecutive_failures": 4,
                    "last_transition_at": "2026-04-14T00:10:00Z",
                }
            }
        }
        state, transitions = evaluate_monitor(
            previous_state,
            [self._status("serverH", ok=True, status=200, detail="HTTP 200", label="서버H")],
            failure_threshold=2,
            checked_at="2026-04-14T00:20:00Z",
        )
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["type"], "recovered")
        self.assertEqual(state["servers"]["serverH"]["status"], "up")
        self.assertEqual(state["servers"]["serverH"]["consecutive_failures"], 0)

    def test_recovery_from_degraded_emits_single_recovered_alert(self) -> None:
        previous_state = {
            "servers": {
                "serverH": {
                    "status": "degraded",
                    "consecutive_failures": 1,
                    "last_transition_at": "2026-04-14T00:05:00Z",
                }
            }
        }
        state, transitions = evaluate_monitor(
            previous_state,
            [self._status("serverH", ok=True, status=200, detail="HTTP 200", label="서버H")],
            failure_threshold=2,
            checked_at="2026-04-14T00:06:00Z",
        )
        self.assertEqual(len(transitions), 1)
        self.assertEqual(transitions[0]["type"], "recovered")
        self.assertEqual(state["servers"]["serverH"]["status"], "up")

    def test_malformed_state_file_resets_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            path.write_text("{broken", encoding="utf-8")
            loaded = load_monitor_state(path)
        self.assertEqual(loaded, {"version": 1, "servers": {}})

    def test_state_round_trip_preserves_server_map(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "state.json"
            original = {"version": 1, "servers": {"serverH": {"status": "up", "consecutive_failures": 0}}}
            save_monitor_state(path, original)
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["servers"]["serverH"]["status"], "up")

    def test_transition_message_aggregates_multiple_events(self) -> None:
        message = format_transition_message(
            [
                {
                    "type": "degraded",
                    "server": "serverV",
                    "label": "서버V",
                    "url": "https://api2.govpress.cloud",
                    "checked_at": "2026-04-14T00:09:00Z",
                    "detail": "timed out",
                    "consecutive_failures": 1,
                },
                {
                    "type": "down",
                    "server": "serverH",
                    "label": "서버H",
                    "url": "https://api.govpress.cloud",
                    "checked_at": "2026-04-14T00:10:00Z",
                    "detail": "HTTP 502",
                    "consecutive_failures": 2,
                },
                {
                    "type": "recovered",
                    "server": "serverW",
                    "label": "서버W",
                    "url": "https://api4.govpress.cloud",
                    "checked_at": "2026-04-14T00:10:00Z",
                    "detail": "HTTP 200",
                },
            ]
        )
        self.assertIn("DEGRADED 서버V", message)
        self.assertIn("DOWN 서버H", message)
        self.assertIn("RECOVERED 서버W", message)
