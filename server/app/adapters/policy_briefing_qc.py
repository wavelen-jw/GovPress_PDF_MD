from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import os
from typing import Callable

from .policy_briefing import PolicyBriefingAttachment, PolicyBriefingCatalogResult, PolicyBriefingClient, PolicyBriefingItem


_QC_PIPELINE_MODULES: tuple[
    Callable[..., dict[str, object]],
    Callable[..., dict[str, object]],
    Callable[..., dict[str, object]],
    Callable[..., dict[str, object]],
] | None = None


def _load_gov_md_converter_qc_pipeline() -> tuple[Callable[..., dict[str, object]], Callable[..., dict[str, object]], Callable[..., dict[str, object]], Callable[..., dict[str, object]]]:
    candidates = []
    env_root = os.environ.get("GOV_MD_CONVERTER_ROOT")
    if env_root:
        candidates.append(Path(env_root).resolve())
    candidates.append(Path(__file__).resolve().parents[4] / "gov-md-converter")
    for root in candidates:
        module_path = root / "src" / "qc_pipeline.py"
        if not module_path.exists():
            continue
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from src.qc_pipeline import (
            build_qc_pipeline_report,
            run_gov_md_batch_local,
            run_gov_md_qc_command,
            run_local_hwpx_qc_pipeline,
        )

        return run_gov_md_qc_command, run_gov_md_batch_local, build_qc_pipeline_report, run_local_hwpx_qc_pipeline
    raise ModuleNotFoundError("gov-md-converter QC pipeline module not found")


def _get_gov_md_converter_qc_pipeline() -> tuple[Callable[..., dict[str, object]], Callable[..., dict[str, object]], Callable[..., dict[str, object]], Callable[..., dict[str, object]]]:
    global _QC_PIPELINE_MODULES
    if _QC_PIPELINE_MODULES is None:
        _QC_PIPELINE_MODULES = _load_gov_md_converter_qc_pipeline()
    return _QC_PIPELINE_MODULES


ScaffoldRunner = Callable[..., str]
GovMdCommandRunner = Callable[..., dict[str, object]]
GovMdBatchRunner = Callable[..., dict[str, object]]


@dataclass(frozen=True)
class ExportedPolicyBriefingArtifact:
    news_item_id: str
    title: str
    export_dir: str
    hwpx_path: str
    pdf_path: str | None
    metadata_path: str
    scaffold_sample_dir: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "news_item_id": self.news_item_id,
            "title": self.title,
            "export_dir": self.export_dir,
            "hwpx_path": self.hwpx_path,
            "pdf_path": self.pdf_path,
            "metadata_path": self.metadata_path,
            "scaffold_sample_dir": self.scaffold_sample_dir,
        }


@dataclass(frozen=True)
class StorageQcArtifact:
    job_id: str
    title: str
    updated_at: str | None
    export_dir: str
    hwpx_path: str
    pdf_path: str | None
    result_md_path: str | None
    golden_md_path: str | None
    scaffold_sample_dir: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "news_item_id": self.job_id,
            "title": self.title,
            "updated_at": self.updated_at,
            "export_dir": self.export_dir,
            "hwpx_path": self.hwpx_path,
            "pdf_path": self.pdf_path,
            "result_md_path": self.result_md_path,
            "golden_md_path": self.golden_md_path,
            "scaffold_sample_dir": self.scaffold_sample_dir,
        }


def resolve_qc_export_root(*, storage_root: str | Path) -> Path:
    env_root = os.environ.get("GOVPRESS_QC_EXPORT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    candidates = []
    gov_md_root = os.environ.get("GOV_MD_CONVERTER_ROOT")
    if gov_md_root:
        candidates.append(Path(gov_md_root).resolve())
    candidates.append(Path(__file__).resolve().parents[4] / "gov-md-converter")
    for root in candidates:
        if (root / "src" / "qc_pipeline.py").exists():
            return root / "exports" / "policy_briefing_qc"
    return Path(storage_root).resolve().parent / "exports" / "policy_briefing_qc"


def resolve_dashboard_paths(qc_export_root: str | Path) -> tuple[Path, Path]:
    html_path = resolve_dashboard_asset_path(qc_export_root, "index.html")
    json_path = resolve_dashboard_asset_path(qc_export_root, "dashboard.json")
    return html_path, json_path


def resolve_dashboard_asset_path(qc_export_root: str | Path, asset_name: str) -> Path:
    roots: list[Path] = []

    def add_root(root: Path | None) -> None:
        if root is None:
            return
        resolved = root.resolve()
        if resolved not in roots:
            roots.append(resolved)

    primary_root = Path(qc_export_root).resolve()
    add_root(primary_root)

    gov_md_root = os.environ.get("GOV_MD_CONVERTER_ROOT")
    if gov_md_root:
        add_root(Path(gov_md_root) / "exports" / "policy_briefing_qc")

    govpress_root = Path(__file__).resolve().parents[4]
    add_root(govpress_root / "exports" / "policy_briefing_qc")
    add_root(govpress_root.parent / "gov-md-converter" / "exports" / "policy_briefing_qc")

    for root in roots:
        candidate = root / "dashboard" / asset_name
        if candidate.exists():
            return candidate
    return primary_root / "dashboard" / asset_name


def _download_pdf(
    client: PolicyBriefingClient,
    item: PolicyBriefingItem,
    *,
    include_pdf: bool,
) -> tuple[PolicyBriefingAttachment | None, bytes | None]:
    if not include_pdf or item.primary_pdf is None:
        return None, None
    downloaded = client.download_attachment(item, item.primary_pdf)
    return item.primary_pdf, downloaded.content


def _write_export_metadata(
    export_dir: Path,
    *,
    item: PolicyBriefingItem,
    hwpx_attachment: PolicyBriefingAttachment,
    pdf_attachment: PolicyBriefingAttachment | None,
    target_date: date,
) -> Path:
    metadata_path = export_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "news_item_id": item.news_item_id,
                "title": item.title,
                "department": item.department,
                "approve_date": item.approve_date,
                "target_date": target_date.isoformat(),
                "original_url": item.original_url,
                "primary_hwpx": {
                    "file_name": hwpx_attachment.file_name,
                    "file_url": hwpx_attachment.file_url,
                    "export_path": "source.hwpx",
                },
                "primary_pdf": (
                    {
                        "file_name": pdf_attachment.file_name,
                        "file_url": pdf_attachment.file_url,
                        "export_path": "source.pdf",
                    }
                    if pdf_attachment is not None
                    else None
                ),
                "exported_at": datetime.now(UTC).isoformat(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return metadata_path


def run_gov_md_scaffold(
    *,
    gov_md_converter_root: str | Path,
    source_path: str | Path,
    pdf_path: str | Path | None,
    qc_root: str | Path,
    sample_id: str,
    autofill: bool = True,
    force: bool = False,
    sample_status: str = "scratch",
) -> str:
    resolved_root = Path(gov_md_converter_root).resolve()
    script_path = resolved_root / "scripts" / "run_hwpx_qc.py"
    if not script_path.exists():
        raise FileNotFoundError(f"gov-md-converter QC CLI not found: {script_path}")

    command = [
        sys.executable,
        str(script_path),
        "scaffold-local",
        str(Path(source_path).resolve()),
        "--root",
        str(qc_root),
        "--sample-id",
        sample_id,
        "--sample-status",
        sample_status,
    ]
    if pdf_path is not None:
        command.extend(["--pdf", str(Path(pdf_path).resolve())])
    if autofill:
        command.append("--autofill")
    if force:
        command.append("--force")

    result = subprocess.run(
        command,
        cwd=resolved_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def run_gov_md_qc_command(
    *,
    gov_md_converter_root: str | Path,
    command: str,
    qc_root: str | Path,
    output_path: str | Path | None = None,
) -> dict[str, object]:
    converter_run_gov_md_qc_command, _, _, _ = _get_gov_md_converter_qc_pipeline()
    return converter_run_gov_md_qc_command(
        gov_md_converter_root=gov_md_converter_root,
        command=command,
        qc_root=qc_root,
        output_path=output_path,
    )


def run_gov_md_batch_local(
    *,
    gov_md_converter_root: str | Path,
    source_root: str | Path,
    qc_root: str | Path,
    limit: int | None = None,
    mode: str = "low",
    autofill: bool = True,
    force: bool = False,
) -> dict[str, object]:
    _, converter_run_gov_md_batch_local, _, _ = _get_gov_md_converter_qc_pipeline()
    return converter_run_gov_md_batch_local(
        gov_md_converter_root=gov_md_converter_root,
        source_root=source_root,
        qc_root=qc_root,
        limit=limit,
        mode=mode,
        autofill=autofill,
        force=force,
    )


def export_policy_briefings_for_qc(
    *,
    client: PolicyBriefingClient,
    catalog,
    target_date: date,
    output_root: str | Path,
    news_item_ids: list[str] | None = None,
    limit: int | None = None,
    include_pdf: bool = True,
    ensure_fresh: bool = True,
    scaffold_runner: ScaffoldRunner | None = None,
    gov_md_converter_root: str | Path | None = None,
    qc_root: str | Path | None = None,
    autofill: bool = True,
    force: bool = False,
    sample_status: str = "scratch",
) -> dict[str, object]:
    catalog_result: PolicyBriefingCatalogResult = catalog.list_cached_items_with_status(
        target_date=target_date,
        ensure_fresh=ensure_fresh,
    )
    items = list(catalog_result.items)
    requested_ids = set(news_item_ids or [])
    missing_ids: list[str] = []
    if requested_ids:
        items_by_id = {item.news_item_id: item for item in items}
        missing_ids = sorted(requested_ids.difference(items_by_id))
        items = [items_by_id[item_id] for item_id in requested_ids if item_id in items_by_id]
    if limit is not None:
        items = items[:limit]

    resolved_root = Path(output_root).resolve() / target_date.isoformat()
    resolved_root.mkdir(parents=True, exist_ok=True)
    exported: list[ExportedPolicyBriefingArtifact] = []
    failed_items: list[dict[str, str]] = []

    for item in items:
        try:
            hwpx_download = client.download_item_hwpx(item)
            export_dir = resolved_root / item.news_item_id
            export_dir.mkdir(parents=True, exist_ok=True)
            hwpx_path = export_dir / "source.hwpx"
            hwpx_path.write_bytes(hwpx_download.content)

            pdf_attachment, pdf_content = _download_pdf(client, item, include_pdf=include_pdf)
            pdf_path: Path | None = None
            if pdf_content is not None:
                pdf_path = export_dir / "source.pdf"
                pdf_path.write_bytes(pdf_content)

            metadata_path = _write_export_metadata(
                export_dir,
                item=item,
                hwpx_attachment=hwpx_download.attachment,
                pdf_attachment=pdf_attachment,
                target_date=target_date,
            )

            scaffold_sample_dir: str | None = None
            if scaffold_runner is not None:
                if gov_md_converter_root is None or qc_root is None:
                    raise ValueError("gov_md_converter_root and qc_root are required when scaffold_runner is used")
                scaffold_sample_dir = scaffold_runner(
                    gov_md_converter_root=gov_md_converter_root,
                    source_path=hwpx_path,
                    pdf_path=pdf_path,
                    qc_root=qc_root,
                    sample_id=f"policy_briefing_{target_date:%Y_%m_%d}_{item.news_item_id}",
                    autofill=autofill,
                    force=force,
                    sample_status=sample_status,
                )

            exported.append(
                ExportedPolicyBriefingArtifact(
                    news_item_id=item.news_item_id,
                    title=item.title,
                    export_dir=str(export_dir),
                    hwpx_path=str(hwpx_path),
                    pdf_path=str(pdf_path) if pdf_path is not None else None,
                    metadata_path=str(metadata_path),
                    scaffold_sample_dir=scaffold_sample_dir,
                )
            )
        except Exception as exc:
            failed_items.append(
                {
                    "news_item_id": item.news_item_id,
                    "title": item.title,
                    "error": str(exc).strip() or exc.__class__.__name__,
                }
            )

    return {
        "date": target_date.isoformat(),
        "output_root": str(resolved_root),
        "ensure_fresh": ensure_fresh,
        "served_stale": catalog_result.served_stale,
        "stale_reason": catalog_result.stale_reason,
        "requested_news_item_ids": sorted(requested_ids),
        "missing_news_item_ids": missing_ids,
        "selected_count": len(items),
        "exported_count": len(exported),
        "scaffolded_count": sum(1 for item in exported if item.scaffold_sample_dir),
        "items": [item.to_dict() for item in exported],
        "failed_items": failed_items,
    }


def _storage_title_from_original(path: Path) -> str:
    stem = path.stem
    if stem.startswith("job_"):
        parts = stem.split("-", 1)
        if len(parts) == 2:
            stem = parts[1]
    return stem.strip()


def _normalize_storage_key(text: str) -> str:
    normalized = re.sub(r":zone.identifier$", "", text, flags=re.IGNORECASE)
    normalized = normalized.strip().lower()
    normalized = normalized.replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^\w\s()-]", "", normalized)
    return normalized.strip()


def normalize_storage_title_key(text: str) -> str:
    return _normalize_storage_key(text)


def _load_storage_job_metadata(storage_root: Path) -> dict[str, dict[str, str | None]]:
    db_path = storage_root / "jobs.sqlite3"
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT job_id, file_name, title, updated_at, final_markdown_path, original_pdf_path
            FROM jobs
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    payload: dict[str, dict[str, str | None]] = {}
    for row in rows:
        payload[str(row["job_id"])] = {
            "file_name": row["file_name"],
            "title": row["title"],
            "updated_at": row["updated_at"],
            "final_markdown_path": row["final_markdown_path"],
            "original_pdf_path": row["original_pdf_path"],
        }
    return payload


def find_storage_job_by_title(*, storage_root: str | Path, query: str) -> StorageQcArtifact | None:
    normalized_query = _normalize_storage_key(query)
    if not normalized_query:
        return None

    artifacts = _discover_storage_qc_artifacts(
        storage_root=storage_root,
        limit=None,
        order_by_recent=True,
    )
    exact_matches: list[StorageQcArtifact] = []
    partial_matches: list[StorageQcArtifact] = []
    for artifact in artifacts:
        normalized_title = _normalize_storage_key(artifact.title)
        if not normalized_title:
            continue
        if normalized_title == normalized_query:
            exact_matches.append(artifact)
        elif normalized_query in normalized_title:
            partial_matches.append(artifact)
    if exact_matches:
        return exact_matches[0]
    if partial_matches:
        return partial_matches[0]
    return None


def _discover_storage_qc_artifacts(
    *,
    storage_root: str | Path,
    limit: int | None = None,
    job_ids: list[str] | None = None,
    order_by_recent: bool = False,
) -> list[StorageQcArtifact]:
    root = Path(storage_root).resolve()
    originals_dir = root / "originals"
    results_dir = root / "results"
    golden_dir = root / "golden"
    job_metadata = _load_storage_job_metadata(root)

    result_by_job_id: dict[str, Path] = {}
    for result_path in sorted(results_dir.glob("job_*.md")):
        result_by_job_id[result_path.stem] = result_path

    golden_by_key: dict[str, Path] = {}
    golden_by_job_preview: dict[str, Path] = {}
    for golden_path in sorted(golden_dir.glob("*.md")):
        golden_by_key[_normalize_storage_key(golden_path.stem)] = golden_path
        preview_match = re.match(r"^(job_[a-z0-9]+)\.preview$", golden_path.stem, flags=re.IGNORECASE)
        if preview_match:
            golden_by_job_preview[preview_match.group(1)] = golden_path

    requested_ids = set(job_ids or [])
    grouped: dict[str, dict[str, Path | str | None]] = {}
    for source_path in sorted(originals_dir.iterdir()):
        if not source_path.is_file():
            continue
        suffix = source_path.suffix.lower()
        if suffix not in {".hwpx", ".pdf"}:
            continue
        stem = source_path.stem
        if not stem.startswith("job_"):
            continue
        job_id = stem.split("-", 1)[0]
        if requested_ids and job_id not in requested_ids:
            continue
        metadata = job_metadata.get(job_id, {})
        title = str(metadata.get("title") or _storage_title_from_original(source_path))
        record = grouped.setdefault(
            job_id,
            {
                "job_id": job_id,
                "title": title,
                "updated_at": metadata.get("updated_at"),
                "hwpx_path": None,
                "pdf_path": None,
                "file_name": metadata.get("file_name"),
            },
        )
        if suffix == ".hwpx" and record.get("hwpx_path") is None:
            record["hwpx_path"] = source_path
        elif suffix == ".pdf" and record.get("pdf_path") is None:
            record["pdf_path"] = source_path

    ordered_items = list(grouped.items())
    if requested_ids:
        index_map = {job_id: index for index, job_id in enumerate(job_ids or [])}
        ordered_items.sort(key=lambda item: index_map.get(item[0], 10**9))
    elif order_by_recent:
        def sort_key(item: tuple[str, dict[str, Path | str | None]]) -> tuple[str, str]:
            updated_at = str(item[1].get("updated_at") or "")
            return (updated_at, item[0])
        ordered_items.sort(key=sort_key, reverse=True)
    else:
        ordered_items.sort(key=lambda item: item[0])

    artifacts: list[StorageQcArtifact] = []
    for job_id, record in ordered_items:
        hwpx_path = record.get("hwpx_path")
        if not isinstance(hwpx_path, Path):
            continue
        title = str(record.get("title") or hwpx_path.stem)
        file_name = str(record.get("file_name") or hwpx_path.name)
        golden_match = (
            golden_by_job_preview.get(job_id)
            or golden_by_key.get(_normalize_storage_key(title))
            or golden_by_key.get(_normalize_storage_key(Path(file_name).stem))
        )
        result_match = result_by_job_id.get(job_id)
        if result_match is None:
            db_result = metadata.get("final_markdown_path")
            if db_result:
                candidate = results_dir / Path(str(db_result)).name
                if candidate.exists():
                    result_match = candidate
        artifacts.append(
            StorageQcArtifact(
                job_id=job_id,
                title=title,
                updated_at=str(record.get("updated_at") or "") or None,
                export_dir=str(hwpx_path.parent),
                hwpx_path=str(hwpx_path),
                pdf_path=str(record["pdf_path"]) if isinstance(record.get("pdf_path"), Path) else None,
                result_md_path=str(result_match) if result_match is not None else None,
                golden_md_path=str(golden_match) if golden_match is not None else None,
            )
        )
        if limit is not None and len(artifacts) >= limit:
            break
    return artifacts


def scaffold_storage_qc_jobs(
    *,
    gov_md_converter_root: str | Path,
    qc_root: str | Path,
    storage_root: str | Path,
    limit: int = 10,
    job_ids: list[str] | None = None,
    autofill: bool = True,
    force: bool = False,
    order_by_recent: bool = True,
    scaffold_runner: ScaffoldRunner = run_gov_md_scaffold,
) -> dict[str, object]:
    discovered = _discover_storage_qc_artifacts(
        storage_root=storage_root,
        limit=limit if job_ids is None else max(limit, len(job_ids)),
        job_ids=job_ids,
        order_by_recent=order_by_recent,
    )
    exported_items: list[dict[str, object]] = []
    for artifact in discovered:
        sample_id = f"storage_{artifact.job_id}"
        existing_sample_dir = Path(qc_root).resolve() / sample_id
        if existing_sample_dir.exists() and not force:
            sample_dir = str(existing_sample_dir)
        else:
            sample_dir = scaffold_runner(
                gov_md_converter_root=gov_md_converter_root,
                source_path=artifact.hwpx_path,
                pdf_path=artifact.pdf_path,
                qc_root=qc_root,
                sample_id=sample_id,
                autofill=autofill,
                force=force,
                sample_status="scratch",
            )
        _attach_storage_sidecars(
            sample_dir=sample_dir,
            result_md_path=artifact.result_md_path,
            golden_md_path=artifact.golden_md_path,
            artifact=artifact,
        )
        item_payload = artifact.to_dict()
        item_payload["scaffold_sample_dir"] = sample_dir
        exported_items.append(item_payload)

    return {
        "limit": limit,
        "job_ids": list(job_ids or []),
        "order_by_recent": order_by_recent,
        "storage_root": str(Path(storage_root).resolve()),
        "qc_root": str(Path(qc_root).resolve()),
        "selected_count": len(discovered),
        "scaffolded_count": len(exported_items),
        "items": exported_items,
    }


def _attach_storage_sidecars(
    *,
    sample_dir: str | Path,
    result_md_path: str | Path | None,
    golden_md_path: str | Path | None,
    artifact: StorageQcArtifact,
) -> None:
    resolved_sample_dir = Path(sample_dir).resolve()
    bridge_payload = {
        "job_id": artifact.job_id,
        "title": artifact.title,
        "hwpx_path": artifact.hwpx_path,
        "pdf_path": artifact.pdf_path,
        "result_md_path": artifact.result_md_path,
        "golden_md_path": artifact.golden_md_path,
    }
    if result_md_path is not None:
        shutil.copy2(Path(result_md_path).resolve(), resolved_sample_dir / "storage_rendered.md")
    if golden_md_path is not None:
        shutil.copy2(Path(golden_md_path).resolve(), resolved_sample_dir / "golden.md")
    (resolved_sample_dir / "storage_bridge.json").write_text(
        json.dumps(bridge_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    meta_path = resolved_sample_dir / "meta.json"
    if meta_path.exists():
        meta_payload = json.loads(meta_path.read_text(encoding="utf-8"))
        meta_payload["source"] = "govpress-storage"
        meta_payload["storage_job_id"] = artifact.job_id
        meta_payload["storage_title"] = artifact.title
        if artifact.result_md_path is not None:
            meta_payload["storage_result_md"] = Path(artifact.result_md_path).name
        if artifact.golden_md_path is not None:
            meta_payload["storage_golden_md"] = Path(artifact.golden_md_path).name
        meta_path.write_text(json.dumps(meta_payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_storage_backed_qc_pipeline(
    *,
    target_date: date,
    output_root: str | Path,
    gov_md_converter_root: str | Path,
    qc_root: str | Path,
    storage_root: str | Path,
    limit: int | None = None,
    autofill: bool = True,
    force: bool = False,
    scaffold_runner: ScaffoldRunner = run_gov_md_scaffold,
    command_runner: GovMdCommandRunner = run_gov_md_qc_command,
) -> dict[str, object]:
    resolved_output_root = Path(output_root).resolve()
    dated_root = resolved_output_root / target_date.isoformat()
    dated_root.mkdir(parents=True, exist_ok=True)

    discovered = _discover_storage_qc_artifacts(storage_root=storage_root, limit=limit)
    exported_items: list[dict[str, object]] = []
    for artifact in discovered:
        sample_dir = scaffold_runner(
            gov_md_converter_root=gov_md_converter_root,
            source_path=artifact.hwpx_path,
            pdf_path=artifact.pdf_path,
            qc_root=qc_root,
            sample_id=f"storage_{artifact.job_id}",
            autofill=autofill,
            force=force,
            sample_status="scratch",
        )
        _attach_storage_sidecars(
            sample_dir=sample_dir,
            result_md_path=artifact.result_md_path,
            golden_md_path=artifact.golden_md_path,
            artifact=artifact,
        )
        item_payload = artifact.to_dict()
        item_payload["scaffold_sample_dir"] = sample_dir
        exported_items.append(item_payload)

    export_report = {
        "date": target_date.isoformat(),
        "output_root": str(dated_root),
        "storage_root": str(Path(storage_root).resolve()),
        "ensure_fresh": False,
        "served_stale": False,
        "stale_reason": "storage_corpus",
        "requested_news_item_ids": [],
        "missing_news_item_ids": [],
        "selected_count": len(exported_items),
        "exported_count": len(exported_items),
        "scaffolded_count": len(exported_items),
        "items": exported_items,
        "source_kind": "storage_backed_corpus",
    }

    _, _, converter_build_qc_pipeline_report, _ = _get_gov_md_converter_qc_pipeline()
    return converter_build_qc_pipeline_report(
        target_date=target_date,
        output_root=output_root,
        export_report=export_report,
        gov_md_converter_root=gov_md_converter_root,
        qc_root=qc_root,
        command_runner=command_runner,
    )


def run_policy_briefing_qc_pipeline(
    *,
    client: PolicyBriefingClient,
    catalog,
    target_date: date,
    output_root: str | Path,
    gov_md_converter_root: str | Path,
    qc_root: str | Path,
    news_item_ids: list[str] | None = None,
    limit: int | None = None,
    include_pdf: bool = True,
    ensure_fresh: bool = True,
    autofill: bool = True,
    force: bool = False,
    sample_status: str = "scratch",
    scaffold_runner: ScaffoldRunner = run_gov_md_scaffold,
    command_runner: GovMdCommandRunner = run_gov_md_qc_command,
) -> dict[str, object]:
    export_report = export_policy_briefings_for_qc(
        client=client,
        catalog=catalog,
        target_date=target_date,
        output_root=output_root,
        news_item_ids=news_item_ids,
        limit=limit,
        include_pdf=include_pdf,
        ensure_fresh=ensure_fresh,
        scaffold_runner=scaffold_runner,
        gov_md_converter_root=gov_md_converter_root,
        qc_root=qc_root,
        autofill=autofill,
        force=force,
        sample_status=sample_status,
    )
    _, _, converter_build_qc_pipeline_report, _ = _get_gov_md_converter_qc_pipeline()
    return converter_build_qc_pipeline_report(
        target_date=target_date,
        output_root=output_root,
        export_report=export_report,
        gov_md_converter_root=gov_md_converter_root,
        qc_root=qc_root,
        command_runner=command_runner,
    )


def run_local_hwpx_qc_pipeline(
    *,
    target_date: date,
    output_root: str | Path,
    gov_md_converter_root: str | Path,
    qc_root: str | Path,
    source_root: str | Path,
    limit: int | None = None,
    mode: str = "low",
    autofill: bool = True,
    force: bool = False,
    batch_runner: GovMdBatchRunner = run_gov_md_batch_local,
    command_runner: GovMdCommandRunner = run_gov_md_qc_command,
) -> dict[str, object]:
    _, _, _, converter_run_local_hwpx_qc_pipeline = _get_gov_md_converter_qc_pipeline()
    return converter_run_local_hwpx_qc_pipeline(
        target_date=target_date,
        output_root=output_root,
        gov_md_converter_root=gov_md_converter_root,
        qc_root=qc_root,
        source_root=source_root,
        limit=limit,
        mode=mode,
        autofill=autofill,
        force=force,
        batch_runner=batch_runner,
        command_runner=command_runner,
    )
