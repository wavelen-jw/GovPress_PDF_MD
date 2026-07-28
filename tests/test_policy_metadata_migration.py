from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import tarfile
import tempfile
import unittest
from unittest import mock


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

    def test_body_title_difference_is_observation_not_rerender_rule(self) -> None:
        body = "# 다른 제목\n\n행정안전부 보도자료 /\n\n본문"
        self.assertEqual(migration.detect_body_differences(body, self.canonical), ["h1_title"])

    def test_missing_press_label_agency_is_metadata_only_compatible(self) -> None:
        body = "# 국민 안전을 위한 정책\n\n보도자료 /\n\n본문"
        self.assertEqual(migration.detect_body_differences(body, self.canonical), [])

    def test_metadata_only_frontmatter_rewrite_preserves_body_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "156751988.md"
            body = "\n\n# 국민 안전을 위한 정책\r\n\r\n본문\r\n".encode()
            path.write_bytes(
                b"---\n"
                b"id: '156751988'\n"
                b"title: 'old'\n"
                b"department: 'unknown'\n"
                b"approve_date: '2026-03-31T00:00:00'\n"
                b"original_url: ''\n"
                b"---\n"
                + body
            )

            migration.replace_frontmatter(path, self.canonical)
            _, rewritten_body = migration.split_markdown_bytes(path.read_bytes())
            frontmatter, _ = migration.parse_markdown(path.read_text(encoding="utf-8"))

            self.assertEqual(rewritten_body, body)
            self.assertEqual(frontmatter["title"], self.canonical["title"])
            self.assertEqual(frontmatter["department"], "행정안전부")
            self.assertEqual(frontmatter["metadata_source"], "policy-briefing-api")
            self.assertIn("자료.hwpx", frontmatter["attachments_json"])

    def test_discover_local_ids_drives_month_scope(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            month = root / "md" / "2026" / "03"
            month.mkdir(parents=True)
            (month / "156751988.md").touch()
            (month / "156751999_제목.md").touch()
            (month / "notes.md").touch()

            self.assertEqual(
                migration.discover_local_ids(root, 2026, 3),
                {"156751988", "156751999"},
            )

    def test_fetch_month_stops_after_all_local_ids_found(self) -> None:
        calls: list[int] = []

        def fake_fetch_day(target, service_key):
            calls.append(target.day)
            if target.day == 2:
                return [self.canonical]
            return []

        with mock.patch.dict(
            migration.os.environ,
            {"GOVPRESS_POLICY_BRIEFING_SERVICE_KEY": "test"},
        ), mock.patch.object(migration, "fetch_day", side_effect=fake_fetch_day):
            result = migration.fetch_month(2026, 3, wanted={"156751988"})

        self.assertEqual(set(result), {"156751988"})
        self.assertEqual(calls, [1, 2])

    def test_fetch_day_retries_truncated_xml(self) -> None:
        response = mock.MagicMock()
        response.__enter__.return_value.read.side_effect = [
            b"<response><header>",
            b"<response><header><resultCode>0</resultCode></header><body /></response>",
        ]
        with mock.patch.object(
            migration.urllib.request,
            "urlopen",
            return_value=response,
        ) as urlopen, mock.patch.object(migration.time, "sleep"):
            items = migration.fetch_day(
                migration.dt.date(2026, 3, 1),
                "test-key",
                attempts=2,
            )

        self.assertEqual(items, [])
        self.assertEqual(urlopen.call_count, 2)

    def test_parallel_month_fetch_records_persistent_day_failure(self) -> None:
        def fake_fetch_day(target, service_key):
            if target.day == 20:
                raise migration.ET.ParseError("truncated")
            return [self.canonical] if target.day == 1 else []

        with mock.patch.dict(
            migration.os.environ,
            {"GOVPRESS_POLICY_BRIEFING_SERVICE_KEY": "test"},
        ), mock.patch.object(migration, "fetch_day", side_effect=fake_fetch_day):
            items, failures = migration.fetch_month_parallel(
                2020,
                8,
                wanted={"156751988"},
                jobs=8,
            )

        self.assertEqual(set(items), {"156751988"})
        self.assertEqual(
            [(failure["day"], failure["error"]) for failure in failures],
            [(20, "ParseError: truncated")],
        )

    def test_bulk_canonical_reuses_superset_api_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cache = root / "shared-cache"
            cache.mkdir()
            migration.atomic_write_json(
                cache / "2026-03.json",
                {
                    "wanted_sha256": "different-superset-scope",
                    "failed_days": [{"day": 20}],
                    "items": [
                        self.canonical,
                        {**self.canonical, "news_item_id": "156751999"},
                    ],
                },
            )
            args = migration.argparse.Namespace(
                output_dir=root / "output",
                api_cache_dir=cache,
                refresh_api_cache=False,
                jobs=8,
            )
            inventory = [
                {
                    "news_item_id": "156751988",
                    "year": 2026,
                    "month": 3,
                }
            ]

            with mock.patch.object(migration, "fetch_month_parallel") as fetch:
                items, failures = migration.load_bulk_canonical(args, inventory)

            fetch.assert_not_called()
            self.assertEqual(set(items), {"156751988"})
            self.assertEqual(failures, [])

    def test_api_node_unescapes_catalog_text(self) -> None:
        node = migration.ET.fromstring(
            "<NewsItem>"
            "<NewsItemId>1</NewsItemId>"
            "<Title>연구 &amp;amp; 개발</Title>"
            "<MinisterCode>과학 &amp;amp; 기술부</MinisterCode>"
            "<FileName1>자료 &amp;amp; 설명.hwpx</FileName1>"
            "<FileUrl1>https://example.test/a</FileUrl1>"
            "</NewsItem>"
        )

        parsed = migration.api_node(node)

        self.assertEqual(parsed["title"], "연구 & 개발")
        self.assertEqual(parsed["department"], "과학 & 기술부")
        self.assertEqual(parsed["attachments"][0]["file_name"], "자료 & 설명.hwpx")

    def test_classify_month_keeps_source_h1_difference_metadata_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            month = root / "md" / "2026" / "03"
            month.mkdir(parents=True)
            path = month / "156751988.md"
            path.write_text(
                "---\n"
                "id: '156751988'\n"
                "title: '옛 API 제목'\n"
                "department: '미상'\n"
                "approve_date: ''\n"
                "original_url: ''\n"
                "---\n\n"
                "# 문서 내부 제목\n\n다른기관 보도자료 /\n",
                encoding="utf-8",
            )

            rows = migration.classify_month(
                root,
                2026,
                3,
                {"156751988": self.canonical},
                wanted={"156751988"},
            )

            self.assertEqual(rows[0]["classification"], "metadata_only")
            self.assertEqual(
                rows[0]["body_differences"],
                ["h1_title", "press_label_department"],
            )

    def test_classify_month_routes_unparseable_frontmatter_to_rerender(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            month = root / "md" / "2026" / "03"
            month.mkdir(parents=True)
            (month / "156751988.md").write_text(
                "# delimiter 없는 문서\n",
                encoding="utf-8",
            )

            rows = migration.classify_month(
                root,
                2026,
                3,
                {"156751988": self.canonical},
                wanted={"156751988"},
            )

            self.assertEqual(rows[0]["classification"], "rerender_reembed")
            self.assertEqual(rows[0]["body_conflicts"], ["frontmatter_unparseable"])

    def test_snapshot_before_apply_captures_sqlite_markdown_and_qdrant(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            data_root = root / "data"
            path = data_root / "md" / "2026" / "03" / "156751988.md"
            path.parent.mkdir(parents=True)
            path.write_text("---\nid: '156751988'\n---\n\n본문\n", encoding="utf-8")
            db_path = data_root / "govpress.db"
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE marker (value TEXT)")
            conn.execute("INSERT INTO marker VALUES ('before')")
            conn.commit()
            conn.close()
            output_dir = data_root / "fetch-log" / "metadata-migration"
            args = migration.argparse.Namespace(
                data_root=data_root,
                db=db_path,
                output_dir=output_dir,
                qdrant_url="http://qdrant",
            )

            with mock.patch.object(
                migration,
                "create_qdrant_snapshot",
                return_value={"result": {"name": "snapshot-1"}},
            ):
                snapshot = migration.snapshot_before_apply(
                    args,
                    "2026-03",
                    [{"md_path": str(path)}],
                )

            backup = sqlite3.connect(snapshot["sqlite_backup"])
            self.assertEqual(backup.execute("SELECT value FROM marker").fetchone(), ("before",))
            backup.close()
            with tarfile.open(snapshot["markdown_backup"], "r:gz") as archive:
                self.assertEqual(
                    archive.getnames(),
                    ["md/2026/03/156751988.md"],
                )
            self.assertEqual(snapshot["qdrant_snapshot"]["result"]["name"], "snapshot-1")

    def test_apply_with_snapshot_persists_failure_recovery_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory)
            args = migration.argparse.Namespace(
                output_dir=output_dir,
                db=output_dir / "govpress.db",
                qdrant_url="http://qdrant",
                batch_size=1,
            )
            snapshot = {
                "sqlite_backup": "/backup/govpress.db",
                "markdown_backup": "/backup/markdown.tar.gz",
                "qdrant_snapshot": {"result": {"name": "snapshot-1"}},
            }

            with mock.patch.object(
                migration,
                "snapshot_before_apply",
                return_value=snapshot,
            ), mock.patch.object(
                migration,
                "apply_metadata_only",
                side_effect=RuntimeError("verification failed"),
            ):
                with self.assertRaisesRegex(RuntimeError, "verification failed"):
                    migration.apply_with_snapshot(args, "2026-03", [{}])

            status = json.loads(
                (output_dir / "2026-03-metadata-only-snapshot.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(status["status"], "failed")
            self.assertEqual(status["qdrant_snapshot"]["result"]["name"], "snapshot-1")
            self.assertIn("RuntimeError: verification failed", status["error"])

    def test_apply_metadata_only_preserves_body_vectors_and_point_count(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data" / "md" / "2026" / "03" / "156751988.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "---\n"
                "id: '156751988'\n"
                "title: '옛 제목'\n"
                "department: '미상'\n"
                "approve_date: ''\n"
                "original_url: ''\n"
                "---\n\n"
                "# 문서 내부 제목\n\n본문\n",
                encoding="utf-8",
            )
            db_path = root / "govpress.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE doc_meta (
                    news_item_id TEXT PRIMARY KEY, title TEXT, department TEXT,
                    approve_date TEXT, source_url TEXT, indexed_at TEXT
                );
                CREATE TABLE briefing_chunks_meta (
                    news_item_id TEXT, department TEXT, approve_date TEXT
                );
                CREATE TABLE indexed_docs (
                    md_path TEXT PRIMARY KEY, md_mtime_ns INTEGER, md_size INTEGER
                );
                """
            )
            conn.execute(
                "INSERT INTO doc_meta VALUES (?, ?, ?, ?, ?, ?)",
                ("156751988", "옛 제목", "미상", "", "", ""),
            )
            conn.execute(
                "INSERT INTO briefing_chunks_meta VALUES (?, ?, ?)",
                ("156751988", "미상", ""),
            )
            stat = path.stat()
            conn.execute(
                "INSERT INTO indexed_docs VALUES (?, ?, ?)",
                ("/app/data/md/2026/03/156751988.md", stat.st_mtime_ns, stat.st_size),
            )
            conn.commit()
            conn.close()

            points = [
                {
                    "id": "point-1",
                    "vector": [0.1, 0.2],
                    "payload": {"news_item_id": "156751988"},
                }
            ]

            def fake_patch_qdrant(qdrant_url, canonical):
                points[0]["payload"].update(
                    {
                        "title": canonical["title"],
                        "department": canonical["department"],
                        "approve_date": canonical["approve_date"],
                        "original_url": canonical["original_url"],
                        "metadata_source": migration.METADATA_SOURCE,
                        "metadata_schema_version": migration.SCHEMA_VERSION,
                        "attachments": canonical["attachments"],
                        "attachments_json": json.dumps(
                            canonical["attachments"],
                            ensure_ascii=False,
                            separators=(",", ":"),
                        ),
                    }
                )

            integrity_path = root / "integrity.jsonl"
            body_before = migration.split_markdown_bytes(path.read_bytes())[1]
            with mock.patch.object(
                migration,
                "qdrant_points",
                side_effect=lambda url, identifier, with_vectors: points,
            ), mock.patch.object(
                migration,
                "patch_qdrant",
                side_effect=fake_patch_qdrant,
            ):
                applied = migration.apply_metadata_only(
                    [
                        {
                            "canonical": self.canonical,
                            "md_path": str(path),
                        }
                    ],
                    db_path=db_path,
                    qdrant_url="http://qdrant",
                    batch_size=1,
                    integrity_path=integrity_path,
                )

            self.assertEqual(applied, 1)
            self.assertEqual(migration.split_markdown_bytes(path.read_bytes())[1], body_before)
            integrity = json.loads(integrity_path.read_text(encoding="utf-8"))
            self.assertEqual(integrity["before"], integrity["after"])
            conn = sqlite3.connect(db_path)
            row = conn.execute(
                "SELECT title, department FROM doc_meta WHERE news_item_id = ?",
                ("156751988",),
            ).fetchone()
            conn.close()
            self.assertEqual(row, ("국민 안전을 위한 정책", "행정안전부"))

    def test_apply_metadata_only_restores_markdown_on_failure(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data" / "md" / "2026" / "03" / "156751988.md"
            path.parent.mkdir(parents=True)
            path.write_text(
                "---\n"
                "id: '156751988'\n"
                "title: '옛 제목'\n"
                "department: '미상'\n"
                "approve_date: ''\n"
                "original_url: ''\n"
                "---\n\n"
                "# 문서 내부 제목\n\n본문\n",
                encoding="utf-8",
            )
            original = path.read_bytes()
            db_path = root / "govpress.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE doc_meta (
                    news_item_id TEXT PRIMARY KEY, title TEXT, department TEXT,
                    approve_date TEXT, source_url TEXT, indexed_at TEXT
                );
                CREATE TABLE briefing_chunks_meta (
                    news_item_id TEXT, department TEXT, approve_date TEXT
                );
                CREATE TABLE indexed_docs (
                    md_path TEXT PRIMARY KEY, md_mtime_ns INTEGER, md_size INTEGER
                );
                """
            )
            conn.execute(
                "INSERT INTO doc_meta VALUES (?, ?, ?, ?, ?, ?)",
                ("156751988", "옛 제목", "미상", "", "", ""),
            )
            conn.execute(
                "INSERT INTO briefing_chunks_meta VALUES (?, ?, ?)",
                ("156751988", "미상", ""),
            )
            stat = path.stat()
            conn.execute(
                "INSERT INTO indexed_docs VALUES (?, ?, ?)",
                ("/app/data/md/2026/03/156751988.md", stat.st_mtime_ns, stat.st_size),
            )
            conn.commit()
            conn.close()
            points = [
                {
                    "id": "point-1",
                    "vector": [0.1, 0.2],
                    "payload": {"news_item_id": "156751988"},
                }
            ]

            with mock.patch.object(
                migration,
                "qdrant_points",
                return_value=points,
            ), mock.patch.object(
                migration,
                "patch_sqlite",
                side_effect=RuntimeError("forced failure"),
            ):
                with self.assertRaisesRegex(RuntimeError, "forced failure"):
                    migration.apply_metadata_only(
                        [{"canonical": self.canonical, "md_path": str(path)}],
                        db_path=db_path,
                        qdrant_url="http://qdrant",
                        batch_size=1,
                        integrity_path=root / "integrity.jsonl",
                    )

            self.assertEqual(path.read_bytes(), original)

    def test_discover_bulk_inventory_respects_month_range_and_ids(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for month, identifier in (("02", "156700001"), ("03", "156700002")):
                path = root / "md" / "2026" / month / f"{identifier}.md"
                path.parent.mkdir(parents=True)
                path.touch()

            rows = migration.discover_bulk_inventory(
                root,
                (2026, 3),
                (2026, 3),
                wanted={"156700002"},
            )

            self.assertEqual(
                [(row["news_item_id"], row["year"], row["month"]) for row in rows],
                [("156700002", 2026, 3)],
            )

    def test_rewrite_bulk_markdown_preserves_exact_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "156751988.md"
            body = b"\n# source title\r\n\r\nbody\r\n"
            path.write_bytes(b"---\ntitle: 'old'\n---\n" + body)
            rows = [
                {
                    "md_path": str(path),
                    "canonical": self.canonical,
                    "body_bytes": len(body),
                    "body_sha256": migration.hashlib.sha256(body).hexdigest(),
                }
            ]

            migration.rewrite_bulk_markdown(rows, jobs=2)

            _, rewritten_body = migration.split_markdown_bytes(path.read_bytes())
            self.assertEqual(rewritten_body, body)

    def test_bulk_preflight_keeps_missing_qdrant_eligible_for_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "156751988.md"
            path.write_text(
                "---\nid: '156751988'\ntitle: 'old'\n---\nbody\n",
                encoding="utf-8",
            )
            inventory = [
                {
                    "news_item_id": "156751988",
                    "md_path": str(path),
                    "year": 2026,
                    "month": 3,
                }
            ]
            coverage = {
                "doc_ids": {"156751988"},
                "chunk_ids": {"156751988"},
                "indexed_paths": {
                    "156751988": "/app/data/md/2026/03/156751988.md"
                },
            }

            with mock.patch.object(
                migration,
                "bulk_sqlite_coverage",
                return_value=coverage,
            ), mock.patch.object(
                migration,
                "scan_qdrant_index",
                return_value=({}, 100),
            ), mock.patch.object(
                migration,
                "qdrant_vector_digest",
                return_value="digest",
            ):
                rows, recovery, _ = migration.bulk_preflight(
                    inventory,
                    {"156751988": self.canonical},
                    db_path=Path(directory) / "db",
                    qdrant_url="http://qdrant",
                )

            self.assertEqual(rows[0]["status"], "vectorization_required")
            self.assertEqual(rows[0]["reason"], "qdrant_points_missing")
            self.assertEqual(len(recovery), 1)

    def test_apply_bulk_sqlite_updates_staged_rows_in_one_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data" / "md" / "2026" / "03" / "156751988.md"
            path.parent.mkdir(parents=True)
            path.write_text("---\nid: '156751988'\n---\nbody\n", encoding="utf-8")
            db_path = root / "govpress.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE doc_meta (
                    news_item_id TEXT PRIMARY KEY, title TEXT, department TEXT,
                    approve_date TEXT, source_url TEXT, indexed_at TEXT
                );
                CREATE TABLE briefing_chunks_meta (
                    news_item_id TEXT, department TEXT, approve_date TEXT
                );
                CREATE TABLE indexed_docs (
                    md_path TEXT PRIMARY KEY, md_mtime_ns INTEGER, md_size INTEGER
                );
                """
            )
            conn.execute(
                "INSERT INTO doc_meta VALUES (?, ?, ?, ?, ?, ?)",
                ("156751988", "old", "미상", "", "", ""),
            )
            conn.executemany(
                "INSERT INTO briefing_chunks_meta VALUES (?, ?, ?)",
                [
                    ("156751988", "미상", ""),
                    ("156751988", "미상", ""),
                ],
            )
            indexed_path = "/app/data/md/2026/03/156751988.md"
            conn.execute(
                "INSERT INTO indexed_docs VALUES (?, ?, ?)",
                (indexed_path, 0, 0),
            )
            conn.commit()
            conn.close()
            rows = [
                {
                    "news_item_id": "156751988",
                    "md_path": str(path),
                    "indexed_md_path": indexed_path,
                    "canonical": self.canonical,
                }
            ]

            migration.apply_bulk_sqlite(db_path, rows)

            conn = sqlite3.connect(db_path)
            self.assertEqual(
                conn.execute(
                    "SELECT title, department, approve_date, source_url "
                    "FROM doc_meta WHERE news_item_id = '156751988'"
                ).fetchone(),
                (
                    self.canonical["title"],
                    self.canonical["department"],
                    self.canonical["approve_date"],
                    self.canonical["original_url"],
                ),
            )
            self.assertEqual(
                conn.execute(
                    "SELECT COUNT(*) FROM briefing_chunks_meta "
                    "WHERE department = '행정안전부'"
                ).fetchone()[0],
                2,
            )
            self.assertEqual(
                conn.execute(
                    "SELECT md_size FROM indexed_docs WHERE md_path = ?",
                    (indexed_path,),
                ).fetchone()[0],
                path.stat().st_size,
            )
            conn.close()

    def test_apply_bulk_qdrant_uses_batched_point_operations(self) -> None:
        rows = [
            {
                "canonical": self.canonical,
                "qdrant_point_ids": ["point-1", "point-2"],
            },
            {
                "canonical": {**self.canonical, "news_item_id": "156751999"},
                "qdrant_point_ids": ["point-3"],
            },
        ]

        with mock.patch.object(migration, "qdrant_json", return_value={}) as request:
            migration.apply_bulk_qdrant("http://qdrant", rows, batch_size=2)

        self.assertEqual(request.call_count, 1)
        url, payload = request.call_args.args
        self.assertTrue(url.endswith("/points/batch?wait=true"))
        self.assertEqual(len(payload["operations"]), 2)
        self.assertEqual(
            payload["operations"][0]["set_payload"]["points"],
            ["point-1", "point-2"],
        )
        self.assertEqual(
            payload["operations"][0]["set_payload"]["payload"]["department"],
            "행정안전부",
        )

    def test_bulk_followup_lists_separate_vectorization_and_deferred_ids(self) -> None:
        rows = [
            {
                "news_item_id": "1",
                "status": "vectorization_required",
                "reason": "qdrant_points_missing",
            },
            {
                "news_item_id": "2",
                "status": "invalid",
                "reason": "frontmatter_unparseable",
            },
            {
                "news_item_id": "3",
                "status": "deferred",
                "reason": "api_metadata_missing",
            },
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = migration.write_bulk_followup_lists(root, rows)

            self.assertEqual(
                (root / "server-v-vectorization.ids").read_text(encoding="ascii"),
                "1\n",
            )
            self.assertEqual(
                (root / "invalid.ids").read_text(encoding="ascii"),
                "2\n",
            )
            self.assertEqual(
                (root / "api-deferred.ids").read_text(encoding="ascii"),
                "3\n",
            )
            self.assertEqual(result["vectorization_count"], 1)


if __name__ == "__main__":
    unittest.main()
