from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Callable

from .policy_briefing import PolicyBriefingAttachment, PolicyBriefingCatalogResult, PolicyBriefingClient, PolicyBriefingItem


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


def resolve_qc_export_root(*, storage_root: str | Path) -> Path:
    return Path(storage_root).resolve().parent / "exports" / "policy_briefing_qc"


def resolve_dashboard_paths(qc_export_root: str | Path) -> tuple[Path, Path]:
    resolved_root = Path(qc_export_root).resolve()
    dashboard_dir = resolved_root / "dashboard"
    return dashboard_dir / "index.html", dashboard_dir / "dashboard.json"


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
    resolved_root = Path(gov_md_converter_root).resolve()
    script_path = resolved_root / "scripts" / "run_hwpx_qc.py"
    if not script_path.exists():
        raise FileNotFoundError(f"gov-md-converter QC CLI not found: {script_path}")

    cmd = [
        sys.executable,
        str(script_path),
        command,
        "--root",
        str(qc_root),
    ]
    if command == "regression":
        cmd.append("--json")
    else:
        if output_path is not None:
            cmd.extend(["--output", str(Path(output_path).resolve())])
        cmd.append("--json")

    result = subprocess.run(
        cmd,
        cwd=resolved_root,
        check=False,
        capture_output=True,
        text=True,
    )
    payload: dict[str, object] | list[object] | None = None
    stdout = result.stdout.strip()
    if stdout:
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            payload = None
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": result.stderr.strip(),
        "output_path": str(Path(output_path).resolve()) if output_path is not None else None,
        "payload": payload,
    }


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
    resolved_root = Path(gov_md_converter_root).resolve()
    script_path = resolved_root / "scripts" / "run_hwpx_qc.py"
    if not script_path.exists():
        raise FileNotFoundError(f"gov-md-converter QC CLI not found: {script_path}")

    cmd = [
        sys.executable,
        str(script_path),
        "batch-local",
        "--source-root",
        str(Path(source_root).resolve()),
        "--output-root",
        str(Path(qc_root).resolve()),
        "--mode",
        mode,
        "--json",
    ]
    if limit is not None:
        cmd.extend(["--limit", str(limit)])
    if not autofill:
        cmd.append("--no-autofill")
    if force:
        cmd.append("--force")

    result = subprocess.run(
        cmd,
        cwd=resolved_root,
        check=False,
        capture_output=True,
        text=True,
    )
    stdout = result.stdout.strip()
    payload: dict[str, object] | None = None
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = None
    return {
        "command": "batch-local",
        "returncode": result.returncode,
        "stdout": stdout,
        "stderr": result.stderr.strip(),
        "payload": payload,
    }


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

    for item in items:
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
    }


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
    if export_report["missing_news_item_ids"]:
        return {
            "date": target_date.isoformat(),
            "export": export_report,
            "reports_dir": None,
            "qc_commands": [],
            "summary": {
                "exported_count": export_report["exported_count"],
                "scaffolded_count": export_report["scaffolded_count"],
                "review_required_count": None,
                "proposal_count": None,
                "draft_count": None,
            },
        }

    reports_dir = Path(output_root).resolve() / target_date.isoformat() / "gov_md_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    qc_steps: list[tuple[str, Path | None]] = [
        ("regression", reports_dir / "regression.json"),
        ("triage", reports_dir / "triage_report.json"),
        ("suggest-fix", reports_dir / "suggest_fix.json"),
        ("patch-template", reports_dir / "patch_templates.json"),
        ("fix-plan", reports_dir / "fix_plan.json"),
        ("apply-fix-hint", reports_dir / "apply_fix_hint.json"),
        ("auto-patch-draft", reports_dir / "auto_patch_draft.json"),
    ]
    qc_results: list[dict[str, object]] = []
    for command, output_path in qc_steps:
        result = command_runner(
            gov_md_converter_root=gov_md_converter_root,
            command=command,
            qc_root=qc_root,
            output_path=None if command == "regression" else output_path,
        )
        if command == "regression" and result.get("payload") is not None:
            (reports_dir / "regression.json").write_text(
                json.dumps(result["payload"], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result["output_path"] = str((reports_dir / "regression.json").resolve())
        qc_results.append(result)

    triage_payload = next(
        (entry.get("payload") for entry in qc_results if entry["command"] == "triage" and isinstance(entry.get("payload"), dict)),
        None,
    )
    suggest_payload = next(
        (entry.get("payload") for entry in qc_results if entry["command"] == "suggest-fix" and isinstance(entry.get("payload"), dict)),
        None,
    )
    auto_patch_payload = next(
        (
            entry.get("payload")
            for entry in qc_results
            if entry["command"] == "auto-patch-draft" and isinstance(entry.get("payload"), dict)
        ),
        None,
    )

    return {
        "date": target_date.isoformat(),
        "export": export_report,
        "reports_dir": str(reports_dir),
        "qc_commands": qc_results,
        "summary": {
            "exported_count": export_report["exported_count"],
            "scaffolded_count": export_report["scaffolded_count"],
            "review_required_count": (
                triage_payload.get("summary", {}).get("review_required_count")
                if isinstance(triage_payload, dict)
                else None
            ),
            "proposal_count": (
                suggest_payload.get("proposal_count")
                if isinstance(suggest_payload, dict)
                else None
            ),
            "draft_count": (
                auto_patch_payload.get("draft_count")
                if isinstance(auto_patch_payload, dict)
                else None
            ),
        },
    }


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
    resolved_output_root = Path(output_root).resolve()
    dated_root = resolved_output_root / target_date.isoformat()
    dated_root.mkdir(parents=True, exist_ok=True)

    batch_result = batch_runner(
        gov_md_converter_root=gov_md_converter_root,
        source_root=source_root,
        qc_root=qc_root,
        limit=limit,
        mode=mode,
        autofill=autofill,
        force=force,
    )
    batch_payload = batch_result.get("payload") if isinstance(batch_result.get("payload"), dict) else {}
    candidates = batch_payload.get("candidates") if isinstance(batch_payload.get("candidates"), list) else []
    exported_items: list[dict[str, object]] = []
    for item in candidates:
        if not isinstance(item, dict):
            continue
        sample_id = item.get("sample_id")
        exported_items.append(
            {
                "news_item_id": str(sample_id),
                "title": Path(str(item.get("source_path", sample_id))).stem,
                "export_dir": str(Path(str(item.get("source_path", ""))).resolve().parent),
                "hwpx_path": item.get("source_path"),
                "pdf_path": item.get("pdf_path"),
                "metadata_path": None,
                "scaffold_sample_dir": str(Path(qc_root).resolve() / str(sample_id)),
                "risk_score": item.get("risk_score"),
                "reasons": item.get("reasons", []),
                "doc_type": item.get("doc_type"),
            }
        )

    export_report = {
        "date": target_date.isoformat(),
        "output_root": str(dated_root),
        "source_root": str(Path(source_root).resolve()),
        "ensure_fresh": False,
        "served_stale": False,
        "stale_reason": "local_corpus",
        "requested_news_item_ids": [],
        "missing_news_item_ids": [],
        "selected_count": len(exported_items),
        "exported_count": len(exported_items),
        "scaffolded_count": len(exported_items),
        "items": exported_items,
        "mode": mode,
        "limit": limit,
        "source_kind": "local_hwpx_corpus",
    }

    reports_dir = dated_root / "gov_md_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    batch_report_path = reports_dir / "batch_local.json"
    batch_report_path.write_text(json.dumps(batch_result, ensure_ascii=False, indent=2), encoding="utf-8")

    qc_steps: list[tuple[str, Path | None]] = [
        ("regression", reports_dir / "regression.json"),
        ("triage", reports_dir / "triage_report.json"),
        ("suggest-fix", reports_dir / "suggest_fix.json"),
        ("patch-template", reports_dir / "patch_templates.json"),
        ("fix-plan", reports_dir / "fix_plan.json"),
        ("apply-fix-hint", reports_dir / "apply_fix_hint.json"),
        ("auto-patch-draft", reports_dir / "auto_patch_draft.json"),
    ]
    qc_results: list[dict[str, object]] = [dict(batch_result, output_path=str(batch_report_path.resolve()))]
    for command, output_path in qc_steps:
        result = command_runner(
            gov_md_converter_root=gov_md_converter_root,
            command=command,
            qc_root=qc_root,
            output_path=None if command == "regression" else output_path,
        )
        if command == "regression" and result.get("payload") is not None:
            (reports_dir / "regression.json").write_text(
                json.dumps(result["payload"], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            result["output_path"] = str((reports_dir / "regression.json").resolve())
        qc_results.append(result)

    triage_payload = next(
        (entry.get("payload") for entry in qc_results if entry["command"] == "triage" and isinstance(entry.get("payload"), dict)),
        None,
    )
    suggest_payload = next(
        (entry.get("payload") for entry in qc_results if entry["command"] == "suggest-fix" and isinstance(entry.get("payload"), dict)),
        None,
    )
    auto_patch_payload = next(
        (
            entry.get("payload")
            for entry in qc_results
            if entry["command"] == "auto-patch-draft" and isinstance(entry.get("payload"), dict)
        ),
        None,
    )

    return {
        "date": target_date.isoformat(),
        "export": export_report,
        "reports_dir": str(reports_dir),
        "qc_commands": qc_results,
        "summary": {
            "exported_count": export_report["exported_count"],
            "scaffolded_count": export_report["scaffolded_count"],
            "review_required_count": (
                triage_payload.get("summary", {}).get("review_required_count")
                if isinstance(triage_payload, dict)
                else None
            ),
            "proposal_count": (
                suggest_payload.get("proposal_count")
                if isinstance(suggest_payload, dict)
                else None
            ),
            "draft_count": (
                auto_patch_payload.get("draft_count")
                if isinstance(auto_patch_payload, dict)
                else None
            ),
        },
    }
