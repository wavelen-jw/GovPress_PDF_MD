from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "smoke_policy_briefing_imports.py"
SPEC = importlib.util.spec_from_file_location("smoke_policy_briefing_imports", SCRIPT_PATH)
assert SPEC and SPEC.loader
smoke = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(smoke)


class PolicyBriefingImportSmokeTests(unittest.TestCase):
    def test_parse_server_requires_label_and_http_url(self) -> None:
        self.assertEqual(smoke.parse_server("serverW=https://api4.example/"), ("serverW", "https://api4.example"))
        with self.assertRaises(Exception):
            smoke.parse_server("https://api4.example")

    def test_request_json_retries_transient_server_error(self) -> None:
        error = HTTPError("https://api.example/test", 502, "bad gateway", {}, None)
        error.read = MagicMock(return_value=b'{"detail":"temporary"}')
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok":true}'
        with patch.object(smoke, "urlopen", side_effect=[error, response]) as mocked_open, patch.object(
            smoke.time, "sleep"
        ):
            payload = smoke.request_json("https://api.example", "/test", "secret")

        self.assertEqual(payload, {"ok": True})
        self.assertEqual(mocked_open.call_count, 2)

    def test_request_json_does_not_retry_not_found(self) -> None:
        error = HTTPError("https://api.example/test", 404, "not found", {}, None)
        error.read = MagicMock(return_value=b'{"detail":"missing"}')
        with patch.object(smoke, "urlopen", side_effect=error) as mocked_open:
            with self.assertRaises(smoke.ApiRequestError) as raised:
                smoke.request_json("https://api.example", "/test", "secret")

        self.assertEqual(raised.exception.status, 404)
        self.assertEqual(mocked_open.call_count, 1)

    def test_main_checks_every_hwpx_item(self) -> None:
        catalogs = {
            "https://one.example": {
                "items": [
                    {"news_item_id": "100", "has_hwpx": True},
                    {"news_item_id": "101", "has_hwpx": False},
                ]
            },
            "https://two.example": {"items": [{"news_item_id": "100", "has_hwpx": True}]},
        }

        def fake_request(base_url, path, api_key, **kwargs):
            self.assertEqual(api_key, "secret")
            self.assertIn("date=2026-07-16", path)
            return catalogs[base_url]

        def fake_smoke(server, item, target_date, api_key, **kwargs):
            return {
                "server": server[0],
                "news_item_id": item["news_item_id"],
                "status": "passed",
                "markdown_chars": 10,
                "elapsed_seconds": 0.01,
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "result.json"
            with patch.object(smoke, "request_json", side_effect=fake_request), patch.object(
                smoke, "smoke_item", side_effect=fake_smoke
            ):
                result = smoke.main(
                    [
                        "--server", "one=https://one.example",
                        "--server", "two=https://two.example",
                        "--date", "2026-07-16",
                        "--api-key", "secret",
                        "--output", str(output),
                    ]
                )
            payload = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(result, 0)
        self.assertEqual(payload["summary"], {"checked": 2, "passed": 2, "failed": 0})
        self.assertTrue(payload["inventory_equal"])

    def test_inventory_mismatch_fails_when_required(self) -> None:
        def fake_request(base_url, path, api_key, **kwargs):
            item_id = "100" if "one" in base_url else "200"
            return {"items": [{"news_item_id": item_id, "has_hwpx": True}]}

        def fake_smoke(server, item, target_date, api_key, **kwargs):
            return {
                "server": server[0],
                "news_item_id": item["news_item_id"],
                "status": "passed",
                "markdown_chars": 10,
                "elapsed_seconds": 0.01,
            }

        with patch.object(smoke, "request_json", side_effect=fake_request), patch.object(
            smoke, "smoke_item", side_effect=fake_smoke
        ):
            result = smoke.main(
                [
                    "--server", "one=https://one.example",
                    "--server", "two=https://two.example",
                    "--date", "2026-07-16",
                    "--api-key", "secret",
                    "--require-equal-inventory",
                ]
            )

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
