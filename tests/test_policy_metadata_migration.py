from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPT = (
    Path(__file__).parents[1]
    / "deploy"
    / "wsl"
    / "govpress-mcp"
    / "scripts"
    / "migrate-api-metadata.py"
)
SPEC = importlib.util.spec_from_file_location("migrate_api_metadata", SCRIPT)
assert SPEC and SPEC.loader
migration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(migration)


class PolicyMetadataMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.canonical = {
            "metadata_schema_version": 1,
            "metadata_source": "policy-briefing-api",
            "news_item_id": "156751988",
            "title": "국민 안전을 위한 정책",
            "department": "행정안전부",
            "approve_date": "2026-03-31T10:00:00",
            "original_url": "https://example.test/156751988",
            "attachments": [{"file_name": "자료.hwpx", "file_url": "https://example.test/a"}],
        }

    def test_body_conflict_requires_rerender_for_wrong_title(self) -> None:
        body = "# 다른 제목\n\n행정안전부 보도자료 /\n\n본문"
        self.assertEqual(migration.detect_body_conflicts(body, self.canonical), ["h1_title"])

    def test_missing_press_label_agency_is_metadata_only_compatible(self) -> None:
        body = "# 국민 안전을 위한 정책\n\n보도자료 /\n\n본문"
        self.assertEqual(migration.detect_body_conflicts(body, self.canonical), [])

    def test_metadata_only_frontmatter_rewrite_preserves_body_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "156751988.md"
            body = "# 국민 안전을 위한 정책\n\n본문\n"
            path.write_text(
                "---\n"
                "id: '156751988'\n"
                "title: '옛 제목'\n"
                "department: '미상'\n"
                "approve_date: '2026-03-31T00:00:00'\n"
                "original_url: ''\n"
                "---\n\n"
                + body,
                encoding="utf-8",
            )

            migration.replace_frontmatter(path, self.canonical)
            frontmatter, rewritten_body = migration.parse_markdown(path.read_text(encoding="utf-8"))

            self.assertEqual(rewritten_body, body)
            self.assertEqual(frontmatter["title"], self.canonical["title"])
            self.assertEqual(frontmatter["department"], "행정안전부")
            self.assertEqual(frontmatter["metadata_source"], "policy-briefing-api")
            self.assertIn("자료.hwpx", frontmatter["attachments_json"])


if __name__ == "__main__":
    unittest.main()
