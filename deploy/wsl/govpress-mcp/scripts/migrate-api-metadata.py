#!/usr/bin/env python3
"""Reconcile published Markdown and vector metadata with the official API.

The default mode only writes a JSONL manifest. With ``--apply-metadata-only``,
documents whose body does not contradict the API are patched without calling
the embedding service. Documents with a conflicting H1 or explicit agency
press label are emitted to a separate ID file for selective reconversion.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile
import time
from typing import Any
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
PRESS_LABEL_RE = re.compile(
    r"^(?P<department>[^#\n]+?)[ \t]+"
    r"(?:공동|합동|정부합동|관계부처합동)?"
    r"(?:보도자료|보도참고자료|보도설명자료|설명자료|동정자료)\s*/?$",
    re.MULTILINE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int)
    parser.add_argument("month", type=int)
    parser.add_argument("--ids-file", type=Path)
    parser.add_argument("--data-root", type=Path, default=Path("data"))
    parser.add_argument("--db", type=Path)
    parser.add_argument("--qdrant-url", default="http://localhost:6333")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--apply-metadata-only", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.month <= 12:
        parser.error("MONTH must be between 1 and 12")
    args.db = args.db or args.data_root / "govpress.db"
    args.output_dir = args.output_dir or args.data_root / "fetch-log" / "metadata-migration"
    return args


def main() -> int:
    args = parse_args()
    wanted = load_ids(args.ids_file)
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
            snapshot_sqlite(args.db, args.output_dir / f"{stem}-govpress.db.bak")
            create_qdrant_snapshot(args.qdrant_url)
            applied = apply_metadata_only(
                candidates,
                db_path=args.db,
                qdrant_url=args.qdrant_url,
            )

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


def load_ids(path: Path | None) -> set[str] | None:
    if path is None:
        return None
    values = {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    invalid = sorted(value for value in values if not value.isdigit())
    if invalid:
        raise SystemExit(f"invalid IDs: {','.join(invalid)}")
    return values


def fetch_month(year: int, month: int, *, wanted: set[str] | None) -> dict[str, dict[str, Any]]:
    service_key = os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY", "").strip()
    if not service_key:
        raise SystemExit("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY is not set")
    result: dict[str, dict[str, Any]] = {}
    for day in range(1, calendar.monthrange(year, month)[1] + 1):
        target = dt.date(year, month, day)
        for item in fetch_day(target, service_key):
            identifier = item["news_item_id"]
            if wanted is None or identifier in wanted:
                result[identifier] = item
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
        except (urllib.error.URLError, TimeoutError):
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
        name = (node.findtext(f"FileName{index}") or "").strip()
        url = (node.findtext(f"FileUrl{index}") or "").strip()
        if name or url:
            attachments.append({"file_name": name, "file_url": url})
    return {
        "metadata_schema_version": SCHEMA_VERSION,
        "metadata_source": METADATA_SOURCE,
        "news_item_id": (node.findtext("NewsItemId") or "").strip(),
        "title": normalize_space(node.findtext("Title") or ""),
        "department": (node.findtext("MinisterCode") or "").strip(),
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
    wanted: set[str] | None,
) -> list[dict[str, Any]]:
    identifiers = sorted(wanted if wanted is not None else items)
    rows: list[dict[str, Any]] = []
    for identifier in identifiers:
        canonical = items.get(identifier)
        path = data_root / "md" / f"{year:04d}" / f"{month:02d}" / f"{identifier}.md"
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
        frontmatter, body = parse_markdown(path.read_text(encoding="utf-8"))
        current = {field: frontmatter.get(field, "") for field in CANONICAL_FIELDS}
        canonical_fields = {field: canonical[field] for field in CANONICAL_FIELDS}
        body_conflicts = detect_body_conflicts(body, canonical)
        if body_conflicts:
            classification = "rerender_reembed"
        elif current == canonical_fields and metadata_contract_current(frontmatter, canonical):
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
                body_conflicts=body_conflicts,
            )
        )
    return rows


def metadata_contract_current(frontmatter: dict[str, str], canonical: dict[str, Any]) -> bool:
    return (
        frontmatter.get("metadata_source") == METADATA_SOURCE
        and frontmatter.get("metadata_schema_version") == str(SCHEMA_VERSION)
        and frontmatter.get("attachments_json")
        == json.dumps(canonical["attachments"], ensure_ascii=False, separators=(",", ":"))
    )


def detect_body_conflicts(body: str, canonical: dict[str, Any]) -> list[str]:
    conflicts: list[str] = []
    title_match = H1_RE.search(body)
    if title_match and normalize_space(title_match.group(1)) != canonical["title"]:
        conflicts.append("h1_title")
    department_match = PRESS_LABEL_RE.search(body)
    if department_match and normalize_space(department_match.group("department")) != canonical["department"]:
        conflicts.append("press_label_department")
    return conflicts


def manifest_row(
    identifier: str,
    path: Path,
    classification: str,
    *,
    canonical: dict[str, Any] | None = None,
    current: dict[str, str] | None = None,
    body_sha256: str | None = None,
    body_conflicts: list[str] | None = None,
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
    document = path.read_text(encoding="utf-8")
    frontmatter, body = parse_markdown(document)
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
    rendered = "\n".join(lines) + "\n---\n\n" + body
    atomic_write(path, rendered)


def atomic_write(path: Path, text: str) -> None:
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            handle.write(text)
            temporary_name = handle.name
        os.chmod(temporary_name, path.stat().st_mode)
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


def create_qdrant_snapshot(qdrant_url: str) -> None:
    qdrant_json(
        f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/snapshots",
        {},
        method="POST",
    )


def apply_metadata_only(
    rows: list[dict[str, Any]],
    *,
    db_path: Path,
    qdrant_url: str,
) -> int:
    conn = sqlite3.connect(db_path, timeout=600)
    conn.execute("PRAGMA busy_timeout = 600000")
    applied = 0
    try:
        for row in rows:
            canonical = row["canonical"]
            path = Path(row["md_path"])
            point_count = qdrant_count(qdrant_url, canonical["news_item_id"])
            if point_count <= 0:
                raise RuntimeError(f"Qdrant points missing: {canonical['news_item_id']}")
            before_body = parse_markdown(path.read_text(encoding="utf-8"))[1]
            replace_frontmatter(path, canonical)
            after_body = parse_markdown(path.read_text(encoding="utf-8"))[1]
            if before_body != after_body:
                raise RuntimeError(f"body changed during metadata-only update: {path}")
            patch_sqlite(conn, path, canonical)
            patch_qdrant(qdrant_url, canonical)
            if qdrant_count(qdrant_url, canonical["news_item_id"]) != point_count:
                raise RuntimeError(f"Qdrant point count changed: {canonical['news_item_id']}")
            applied += 1
        conn.commit()
    except BaseException:
        conn.rollback()
        raise
    finally:
        conn.close()
    return applied


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
    indexed_result = conn.execute(
        "UPDATE indexed_docs SET md_mtime_ns = ?, md_size = ? WHERE md_path = ?",
        (stat.st_mtime_ns, stat.st_size, str(path)),
    )
    if doc_result.rowcount != 1:
        raise RuntimeError(f"SQLite doc_meta row missing: {identifier}")
    if chunk_result.rowcount <= 0:
        raise RuntimeError(f"SQLite chunk rows missing: {identifier}")
    if indexed_result.rowcount != 1:
        raise RuntimeError(f"SQLite indexed_docs row missing: {path}")


def patch_qdrant(qdrant_url: str, canonical: dict[str, Any]) -> None:
    qdrant_json(
        f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/points/payload?wait=true",
        {
            "payload": {
                "department": canonical["department"],
                "approve_date": canonical["approve_date"],
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


def qdrant_count(qdrant_url: str, news_item_id: str) -> int:
    response = qdrant_json(
        f"{qdrant_url.rstrip('/')}/collections/{COLLECTION}/points/count",
        {
            "filter": {
                "must": [
                    {
                        "key": "news_item_id",
                        "match": {"value": news_item_id},
                    }
                ]
            },
            "exact": True,
        },
        method="POST",
    )
    return int(response.get("result", {}).get("count", 0))


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


if __name__ == "__main__":
    raise SystemExit(main())
