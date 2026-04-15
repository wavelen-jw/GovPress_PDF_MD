from __future__ import annotations

from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
import io
import zipfile
import os
from pathlib import Path
import tempfile
import json
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from server.app.adapters.policy_briefing import (
    DownloadedPolicyBriefingFile,
    PolicyBriefingAttachment,
    PolicyBriefingClient,
    PolicyBriefingItem,
    _build_attachment_request_headers,
    _inject_policy_briefing_department,
    _looks_like_html_error,
)
from server.app.main import create_app


class PolicyBriefingClientStub:
    def __init__(self) -> None:
        self.list_calls: list[date] = []
        self.download_calls: list[str] = []
        self.fixture_hwpx = _build_minimal_hwpx_bytes()
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
                        file_name="today-briefing.pdf",
                        file_url="https://example.test/files/today-briefing.pdf",
                    ),
                    PolicyBriefingAttachment(
                        file_name="[별첨] today-appendix.hwpx",
                        file_url="https://example.test/files/today-appendix.hwpx",
                    ),
                ),
            )
        ]
        self.items_by_date: dict[date, list[PolicyBriefingItem]] = {
            date(2026, 4, 9): list(self.items),
            date(
                2026,
                4,
                8,
            ): [
                PolicyBriefingItem(
                    news_item_id="156700000",
                    title="어제 보도자료 테스트",
                    department="교육부",
                    approve_date="04/08/2026 12:00:00",
                    original_url="https://example.test/briefing/156700000",
                    attachments=(
                        PolicyBriefingAttachment(
                            file_name="yesterday-briefing.hwpx",
                            file_url="https://example.test/files/yesterday-briefing.hwpx",
                        ),
                    ),
                )
            ],
        }
        self.raise_on_dates: set[date] = set()

    @property
    def configured(self) -> bool:
        return True

    def list_today_hwpx_items(self, target_date: date) -> list[PolicyBriefingItem]:
        self.list_calls.append(target_date)
        if target_date in self.raise_on_dates:
            raise TimeoutError("upstream policy briefing timeout")
        return list(self.items_by_date.get(target_date, []))

    def download_primary_hwpx(self, news_item_id: str, *, target_date: date) -> DownloadedPolicyBriefingFile:
        item = next(entry for entry in self.items if entry.news_item_id == news_item_id)
        return self.download_item_hwpx(item)

    def download_item_hwpx(self, item: PolicyBriefingItem) -> DownloadedPolicyBriefingFile:
        self.download_calls.append(item.news_item_id)
        attachment = item.primary_hwpx
        assert attachment is not None
        return DownloadedPolicyBriefingFile(
            item=item,
            attachment=attachment,
            content=self.fixture_hwpx,
        )

    def download_attachment(
        self,
        item: PolicyBriefingItem,
        attachment: PolicyBriefingAttachment,
    ) -> DownloadedPolicyBriefingFile:
        self.download_calls.append(f"{item.news_item_id}:{attachment.file_name}")
        content = b"%PDF-1.7 stub" if attachment.is_pdf else self.fixture_hwpx
        return DownloadedPolicyBriefingFile(item=item, attachment=attachment, content=content)



class PolicyBriefingApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.previous_api_key = os.environ.get("GOVPRESS_API_KEY")
        self.previous_admin_api_key = os.environ.get("GOVPRESS_ADMIN_API_KEY")
        self.previous_qc_export_root = os.environ.get("GOVPRESS_QC_EXPORT_ROOT")
        os.environ["GOVPRESS_API_KEY"] = "test-api-key"
        os.environ["GOVPRESS_ADMIN_API_KEY"] = "test-admin-key"
        os.environ["GOVPRESS_QC_EXPORT_ROOT"] = str(Path(self.temp_dir.name) / "exports" / "policy_briefing_qc")
        self.addCleanup(self._restore_api_key)
        self.addCleanup(self._restore_qc_export_root)
        self.client_stub = PolicyBriefingClientStub()
        self.app = create_app(Path(self.temp_dir.name), policy_briefing_client=self.client_stub)
        self.client = TestClient(self.app)
        self.headers = {"X-API-Key": "test-api-key"}
        self.convert_hwpx_patcher = patch(
            "server.app.adapters.hwpx_converter.convert_hwpx",
            side_effect=lambda path, table_mode="text": "# 제목\n\n보도자료\n보도시점: 2026. 4. 9.\n",
        )
        self.render_preview_patcher = patch(
            "server.app.adapters.opendataloader.render_preview_html",
            side_effect=lambda markdown: f"<p>{markdown}</p>",
        )
        self.extract_metadata_patcher = patch(
            "server.app.adapters.opendataloader.extract_metadata",
            return_value=("제목", "행정안전부"),
        )
        self.convert_hwpx_patcher.start()
        self.render_preview_patcher.start()
        self.extract_metadata_patcher.start()
        self.addCleanup(self.convert_hwpx_patcher.stop)
        self.addCleanup(self.render_preview_patcher.stop)
        self.addCleanup(self.extract_metadata_patcher.stop)

    def tearDown(self) -> None:
        self.client.close()
        self.app.state.worker.stop()

    def _restore_api_key(self) -> None:
        if self.previous_api_key is None:
            os.environ.pop("GOVPRESS_API_KEY", None)
        else:
            os.environ["GOVPRESS_API_KEY"] = self.previous_api_key
        if self.previous_admin_api_key is None:
            os.environ.pop("GOVPRESS_ADMIN_API_KEY", None)
        else:
            os.environ["GOVPRESS_ADMIN_API_KEY"] = self.previous_admin_api_key

    def _restore_qc_export_root(self) -> None:
        if self.previous_qc_export_root is None:
            os.environ.pop("GOVPRESS_QC_EXPORT_ROOT", None)
        else:
            os.environ["GOVPRESS_QC_EXPORT_ROOT"] = self.previous_qc_export_root

    def test_list_today_policy_briefings_returns_hwpx_items(self) -> None:
        response = self.client.get("/v1/policy-briefings/today?date=2026-04-09", headers=self.headers)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload["items"]), 1)
        self.assertEqual(payload["items"][0]["news_item_id"], "156700001")
        self.assertTrue(payload["items"][0]["has_appendix_hwpx"])
        self.assertEqual(len(self.client_stub.list_calls), 1)

    def test_list_today_policy_briefings_uses_daily_cache(self) -> None:
        first = self.client.get("/v1/policy-briefings/today?date=2026-04-09", headers=self.headers)
        second = self.client.get("/v1/policy-briefings/today?date=2026-04-09", headers=self.headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(self.client_stub.list_calls), 1)

    def test_list_today_policy_briefings_filters_cached_items_by_requested_date(self) -> None:
        first = self.client.get("/v1/policy-briefings/today?date=2026-04-09", headers=self.headers)
        second = self.client.get("/v1/policy-briefings/today?date=2026-04-08", headers=self.headers)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual([item["news_item_id"] for item in first.json()["items"]], ["156700001"])
        self.assertEqual([item["news_item_id"] for item in second.json()["items"]], ["156700000"])

    def test_list_today_policy_briefings_falls_back_to_stale_cache_when_refresh_fails(self) -> None:
        today = date.today()
        self.client_stub.items_by_date[today] = [
            replace(item, approve_date=f"{today:%m/%d/%Y} 00:00:00") for item in self.client_stub.items
        ]
        first = self.client.get(f"/v1/policy-briefings/today?date={today.isoformat()}", headers=self.headers)

        self.assertEqual(first.status_code, 200)
        day_store = Path(self.temp_dir.name) / "policy_briefing_catalog" / f"{today.isoformat()}.json"
        payload = json.loads(day_store.read_text())
        payload["last_refreshed_at"] = (datetime.now(UTC) - timedelta(hours=2)).isoformat()
        day_store.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        self.client_stub.raise_on_dates.add(today)

        second = self.client.get(f"/v1/policy-briefings/today?date={today.isoformat()}", headers=self.headers)

        self.assertEqual(second.status_code, 200)
        self.assertEqual([item["news_item_id"] for item in second.json()["items"]], ["156700001"])
        self.assertTrue(second.json()["served_stale"])
        self.assertIn("제공기관 API", second.json()["warning"])
        self.assertTrue(second.json()["last_refreshed_at"])
        self.assertEqual(self.client_stub.list_calls, [today, today])

    def test_list_today_policy_briefings_returns_502_when_no_cache_and_refresh_fails(self) -> None:
        self.client_stub.raise_on_dates.add(date(2026, 4, 10))

        response = self.client.get("/v1/policy-briefings/today?date=2026-04-10", headers=self.headers)

        self.assertEqual(response.status_code, 502)
        self.assertIn("제공기관 API", response.json()["detail"])

    def test_import_policy_briefing_creates_job(self) -> None:
        response = self.client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001", "date": "2026-04-09"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["news_item_id"], "156700001")
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["file_name"], "today-briefing.hwpx")
        cache_index = Path(self.temp_dir.name) / "policy_briefing_cache" / "index.json"
        self.assertTrue(cache_index.exists())
        original_path = next((Path(self.temp_dir.name) / "originals").glob(f"{payload['job_id']}-*.hwpx"))
        self.assertGreater(original_path.stat().st_size, 0)
        pdf_path = next((Path(self.temp_dir.name) / "originals").glob(f"{payload['job_id']}-*.pdf"))
        self.assertGreater(pdf_path.stat().st_size, 0)

    def test_import_policy_briefing_recovers_missing_cached_original(self) -> None:
        first = self.client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001", "date": "2026-04-09"},
            headers=self.headers,
        )
        self.assertEqual(first.status_code, 200)

        cached_originals_dir = Path(self.temp_dir.name) / "policy_briefing_cache" / "originals"
        for path in cached_originals_dir.glob("*"):
            path.unlink()

        second = self.client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001", "date": "2026-04-09"},
            headers=self.headers,
        )

        self.assertEqual(second.status_code, 200)
        self.assertEqual(self.client_stub.download_calls, ["156700001", "156700001"])
        payload = second.json()
        original_path = next((Path(self.temp_dir.name) / "originals").glob(f"{payload['job_id']}-*.hwpx"))
        self.assertGreater(original_path.stat().st_size, 0)

    def test_reset_policy_briefing_cache_requires_admin_key(self) -> None:
        self.client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001", "date": "2026-04-09"},
            headers=self.headers,
        )

        response = self.client.post("/v1/policy-briefings/cache/reset", headers=self.headers)

        self.assertEqual(response.status_code, 403)

    def test_reset_policy_briefing_cache_deletes_cached_entries(self) -> None:
        self.client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001", "date": "2026-04-09"},
            headers=self.headers,
        )

        response = self.client.post(
            "/v1/policy-briefings/cache/reset",
            headers={"X-Admin-Key": "test-admin-key"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["deleted_entries"], 1)
        cache_index = Path(self.temp_dir.name) / "policy_briefing_cache" / "index.json"
        self.assertFalse(cache_index.exists())
        cached_originals_dir = Path(self.temp_dir.name) / "policy_briefing_cache" / "originals"
        self.assertEqual(list(cached_originals_dir.glob("*")), [])

    def test_get_policy_briefing_qc_dashboard_returns_html(self) -> None:
        dashboard_dir = Path(self.temp_dir.name) / "exports" / "policy_briefing_qc" / "dashboard"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        (dashboard_dir / "index.html").write_text("<html><body>QC Dashboard</body></html>", encoding="utf-8")
        (dashboard_dir / "dashboard.json").write_text("{\"run_count\":1}", encoding="utf-8")

        response = self.client.get("/v1/policy-briefings/qc/dashboard")

        self.assertEqual(response.status_code, 200)
        self.assertIn("QC Dashboard", response.text)
        self.assertIn("text/html", response.headers["content-type"])

    def test_get_policy_briefing_qc_dashboard_json_returns_payload(self) -> None:
        dashboard_dir = Path(self.temp_dir.name) / "exports" / "policy_briefing_qc" / "dashboard"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        (dashboard_dir / "index.html").write_text("<html><body>QC Dashboard</body></html>", encoding="utf-8")
        (dashboard_dir / "dashboard.json").write_text("{\"run_count\":1}", encoding="utf-8")

        response = self.client.get("/v1/policy-briefings/qc/dashboard.json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["run_count"], 1)

    def test_get_policy_briefing_qc_dashboard_returns_404_when_missing(self) -> None:
        response = self.client.get("/v1/policy-briefings/qc/dashboard")

        self.assertEqual(response.status_code, 404)
        self.assertIn("not available", response.json()["detail"])

    def test_inject_policy_briefing_department_prefixes_press_label(self) -> None:
        markdown = "# 제목\n\n보도자료\n보도시점: 2026. 4. 9.\n"

        injected = _inject_policy_briefing_department(markdown, "행정안전부")

        self.assertEqual(injected, "# 제목\n\n행정안전부 보도자료 /\n보도시점: 2026. 4. 9.\n")

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
            json={"news_item_id": "156700001", "date": "2026-04-09"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("실제 파일 형식이 HWPX(zip)", response.json()["detail"])

    def test_import_policy_briefing_maps_timeout_to_provider_api_message(self) -> None:
        class TimeoutClientStub(PolicyBriefingClientStub):
            def download_item_hwpx(self, item: PolicyBriefingItem) -> DownloadedPolicyBriefingFile:
                raise TimeoutError("upstream policy briefing timeout")

        app = create_app(Path(self.temp_dir.name), policy_briefing_client=TimeoutClientStub())
        client = TestClient(app)
        self.addCleanup(client.close)
        self.addCleanup(app.state.worker.stop)

        response = client.post(
            "/v1/policy-briefings/import",
            json={"news_item_id": "156700001", "date": "2026-04-09"},
            headers=self.headers,
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("제공기관 API", response.json()["detail"])


class PolicyBriefingClientTests(unittest.TestCase):
    def test_list_items_collapses_redundant_title_whitespace(self) -> None:
        payload = """\
<response>
  <header><resultCode>0</resultCode></header>
  <body>
    <NewsItem>
      <NewsItemId>156755766</NewsItemId>
      <Title>정부, 쉰들러 ISDS 소송비용 약 96억 원  전액 환수</Title>
      <MinisterCode>법무부</MinisterCode>
      <ApproveDate>04/15/2026 09:00:00</ApproveDate>
      <OriginalUrl>https://www.korea.kr/briefing/pressReleaseView.do?newsId=156755766</OriginalUrl>
      <FileName1>260415.hwpx</FileName1>
      <FileUrl1>https://example.test/files/260415.hwpx</FileUrl1>
    </NewsItem>
  </body>
</response>
"""

        class _FakeResponse:
            def __init__(self, body: str) -> None:
                self._body = body.encode("utf-8")

            def read(self) -> bytes:
                return self._body

            def __enter__(self) -> "_FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        client = PolicyBriefingClient(service_key="dummy")
        with patch("server.app.adapters.policy_briefing.urllib.request.urlopen", return_value=_FakeResponse(payload)):
            items = client.list_items(date(2026, 4, 15))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "정부, 쉰들러 ISDS 소송비용 약 96억 원 전액 환수")

    def test_build_attachment_request_headers_uses_original_url_as_referer(self) -> None:
        item = PolicyBriefingItem(
            news_item_id="156755793",
            title="테스트",
            department="부처",
            approve_date="04/15/2026 17:00:00",
            original_url="https://www.korea.kr/briefing/pressReleaseView.do?newsId=156755793",
            attachments=(),
        )
        headers = _build_attachment_request_headers(item)
        self.assertIn("Mozilla/5.0", headers["User-Agent"])
        self.assertEqual(headers["Referer"], item.original_url)

    def test_looks_like_html_error_detects_error_document(self) -> None:
        self.assertTrue(_looks_like_html_error(b'<!DOCTYPE html><html lang="ko"><title>Error</title>'))
        self.assertFalse(_looks_like_html_error(_build_minimal_hwpx_bytes()))

    def test_download_attachment_rejects_html_error_page(self) -> None:
        item = PolicyBriefingItem(
            news_item_id="156755793",
            title="테스트",
            department="부처",
            approve_date="04/15/2026 17:00:00",
            original_url="https://www.korea.kr/briefing/pressReleaseView.do?newsId=156755793",
            attachments=(
                PolicyBriefingAttachment(
                    file_name="sample.hwpx",
                    file_url="https://www.korea.kr/common/download.do?tblKey=GMN&fileId=198427528",
                ),
            ),
        )

        class _FakeResponse:
            def read(self) -> bytes:
                return b'<!DOCTYPE html><html lang="ko"><title>Error</title></html>'

            def __enter__(self) -> "_FakeResponse":
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        client = PolicyBriefingClient(service_key="dummy")
        with patch("server.app.adapters.policy_briefing.urllib.request.urlopen", return_value=_FakeResponse()):
            with self.assertRaisesRegex(ValueError, "HTML 에러 페이지"):
                client.download_attachment(item, item.attachments[0])


def _build_minimal_hwpx_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("mimetype", "application/hwp+zip")
        archive.writestr("Contents/content.hpf", "<hpf></hpf>")
    return buffer.getvalue()
