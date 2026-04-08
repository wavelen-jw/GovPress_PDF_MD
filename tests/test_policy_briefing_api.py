from __future__ import annotations

from dataclasses import replace
from datetime import date
import os
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from server.app.adapters.policy_briefing import (
    DownloadedPolicyBriefingFile,
    PolicyBriefingAttachment,
    PolicyBriefingItem,
)
from server.app.main import create_app


class PolicyBriefingClientStub:
    def __init__(self) -> None:
        self.list_calls: list[date] = []
        self.fixture_hwpx = Path("tests/260121 AI시대 공공문서 혁신 추진계획_수정.hwpx").read_bytes()
        self.items = [
            PolicyBriefingItem(
                news_item_id="156700001",
                title="오늘 보도자료 테스트",
                department="행정안전부",
                approve_date="04/09/2026 00:00:00",
                original_url="https://example.test/briefing/156700001",
                attachments=(
                    PolicyBriefingAttachment(
                        file_name="today-briefing.hwpx",
                        file_url="https://example.test/files/today-briefing.hwpx",
                    ),
                    PolicyBriefingAttachment(
                        file_name="[별첨] today-appendix.hwpx",
                        file_url="https://example.test/files/today-appendix.hwpx",
                    ),
                ),
            )
        ]

    @property
    def configured(self) -> bool:
        return True

    def list_today_hwpx_items(self, target_date: date) -> list[PolicyBriefingItem]:
        self.list_calls.append(target_date)
        return list(self.items)

    def download_primary_hwpx(self, news_item_id: str, *, target_date: date) -> DownloadedPolicyBriefingFile:
        item = next(entry for entry in self.items if entry.news_item_id == news_item_id)
        return self.download_item_hwpx(item)

    def download_item_hwpx(self, item: PolicyBriefingItem) -> DownloadedPolicyBriefingFile:
        attachment = item.primary_hwpx
        assert attachment is not None
        return DownloadedPolicyBriefingFile(
            item=item,
            attachment=attachment,
            content=self.fixture_hwpx,
        )


class PolicyBriefingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_api_key = os.environ.get("GOVPRESS_API_KEY")
        os.environ["GOVPRESS_API_KEY"] = "test-api-key"
        self.addCleanup(self._restore_api_key)
        self.client_stub = PolicyBriefingClientStub()
        self.app = create_app(Path(self.temp_dir.name), policy_briefing_client=self.client_stub)
        self.client = TestClient(self.app)
        self.headers = {"X-API-Key": "test-api-key"}

    def tearDown(self) -> None:
        self.client.close()
        self.app.state.worker.stop()

    def _restore_api_key(self) -> None:
        if self.previous_api_key is None:
            os.environ.pop("GOVPRESS_API_KEY", None)
        else:
            os.environ["GOVPRESS_API_KEY"] = self.previous_api_key

    def test_list_today_policy_briefings_returns_hwpx_items(self) -> None:
        response = self.client.get("/v1/policy-briefings/today", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["news_item_id"], "156700001")
        self.assertTrue(payload["items"][0]["has_appendix_hwpx"])
        self.assertEqual(len(self.client_stub.list_calls), 1)

    def test_list_today_policy_briefings_uses_daily_cache(self) -> None:
        first = self.client.get("/v1/policy-briefings/today", headers=self.headers)
        second = self.client.get("/v1/policy-briefings/today", headers=self.headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(self.client_stub.list_calls), 1)

    def test_import_policy_briefing_creates_job(self) -> None:
        response = self.client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["news_item_id"], "156700001")
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["file_name"], "today-briefing.hwpx")
        cache_index = Path(self.temp_dir.name) / "policy_briefing_cache" / "index.json"
        self.assertTrue(cache_index.exists())

    def test_import_policy_briefing_rejects_non_zip_hwpx_payload(self) -> None:
        class NonZipClientStub(PolicyBriefingClientStub):
            def download_item_hwpx(self, item: PolicyBriefingItem) -> DownloadedPolicyBriefingFile:
                downloaded = super().download_item_hwpx(item)
                return replace(downloaded, content=b"\xd0\xcf\x11\xe0legacy-hwp")

        app = create_app(Path(self.temp_dir.name), policy_briefing_client=NonZipClientStub())
        client = TestClient(app)
        self.addCleanup(client.close)
        self.addCleanup(app.state.worker.stop)

        response = client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("실제 파일 형식이 HWPX(zip)", response.json()["detail"])
