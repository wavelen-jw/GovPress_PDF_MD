from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.adapters.policy_briefing import PolicyBriefingCatalog, PolicyBriefingClient, PolicyBriefingItem
from server.app.core.config import load_settings
from server.app.services.storage_service import StorageService


def _load_curated_samples(qc_root: Path) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for meta_path in sorted(qc_root.glob("*/meta.json")):
        payload = json.loads(meta_path.read_text(encoding="utf-8"))
        if payload.get("sample_status") != "curated":
            continue
        sample_dir = meta_path.parent
        bridge_path = sample_dir / "storage_bridge.json"
        bridge_payload = json.loads(bridge_path.read_text(encoding="utf-8")) if bridge_path.exists() else {}
        title = str(bridge_payload.get("title") or payload.get("storage_title") or "")
        job_id = str(bridge_payload.get("job_id") or payload.get("storage_job_id") or "")
        if not title or not job_id:
            continue
        samples.append(
            {
                "sample_dir": sample_dir,
                "title": title,
                "job_id": job_id,
                "source_hwpx": str(payload.get("source_hwpx") or bridge_payload.get("hwpx_path") or ""),
            }
        )
    return samples


def _build_title_index(catalog_dir: Path) -> dict[str, PolicyBriefingItem]:
    client = PolicyBriefingClient(service_key=load_settings().policy_briefing_service_key)
    catalog = PolicyBriefingCatalog(client=client, cache_path=catalog_dir.parent / "policy_briefing_catalog.json")
    items_by_title: dict[str, PolicyBriefingItem] = {}
    for path in sorted(catalog_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for item_payload in payload.get("items", {}).values():
            item = catalog.get_cached_item(str(item_payload.get("news_item_id", "")))
            if item is None or item.primary_pdf is None:
                continue
            items_by_title.setdefault(item.title, item)
    return items_by_title


def _normalize_title(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", value)


def _candidate_dates(source_hwpx: str) -> list[date]:
    name = Path(source_hwpx).name
    candidates: list[date] = []

    ymd_match = re.search(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", name)
    if ymd_match:
        yy, mm, dd = map(int, ymd_match.groups())
        try:
            candidates.append(date(2000 + yy, mm, dd))
        except ValueError:
            pass

    mmdd_matches = re.findall(r"(?<!\d)(\d{1,2})-(\d{1,2})(?!\d)", name)
    for mm_raw, dd_raw in mmdd_matches:
        mm = int(mm_raw)
        dd = int(dd_raw)
        for year in (2026, 2025):
            try:
                candidate = date(year, mm, dd)
            except ValueError:
                continue
            if candidate not in candidates:
                candidates.append(candidate)

    compact_mmdd = re.search(r"(?<!\d)(\d{2})(\d{2})(?!\d)", name)
    if compact_mmdd and not ymd_match:
        mm, dd = map(int, compact_mmdd.groups())
        for year in (2026, 2025):
            try:
                candidate = date(year, mm, dd)
            except ValueError:
                continue
            if candidate not in candidates:
                candidates.append(candidate)
    return candidates


def _find_item_from_live_api(
    client: PolicyBriefingClient,
    *,
    title: str,
    source_hwpx: str,
) -> PolicyBriefingItem | None:
    norm_title = _normalize_title(title)
    norm_hwpx = _normalize_title(Path(source_hwpx).name.replace(".hwpx", "").replace(".hwp", ""))

    for candidate_date in _candidate_dates(source_hwpx):
        try:
            items = client.list_items(candidate_date)
        except Exception:
            continue
        best_item: PolicyBriefingItem | None = None
        best_score = -1
        for item in items:
            score = 0
            item_title = _normalize_title(item.title)
            if item_title == norm_title:
                score += 5
            elif item_title and (item_title in norm_title or norm_title in item_title):
                score += 3
            for attachment in item.attachments:
                attachment_norm = _normalize_title(Path(attachment.file_name).stem)
                if attachment_norm == norm_hwpx:
                    score += 6
                elif attachment_norm and (attachment_norm in norm_hwpx or norm_hwpx in attachment_norm):
                    score += 4
            if item.primary_pdf is not None:
                score += 1
            if score > best_score:
                best_score = score
                best_item = item
        if best_item is not None and best_score >= 5:
            return best_item
    return None


def backfill_curated_sample_pdfs(*, storage_root: Path, qc_root: Path) -> dict[str, Any]:
    settings = load_settings()
    client = PolicyBriefingClient(service_key=settings.policy_briefing_service_key)
    storage = StorageService(storage_root)
    items_by_title = _build_title_index(storage_root / "policy_briefing_catalog")
    normalized_items = {_normalize_title(title): item for title, item in items_by_title.items()}

    results: list[dict[str, str]] = []
    for sample in _load_curated_samples(qc_root):
        sample_dir = sample["sample_dir"]
        title = str(sample["title"])
        job_id = str(sample["job_id"])
        source_hwpx = str(sample.get("source_hwpx") or "")
        sample_pdf_path = sample_dir / "source.pdf"
        storage_pdf_candidates = list(storage.originals_dir.glob(f"{job_id}-*.pdf"))

        if sample_pdf_path.exists() and storage_pdf_candidates:
            results.append({"job_id": job_id, "title": title, "status": "already_present"})
            continue

        item = items_by_title.get(title) or normalized_items.get(_normalize_title(title))
        if item is None:
            item = _find_item_from_live_api(client, title=title, source_hwpx=source_hwpx)
        if item is None or item.primary_pdf is None:
            results.append({"job_id": job_id, "title": title, "status": "catalog_miss"})
            continue

        downloaded = client.download_attachment(item, item.primary_pdf)
        if not sample_pdf_path.exists():
            sample_pdf_path.write_bytes(downloaded.content)
        storage_status = "already_present" if storage_pdf_candidates else "backfilled"
        if not storage_pdf_candidates:
            try:
                storage.save_original_file(job_id, item.primary_pdf.file_name, downloaded.content)
            except PermissionError:
                storage_status = "storage_write_denied"
        results.append({"job_id": job_id, "title": title, "status": storage_status})

    return {
        "curated_count": len(_load_curated_samples(qc_root)),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill missing PDFs for curated storage QC samples")
    parser.add_argument(
        "--storage-root",
        default="deploy/wsl/data/storage",
        help="GovPress storage root containing originals/results/jobs.sqlite3",
    )
    parser.add_argument(
        "--qc-root",
        default="/home/wavel/gov-md-converter/tests/qc_samples",
        help="Curated QC sample root",
    )
    args = parser.parse_args()

    report = backfill_curated_sample_pdfs(
        storage_root=Path(args.storage_root).resolve(),
        qc_root=Path(args.qc_root).resolve(),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
