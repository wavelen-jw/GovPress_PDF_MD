#!/usr/bin/env python3
"""Reconcile published Markdown and vector metadata with the official API.

The default mode only writes a JSONL manifest for Markdown already present in
the vector corpus. With ``--apply-metadata-only``, parseable documents are
patched without calling the embedding service. Source-body/API differences are
reported for review; only documents that cannot be patched safely are emitted
for selective reconversion.
"""

from __future__ import annotations

import argparse
import base64
import calendar
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
from html import unescape
import json
import os
from pathlib import Path
import re
import sqlite3
import tarfile
import tempfile
import time
from typing import Any, Iterator
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


API_URL = "https://apis.data.go.kr/1371000/pressReleaseService/pressReleaseList"
COLLECTION = "briefing_chunks"
SCHEMA_VERSION = 1
METADATA_SOURCE = "policy-briefing-api"
CANONICAL_FIELDS = ("title", "department", "approve_date", "original_url")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
NEWS_ITEM_ID_RE = re.compile(r"^(?P<id>\d+)(?:_|$)")
PRESS_LABEL_RE = re.compile(
    r"^(?P<department>[^#\n]+?)[ \t]+"
    r"(?:공동|합동|정부합동|관계부처합동)?"
    r"(?:보도자료|보도참고자료|보도설명자료|설명자료|동정자료)\s*/?$",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int, nargs="?")
    parser.add_argument("month", type=int, nargs="?")
    parser.add_argument("--ids-file", type=Path)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--db", type=Path)
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--apply-metadata-only", action="store_true")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--bulk-batch-size", type=int, default=250)
    parser.add_argument(
        "--overwrite-all",
        nargs=2,
        metavar=("START_MONTH", "END_MONTH"),
        help="overwrite API-owned metadata for every local document in YYYY-MM range",
    )
    parser.add_argument(
        "--apply-overwrite",
        action="store_true",
        help="apply --overwrite-all after preflight and one global snapshot",
    )
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--refresh-api-cache", action="store_true")
    parser.add_argument(
        "--api-cache-dir",
        type=Path,
        help="reuse monthly API cache from another overwrite run",
    )
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    if args.bulk_batch_size < 1:
        parser.error("--bulk-batch-size must be positive")
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.overwrite_all:
        if args.year is not None or args.month is not None:
            parser.error("YEAR and MONTH cannot be combined with --overwrite-all")
        args.start_month = parse_month_key(args.overwrite_all[0])
        args.end_month = parse_month_key(args.overwrite_all[1])
        if args.start_month > args.end_month:
            parser.error("START_MONTH must not be after END_MONTH")
        if args.apply_metadata_only:
            parser.error("--apply-metadata-only cannot be combined with --overwrite-all")
    else:
        if args.year is None or args.month is None:
            parser.error("YEAR and MONTH are required unless --overwrite-all is used")
        if not 1 <= args.month <= 12:
            parser.error("MONTH must be between 1 and 12")
        if args.apply_overwrite:
            parser.error("--apply-overwrite requires --overwrite-all")
    args.db = args.db or args.data_root / "govpress.db"
    args.output_dir = args.output_dir or args.data_root / "fetch-log" / "metadata-migration"
    return args


def main() -> int:
    args = parse_args()
    if args.overwrite_all:
        return run_bulk_overwrite(args)
    wanted = load_ids(args.ids_file)
    if wanted is None:
        wanted = discover_local_ids(args.data_root, args.year, args.month)
    items = fetch_month(args.year, args.month, wanted=wanted)
    rows = classify_month(args.data_root, args.year, args.month, items, wanted=wanted)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.year:04d}-{args.month:02d}"
    manifest_path = args.output_dir / f"{stem}.jsonl"
    write_jsonl(manifest_path, rows)
    rerender_ids = [
        row["news_item_id"] for row in rows if row["classification"] == "rerender_reembed"
    ]
    (args.output_dir / f"{stem}-rerender-reembed.ids").write_text(
        "".join(f"{identifier}\n" for identifier in rerender_ids),
        encoding="utf-8",
    )

    applied = 0
    if args.apply_metadata_only:
        candidates = [row for row in rows if row["classification"] == "metadata_only"]
        if candidates:
            applied = apply_with_snapshot(args, stem, candidates)

    counts: dict[str, int] = {}
    for row in rows:
        key = str(row["classification"])
        counts[key] = counts.get(key, 0) + 1
    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "counts": counts,
                "metadata_only_applied": applied,
                "rerender_ids": len(rerender_ids),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


def parse_month_key(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d{4})-(\d{2})", value)
    if not match:
        raise argparse.ArgumentTypeError(f"invalid month: {value}")
    year, month = (int(part) for part in match.groups())
    if not 1 <= month <= 12:
        raise argparse.ArgumentTypeError(f"invalid month: {value}")
    return year, month


def run_bulk_overwrite(args: argparse.Namespace) -> int:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    state_path = args.output_dir / "bulk-overwrite-state.json"
    manifest_path = args.output_dir / "bulk-overwrite-manifest.jsonl"
    recovery_path = args.output_dir / "bulk-overwrite-frontmatter-recovery.jsonl"
    state = load_json(state_path) if state_path.exists() else {}
    wanted = load_ids(args.ids_file)
    scope = {
        "start_month": month_key(args.start_month),
        "end_month": month_key(args.end_month),
        "wanted_sha256": hash_ids(wanted),
    }
    if state and any(state.get(key) != value for key, value in scope.items()):
        raise SystemExit(
            "output directory belongs to a different overwrite scope; "
            "use a new --output-dir"
        )

    if manifest_path.exists() and state.get("preflight_complete"):
        rows = read_jsonl(manifest_path)
    else:
        inventory = discover_bulk_inventory(
            args.data_root,
            args.start_month,
            args.end_month,
            wanted=wanted,
        )
        canonical, api_failures = load_bulk_canonical(args, inventory)
        rows, recovery, qdrant_summary = bulk_preflight(
            inventory,
            canonical,
            db_path=args.db,
            qdrant_url=args.qdrant_url,
            failed_months={
                (failure["year"], failure["month"]) for failure in api_failures
            },
        )
        write_jsonl(manifest_path, rows)
        write_jsonl(recovery_path, recovery)
        state = {
            "created_at": dt.datetime.now(dt.UTC).isoformat(),
            **scope,
            "inventory_count": len(inventory),
            "api_failed_days": api_failures,
            "preflight_complete": True,
            "point_count_before": qdrant_summary["point_count"],
            "vector_sample_ids": qdrant_summary["vector_sample_ids"],
            "vector_sample_sha256": qdrant_summary["vector_sample_sha256"],
            "manifest": str(manifest_path),
            "frontmatter_recovery": str(recovery_path),
            "status": "preflight_complete",
        }
        atomic_write_json(state_path, state)

    counts = count_bulk_statuses(rows)
    followups = write_bulk_followup_lists(args.output_dir, rows)
    state.update(followups)
    atomic_write_json(state_path, state)
    if not args.apply_overwrite:
        print_bulk_result(state_path, manifest_path, counts, applied=False)
        return 0

    eligible = [row for row in rows if row["status"] == "eligible"]
    metadata_rows = [
        row
        for row in rows
        if row["status"] in {"eligible", "vectorization_required"}
    ]
    state.pop("error", None)
    state.pop("failed_at", None)
    try:
        if not state.get("snapshot_complete"):
            snapshot = create_bulk_snapshot(args, recovery_path, len(metadata_rows))
            state.update(snapshot)
            state.update({"snapshot_complete": True, "status": "snapshot_complete"})
            atomic_write_json(state_path, state)

        if not state.get("markdown_complete"):
            rewrite_bulk_markdown(metadata_rows, jobs=args.jobs)
            state.update(
                {
                    "markdown_complete": True,
                    "markdown_completed_at": dt.datetime.now(dt.UTC).isoformat(),
                    "status": "markdown_complete",
                }
            )
            atomic_write_json(state_path, state)

        if not state.get("sqlite_complete"):
            apply_bulk_sqlite(args.db, metadata_rows)
            state.update(
                {
                    "sqlite_complete": True,
                    "sqlite_completed_at": dt.datetime.now(dt.UTC).isoformat(),
                    "status": "sqlite_complete",
                }
            )
            atomic_write_json(state_path, state)

        if not state.get("qdrant_complete"):
            apply_bulk_qdrant(
                args.qdrant_url,
                eligible,
                batch_size=args.bulk_batch_size,
            )
            state.update(
                {
                    "qdrant_complete": True,
                    "qdrant_completed_at": dt.datetime.now(dt.UTC).isoformat(),
                    "status": "qdrant_complete",
                }
            )
            atomic_write_json(state_path, state)

        verification = verify_bulk_result(
            args.db,
            args.qdrant_url,
            metadata_rows,
            qdrant_rows=eligible,
            point_count_before=int(state["point_count_before"]),
            vector_sample_ids=list(state["vector_sample_ids"]),
            vector_sample_sha256=str(state["vector_sample_sha256"]),
        )
    except BaseException as exc:
        state.update(
            {
                "status": "failed",
                "failed_at": dt.datetime.now(dt.UTC).isoformat(),
                "error": f"{exc.__class__.__name__}: {exc}",
            }
        )
        atomic_write_json(state_path, state)
        raise

    state.update(
        {
            "status": "completed",
            "completed_at": dt.datetime.now(dt.UTC).isoformat(),
            "verified": verification,
        }
    )
    atomic_write_json(state_path, state)
    print_bulk_result(state_path, manifest_path, counts, applied=True)
    return 0


def month_key(value: tuple[int, int]) -> str:
    return f"{value[0]:04d}-{value[1]:02d}"


def hash_ids(values: set[str] | None) -> str:
    marker = "*" if values is None else "\n".join(sorted(values))
    return hashlib.sha256(marker.encode("ascii")).hexdigest()


def iter_months(
    start: tuple[int, int],
    end: tuple[int, int],
) -> Iterator[tuple[int, int]]:
    year, month = start
    while (year, month) <= end:
        yield year, month
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1


def discover_bulk_inventory(
    data_root: Path,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    wanted: set[str] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for year, month in iter_months(start, end):
        month_root = data_root / "md" / f"{year:04d}" / f"{month:02d}"
        if not month_root.is_dir():
            continue
        for path in sorted(month_root.glob("*.md")):
            match = NEWS_ITEM_ID_RE.match(path.stem)
            if not match:
                continue
            identifier = match.group("id")
            if wanted is not None and identifier not in wanted:
                continue
            rows.append(
                {
                    "news_item_id": identifier,
                    "md_path": str(path),
                    "year": year,
                    "month": month,
                }
            )
    return rows


def load_bulk_canonical(
    args: argparse.Namespace,
    inventory: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    by_month: dict[tuple[int, int], set[str]] = {}
    for row in inventory:
        by_month.setdefault((row["year"], row["month"]), set()).add(row["news_item_id"])
    cache_root = args.api_cache_dir or args.output_dir / "api-cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []
    for (year, month), wanted in sorted(by_month.items()):
        cache_path = cache_root / f"{year:04d}-{month:02d}.json"
        wanted_sha256 = hashlib.sha256(
            "\n".join(sorted(wanted)).encode("ascii")
        ).hexdigest()
        cached = load_json(cache_path) if cache_path.exists() else {}
        cached_items = list(cached.get("items", []))
        cached_ids = {item["news_item_id"] for item in cached_items}
        if (
            not args.refresh_api_cache
            and (
                wanted <= cached_ids
                or (
                    cached.get("wanted_sha256") == wanted_sha256
                    and not cached.get("failed_days")
                )
            )
        ):
            items = [item for item in cached_items if item["news_item_id"] in wanted]
            failed_days: list[dict[str, Any]] = []
        else:
            month_items, failed_days = fetch_month_parallel(
                year,
                month,
                wanted=wanted,
                jobs=args.jobs,
            )
            items = list(month_items.values())
            atomic_write_json(
                cache_path,
                {
                    "year": year,
                    "month": month,
                    "wanted_count": len(wanted),
                    "wanted_sha256": wanted_sha256,
                    "items": items,
                    "failed_days": failed_days,
                },
            )
        result.update({item["news_item_id"]: item for item in items})
        failures.extend(failed_days)
    return result, failures


def fetch_month_parallel(
    year: int,
    month: int,
    *,
    wanted: set[str],
    jobs: int,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    service_key = os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY", "").strip()
    if not service_key:
        raise SystemExit("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY is not set")
    days = [
        dt.date(year, month, day)
        for day in range(1, calendar.monthrange(year, month)[1] + 1)
    ]
    result: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, Any]] = []

    def fetch_target(
        target: dt.date,
    ) -> tuple[dt.date, list[dict[str, Any]] | None, str | None]:
        try:
            return target, fetch_day(target, service_key), None
        except (urllib.error.URLError, TimeoutError, ET.ParseError) as exc:
            return target, None, f"{exc.__class__.__name__}: {exc}"

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        for target, items, error in executor.map(fetch_target, days):
            if error is not None:
                failures.append(
                    {
                        "year": target.year,
                        "month": target.month,
                        "day": target.day,
                        "error": error,
                    }
                )
                continue
            assert items is not None
            for item in items:
                identifier = item["news_item_id"]
                if identifier in wanted:
                    result[identifier] = item
    return result, failures


def bulk_preflight(
    inventory: list[dict[str, Any]],
    canonical: dict[str, dict[str, Any]],
    *,
    db_path: Path,
    qdrant_url: str,
    failed_months: set[tuple[int, int]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    failed_months = failed_months or set()
    duplicate_ids = {
        identifier
        for identifier, count in count_values(
            row["news_item_id"] for row in inventory
        ).items()
        if count > 1
    }
    db_coverage = bulk_sqlite_coverage(db_path)
    wanted_ids = {row["news_item_id"] for row in inventory}
    point_map, point_count = scan_qdrant_index(qdrant_url, wanted_ids)
    rows: list[dict[str, Any]] = []
    recovery: list[dict[str, Any]] = []

    for item in inventory:
        identifier = item["news_item_id"]
        row = {**item, "canonical": canonical.get(identifier)}
        reasons: list[str] = []
        if identifier in duplicate_ids:
            reasons.append("duplicate_markdown_id")
        if row["canonical"] is None:
            reason = (
                "api_metadata_unavailable_after_day_failure"
                if (row["year"], row["month"]) in failed_months
                else "api_metadata_missing"
            )
            row.update({"status": "deferred", "reason": reason})
            rows.append(row)
            continue
        try:
            document = Path(row["md_path"]).read_bytes()
            header, body = split_markdown_bytes(document)
            parse_markdown("---\n" + header.decode("utf-8") + "\n---\n")
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            row.update(
                {
                    "status": "invalid",
                    "reason": "frontmatter_unparseable",
                    "detail": str(exc),
                }
            )
            rows.append(row)
            continue
        if identifier not in db_coverage["doc_ids"]:
            reasons.append("sqlite_doc_meta_missing")
        if identifier not in db_coverage["chunk_ids"]:
            reasons.append("sqlite_chunks_missing")
        indexed_path = db_coverage["indexed_paths"].get(identifier)
        if indexed_path is None:
            reasons.append("sqlite_indexed_doc_missing")
        point_ids = point_map.get(identifier, [])
        if not point_ids:
            reasons.append("qdrant_points_missing")
        if reasons and reasons != ["qdrant_points_missing"]:
            row.update({"status": "invalid", "reason": ",".join(reasons)})
        else:
            status = "vectorization_required" if reasons else "eligible"
            row.update(
                {
                    "status": status,
                    "reason": "qdrant_points_missing" if reasons else None,
                    "indexed_md_path": indexed_path,
                    "qdrant_point_ids": point_ids,
                    "body_bytes": len(body),
                    "body_sha256": hashlib.sha256(body).hexdigest(),
                }
            )
            recovery.append(
                {
                    "news_item_id": identifier,
                    "md_path": row["md_path"],
                    "original_file_sha256": hashlib.sha256(document).hexdigest(),
                    "original_header_base64": base64.b64encode(header).decode("ascii"),
                    "body_bytes": len(body),
                    "body_sha256": row["body_sha256"],
                }
            )
        rows.append(row)

    all_point_ids = sorted(
        (point_id for ids in point_map.values() for point_id in ids),
        key=str,
    )
    sample_ids = all_point_ids[: min(64, len(all_point_ids))]
    return (
        rows,
        recovery,
        {
            "point_count": point_count,
            "vector_sample_ids": sample_ids,
            "vector_sample_sha256": qdrant_vector_digest(qdrant_url, sample_ids),
        },
    )


def count_values(values: Iterator[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def bulk_sqlite_coverage(db_path: Path) -> dict[str, Any]:
    conn = sqlite3.connect(db_path)
    try:
        doc_ids = {str(row[0]) for row in conn.execute("SELECT news_item_id FROM doc_meta")}
        chunk_ids = {
            str(row[0])
            for row in conn.execute("SELECT DISTINCT news_item_id FROM briefing_chunks_meta")
        }
        indexed_paths: dict[str, str] = {}
        duplicate_indexed: set[str] = set()
        for (raw_path,) in conn.execute("SELECT md_path FROM indexed_docs"):
            path = str(raw_path)
            match = NEWS_ITEM_ID_RE.match(Path(path).stem)
            if not match:
                continue
            identifier = match.group("id")
            if identifier in indexed_paths:
                duplicate_indexed.add(identifier)
            else:
                indexed_paths[identifier] = path
        for identifier in duplicate_indexed:
            indexed_paths.pop(identifier, None)
        return {
            "doc_ids": doc_ids,
            "chunk_ids": chunk_ids,
            "indexed_paths": indexed_paths,
        }
    finally:
        conn.close()


def scan_qdrant_index(
    qdrant_url: str,
    wanted_ids: set[str],
) -> tuple[dict[str, list[str | int]], int]:
    point_map: dict[str, list[str | int]] = {}
    point_count = 0
    for points in qdrant_scroll_pages(qdrant_url):
        point_count += len(points)
        for point in points:
            identifier = str(point.get("payload", {}).get("news_item_id", ""))
            if identifier in wanted_ids:
                point_map.setdefault(identifier, []).append(point["id"])
    return point_map, point_count


def qdrant_scroll_pages(
    qdrant_url: str,
    *,
    limit: int = 1000,
) -> Iterator[list[dict[str, Any]]]:
    offset: str | int | None = None
    while True:
        payload: dict[str, Any] = {
            "limit": limit,
            "with_payload": True,
            "with_vector": False,
        }
        if offset is not None:
            payload["offset"] = offset
        response = qdrant_json(
            f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/points/scroll",
            payload,
            method="POST",
        )
        result = response.get("result", {})
        points = list(result.get("points", []))
        yield points
        offset = result.get("next_page_offset")
        if offset is None:
            break


def qdrant_vector_digest(
    qdrant_url: str,
    point_ids: list[str | int],
) -> str:
    if not point_ids:
        return hashlib.sha256(b"[]").hexdigest()
    response = qdrant_json(
        f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/points",
        {
            "ids": point_ids,
            "with_payload": False,
            "with_vector": True,
        },
        method="POST",
    )
    vectors = [
        {"id": str(point["id"]), "vector": point.get("vector")}
        for point in sorted(response.get("result", []), key=lambda point: str(point["id"]))
    ]
    return hashlib.sha256(
        json.dumps(vectors, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()


def create_bulk_snapshot(
    args: argparse.Namespace,
    recovery_path: Path,
    candidate_count: int,
) -> dict[str, Any]:
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = args.output_dir / "snapshots" / f"bulk-{stamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    sqlite_path = snapshot_dir / "govpress.db.bak"
    recovery_copy = snapshot_dir / recovery_path.name
    snapshot_sqlite(args.db, sqlite_path)
    atomic_write(recovery_copy, recovery_path.read_bytes())
    return {
        "snapshot_created_at": dt.datetime.now(dt.UTC).isoformat(),
        "candidate_count": candidate_count,
        "sqlite_backup": str(sqlite_path),
        "frontmatter_recovery_snapshot": str(recovery_copy),
        "qdrant_snapshot": create_qdrant_snapshot(args.qdrant_url),
    }


def rewrite_bulk_markdown(rows: list[dict[str, Any]], *, jobs: int) -> None:
    def rewrite(row: dict[str, Any]) -> None:
        path = Path(row["md_path"])
        replace_frontmatter(path, row["canonical"])
        _, body = split_markdown_bytes(path.read_bytes())
        if len(body) != row["body_bytes"]:
            raise RuntimeError(f"Markdown body length changed: {path}")
        if hashlib.sha256(body).hexdigest() != row["body_sha256"]:
            raise RuntimeError(f"Markdown body hash changed: {path}")

    with ThreadPoolExecutor(max_workers=jobs) as executor:
        for _ in executor.map(rewrite, rows):
            pass


def stage_bulk_metadata(
    conn: sqlite3.Connection,
    rows: list[dict[str, Any]],
) -> None:
    conn.execute("DROP TABLE IF EXISTS temp.bulk_api_metadata")
    conn.execute(
        """
        CREATE TEMP TABLE bulk_api_metadata (
            news_item_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            approve_date TEXT NOT NULL,
            original_url TEXT NOT NULL,
            indexed_md_path TEXT NOT NULL,
            md_mtime_ns INTEGER NOT NULL,
            md_size INTEGER NOT NULL
        )
        """
    )
    conn.execute(
        "CREATE UNIQUE INDEX bulk_api_metadata_indexed_path "
        "ON bulk_api_metadata(indexed_md_path)"
    )
    conn.executemany(
        "INSERT INTO bulk_api_metadata VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        [
            (
                row["news_item_id"],
                row["canonical"]["title"],
                row["canonical"]["department"],
                row["canonical"]["approve_date"],
                row["canonical"]["original_url"],
                row["indexed_md_path"],
                Path(row["md_path"]).stat().st_mtime_ns,
                Path(row["md_path"]).stat().st_size,
            )
            for row in rows
        ],
    )


def apply_bulk_sqlite(db_path: Path, rows: list[dict[str, Any]]) -> None:
    conn = sqlite3.connect(db_path, timeout=600)
    conn.execute("PRAGMA busy_timeout = 600000")
    try:
        conn.execute("BEGIN IMMEDIATE")
        stage_bulk_metadata(conn, rows)
        indexed_at = dt.datetime.now(dt.UTC).isoformat()
        doc_result = conn.execute(
            """
            UPDATE doc_meta
            SET title = (SELECT title FROM bulk_api_metadata b
                         WHERE b.news_item_id = doc_meta.news_item_id),
                department = (SELECT department FROM bulk_api_metadata b
                              WHERE b.news_item_id = doc_meta.news_item_id),
                approve_date = (SELECT approve_date FROM bulk_api_metadata b
                                WHERE b.news_item_id = doc_meta.news_item_id),
                source_url = (SELECT original_url FROM bulk_api_metadata b
                              WHERE b.news_item_id = doc_meta.news_item_id),
                indexed_at = ?
            WHERE news_item_id IN (SELECT news_item_id FROM bulk_api_metadata)
            """,
            (indexed_at,),
        )
        chunk_result = conn.execute(
            """
            UPDATE briefing_chunks_meta
            SET department = (SELECT department FROM bulk_api_metadata b
                              WHERE b.news_item_id = briefing_chunks_meta.news_item_id),
                approve_date = (SELECT approve_date FROM bulk_api_metadata b
                                WHERE b.news_item_id = briefing_chunks_meta.news_item_id)
            WHERE news_item_id IN (SELECT news_item_id FROM bulk_api_metadata)
            """
        )
        indexed_result = conn.execute(
            """
            UPDATE indexed_docs
            SET md_mtime_ns = (SELECT md_mtime_ns FROM bulk_api_metadata b
                              WHERE b.indexed_md_path = indexed_docs.md_path),
                md_size = (SELECT md_size FROM bulk_api_metadata b
                           WHERE b.indexed_md_path = indexed_docs.md_path)
            WHERE md_path IN (SELECT indexed_md_path FROM bulk_api_metadata)
            """
        )
        expected_chunks = conn.execute(
            "SELECT COUNT(*) FROM briefing_chunks_meta "
            "WHERE news_item_id IN (SELECT news_item_id FROM bulk_api_metadata)"
        ).fetchone()[0]
        if doc_result.rowcount != len(rows):
            raise RuntimeError(
                f"SQLite doc_meta coverage changed: {doc_result.rowcount}/{len(rows)}"
            )
        if indexed_result.rowcount != len(rows):
            raise RuntimeError(
                f"SQLite indexed_docs coverage changed: {indexed_result.rowcount}/{len(rows)}"
            )
        if chunk_result.rowcount != expected_chunks:
            raise RuntimeError(
                f"SQLite chunk coverage changed: {chunk_result.rowcount}/{expected_chunks}"
            )
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()


def canonical_payload(canonical: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": canonical["title"],
        "department": canonical["department"],
        "approve_date": canonical["approve_date"],
        "original_url": canonical["original_url"],
        "metadata_source": METADATA_SOURCE,
        "metadata_schema_version": SCHEMA_VERSION,
        "attachments": canonical["attachments"],
        "attachments_json": json.dumps(
            canonical["attachments"], ensure_ascii=False, separators=(",", ":")
        ),
    }


def apply_bulk_qdrant(
    qdrant_url: str,
    rows: list[dict[str, Any]],
    *,
    batch_size: int,
) -> None:
    operations = [
        {
            "set_payload": {
                "payload": canonical_payload(row["canonical"]),
                "points": row["qdrant_point_ids"],
            }
        }
        for row in rows
    ]
    for start in range(0, len(operations), batch_size):
        qdrant_json(
            f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/points/batch?wait=true",
            {"operations": operations[start : start + batch_size]},
            method="POST",
        )


def verify_bulk_result(
    db_path: Path,
    qdrant_url: str,
    rows: list[dict[str, Any]],
    *,
    qdrant_rows: list[dict[str, Any]] | None = None,
    point_count_before: int,
    vector_sample_ids: list[str | int],
    vector_sample_sha256: str,
) -> dict[str, Any]:
    qdrant_rows = rows if qdrant_rows is None else qdrant_rows
    markdown_mismatches = 0
    for row in rows:
        path = Path(row["md_path"])
        frontmatter, _ = parse_markdown(path.read_text(encoding="utf-8"))
        _, body = split_markdown_bytes(path.read_bytes())
        expected = row["canonical"]
        if any(frontmatter.get(field) != expected[field] for field in CANONICAL_FIELDS):
            markdown_mismatches += 1
        elif not metadata_contract_current(frontmatter, expected):
            markdown_mismatches += 1
        elif (
            len(body) != row["body_bytes"]
            or hashlib.sha256(body).hexdigest() != row["body_sha256"]
        ):
            markdown_mismatches += 1

    sqlite_mismatches = verify_bulk_sqlite(db_path, rows)
    wanted = {row["news_item_id"] for row in qdrant_rows}
    expected_by_id = {
        row["news_item_id"]: canonical_payload(row["canonical"])
        for row in qdrant_rows
    }
    seen: dict[str, int] = {}
    qdrant_mismatches = 0
    point_count_after = 0
    for points in qdrant_scroll_pages(qdrant_url):
        point_count_after += len(points)
        for point in points:
            identifier = str(point.get("payload", {}).get("news_item_id", ""))
            if identifier not in wanted:
                continue
            seen[identifier] = seen.get(identifier, 0) + 1
            payload = point.get("payload", {})
            if any(
                payload.get(key) != value
                for key, value in expected_by_id[identifier].items()
            ):
                qdrant_mismatches += 1
    qdrant_missing = sum(
        1
        for row in qdrant_rows
        if seen.get(row["news_item_id"], 0) != len(row["qdrant_point_ids"])
    )
    vector_after = qdrant_vector_digest(qdrant_url, vector_sample_ids)
    if markdown_mismatches or sqlite_mismatches or qdrant_mismatches or qdrant_missing:
        raise RuntimeError(
            "bulk metadata verification failed: "
            f"markdown={markdown_mismatches}, sqlite={sqlite_mismatches}, "
            f"qdrant={qdrant_mismatches}, qdrant_missing={qdrant_missing}"
        )
    if point_count_after != point_count_before:
        raise RuntimeError(
            f"Qdrant point count changed: {point_count_before}/{point_count_after}"
        )
    if vector_after != vector_sample_sha256:
        raise RuntimeError("Qdrant vector sample changed")
    return {
        "metadata_rows": len(rows),
        "qdrant_rows": len(qdrant_rows),
        "markdown_mismatches": 0,
        "sqlite_mismatches": 0,
        "qdrant_mismatches": 0,
        "qdrant_point_count": point_count_after,
        "vector_sample_size": len(vector_sample_ids),
        "vector_sample_sha256": vector_after,
    }


def verify_bulk_sqlite(db_path: Path, rows: list[dict[str, Any]]) -> int:
    conn = sqlite3.connect(db_path)
    try:
        stage_bulk_metadata(conn, rows)
        doc_mismatches = conn.execute(
            """
            SELECT COUNT(*)
            FROM bulk_api_metadata b
            LEFT JOIN doc_meta d ON d.news_item_id = b.news_item_id
            WHERE d.news_item_id IS NULL
               OR d.title != b.title
               OR d.department != b.department
               OR d.approve_date != b.approve_date
               OR d.source_url != b.original_url
            """
        ).fetchone()[0]
        chunk_mismatches = conn.execute(
            """
            SELECT COUNT(*)
            FROM briefing_chunks_meta c
            JOIN bulk_api_metadata b ON b.news_item_id = c.news_item_id
            WHERE c.department != b.department OR c.approve_date != b.approve_date
            """
        ).fetchone()[0]
        indexed_mismatches = conn.execute(
            """
            SELECT COUNT(*)
            FROM bulk_api_metadata b
            LEFT JOIN indexed_docs i ON i.md_path = b.indexed_md_path
            WHERE i.md_path IS NULL
               OR i.md_mtime_ns != b.md_mtime_ns
               OR i.md_size != b.md_size
            """
        ).fetchone()[0]
        return int(doc_mismatches + chunk_mismatches + indexed_mismatches)
    finally:
        conn.close()


def count_bulk_statuses(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = str(row["status"])
        counts[status] = counts.get(status, 0) + 1
    return counts


def write_bulk_followup_lists(
    output_dir: Path,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    vectorization = [
        row["news_item_id"]
        for row in rows
        if row["status"] == "vectorization_required"
        or (
            row["status"] == "invalid"
            and row["reason"] == "qdrant_points_missing"
        )
    ]
    invalid = [row["news_item_id"] for row in rows if row["status"] == "invalid"]
    deferred = [row["news_item_id"] for row in rows if row["status"] == "deferred"]
    paths = {
        "vectorization_ids": output_dir / "server-v-vectorization.ids",
        "invalid_ids": output_dir / "invalid.ids",
        "deferred_ids": output_dir / "api-deferred.ids",
    }
    for key, values in (
        ("vectorization_ids", vectorization),
        ("invalid_ids", invalid),
        ("deferred_ids", deferred),
    ):
        atomic_write(
            paths[key],
            "".join(f"{identifier}\n" for identifier in values).encode("ascii"),
        )
    return {
        "vectorization_ids": str(paths["vectorization_ids"]),
        "vectorization_count": len(vectorization),
        "invalid_ids": str(paths["invalid_ids"]),
        "invalid_count": len(invalid),
        "deferred_ids": str(paths["deferred_ids"]),
        "deferred_count": len(deferred),
    }


def print_bulk_result(
    state_path: Path,
    manifest_path: Path,
    counts: dict[str, int],
    *,
    applied: bool,
) -> None:
    print(
        json.dumps(
            {
                "mode": "overwrite-all",
                "state": str(state_path),
                "manifest": str(manifest_path),
                "counts": counts,
                "applied": applied,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_ids(path: Path | None) -> set[str] | None:
    if path is None:
        return None
    values = {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    invalid = sorted(value for value in values if not value.isdigit())
    if invalid:
        raise SystemExit(f"invalid IDs: {','.join(invalid)}")
    return values


def discover_local_ids(data_root: Path, year: int, month: int) -> set[str]:
    month_root = data_root / "md" / f"{year:04d}" / f"{month:02d}"
    if not month_root.is_dir():
        return set()
    identifiers: set[str] = set()
    for path in month_root.glob("*.md"):
        match = NEWS_ITEM_ID_RE.match(path.stem)
        if match:
            identifiers.add(match.group("id"))
    return identifiers


def fetch_month(year: int, month: int, *, wanted: set[str]) -> dict[str, dict[str, Any]]:
    service_key = os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY", "").strip()
    if not service_key:
        raise SystemExit("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY is not set")
    if not wanted:
        return {}
    result: dict[str, dict[str, Any]] = {}
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        target = dt.date(year, month, day)
        for item in fetch_day(target, service_key):
            identifier = item["news_item_id"]
            if identifier in wanted:
                result[identifier] = item
        if wanted <= result.keys():
            break
    return result


def fetch_day(
    target: dt.date,
    service_key: str,
    *,
    attempts: int = 5,
) -> list[dict[str, Any]]:
    ymd = target.strftime("%Y%m%d")
    query = urllib.parse.urlencode(
        {"serviceKey": service_key, "startDate": ymd, "endDate": ymd}
    )
    request = urllib.request.Request(
        f"{API_URL}?{query}",
        headers={"User-Agent": "GovPress-Metadata-Migration/1.0"},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                root = ET.fromstring(response.read())
            break
        except (urllib.error.URLError, TimeoutError, ET.ParseError):
            if attempt == attempts - 1:
                raise
            time.sleep(min(8.0, 0.5 * (2**attempt)))
    code = (root.findtext("./header/resultCode") or "").strip()
    if code and code != "0":
        message = (root.findtext("./header/resultMsg") or "API call failed").strip()
        raise RuntimeError(f"API failure for {target}: {code} {message}")
    return [api_node(node) for node in root.findall("./body/NewsItem")]


def api_node(node: ET.Element) -> dict[str, Any]:
    attachments: list[dict[str, str]] = []
    for index in range(1, 20):
        name = unescape((node.findtext(f"FileName{index}") or "").strip())
        url = (node.findtext(f"FileUrl{index}") or "").strip()
        if name or url:
            attachments.append({"file_name": name, "file_url": url})
    return {
        "metadata_schema_version": SCHEMA_VERSION,
        "metadata_source": METADATA_SOURCE,
        "news_item_id": (node.findtext("NewsItemId") or "").strip(),
        "title": normalize_space(unescape(node.findtext("Title") or "")),
        "department": unescape((node.findtext("MinisterCode") or "").strip()),
        "approve_date": normalize_approve_date(node.findtext("ApproveDate") or ""),
        "original_url": (node.findtext("OriginalUrl") or "").strip(),
        "attachments": attachments,
    }


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_approve_date(value: str) -> str:
    raw = value.strip()
    for fmt in ("%m/%d/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return dt.datetime.strptime(raw, fmt).isoformat(timespec="seconds")
        except ValueError:
            continue
    return raw


def classify_month(
    data_root: Path,
    year: int,
    month: int,
    items: dict[str, dict[str, Any]],
    *,
    wanted: set[str],
) -> list[dict[str, Any]]:
    identifiers = sorted(wanted)
    rows: list[dict[str, Any]] = []
    for identifier in identifiers:
        canonical = items.get(identifier)
        path = find_markdown_path(data_root, year, month, identifier)
        if canonical is None:
            rows.append(manifest_row(identifier, path, "deferred", reason="api_metadata_missing"))
            continue
        if not path.is_file():
            rows.append(
                manifest_row(
                    identifier,
                    path,
                    "deferred",
                    canonical=canonical,
                    reason="markdown_missing",
                )
            )
            continue
        try:
            frontmatter, body = parse_markdown(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            rows.append(
                manifest_row(
                    identifier,
                    path,
                    "rerender_reembed",
                    canonical=canonical,
                    body_conflicts=["frontmatter_unparseable"],
                    reason=str(exc),
                )
            )
            continue
        current = {field: frontmatter.get(field, "") for field in CANONICAL_FIELDS}
        canonical_fields = {field: canonical[field] for field in CANONICAL_FIELDS}
        body_differences = detect_body_differences(body, canonical)
        if current == canonical_fields and metadata_contract_current(frontmatter, canonical):
            classification = "unchanged"
        else:
            classification = "metadata_only"
        rows.append(
            manifest_row(
                identifier,
                path,
                classification,
                canonical=canonical,
                current=current,
                body_sha256=hashlib.sha256(body.encode("utf-8")).hexdigest(),
                body_differences=body_differences,
            )
        )
    return rows


def find_markdown_path(data_root: Path, year: int, month: int, identifier: str) -> Path:
    month_root = data_root / "md" / f"{year:04d}" / f"{month:02d}"
    exact = month_root / f"{identifier}.md"
    if exact.is_file():
        return exact
    matches = sorted(month_root.glob(f"{identifier}_*.md"))
    if len(matches) == 1:
        return matches[0]
    return exact


def metadata_contract_current(frontmatter: dict[str, str], canonical: dict[str, Any]) -> bool:
    return (
        frontmatter.get("metadata_source") == METADATA_SOURCE
        and frontmatter.get("metadata_schema_version") == str(SCHEMA_VERSION)
        and frontmatter.get("attachments_json")
        == json.dumps(canonical["attachments"], ensure_ascii=False, separators=(",", ":"))
    )


def detect_body_differences(body: str, canonical: dict[str, Any]) -> list[str]:
    """Record source-body/API differences without treating them as conversion errors."""
    differences: list[str] = []
    title_match = H1_RE.search(body)
    if title_match and normalize_space(title_match.group(1)) != canonical["title"]:
        differences.append("h1_title")
    department_match = PRESS_LABEL_RE.search(body)
    if department_match and normalize_space(department_match.group("department")) != canonical["department"]:
        differences.append("press_label_department")
    return differences


def manifest_row(
    identifier: str,
    path: Path,
    classification: str,
    *,
    canonical: dict[str, Any] | None = None,
    current: dict[str, str] | None = None,
    body_sha256: str | None = None,
    body_conflicts: list[str] | None = None,
    body_differences: list[str] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    return {
        "news_item_id": identifier,
        "md_path": str(path),
        "classification": classification,
        "current": current,
        "canonical": canonical,
        "body_sha256": body_sha256,
        "body_conflicts": body_conflicts or [],
        "body_differences": body_differences or [],
        "reason": reason,
    }


def parse_markdown(document: str) -> tuple[dict[str, str], str]:
    if not document.startswith("---\n"):
        raise ValueError("frontmatter start delimiter is missing")
    header, separator, body = document[4:].partition("\n---\n")
    if not separator:
        raise ValueError("frontmatter end delimiter is missing")
    fields: dict[str, str] = {}
    for line in header.splitlines():
        key, marker, value = line.partition(":")
        if marker:
            fields[key.strip()] = deserialize_scalar(value.strip())
    return fields, body.lstrip("\n")


def deserialize_scalar(value: str) -> str:
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'").replace("\\\\", "\\")
    return value


def serialize_scalar(value: object) -> str:
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{text}'"


def replace_frontmatter(path: Path, canonical: dict[str, Any]) -> None:
    document = path.read_bytes()
    header, body = split_markdown_bytes(document)
    frontmatter, _ = parse_markdown(
        "---\n" + header.decode("utf-8") + "\n---\n"
    )
    updates: dict[str, object] = {
        **{field: canonical[field] for field in CANONICAL_FIELDS},
        "metadata_source": METADATA_SOURCE,
        "metadata_schema_version": SCHEMA_VERSION,
        "attachments_json": json.dumps(
            canonical["attachments"], ensure_ascii=False, separators=(",", ":")
        ),
    }
    frontmatter.update({key: str(value) for key, value in updates.items()})
    lines = ["---"]
    for key, value in frontmatter.items():
        lines.append(f"{key}: {serialize_scalar(value)}")
    rendered = ("\n".join(lines) + "\n---\n").encode("utf-8") + body
    atomic_write(path, rendered)


def split_markdown_bytes(document: bytes) -> tuple[bytes, bytes]:
    if not document.startswith(b"---\n"):
        raise ValueError("frontmatter start delimiter is missing")
    separator = document.find(b"\n---\n", 4)
    if separator < 0:
        raise ValueError("frontmatter end delimiter is missing")
    return document[4:separator], document[separator + len(b"\n---\n") :]


def atomic_write(path: Path, content: bytes) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            handle.write(content)
            temporary_name = handle.name
        mode = path.stat().st_mode if path.exists() else 0o644
        os.chmod(temporary_name, mode)
        os.replace(temporary_name, path)
    finally:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)


def snapshot_sqlite(db_path: Path, backup_path: Path) -> None:
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(db_path)
    destination = sqlite3.connect(backup_path)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()


def create_qdrant_snapshot(qdrant_url: str) -> dict[str, Any]:
    return qdrant_json(
        f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/snapshots",
        {},
        method="POST",
    )


def snapshot_before_apply(
    args: argparse.Namespace,
    stem: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = args.output_dir / "snapshots" / f"{stem}-{stamp}"
    snapshot_dir.mkdir(parents=True, exist_ok=False)
    sqlite_path = snapshot_dir / "govpress.db.bak"
    markdown_path = snapshot_dir / "metadata-only-markdown.tar.gz"
    snapshot_sqlite(args.db, sqlite_path)
    with tarfile.open(markdown_path, "w:gz") as archive:
        for row in rows:
            path = Path(row["md_path"])
            archive.add(
                path,
                arcname=path.relative_to(args.data_root).as_posix(),
                recursive=False,
            )
    return {
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "candidate_count": len(rows),
        "sqlite_backup": str(sqlite_path),
        "markdown_backup": str(markdown_path),
        "qdrant_snapshot": create_qdrant_snapshot(args.qdrant_url),
    }


def apply_with_snapshot(
    args: argparse.Namespace,
    stem: str,
    rows: list[dict[str, Any]],
) -> int:
    integrity_path = args.output_dir / f"{stem}-metadata-only-integrity.jsonl"
    status_path = args.output_dir / f"{stem}-metadata-only-snapshot.json"
    snapshot = snapshot_before_apply(args, stem, rows)
    snapshot.update(
        {
            "status": "ready",
            "integrity_manifest": str(integrity_path),
        }
    )
    atomic_write_json(status_path, snapshot)
    try:
        applied = apply_metadata_only(
            rows,
            db_path=args.db,
            qdrant_url=args.qdrant_url,
            batch_size=args.batch_size,
            integrity_path=integrity_path,
        )
    except BaseException as exc:
        snapshot.update(
            {
                "status": "failed",
                "failed_at": dt.datetime.now(dt.UTC).isoformat(),
                "error": f"{exc.__class__.__name__}: {exc}",
            }
        )
        atomic_write_json(status_path, snapshot)
        raise
    snapshot.update(
        {
            "status": "completed",
            "completed_at": dt.datetime.now(dt.UTC).isoformat(),
            "applied_count": applied,
        }
    )
    atomic_write_json(status_path, snapshot)
    return applied


def apply_metadata_only(
    rows: list[dict[str, Any]],
    *,
    db_path: Path,
    qdrant_url: str,
    batch_size: int,
    integrity_path: Path,
) -> int:
    applied = 0
    integrity_path.unlink(missing_ok=True)
    for start in range(0, len(rows), batch_size):
        batch = rows[start : start + batch_size]
        conn = sqlite3.connect(db_path, timeout=600)
        conn.execute("PRAGMA busy_timeout = 600000")
        integrity_rows: list[dict[str, Any]] = []
        document_backups: dict[Path, bytes] = {}
        try:
            conn.execute("BEGIN IMMEDIATE")
            baselines: dict[str, dict[str, Any]] = {}
            for row in batch:
                canonical = row["canonical"]
                path = Path(row["md_path"])
                verify_sqlite_targets(conn, path, canonical["news_item_id"])
                document_backups[path] = path.read_bytes()
                baselines[canonical["news_item_id"]] = integrity_baseline(
                    qdrant_url,
                    path,
                    canonical["news_item_id"],
                )
            for row in batch:
                canonical = row["canonical"]
                path = Path(row["md_path"])
                before = baselines[canonical["news_item_id"]]
                replace_frontmatter(path, canonical)
                patch_sqlite(conn, path, canonical)
                patch_qdrant(qdrant_url, canonical)
                after = integrity_baseline(qdrant_url, path, canonical["news_item_id"])
                verify_invariants(before, after, path)
                verify_sqlite_metadata(conn, canonical)
                verify_qdrant_metadata(
                    qdrant_points(qdrant_url, canonical["news_item_id"], with_vectors=False),
                    canonical,
                )
                integrity_rows.append(
                    {
                        "news_item_id": canonical["news_item_id"],
                        "before": before,
                        "after": after,
                    }
                )
            conn.commit()
        except BaseException:
            conn.rollback()
            for path, content in document_backups.items():
                atomic_write(path, content)
            raise
        finally:
            conn.close()
        append_jsonl(integrity_path, integrity_rows)
        applied += len(batch)
    return applied


def integrity_baseline(qdrant_url: str, path: Path, news_item_id: str) -> dict[str, Any]:
    _, body = split_markdown_bytes(path.read_bytes())
    points = qdrant_points(qdrant_url, news_item_id, with_vectors=True)
    if not points:
        raise RuntimeError(f"Qdrant points missing: {news_item_id}")
    vectors = [
        {"id": str(point["id"]), "vector": point.get("vector")}
        for point in sorted(points, key=lambda point: str(point["id"]))
    ]
    vector_sha256 = hashlib.sha256(
        json.dumps(vectors, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()
    return {
        "body_bytes": len(body),
        "body_sha256": hashlib.sha256(body).hexdigest(),
        "qdrant_point_count": len(points),
        "vector_sha256": vector_sha256,
    }


def verify_invariants(before: dict[str, Any], after: dict[str, Any], path: Path) -> None:
    for field in ("body_bytes", "body_sha256", "qdrant_point_count", "vector_sha256"):
        if before[field] != after[field]:
            raise RuntimeError(f"metadata-only invariant changed ({field}): {path}")


def patch_sqlite(conn: sqlite3.Connection, path: Path, canonical: dict[str, Any]) -> None:
    identifier = canonical["news_item_id"]
    doc_result = conn.execute(
        """
        UPDATE doc_meta
        SET title = ?, department = ?, approve_date = ?, source_url = ?, indexed_at = ?
        WHERE news_item_id = ?
        """,
        (
            canonical["title"],
            canonical["department"],
            canonical["approve_date"],
            canonical["original_url"],
            dt.datetime.now(dt.UTC).isoformat(),
            identifier,
        ),
    )
    chunk_result = conn.execute(
        "UPDATE briefing_chunks_meta SET department = ?, approve_date = ? WHERE news_item_id = ?",
        (canonical["department"], canonical["approve_date"], identifier),
    )
    stat = path.stat()
    indexed_paths = indexed_doc_path_candidates(path)
    placeholders = ",".join("?" for _ in indexed_paths)
    indexed_result = conn.execute(
        f"UPDATE indexed_docs SET md_mtime_ns = ?, md_size = ? "
        f"WHERE md_path IN ({placeholders})",
        (stat.st_mtime_ns, stat.st_size, *indexed_paths),
    )
    if doc_result.rowcount != 1:
        raise RuntimeError(f"SQLite doc_meta row missing: {identifier}")
    if chunk_result.rowcount <= 0:
        raise RuntimeError(f"SQLite chunk rows missing: {identifier}")
    if indexed_result.rowcount != 1:
        raise RuntimeError(f"SQLite indexed_docs row missing: {path}")


def indexed_doc_path_candidates(path: Path) -> tuple[str, ...]:
    candidates = {str(path), str(path.resolve())}
    parts = path.parts
    if "md" in parts:
        md_index = parts.index("md")
        candidates.add("/app/data/" + "/".join(parts[md_index:]))
    return tuple(sorted(candidates))


def verify_sqlite_targets(
    conn: sqlite3.Connection,
    path: Path,
    news_item_id: str,
) -> None:
    if conn.execute(
        "SELECT COUNT(*) FROM doc_meta WHERE news_item_id = ?",
        (news_item_id,),
    ).fetchone()[0] != 1:
        raise RuntimeError(f"SQLite doc_meta row missing: {news_item_id}")
    if conn.execute(
        "SELECT COUNT(*) FROM briefing_chunks_meta WHERE news_item_id = ?",
        (news_item_id,),
    ).fetchone()[0] <= 0:
        raise RuntimeError(f"SQLite chunk rows missing: {news_item_id}")
    indexed_paths = indexed_doc_path_candidates(path)
    placeholders = ",".join("?" for _ in indexed_paths)
    if conn.execute(
        f"SELECT COUNT(*) FROM indexed_docs WHERE md_path IN ({placeholders})",
        indexed_paths,
    ).fetchone()[0] != 1:
        raise RuntimeError(f"SQLite indexed_docs row missing: {path}")


def patch_qdrant(qdrant_url: str, canonical: dict[str, Any]) -> None:
    qdrant_json(
        f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/points/payload?wait=true",
        {
            "payload": {
                "title": canonical["title"],
                "department": canonical["department"],
                "approve_date": canonical["approve_date"],
                "original_url": canonical["original_url"],
                "metadata_source": METADATA_SOURCE,
                "metadata_schema_version": SCHEMA_VERSION,
                "attachments": canonical["attachments"],
                "attachments_json": json.dumps(
                    canonical["attachments"], ensure_ascii=False, separators=(",", ":")
                ),
            },
            "filter": {
                "must": [
                    {
                        "key": "news_item_id",
                        "match": {"value": canonical["news_item_id"]},
                    }
                ]
            },
        },
        method="POST",
    )


def qdrant_points(
    qdrant_url: str,
    news_item_id: str,
    *,
    with_vectors: bool,
) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    offset: str | int | None = None
    while True:
        payload: dict[str, Any] = {
            "filter": {
                "must": [
                    {
                        "key": "news_item_id",
                        "match": {"value": news_item_id},
                    }
                ]
            },
            "limit": 256,
            "with_payload": True,
            "with_vector": with_vectors,
        }
        if offset is not None:
            payload["offset"] = offset
        response = qdrant_json(
            f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/points/scroll",
            payload,
            method="POST",
        )
        result = response.get("result", {})
        points.extend(result.get("points", []))
        offset = result.get("next_page_offset")
        if offset is None:
            return points


def verify_sqlite_metadata(conn: sqlite3.Connection, canonical: dict[str, Any]) -> None:
    row = conn.execute(
        "SELECT title, department, approve_date, source_url FROM doc_meta "
        "WHERE news_item_id = ?",
        (canonical["news_item_id"],),
    ).fetchone()
    expected = (
        canonical["title"],
        canonical["department"],
        canonical["approve_date"],
        canonical["original_url"],
    )
    if row != expected:
        raise RuntimeError(f"SQLite metadata mismatch: {canonical['news_item_id']}")


def verify_qdrant_metadata(
    points: list[dict[str, Any]],
    canonical: dict[str, Any],
) -> None:
    expected = {
        "title": canonical["title"],
        "department": canonical["department"],
        "approve_date": canonical["approve_date"],
        "original_url": canonical["original_url"],
        "metadata_source": METADATA_SOURCE,
        "metadata_schema_version": SCHEMA_VERSION,
        "attachments": canonical["attachments"],
        "attachments_json": json.dumps(
            canonical["attachments"], ensure_ascii=False, separators=(",", ":")
        ),
    }
    if not points:
        raise RuntimeError(f"Qdrant points missing: {canonical['news_item_id']}")
    for point in points:
        payload = point.get("payload", {})
        if any(payload.get(key) != value for key, value in expected.items()):
            raise RuntimeError(f"Qdrant metadata mismatch: {canonical['news_item_id']}")


def qdrant_json(url: str, payload: dict[str, Any], *, method: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    content = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    atomic_write(path, content)


if __name__ == "__main__":
    raise SystemExit(main())
