from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from server.app.adapters.policy_briefing import (
    DownloadedPolicyBriefingFile,
    PolicyBriefingAttachment,
    PolicyBriefingCatalogResult,
    PolicyBriefingItem,
)
from server.app.adapters.policy_briefing_qc import export_policy_briefings_for_qc, run_policy_briefing_qc_pipeline


class PolicyBriefingQcClientStub:
    def __init__(self) -> None:
        self.download_calls: list[tuple[str, str]] = []
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
                ),
            )
        ]

    def download_item_hwpx(self, item: PolicyBriefingItem) -> DownloadedPolicyBriefingFile:
        attachment = item.primary_hwpx
        assert attachment is not None
        self.download_calls.append((item.news_item_id, attachment.file_name))
        return DownloadedPolicyBriefingFile(item=item, attachment=attachment, content=b"PK\x03\x04stub")

    def download_attachment(
        self,
        item: PolicyBriefingItem,
        attachment: PolicyBriefingAttachment,
    ) -> DownloadedPolicyBriefingFile:
        self.download_calls.append((item.news_item_id, attachment.file_name))
        return DownloadedPolicyBriefingFile(item=item, attachment=attachment, content=b"%PDF-1.7 stub")


class PolicyBriefingQcCatalogStub:
    def __init__(self, items: list[PolicyBriefingItem]) -> None:
        self.items = list(items)
        self.calls: list[tuple[date, bool]] = []

    def list_cached_items_with_status(self, *, target_date: date, ensure_fresh: bool = True) -> PolicyBriefingCatalogResult:
        self.calls.append((target_date, ensure_fresh))
        return PolicyBriefingCatalogResult(items=list(self.items), last_refreshed_at="2026-04-09T00:00:00+00:00")


class PolicyBriefingQcExportTests(unittest.TestCase):
    def test_export_policy_briefings_for_qc_writes_hwpx_pdf_and_metadata(self) -> None:
        client = PolicyBriefingQcClientStub()
        catalog = PolicyBriefingQcCatalogStub(client.items)

        with tempfile.TemporaryDirectory() as tmpdir:
            report = export_policy_briefings_for_qc(
                client=client,
                catalog=catalog,
                target_date=date(2026, 4, 9),
                output_root=tmpdir,
            )

            self.assertEqual(report["exported_count"], 1)
            exported = report["items"][0]
            export_dir = Path(exported["export_dir"])
            self.assertTrue((export_dir / "source.hwpx").exists())
            self.assertTrue((export_dir / "source.pdf").exists())
            self.assertTrue((export_dir / "metadata.json").exists())
            self.assertEqual(catalog.calls, [(date(2026, 4, 9), True)])
            self.assertEqual(
                client.download_calls,
                [
                    ("156700001", "today-briefing.hwpx"),
                    ("156700001", "today-briefing.pdf"),
                ],
            )

    def test_export_policy_briefings_for_qc_can_scaffold_into_gov_md_converter(self) -> None:
        client = PolicyBriefingQcClientStub()
        catalog = PolicyBriefingQcCatalogStub(client.items)
        scaffold_calls: list[dict[str, object]] = []

        def fake_scaffold_runner(**kwargs) -> str:
            scaffold_calls.append(kwargs)
            return "/tmp/gov-md-converter/tests/manual_samples/policy/156700001"

        with tempfile.TemporaryDirectory() as tmpdir:
            report = export_policy_briefings_for_qc(
                client=client,
                catalog=catalog,
                target_date=date(2026, 4, 9),
                output_root=tmpdir,
                scaffold_runner=fake_scaffold_runner,
                gov_md_converter_root="/home/wavel/projects/gov-md-converter",
                qc_root="tests/manual_samples/policy_briefings",
                sample_status="scratch",
            )

            self.assertEqual(report["scaffolded_count"], 1)
            self.assertEqual(len(scaffold_calls), 1)
            self.assertEqual(scaffold_calls[0]["sample_id"], "policy_briefing_2026_04_09_156700001")
            self.assertEqual(scaffold_calls[0]["sample_status"], "scratch")
            self.assertTrue(Path(scaffold_calls[0]["source_path"]).exists())
            self.assertTrue(Path(scaffold_calls[0]["pdf_path"]).exists())

    def test_export_policy_briefings_for_qc_records_failures_and_continues(self) -> None:
        client = PolicyBriefingQcClientStub()
        failing_item = PolicyBriefingItem(
            news_item_id="156700002",
            title="실패 문서",
            department="행정안전부",
            approve_date="04/09/2026 01:00:00",
            original_url="https://example.test/briefing/156700002",
            attachments=(
                PolicyBriefingAttachment(
                    file_name="broken.hwpx",
                    file_url="https://example.test/files/broken.hwpx",
                ),
            ),
        )
        client.items.append(failing_item)
        catalog = PolicyBriefingQcCatalogStub(client.items)

        original_download = client.download_item_hwpx

        def flaky_download(item: PolicyBriefingItem) -> DownloadedPolicyBriefingFile:
            if item.news_item_id == "156700002":
                raise ValueError("첨부파일 다운로드 결과가 실제 문서가 아니라 HTML 에러 페이지입니다.")
            return original_download(item)

        client.download_item_hwpx = flaky_download  # type: ignore[method-assign]

        with tempfile.TemporaryDirectory() as tmpdir:
            report = export_policy_briefings_for_qc(
                client=client,
                catalog=catalog,
                target_date=date(2026, 4, 9),
                output_root=tmpdir,
            )

            self.assertEqual(report["exported_count"], 1)
            self.assertEqual(len(report["failed_items"]), 1)
            self.assertEqual(report["failed_items"][0]["news_item_id"], "156700002")

    def test_run_policy_briefing_qc_pipeline_aggregates_gov_md_reports(self) -> None:
        client = PolicyBriefingQcClientStub()
        catalog = PolicyBriefingQcCatalogStub(client.items)
        command_calls: list[tuple[str, str]] = []
        scaffold_calls: list[dict[str, object]] = []

        def fake_scaffold_runner(**kwargs) -> str:
            scaffold_calls.append(kwargs)
            return "/tmp/gov-md-converter/tests/manual_samples/policy/156700001"

        def fake_command_runner(**kwargs) -> dict[str, object]:
            command_calls.append((kwargs["command"], kwargs["qc_root"]))
            payloads = {
                "regression": [{"sample_id": "policy_briefing_2026_04_09_156700001", "passed": False, "findings": []}],
                "triage": {"summary": {"review_required_count": 1}},
                "suggest-fix": {"proposal_count": 1},
                "patch-template": {"template_count": 1},
                "fix-plan": {"plan_count": 1},
                "apply-fix-hint": {"hint_count": 1},
                "auto-patch-draft": {"draft_count": 1},
            }
            return {
                "command": kwargs["command"],
                "returncode": 1 if kwargs["command"] == "regression" else 0,
                "stdout": "",
                "stderr": "",
                "output_path": str(kwargs["output_path"]) if kwargs["output_path"] is not None else None,
                "payload": payloads[kwargs["command"]],
            }

        with tempfile.TemporaryDirectory() as tmpdir:
            report = run_policy_briefing_qc_pipeline(
                client=client,
                catalog=catalog,
                target_date=date(2026, 4, 9),
                output_root=tmpdir,
                gov_md_converter_root="/home/wavel/projects/gov-md-converter",
                qc_root="tests/manual_samples/policy_briefings",
                scaffold_runner=fake_scaffold_runner,
                command_runner=fake_command_runner,
            )

            self.assertEqual(report["summary"]["review_required_count"], 1)
            self.assertEqual(report["summary"]["proposal_count"], 1)
            self.assertEqual(report["summary"]["draft_count"], 1)
            self.assertEqual(len(scaffold_calls), 1)
            self.assertEqual(
                [name for name, _ in command_calls],
                [
                    "regression",
                    "triage",
                    "suggest-fix",
                    "patch-template",
                    "fix-plan",
                    "apply-fix-hint",
                    "auto-patch-draft",
                ],
            )
            regression_report = Path(report["reports_dir"]) / "regression.json"
            self.assertTrue(regression_report.exists())
            self.assertEqual(json.loads(regression_report.read_text(encoding="utf-8"))[0]["passed"], False)


if __name__ == "__main__":
    unittest.main()
