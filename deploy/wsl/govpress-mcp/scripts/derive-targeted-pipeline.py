#!/usr/bin/env python3
"""High-throughput targeted derive for selected Markdown documents.

Preparation is process-parallel, TEI receives cross-document batches, and
SQLite writes are performed in bulk after durable Qdrant upserts.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib
import sqlite3
import time
import urllib.error
import urllib.parse

import grpc as grpc_runtime
from qdrant_client import QdrantClient, models

from dataclasses import dataclass
from datetime import UTC, datetime

import govpress_mcp.derive_hot as m


@dataclass
class Prepared:
    index: int
    md_path: pathlib.Path
    chunks: list[m.Chunk]
    frontmatter: dict[str, str]
    mtime_ns: int
    size: int


def prepare(index: int, md_path: pathlib.Path) -> Prepared:
    """Read and parse each Markdown file once in a worker process."""
    frontmatter, body = m.frontmatter.parse(md_path.read_text(encoding="utf-8"))
    paragraphs = [part.strip() for part in body.split("\n\n") if part.strip()]
    windows = m._paragraph_windows(paragraphs)
    chunks: list[m.Chunk] = []
    total = len(windows)
    for chunk_index, paragraph_group in enumerate(windows):
        chunk_body = "\n\n".join(paragraph_group).strip()
        if chunk_body:
            chunks.append(
                m.Chunk(
                    chunk_id=f"{frontmatter['id']}_{chunk_index:04d}",
                    news_item_id=frontmatter["id"],
                    approve_date=frontmatter["approve_date"],
                    department=frontmatter["department"],
                    entity_type=frontmatter["entity_type"],
                    chunk_index=chunk_index,
                    chunk_total=total,
                    body=chunk_body,
                )
            )
    stat = md_path.stat()
    return Prepared(index, md_path, chunks, frontmatter, stat.st_mtime_ns, stat.st_size)


def embed_with_retry(tei_url: str, texts: list[str], retries: int = 7) -> list[list[float]]:
    for attempt in range(retries):
        try:
            return m._tei_embed(tei_url, texts)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == retries - 1:
                raise
            time.sleep(min(8.0, 0.25 * (2 ** attempt)))
    raise RuntimeError("unreachable")


TRANSIENT_GRPC_CODES = {
    grpc_runtime.StatusCode.UNAVAILABLE,
    grpc_runtime.StatusCode.DEADLINE_EXCEEDED,
    grpc_runtime.StatusCode.RESOURCE_EXHAUSTED,
}


def api_owned_payload(frontmatter: dict[str, str]) -> dict[str, object]:
    required = (
        "title",
        "original_url",
        "metadata_source",
        "metadata_schema_version",
        "attachments_json",
    )
    missing = [
        field
        for field in required
        if not str(frontmatter.get(field, "")).strip()
    ]
    if missing:
        raise ValueError(f"API metadata missing fields: {','.join(missing)}")
    try:
        attachments = json.loads(frontmatter["attachments_json"])
        schema_version = int(frontmatter["metadata_schema_version"])
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("invalid API metadata frontmatter") from exc
    if not isinstance(attachments, list):
        raise ValueError("attachments_json must be a JSON array")
    if schema_version < 1:
        raise ValueError("metadata_schema_version must be positive")
    return {
        "title": frontmatter["title"],
        "original_url": frontmatter["original_url"],
        "metadata_source": frontmatter["metadata_source"],
        "metadata_schema_version": schema_version,
        "attachments": attachments,
        "attachments_json": frontmatter["attachments_json"],
    }


def qdrant_point(
    chunk: m.Chunk,
    vector: list[float],
    frontmatter: dict[str, str],
) -> models.PointStruct:
    payload: dict[str, object] = {
        "chunk_id": chunk.chunk_id,
        "news_item_id": chunk.news_item_id,
        "approve_date": chunk.approve_date,
        "department": chunk.department,
        "entity_type": chunk.entity_type,
        "chunk_index": chunk.chunk_index,
        "chunk_total": chunk.chunk_total,
    }
    payload.update(api_owned_payload(frontmatter))
    return models.PointStruct(
        id=str(m.uuid.uuid5(m.QDRANT_NAMESPACE, chunk.chunk_id)),
        vector=vector,
        payload=payload,
    )


def qdrant_upsert(client: QdrantClient, points: list[models.PointStruct], retries: int = 6) -> None:
    for attempt in range(retries):
        try:
            client.upsert(collection_name=m.COLLECTION_NAME, points=points, wait=True)
            return
        except grpc_runtime.RpcError as exc:
            if exc.code() not in TRANSIENT_GRPC_CODES or attempt == retries - 1:
                raise
            time.sleep(min(8.0, 0.25 * (2**attempt)))
    raise RuntimeError("unreachable")


def verify_qdrant(
    client: QdrantClient,
    expected_payloads: dict[str, dict[str, object]],
    batch_size: int,
) -> None:
    expected_ids = list(expected_payloads)
    found: set[str] = set()
    for offset in range(0, len(expected_ids), batch_size):
        records = client.retrieve(
            collection_name=m.COLLECTION_NAME,
            ids=expected_ids[offset : offset + batch_size],
            with_payload=True,
            with_vectors=False,
        )
        for record in records:
            point_id = str(record.id)
            found.add(point_id)
            expected = expected_payloads[point_id]
            payload = record.payload or {}
            if any(payload.get(key) != value for key, value in expected.items()):
                raise RuntimeError(f"Qdrant payload mismatch: {point_id}")
    missing = set(expected_ids) - found
    if missing:
        raise RuntimeError(f"Qdrant verification missing={len(missing)}")

def sqlite_bulk_upsert(conn: sqlite3.Connection, documents: list[Prepared]) -> dict[str, float]:
    """Replace a month atomically using one set-delete per target table."""
    now = datetime.now(UTC).isoformat()
    identifiers = sorted({doc.frontmatter["id"] for doc in documents})
    conn.execute(
        "CREATE TEMP TABLE IF NOT EXISTS derive_target_ids "
        "(news_item_id TEXT PRIMARY KEY) WITHOUT ROWID"
    )
    chunk_rows = [
        (chunk.chunk_id, chunk.news_item_id, chunk.chunk_index, chunk.chunk_total,
         chunk.approve_date, chunk.department, chunk.entity_type, chunk.body)
        for doc in documents for chunk in doc.chunks
    ]
    fts_rows = [
        (chunk.news_item_id, chunk.chunk_index, chunk.body)
        for doc in documents for chunk in doc.chunks
    ]
    timings: dict[str, float] = {}
    conn.execute("BEGIN IMMEDIATE")
    try:
        conn.execute("DELETE FROM derive_target_ids")
        conn.executemany(
            "INSERT INTO derive_target_ids(news_item_id) VALUES (?)",
            [(identifier,) for identifier in identifiers],
        )
        started = time.perf_counter()
        conn.execute(
            "DELETE FROM briefing_chunks_meta "
            "WHERE news_item_id IN (SELECT news_item_id FROM derive_target_ids)"
        )
        timings["sqlite_delete_meta"] = time.perf_counter() - started

        started = time.perf_counter()
        conn.execute(
            "DELETE FROM briefing_fts "
            "WHERE news_item_id IN (SELECT news_item_id FROM derive_target_ids)"
        )
        timings["sqlite_delete_fts"] = time.perf_counter() - started

        started = time.perf_counter()
        conn.executemany(
            """INSERT OR REPLACE INTO briefing_chunks_meta
               (chunk_id, news_item_id, chunk_index, chunk_total, approve_date, department, entity_type, body)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            chunk_rows,
        )
        timings["sqlite_insert_meta_chunks"] = time.perf_counter() - started

        started = time.perf_counter()
        conn.executemany(
            "INSERT INTO briefing_fts (news_item_id, chunk_index, body) VALUES (?, ?, ?)",
            fts_rows,
        )
        timings["sqlite_insert_fts"] = time.perf_counter() - started

        started = time.perf_counter()
        conn.executemany(
            """INSERT INTO indexed_docs (md_path, md_mtime_ns, md_size, chunk_count, indexed_at)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(md_path) DO UPDATE SET md_mtime_ns=excluded.md_mtime_ns,
                 md_size=excluded.md_size, chunk_count=excluded.chunk_count, indexed_at=excluded.indexed_at""",
            [(str(doc.md_path), doc.mtime_ns, doc.size, len(doc.chunks), now) for doc in documents],
        )
        conn.executemany(
            """INSERT INTO doc_meta
               (news_item_id, title, department, approve_date, entity_type, source_url, source_format, indexed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(news_item_id) DO UPDATE SET title=excluded.title,
                 department=excluded.department, approve_date=excluded.approve_date,
                 entity_type=excluded.entity_type, source_url=excluded.source_url,
                 source_format=excluded.source_format, indexed_at=excluded.indexed_at""",
            [(doc.frontmatter["id"], doc.frontmatter["title"], doc.frontmatter.get("department"),
              doc.frontmatter.get("approve_date"), doc.frontmatter.get("entity_type"),
              doc.frontmatter.get("original_url"), doc.frontmatter.get("source_format"), now)
             for doc in documents],
        )
        timings["sqlite_insert_doc_state"] = time.perf_counter() - started

        started = time.perf_counter()
        conn.commit()
        timings["sqlite_commit"] = time.perf_counter() - started
    except BaseException:
        conn.rollback()
        raise

    expected_docs = len(documents)
    expected_chunks = len(chunk_rows)
    counts = {
        "doc_meta": conn.execute(
            "SELECT COUNT(*) FROM doc_meta "
            "WHERE news_item_id IN (SELECT news_item_id FROM derive_target_ids)"
        ).fetchone()[0],
        "chunk_meta": conn.execute(
            "SELECT COUNT(*) FROM briefing_chunks_meta "
            "WHERE news_item_id IN (SELECT news_item_id FROM derive_target_ids)"
        ).fetchone()[0],
        "fts": conn.execute(
            "SELECT COUNT(*) FROM briefing_fts "
            "WHERE news_item_id IN (SELECT news_item_id FROM derive_target_ids)"
        ).fetchone()[0],
    }
    placeholders = ",".join("?" for _ in documents)
    counts["indexed_docs"] = conn.execute(
        f"SELECT COUNT(*) FROM indexed_docs WHERE md_path IN ({placeholders})",
        [str(doc.md_path) for doc in documents],
    ).fetchone()[0]
    expected = {
        "doc_meta": expected_docs,
        "indexed_docs": expected_docs,
        "chunk_meta": expected_chunks,
        "fts": expected_chunks,
    }
    if counts != expected:
        raise RuntimeError(f"SQLite verification counts={counts} expected={expected}")
    return timings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("members", type=pathlib.Path)
    parser.add_argument("data_root", type=pathlib.Path)
    parser.add_argument("db", type=pathlib.Path)
    parser.add_argument("qdrant")
    parser.add_argument("tei")
    parser.add_argument("checkpoint", type=int)
    parser.add_argument("--batch", type=int, default=512)
    parser.add_argument("--inflight", type=int, default=4)
    parser.add_argument("--prepare-workers", type=int, default=8)
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-index every member even when indexed_docs mtime and size match",
    )
    parser.add_argument(
        "--qdrant-only",
        action="store_true",
        help="skip SQLite rewrites after verified Qdrant upsert",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    data_root = m._canonical_data_root(args.data_root)
    entries = [pathlib.PurePosixPath(line) for line in args.members.read_text().splitlines() if line.lower().endswith(".hwpx")]
    candidates = {
        data_root / "md" / entry.parts[-3] / entry.parts[-2] / f"{entry.stem}.md"
        for entry in entries
    }
    missing = [path for path in candidates if not path.is_file()]
    if missing:
        raise SystemExit(f"member Markdown missing: {len(missing)}")
    m._check_health(args.tei)
    m._ensure_qdrant_collection(args.qdrant)
    conn = sqlite3.connect(args.db, timeout=600)
    conn.execute("PRAGMA busy_timeout = 600000")
    try:
        schema_started = time.perf_counter()
        m._ensure_sqlite_schema(conn)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_briefing_chunks_meta_news_item_id "
            "ON briefing_chunks_meta(news_item_id)"
        )
        conn.commit()
        print(
            f"targeted_pipeline schema_seconds={time.perf_counter()-schema_started:.1f}",
            flush=True,
        )
        stale = sorted(
            candidates
            if args.force
            else (path for path in candidates if m._needs_reindex(conn, path))
        )
        print(f"targeted_pipeline matched={len(candidates)} stale={len(stale)}", flush=True)
        if not stale:
            return 0
        with concurrent.futures.ProcessPoolExecutor(max_workers=args.prepare_workers) as pool:
            futures = [pool.submit(prepare, index, path) for index, path in enumerate(stale)]
            documents = [future.result() for future in concurrent.futures.as_completed(futures)]
        documents.sort(key=lambda doc: doc.index)
        print(f"targeted_pipeline prepared={len(documents)} seconds={time.perf_counter()-started:.1f}", flush=True)
        flat_chunks = [
            (doc_index, chunk_index, chunk.body)
            for doc_index, doc in enumerate(documents)
            for chunk_index, chunk in enumerate(doc.chunks)
        ]
        jobs = [flat_chunks[offset:offset + 64] for offset in range(0, len(flat_chunks), 64)]
        vectors: list[list[list[float] | None]] = [[None] * len(doc.chunks) for doc in documents]
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(args.inflight, 4)) as pool:
            futures = {pool.submit(embed_with_retry, args.tei, [body for _, _, body in job]): job for job in jobs}
            for future in concurrent.futures.as_completed(futures):
                job = futures[future]
                result = future.result()
                if len(result) != len(job):
                    raise RuntimeError("TEI embed response size mismatch")
                for (doc_index, chunk_index, _body), vector in zip(job, result, strict=True):
                    vectors[doc_index][chunk_index] = vector
        embedded: list[tuple[Prepared, list[list[float]]]] = []
        for doc, doc_vectors in zip(documents, vectors, strict=True):
            if any(vector is None for vector in doc_vectors):
                raise RuntimeError(f"missing embedding: {doc.md_path}")
            embedded.append((doc, list(doc_vectors)))
        print(f"targeted_pipeline embedded_chunks={sum(len(doc.chunks) for doc in documents)} seconds={time.perf_counter()-started:.1f}", flush=True)
        point_rows = [
            (document.frontmatter, chunk, vector)
            for document, doc_vectors in embedded
            for chunk, vector in zip(document.chunks, doc_vectors, strict=True)
        ]
        parsed = urllib.parse.urlparse(args.qdrant)
        client = QdrantClient(
            host=parsed.hostname or "qdrant",
            port=parsed.port or 6333,
            grpc_port=6334,
            prefer_grpc=True,
            timeout=300,
        )
        try:
            qdrant_started = time.perf_counter()
            expected_payloads: dict[str, dict[str, object]] = {}
            for offset in range(0, len(point_rows), args.batch):
                points = [
                    qdrant_point(chunk, vector, frontmatter)
                    for frontmatter, chunk, vector in point_rows[
                        offset : offset + args.batch
                    ]
                ]
                expected_payloads.update(
                    {
                        str(point.id): dict(point.payload or {})
                        for point in points
                    }
                )
                batch_started = time.perf_counter()
                qdrant_upsert(client, points)
                print(
                    f"targeted_pipeline qdrant_batch={offset//args.batch + 1} "
                    f"points={len(points)} seconds={time.perf_counter()-batch_started:.1f}",
                    flush=True,
                )
            qdrant_seconds = time.perf_counter() - qdrant_started
            verify_started = time.perf_counter()
            verify_qdrant(client, expected_payloads, args.batch)
            qdrant_verify_seconds = time.perf_counter() - verify_started
        finally:
            client.close()
        print(
            f"targeted_pipeline qdrant_seconds={qdrant_seconds:.1f} "
            f"qdrant_verify_seconds={qdrant_verify_seconds:.1f}",
            flush=True,
        )
        if args.qdrant_only:
            print("targeted_pipeline sqlite_skipped=qdrant_only", flush=True)
        else:
            sqlite_started = time.perf_counter()
            sqlite_timings = sqlite_bulk_upsert(conn, documents)
            sqlite_seconds = time.perf_counter() - sqlite_started
            for name, seconds in sqlite_timings.items():
                print(f"targeted_pipeline {name}_seconds={seconds:.3f}", flush=True)
            checkpoint_started = time.perf_counter()
            checkpoint = conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
            print(
                f"targeted_pipeline sqlite_seconds={sqlite_seconds:.1f} "
                f"wal_checkpoint_seconds={time.perf_counter()-checkpoint_started:.1f} "
                f"wal_checkpoint={checkpoint}",
                flush=True,
            )
        print(f"targeted_pipeline complete={len(documents)} chunks={sum(len(doc.chunks) for doc in documents)} seconds={time.perf_counter()-started:.1f}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
