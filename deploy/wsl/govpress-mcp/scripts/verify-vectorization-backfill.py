#!/usr/bin/env python3
"""Verify a targeted vector backfill across Markdown, SQLite, and Qdrant."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sqlite3

from qdrant_client import QdrantClient

import govpress_mcp.derive_hot as derive


ID_RE = re.compile(r"^(\d+)(?:_|$)")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ids_file", type=Path)
    parser.add_argument("data_root", type=Path)
    parser.add_argument("db", type=Path)
    parser.add_argument("qdrant_host")
    args = parser.parse_args()

    ids = {
        line.strip()
        for line in args.ids_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    expected_payloads: dict[str, dict[str, object]] = {}
    duplicate_markdown: set[str] = set()
    for path in (args.data_root / "md").glob("*/*/*.md"):
        match = ID_RE.match(path.stem)
        if not match or match.group(1) not in ids:
            continue
        identifier = match.group(1)
        if identifier in expected_payloads:
            duplicate_markdown.add(identifier)
            continue
        frontmatter, _ = derive.frontmatter.parse(path.read_text(encoding="utf-8"))
        attachments = json.loads(frontmatter["attachments_json"])
        expected_payloads[identifier] = {
            "news_item_id": identifier,
            "title": frontmatter["title"],
            "department": frontmatter["department"],
            "approve_date": frontmatter["approve_date"],
            "entity_type": frontmatter["entity_type"],
            "original_url": frontmatter["original_url"],
            "metadata_source": frontmatter["metadata_source"],
            "metadata_schema_version": int(frontmatter["metadata_schema_version"]),
            "attachments": attachments,
            "attachments_json": frontmatter["attachments_json"],
        }

    conn = sqlite3.connect(args.db)
    try:
        conn.execute(
            "CREATE TEMP TABLE verify_ids "
            "(news_item_id TEXT PRIMARY KEY) WITHOUT ROWID"
        )
        conn.executemany(
            "INSERT INTO verify_ids VALUES (?)",
            [(identifier,) for identifier in ids],
        )
        sqlite_missing = {
            "doc_meta": conn.execute(
                "SELECT COUNT(*) FROM verify_ids v LEFT JOIN doc_meta d "
                "ON d.news_item_id=v.news_item_id WHERE d.news_item_id IS NULL"
            ).fetchone()[0],
            "briefing_chunks_meta": conn.execute(
                "SELECT COUNT(*) FROM verify_ids v LEFT JOIN "
                "(SELECT DISTINCT news_item_id FROM briefing_chunks_meta) c "
                "ON c.news_item_id=v.news_item_id WHERE c.news_item_id IS NULL"
            ).fetchone()[0],
            "briefing_fts": conn.execute(
                "SELECT COUNT(*) FROM verify_ids v LEFT JOIN "
                "(SELECT DISTINCT news_item_id FROM briefing_fts) f "
                "ON f.news_item_id=v.news_item_id WHERE f.news_item_id IS NULL"
            ).fetchone()[0],
        }
        sqlite_chunk_counts = {
            str(identifier): int(count)
            for identifier, count in conn.execute(
                "SELECT c.news_item_id, COUNT(*) FROM briefing_chunks_meta c "
                "JOIN verify_ids v ON v.news_item_id=c.news_item_id "
                "GROUP BY c.news_item_id"
            )
        }
        indexed_ids: set[str] = set()
        for (raw_path,) in conn.execute("SELECT md_path FROM indexed_docs"):
            match = ID_RE.match(Path(str(raw_path)).stem)
            if match and match.group(1) in ids:
                indexed_ids.add(match.group(1))
        sqlite_missing["indexed_docs"] = len(ids - indexed_ids)
    finally:
        conn.close()

    qdrant_counts: dict[str, int] = {}
    payload_mismatches = 0
    client = QdrantClient(host=args.qdrant_host, port=6333, grpc_port=6334)
    try:
        offset = None
        while True:
            points, offset = client.scroll(
                collection_name=derive.COLLECTION_NAME,
                limit=1000,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for point in points:
                payload = point.payload or {}
                identifier = str(payload.get("news_item_id", ""))
                if identifier not in ids:
                    continue
                qdrant_counts[identifier] = qdrant_counts.get(identifier, 0) + 1
                expected = expected_payloads[identifier]
                if any(payload.get(key) != value for key, value in expected.items()):
                    payload_mismatches += 1
            if offset is None:
                break
    finally:
        client.close()

    qdrant_missing = len(ids - qdrant_counts.keys())
    chunk_count_mismatches = sum(
        1
        for identifier in ids
        if qdrant_counts.get(identifier, 0)
        != sqlite_chunk_counts.get(identifier, 0)
    )
    result = {
        "target_ids": len(ids),
        "markdown_found": len(expected_payloads),
        "markdown_missing": len(ids - expected_payloads.keys()),
        "markdown_duplicates": len(duplicate_markdown),
        "sqlite_missing": sqlite_missing,
        "qdrant_missing": qdrant_missing,
        "qdrant_payload_mismatches": payload_mismatches,
        "qdrant_chunk_count_mismatches": chunk_count_mismatches,
        "qdrant_points": sum(qdrant_counts.values()),
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    failures = [
        result["markdown_missing"],
        result["markdown_duplicates"],
        *sqlite_missing.values(),
        qdrant_missing,
        payload_mismatches,
        chunk_count_mismatches,
    ]
    return 1 if any(failures) else 0


if __name__ == "__main__":
    raise SystemExit(main())
