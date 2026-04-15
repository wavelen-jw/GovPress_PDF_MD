from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
import tempfile
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import time
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_GOV_MD_ROOT = Path(
    __import__("os").environ.get("GOV_MD_CONVERTER_ROOT", PROJECT_ROOT.parent / "gov-md-converter")
).resolve()
if str(DEFAULT_GOV_MD_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_GOV_MD_ROOT))
DEFAULT_GOV_MD_EXPORT_ROOT = DEFAULT_GOV_MD_ROOT / "exports" / "policy_briefing_qc"

from src.qc_dashboard import build_dashboard_payload
from src.qc_issue import build_issue_payload, load_report as load_issue_report
from src.qc_report import build_markdown_summary
from server.app.adapters.policy_briefing import (
    PolicyBriefingCatalog,
    PolicyBriefingClient,
    find_cached_policy_briefing_by_title,
)
from server.app.adapters.policy_briefing_qc import (
    export_policy_briefings_for_qc,
    find_storage_job_by_title,
    run_gov_md_scaffold,
    scaffold_storage_qc_jobs,
)

DEFAULT_EXPORT_ROOT = Path(
    __import__("os").environ.get("GOVPRESS_QC_EXPORT_ROOT", DEFAULT_GOV_MD_EXPORT_ROOT)
).resolve()
DEFAULT_QC_ROOT = Path(
    __import__("os").environ.get("GOVPRESS_QC_ROOT", DEFAULT_GOV_MD_ROOT / "tests" / "manual_samples" / "policy_briefings")
).resolve()
DEFAULT_REMOTE_QC_ROOT = Path(
    __import__("os").environ.get("GOVPRESS_REMOTE_QC_ROOT", DEFAULT_GOV_MD_ROOT / "tests" / "manual_samples" / "storage_batch")
).resolve()
DEFAULT_CURATED_QC_ROOT = Path(
    __import__("os").environ.get("GOVPRESS_CURATED_QC_ROOT", DEFAULT_GOV_MD_ROOT / "tests" / "qc_samples")
).resolve()
DEFAULT_STATE_ROOT = Path(
    __import__("os").environ.get(
        "GOVPRESS_OPENCLAW_STATE_ROOT",
        Path.home() / ".openclaw" / "agents" / "govpress_qc_ops" / "state",
    )
).resolve()
DEFAULT_OPENCLAW_MEDIA_INBOUND_ROOT = Path(
    __import__("os").environ.get(
        "GOVPRESS_OPENCLAW_MEDIA_INBOUND_ROOT",
        Path.home() / ".openclaw" / "media" / "inbound",
    )
).resolve()
MOBILE_CONSTANTS_PATH = PROJECT_ROOT / "mobile" / "src" / "constants.ts"
DEPLOY_ENV_PATH = PROJECT_ROOT / "deploy" / "wsl" / ".env"
DEFAULT_DASHBOARD_PATH = "/v1/policy-briefings/qc/dashboard"
DEFAULT_TELEGRAM_ACCOUNT = str(__import__("os").environ.get("GOVPRESS_TELEGRAM_ACCOUNT", "govpress_bot")).strip()
DEFAULT_TELEGRAM_CHANNEL = "telegram"
DEFAULT_TELEGRAM_SENDER_ID = str(
    __import__("os").environ.get("GOVPRESS_QC_DEFAULT_SENDER_ID")
    or __import__("os").environ.get("TELEGRAM_CHAT_ID")
    or ""
).strip()
DEFAULT_QC_WORKER_AGENT = "govpress_qc_worker"
DEFAULT_CODEX_MODEL = "gpt-5.4"
DEFAULT_QC_MEMORY_ROOT = "tests/manual_samples/qc_memory"
DEFAULT_STORAGE_ROOT = (PROJECT_ROOT / "deploy" / "wsl" / "data" / "storage").resolve()
AUTO_JUDGE_TEMPLATE_PATH = DEFAULT_GOV_MD_ROOT / ".agents" / "skills" / "hwpx-md-qc-autopilot" / "auto_judge_template.md"
MAX_BATCH_TURNS = 40
MAX_BATCH_SAMPLES = 8
AUTO_MAX_ATTEMPTS = 5
_POLICY_SAMPLE_ID_RE = re.compile(r"^policy_briefing_(\d{4})_(\d{2})_(\d{2})_(\d+)$")


@dataclass(frozen=True)
class ServerPreset:
    key: str
    label: str
    url: str


@dataclass(frozen=True)
class TelegramContext:
    sender_id: str | None
    message_id: str | None
    media_paths: tuple[Path, ...]


@dataclass(frozen=True)
class SampleRecord:
    sample_id: str
    sample_dir: Path
    status: str
    source_name: str
    has_golden: bool
    has_review: bool


@dataclass(frozen=True)
class PolicyQueueEntry:
    sample: SampleRecord
    title: str
    approve_date: str
    news_item_id: str
    review_required: bool
    risk_score: int
    finding_count: int
    hard_finding_count: int
    defect_classes: tuple[str, ...]


@dataclass(frozen=True)
class AutoJudgeResult:
    decision: str
    confidence: str
    blocking_findings: tuple[str, ...]
    next_fix_instruction: str
    user_summary: str


def _load_deploy_env_value(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if value:
        return value
    if DEPLOY_ENV_PATH.exists():
        for line in DEPLOY_ENV_PATH.read_text(encoding="utf-8").splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _valid_date(value: str) -> str:
    if value == "latest":
        return value
    date.fromisoformat(value)
    return value


def _valid_sample_id(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", value):
        raise argparse.ArgumentTypeError("sample_id must match [A-Za-z0-9._-]+")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _parse_sender_id(message: str) -> str | None:
    match = re.search(r'"sender_id"\s*:\s*"([^"]+)"', message)
    if match:
        return match.group(1)
    match = re.search(r'"id"\s*:\s*"([^"]+)"', message)
    if match:
        return match.group(1)
    return None


def _parse_message_id(message: str) -> str | None:
    match = re.search(r'"message_id"\s*:\s*"([^"]+)"', message)
    return match.group(1) if match else None


def _extract_media_paths(message: str) -> tuple[Path, ...]:
    matches = re.findall(r"\[media attached:\s*([^\]\n|]+?)(?:\s+\([^)]+\))?(?:\s*\|\s*[^\]]+)?\]", message)
    paths: list[Path] = []
    for raw in matches:
        candidate = Path(raw.strip())
        if candidate.exists():
            paths.append(candidate)
    return tuple(paths)


def _find_recent_inbound_markdown(
    media_root: Path | None = None,
    *,
    max_age_seconds: int = 15 * 60,
) -> tuple[Path, ...]:
    media_root = (media_root or DEFAULT_OPENCLAW_MEDIA_INBOUND_ROOT).resolve()
    if not media_root.exists():
        return ()
    now = time.time()
    candidates: list[tuple[float, Path]] = []
    for candidate in media_root.glob("*.md"):
        try:
            stat = candidate.stat()
        except OSError:
            continue
        age_seconds = now - stat.st_mtime
        if age_seconds < 0 or age_seconds > max_age_seconds:
            continue
        candidates.append((stat.st_mtime, candidate))
    candidates.sort(key=lambda item: item[0], reverse=True)
    return tuple(path for _, path in candidates[:1])


def _fallback_sender_id_from_state_root(state_root: Path) -> str | None:
    session_dir = state_root / "telegram_qc_sessions"
    if not session_dir.exists():
        return None
    session_files = sorted(session_dir.glob("*.json"))
    if len(session_files) == 1:
        return session_files[0].stem
    return None


def build_telegram_context(message: str, *, state_root: Path | None = None) -> TelegramContext:
    sender_id = _parse_sender_id(message) or DEFAULT_TELEGRAM_SENDER_ID
    if not sender_id and state_root is not None:
        sender_id = _fallback_sender_id_from_state_root(state_root)
    return TelegramContext(
        sender_id=sender_id or None,
        message_id=_parse_message_id(message),
        media_paths=_extract_media_paths(message),
    )


def _session_state_path(state_root: Path, sender_id: str) -> Path:
    return state_root / "telegram_qc_sessions" / f"{sender_id}.json"


def _load_session_state(state_root: Path, sender_id: str) -> dict[str, Any]:
    path = _session_state_path(state_root, sender_id)
    if not path.exists():
        return {}
    return _load_json(path)


def _save_session_state(state_root: Path, sender_id: str, payload: dict[str, Any]) -> Path:
    path = _session_state_path(state_root, sender_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _background_auto_report_dir(state_root: Path) -> Path:
    path = state_root / "auto_batch_reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _batch_report_slug(batch_id: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(batch_id).strip()) or "auto-batch"


def _auto_metrics_defaults() -> dict[str, Any]:
    return {
        "auto_batch_started_at": "",
        "auto_batch_finished_at": "",
        "auto_batch_metrics": {"sample_count": 0, "completed_count": 0},
        "auto_sample_metrics": {},
        "auto_batch_report_path": "",
    }


def _ensure_auto_sample_metric(
    state: dict[str, Any],
    *,
    sample_id: str,
    title: str,
    queue_position: int,
) -> dict[str, Any]:
    metrics = state.setdefault("auto_sample_metrics", {})
    sample_metric = metrics.get(sample_id)
    if not isinstance(sample_metric, dict):
        sample_metric = {
            "sample_id": sample_id,
            "title": title,
            "queue_position": queue_position,
            "attempts": 0,
            "started_at": _now_iso(),
            "finished_at": "",
            "outcome": "",
            "total_duration_ms": 0,
            "inspect_total_ms": 0,
            "fix_total_ms": 0,
            "judge_total_ms": 0,
            "bottleneck_stage": "",
            "latest_decision": "",
            "attempt_metrics": [],
        }
        metrics[sample_id] = sample_metric
    else:
        sample_metric["title"] = title or sample_metric.get("title", "")
        sample_metric["queue_position"] = queue_position
        if not sample_metric.get("started_at"):
            sample_metric["started_at"] = _now_iso()
    return sample_metric


def _finalize_auto_sample_metric(
    state: dict[str, Any],
    *,
    sample_id: str,
    outcome: str,
) -> None:
    sample_metric = state.get("auto_sample_metrics", {}).get(sample_id)
    if not isinstance(sample_metric, dict):
        return
    sample_metric["outcome"] = outcome
    if not sample_metric.get("finished_at"):
        sample_metric["finished_at"] = _now_iso()
    started_at = str(sample_metric.get("started_at", "")).strip()
    finished_at = str(sample_metric.get("finished_at", "")).strip()
    if started_at and finished_at:
        try:
            started = datetime.fromisoformat(started_at)
            finished = datetime.fromisoformat(finished_at)
            sample_metric["total_duration_ms"] = max(int((finished - started).total_seconds() * 1000), 0)
        except ValueError:
            sample_metric["total_duration_ms"] = int(sample_metric.get("total_duration_ms", 0) or 0)
    stage_totals = {
        "inspect": int(sample_metric.get("inspect_total_ms", 0) or 0),
        "fix": int(sample_metric.get("fix_total_ms", 0) or 0),
        "judge": int(sample_metric.get("judge_total_ms", 0) or 0),
    }
    sample_metric["bottleneck_stage"] = max(stage_totals, key=stage_totals.get) if any(stage_totals.values()) else ""


def _update_auto_batch_metrics(state: dict[str, Any]) -> None:
    sample_metrics = state.get("auto_sample_metrics", {})
    completed = [
        item
        for item in sample_metrics.values()
        if isinstance(item, dict) and str(item.get("finished_at", "")).strip()
    ]
    state["auto_batch_metrics"] = {
        "sample_count": len(sample_metrics),
        "completed_count": len(completed),
    }


def _write_auto_batch_report(state_root: Path, sender_id: str, state: dict[str, Any]) -> Path | None:
    batch_id = str(state.get("auto_batch_id", "")).strip()
    if not batch_id:
        return None
    _update_auto_batch_metrics(state)
    report_dir = _background_auto_report_dir(state_root)
    report_path = report_dir / f"{_batch_report_slug(batch_id)}-{sender_id}.json"
    payload = {
        "batch_id": batch_id,
        "sender_id": sender_id,
        "source": state.get("auto_source", "policy_briefing"),
        "requested_count": int(state.get("auto_requested_count", 0) or 0),
        "queue_sample_ids": [str(item) for item in state.get("auto_queue_sample_ids", []) if isinstance(item, str)],
        "queue_index": int(state.get("auto_queue_index", 0) or 0),
        "current_sample_id": str(state.get("auto_current_sample_id", "")).strip(),
        "current_status": str(state.get("auto_current_status", "")).strip(),
        "auto_mode": bool(state.get("auto_mode")),
        "started_at": str(state.get("auto_batch_started_at", "")).strip(),
        "finished_at": str(state.get("auto_batch_finished_at", "")).strip(),
        "summary": dict(state.get("auto_batch_metrics", {})),
        "results": list(state.get("auto_results", [])),
        "samples": [
            item
            for item in sorted(
                (
                    value
                    for value in state.get("auto_sample_metrics", {}).values()
                    if isinstance(value, dict)
                ),
                key=lambda item: (int(item.get("queue_position", 0) or 0), str(item.get("sample_id", ""))),
            )
        ],
    }
    report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    state["auto_batch_report_path"] = str(report_path)
    return report_path


def _qc_memory_root(gov_md_root: Path) -> Path:
    return gov_md_root / DEFAULT_QC_MEMORY_ROOT


def _global_rules_path(gov_md_root: Path) -> Path:
    return _qc_memory_root(gov_md_root) / "global_ground_rules.md"


def _active_batch_path(gov_md_root: Path) -> Path:
    return _qc_memory_root(gov_md_root) / "active_qc_batch.md"


def _sample_note_path(gov_md_root: Path, sample_id: str) -> Path:
    return _qc_memory_root(gov_md_root) / "sample_notes" / f"{sample_id}.md"


def _ensure_qc_memory_files(gov_md_root: Path) -> dict[str, Path]:
    memory_root = _qc_memory_root(gov_md_root)
    memory_root.mkdir(parents=True, exist_ok=True)
    sample_notes_root = memory_root / "sample_notes"
    sample_notes_root.mkdir(parents=True, exist_ok=True)
    global_rules = _global_rules_path(gov_md_root)
    active_batch = _active_batch_path(gov_md_root)
    if not global_rules.exists():
        global_rules.write_text("# Global Ground Rules\n\n", encoding="utf-8")
    if not active_batch.exists():
        active_batch.write_text("# Active QC Batch\n\n", encoding="utf-8")
    return {
        "memory_root": memory_root,
        "global_rules": global_rules,
        "active_batch": active_batch,
        "sample_notes_root": sample_notes_root,
    }


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _sample_record(sample_dir: Path) -> SampleRecord:
    meta = _load_json(sample_dir / "meta.json") if (sample_dir / "meta.json").exists() else {}
    status = str(meta.get("sample_status", "")).strip() or ("curated" if (sample_dir / "golden_slices.json").exists() else "scratch")
    return SampleRecord(
        sample_id=sample_dir.name,
        sample_dir=sample_dir,
        status=status,
        source_name=str(meta.get("source_hwpx", "source.hwpx")),
        has_golden=(sample_dir / "golden.md").exists(),
        has_review=(sample_dir / "review.md").exists(),
    )


def _list_samples(remote_qc_root: Path) -> list[SampleRecord]:
    records = [_sample_record(path) for path in sorted(remote_qc_root.iterdir()) if path.is_dir() and (path / "source.hwpx").exists()]
    records.sort(key=lambda item: (item.status == "curated", item.sample_id))
    return records


def _build_policy_catalog(storage_root: Path) -> PolicyBriefingCatalog:
    return PolicyBriefingCatalog(
        client=PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY")),
        cache_path=storage_root / "policy_briefing_catalog.json",
    )


def _approve_datetime(value: str) -> datetime:
    for fmt in ("%m/%d/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    if len(value) >= 10:
        return datetime.fromisoformat(value[:10])
    raise ValueError(f"Unsupported approve_date: {value}")


def _collect_latest_policy_briefing_items(
    *,
    storage_root: Path,
    limit: int,
    lookback_days: int = 14,
) -> list[Any]:
    catalog = _build_policy_catalog(storage_root)
    items_by_id: dict[str, Any] = {}
    for offset in range(lookback_days):
        target_date = date.today() - timedelta(days=offset)
        result = catalog.list_cached_items_with_status(target_date=target_date, ensure_fresh=True)
        for item in result.items:
            if item.news_item_id not in items_by_id:
                items_by_id[item.news_item_id] = item
        if len(items_by_id) >= limit:
            break
    items = list(items_by_id.values())
    items.sort(key=lambda item: _approve_datetime(item.approve_date), reverse=True)
    return items[:limit]


def _load_policy_meta(sample_dir: Path) -> dict[str, str]:
    metadata_path = sample_dir / "metadata.json"
    if metadata_path.exists():
        payload = _load_json(metadata_path)
        return {
            "title": str(payload.get("title", "")).strip(),
            "approve_date": str(payload.get("approve_date", "")).strip(),
            "news_item_id": str(payload.get("news_item_id", "")).strip(),
        }
    meta_path = sample_dir / "meta.json"
    if meta_path.exists():
        payload = _load_json(meta_path)
        return {
            "title": str(payload.get("title", "")).strip(),
            "approve_date": str(payload.get("approve_date", "")).strip(),
            "news_item_id": str(payload.get("news_item_id", "")).strip(),
        }
    return {"title": "", "approve_date": "", "news_item_id": ""}


def _load_qc_triage_modules() -> tuple[Any, Any]:
    root = DEFAULT_GOV_MD_ROOT.resolve()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from src.hwpx_qc_runner import run_qc_for_manifest  # type: ignore
    from src.hwpx_qc_triage import build_triage_entry  # type: ignore

    return run_qc_for_manifest, build_triage_entry


def _evaluate_policy_queue(sample_dirs: list[Path]) -> dict[str, dict[str, Any]]:
    run_qc_for_manifest, build_triage_entry = _load_qc_triage_modules()
    evaluations: dict[str, dict[str, Any]] = {}
    for sample_dir in sample_dirs:
        manifest_path = sample_dir / "assertions.json"
        if not manifest_path.exists():
            continue
        result = run_qc_for_manifest(manifest_path)
        triage = build_triage_entry(manifest_path, result).to_dict()
        evaluations[sample_dir.name] = triage
    return evaluations


def _scaffold_latest_policy_queue(
    *,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    storage_root: Path,
    limit: int = 20,
) -> list[PolicyQueueEntry]:
    items = _collect_latest_policy_briefing_items(storage_root=storage_root, limit=limit)
    curated_ids = {path.name for path in DEFAULT_CURATED_QC_ROOT.iterdir() if path.is_dir()}
    queued_items = [item for item in items if f"policy_briefing_{_approve_datetime(item.approve_date):%Y_%m_%d}_{item.news_item_id}" not in curated_ids]
    if not queued_items:
        return []

    grouped: dict[date, list[Any]] = {}
    item_by_sample_id: dict[str, Any] = {}
    for item in queued_items:
        approved_at = _approve_datetime(item.approve_date).date()
        sample_id = f"policy_briefing_{approved_at:%Y_%m_%d}_{item.news_item_id}"
        item_by_sample_id[sample_id] = item
        if (remote_qc_root / sample_id).exists():
            continue
        grouped.setdefault(approved_at, []).append(item)

    for target_date, day_items in grouped.items():
        export_policy_briefings_for_qc(
            client=PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY")),
            catalog=_build_policy_catalog(storage_root),
            target_date=target_date,
            output_root=export_root,
            news_item_ids=[item.news_item_id for item in day_items],
            include_pdf=True,
            ensure_fresh=True,
            scaffold_runner=run_gov_md_scaffold,
            gov_md_converter_root=gov_md_root,
            qc_root=remote_qc_root,
            autofill=True,
            force=False,
            sample_status="scratch",
        )

    sample_dirs = [remote_qc_root / sample_id for sample_id in item_by_sample_id if (remote_qc_root / sample_id / "assertions.json").exists()]
    evaluations = _evaluate_policy_queue(sample_dirs)

    entries: list[PolicyQueueEntry] = []
    for sample_id, item in item_by_sample_id.items():
        sample_dir = remote_qc_root / sample_id
        if not sample_dir.exists():
            continue
        sample = _sample_record(sample_dir)
        triage = evaluations.get(sample_id, {})
        meta = _load_policy_meta(sample_dir)
        title = meta["title"] or str(item.title)
        approve_date = meta["approve_date"] or str(item.approve_date)
        news_item_id = meta["news_item_id"] or str(item.news_item_id)
        entries.append(
            PolicyQueueEntry(
                sample=sample,
                title=title,
                approve_date=approve_date,
                news_item_id=news_item_id,
                review_required=bool(triage.get("review_required", sample.status != "curated")),
                risk_score=int(triage.get("risk_score", 0) or 0),
                finding_count=int(triage.get("finding_count", 0) or 0),
                hard_finding_count=int(triage.get("hard_finding_count", 0) or 0),
                defect_classes=tuple(str(value) for value in triage.get("defect_classes", []) if str(value)),
            )
        )
    entries.sort(
        key=lambda entry: (
            -int(entry.review_required),
            -entry.hard_finding_count,
            -entry.risk_score,
            -entry.finding_count,
            entry.sample.sample_id,
        )
    )
    return entries


def _auto_queue_entries(
    *,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    storage_root: Path,
    limit: int,
) -> list[PolicyQueueEntry]:
    entries = _scaffold_latest_policy_queue(
        export_root=export_root,
        gov_md_root=gov_md_root,
        remote_qc_root=remote_qc_root,
        storage_root=storage_root,
        limit=limit,
    )
    return [entry for entry in entries if entry.review_required]


def _auto_state_defaults() -> dict[str, Any]:
    return {
        "auto_mode": False,
        "auto_source": "policy_briefing",
        "auto_requested_count": 0,
        "auto_candidate_news_ids": [],
        "auto_queue_sample_ids": [],
        "auto_queue_index": 0,
        "auto_current_sample_id": "",
        "auto_current_attempt": 0,
        "auto_current_status": "",
        "auto_pass_gate": "code+ai",
        "auto_max_attempts": AUTO_MAX_ATTEMPTS,
        "auto_results": [],
        **_auto_metrics_defaults(),
    }


def _apply_auto_state(state: dict[str, Any], **updates: Any) -> dict[str, Any]:
    merged = {**_auto_state_defaults(), **state}
    merged.update(updates)
    return merged


def _current_auto_sample_id(state: dict[str, Any]) -> str:
    queue = [str(item) for item in state.get("auto_queue_sample_ids", []) if isinstance(item, str)]
    index = int(state.get("auto_queue_index", 0) or 0)
    if 0 <= index < len(queue):
        return queue[index]
    return ""


def _append_auto_result(
    state: dict[str, Any],
    *,
    sample_id: str,
    outcome: str,
    attempts: int,
    note: str = "",
) -> None:
    results = list(state.get("auto_results", []))
    results.append(
        {
            "sample_id": sample_id,
            "outcome": outcome,
            "attempts": attempts,
            "note": note.strip(),
        }
    )
    state["auto_results"] = results


def _reconcile_manual_auto_result(
    *,
    state_root: Path,
    sender_id: str,
    sample_id: str,
    outcome: str,
    note: str,
) -> None:
    state = _apply_auto_state(_load_session_state(state_root, sender_id))
    changed = False
    for item in state.get("auto_results", []):
        if not isinstance(item, dict):
            continue
        if str(item.get("sample_id", "")).strip() != sample_id:
            continue
        item["outcome"] = outcome
        item["note"] = note
        changed = True
    if not changed:
        return
    _finalize_auto_sample_metric(state, sample_id=sample_id, outcome=outcome)
    state["last_action"] = f"manual-{outcome}"
    state["last_sample_outcome"] = outcome
    _save_session_state(state_root, sender_id, state)
    _write_auto_batch_report(state_root, sender_id, state)


def _auto_result_counts(state: dict[str, Any]) -> dict[str, int]:
    counts = {"pass": 0, "defer": 0, "other": 0}
    for item in state.get("auto_results", []):
        if not isinstance(item, dict):
            continue
        outcome = str(item.get("outcome", "")).strip()
        if outcome == "pass":
            counts["pass"] += 1
        elif outcome in {"defer", "deferred"}:
            counts["defer"] += 1
        else:
            counts["other"] += 1
    return counts


def _advance_auto_queue(state: dict[str, Any]) -> None:
    state["auto_queue_index"] = int(state.get("auto_queue_index", 0) or 0) + 1
    state["auto_current_attempt"] = 0
    state["auto_current_sample_id"] = _current_auto_sample_id(state)
    state["selected_sample_id"] = state["auto_current_sample_id"]
    state["auto_current_status"] = "queued" if state["auto_current_sample_id"] else "finished"


def _auto_batch_finished(state: dict[str, Any]) -> bool:
    queue = [str(item) for item in state.get("auto_queue_sample_ids", []) if isinstance(item, str)]
    index = int(state.get("auto_queue_index", 0) or 0)
    return index >= len(queue)


def _load_auto_judge_template() -> str:
    if AUTO_JUDGE_TEMPLATE_PATH.exists():
        return AUTO_JUDGE_TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        "You are the final AI judge for an autonomous policy briefing QC loop.\n"
        "Return JSON with keys: decision, confidence, blocking_findings, next_fix_instruction, user_summary.\n"
        "Decisions: pass|retry|defer.\n"
    )


def _find_sample(sample_id: str, remote_qc_root: Path, curated_qc_root: Path | None = None) -> SampleRecord:
    candidate_roots = [remote_qc_root]
    if DEFAULT_QC_ROOT not in candidate_roots:
        candidate_roots.append(DEFAULT_QC_ROOT)
    if DEFAULT_REMOTE_QC_ROOT not in candidate_roots:
        candidate_roots.append(DEFAULT_REMOTE_QC_ROOT)
    if curated_qc_root is not None and curated_qc_root not in candidate_roots:
        candidate_roots.append(curated_qc_root)
    for root in candidate_roots:
        sample_dir = root / sample_id
        if sample_dir.exists():
            return _sample_record(sample_dir)
    raise FileNotFoundError(f"Unknown QC sample: {sample_id}")


def _resolve_remote_sample(
    sample_id: str,
    *,
    gov_md_root: Path,
    remote_qc_root: Path,
    storage_root: Path,
) -> SampleRecord:
    try:
        return _find_sample(sample_id, remote_qc_root, DEFAULT_CURATED_QC_ROOT)
    except FileNotFoundError:
        pass
    if sample_id.startswith("storage_job_"):
        job_id = "job_" + sample_id.removeprefix("storage_job_")
        scaffold_storage_qc_jobs(
            storage_root=storage_root,
            output_root=PROJECT_ROOT / "exports" / "policy_briefing_qc",
            gov_md_converter_root=gov_md_root,
            qc_root=remote_qc_root,
            job_ids=[job_id],
            limit=1,
            force=False,
            autofill=True,
            sample_status="scratch",
        )
        return _find_sample(sample_id, remote_qc_root, DEFAULT_CURATED_QC_ROOT)
    policy_match = re.fullmatch(r"policy_briefing_(\d{4})_(\d{2})_(\d{2})_(\d+)", sample_id)
    if policy_match:
        year, month, day, news_item_id = policy_match.groups()
        target_date = date(int(year), int(month), int(day))
        catalog = _build_policy_catalog(storage_root)
        report = export_policy_briefings_for_qc(
            client=PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY")),
            catalog=catalog,
            target_date=target_date,
            output_root=PROJECT_ROOT / "exports" / "policy_briefing_qc",
            news_item_ids=[news_item_id],
            include_pdf=True,
            ensure_fresh=False,
            scaffold_runner=run_gov_md_scaffold,
            gov_md_converter_root=gov_md_root,
            qc_root=remote_qc_root,
            autofill=True,
            force=False,
            sample_status="scratch",
        )
        if int(report.get("scaffolded_count", 0) or 0) > 0:
            return _find_sample(sample_id, remote_qc_root, DEFAULT_CURATED_QC_ROOT)
    raise FileNotFoundError(f"Unknown QC sample: {sample_id}")


def _maybe_export_policy_briefing_sample(
    title_query: str,
    *,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    storage_root: Path,
) -> SampleRecord | None:
    policy_qc_root = DEFAULT_QC_ROOT if remote_qc_root == DEFAULT_REMOTE_QC_ROOT else remote_qc_root
    catalog = PolicyBriefingCatalog(
        client=PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY")),
        cache_path=storage_root / "policy_briefing_catalog.json",
    )
    item = find_cached_policy_briefing_by_title(catalog, title_query)
    if item is None:
        return None
    target_date = date.fromisoformat(item.approve_date.split()[0]) if "-" in item.approve_date[:10] else None
    if target_date is None:
        try:
            from datetime import datetime

            target_date = datetime.strptime(item.approve_date, "%m/%d/%Y %H:%M:%S").date()
        except ValueError:
            return None

    sample_id = f"policy_briefing_{target_date:%Y_%m_%d}_{item.news_item_id}"
    try:
        return _find_sample(sample_id, policy_qc_root, DEFAULT_CURATED_QC_ROOT)
    except FileNotFoundError:
        pass

    report = export_policy_briefings_for_qc(
        client=PolicyBriefingClient(service_key=os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY")),
        catalog=catalog,
        target_date=target_date,
        output_root=export_root,
        news_item_ids=[item.news_item_id],
        include_pdf=True,
        ensure_fresh=False,
        scaffold_runner=run_gov_md_scaffold,
        gov_md_converter_root=gov_md_root,
        qc_root=policy_qc_root,
        autofill=True,
        force=False,
        sample_status="scratch",
    )
    if int(report.get("scaffolded_count", 0) or 0) <= 0:
        try:
            return _find_sample(sample_id, policy_qc_root)
        except FileNotFoundError:
            return None
    return _find_sample(sample_id, policy_qc_root)


def _ensure_selected_sample(state_root: Path, sender_id: str, remote_qc_root: Path) -> SampleRecord:
    state = _load_session_state(state_root, sender_id)
    sample_id = str(state.get("selected_sample_id", "")).strip()
    if not sample_id:
        raise ValueError("현재 선택된 job이 없습니다. 먼저 `job 목록 보여줘` 또는 `<sample-id> 열어줘`를 보내주세요.")
    return _find_sample(sample_id, remote_qc_root, DEFAULT_CURATED_QC_ROOT)


def _rewrite_sample_review(gov_md_root: Path, sample_dir: Path) -> None:
    if str(gov_md_root) not in sys.path:
        sys.path.insert(0, str(gov_md_root))
    from src.hwpx_qc_scaffold import _write_review_markdown  # type: ignore

    _write_review_markdown(sample_dir)


def _send_telegram_media(
    *,
    sender_id: str,
    message_id: str | None,
    media_path: Path,
    caption: str | None = None,
    account: str = DEFAULT_TELEGRAM_ACCOUNT,
    channel: str = DEFAULT_TELEGRAM_CHANNEL,
) -> dict[str, Any]:
    command = [
        "openclaw",
        "message",
        "send",
        "--channel",
        channel,
        "--account",
        account,
        "--target",
        sender_id,
        "--media",
        str(media_path),
        "--force-document",
        "--json",
    ]
    if caption:
        command.extend(["--message", caption])
    if message_id:
        command.extend(["--reply-to", message_id])
    return _run_subprocess(command, cwd=PROJECT_ROOT)


def _send_telegram_text(
    *,
    sender_id: str,
    message: str,
    message_id: str | None = None,
    account: str = DEFAULT_TELEGRAM_ACCOUNT,
    channel: str = DEFAULT_TELEGRAM_CHANNEL,
) -> dict[str, Any]:
    command = [
        "openclaw",
        "message",
        "send",
        "--channel",
        channel,
        "--account",
        account,
        "--target",
        sender_id,
        "--message",
        message,
        "--json",
    ]
    if message_id:
        command.extend(["--reply-to", message_id])
    return _run_subprocess(command, cwd=PROJECT_ROOT)


def _background_fix_log_dir(state_root: Path) -> Path:
    path = state_root / "background_fix_logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _spawn_background_fix(
    *,
    sender_id: str,
    message_id: str | None,
    sample: SampleRecord,
    user_text: str,
    export_root: Path,
    gov_md_root: Path,
    qc_root: Path,
    remote_qc_root: Path,
    state_root: Path,
) -> dict[str, Any]:
    log_path = _background_fix_log_dir(state_root) / f"{sample.sample_id}-{int(time.time())}.log"
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "openclaw_ops.py"),
        "--export-root",
        str(export_root),
        "--gov-md-root",
        str(gov_md_root),
        "--qc-root",
        str(qc_root),
        "--remote-qc-root",
        str(remote_qc_root),
        "--state-root",
        str(state_root),
        "remote-qc-run-fix",
        "--sender-id",
        sender_id,
        "--sample-id",
        sample.sample_id,
        "--user-text",
        user_text,
    ]
    if message_id:
        command.extend(["--message-id", message_id])
    log_handle = log_path.open("ab")
    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log_handle.close()
    return {
        "command": "remote-qc-fix-queued",
        "ok": True,
        "sample_id": sample.sample_id,
        "pid": process.pid,
        "log_path": str(log_path),
    }


def _send_requested_files(
    *,
    sender_id: str,
    message_id: str | None,
    sample: SampleRecord,
    file_keys: list[str],
) -> list[dict[str, Any]]:
    key_to_name = {
        "source": "source.hwpx",
        "rendered": "rendered.md",
        "review": "review.md",
        "golden": "golden.md",
    }
    results: list[dict[str, Any]] = []
    for key in file_keys:
        filename = key_to_name[key]
        target = sample.sample_dir / filename
        if not target.exists():
            results.append({"file": filename, "ok": False, "error": f"missing: {target}"})
            continue
        send_result = _send_telegram_media(
            sender_id=sender_id,
            message_id=message_id,
            media_path=target,
            caption=f"{sample.sample_id} / {filename}",
        )
        results.append({"file": filename, "ok": send_result["returncode"] == 0, **send_result})
    return results


def _report_dates(root: Path) -> list[str]:
    dates = [path.parent.name for path in root.glob("*/pipeline_report.json") if path.parent.is_dir()]
    return sorted({item for item in dates if re.fullmatch(r"\d{4}-\d{2}-\d{2}", item)})


def resolve_report_path(export_root: Path, requested_date: str) -> Path:
    dates = _report_dates(export_root)
    if not dates:
        raise FileNotFoundError(f"No pipeline_report.json found under {export_root}")
    target_date = dates[-1] if requested_date == "latest" else requested_date
    report_path = export_root / target_date / "pipeline_report.json"
    if not report_path.exists():
        raise FileNotFoundError(f"Pipeline report not found: {report_path}")
    return report_path


def _find_qc_command(report: dict[str, Any], command: str) -> dict[str, Any] | None:
    for entry in report.get("qc_commands", []):
        if isinstance(entry, dict) and entry.get("command") == command:
            return entry
    return None


def _triage_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    entry = _find_qc_command(report, "triage")
    payload = entry.get("payload") if isinstance(entry, dict) else None
    entries = payload.get("entries") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return []
    return [item for item in entries if isinstance(item, dict)]


def _regression_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    entry = _find_qc_command(report, "regression")
    payload = entry.get("payload") if isinstance(entry, dict) else None
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def _proposal_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    entry = _find_qc_command(report, "suggest-fix")
    payload = entry.get("payload") if isinstance(entry, dict) else None
    proposals = payload.get("proposals") if isinstance(payload, dict) else None
    if not isinstance(proposals, list):
        return []
    return [item for item in proposals if isinstance(item, dict)]


def parse_server_presets(constants_path: Path = MOBILE_CONSTANTS_PATH) -> tuple[list[ServerPreset], str]:
    text = constants_path.read_text(encoding="utf-8")
    presets = [
        ServerPreset(key=match[0], label=match[1], url=match[2])
        for match in re.findall(
            r'\{\s*key:\s*"([^"]+)",\s*label:\s*"([^"]+)",[^}]*url:\s*"([^"]+)"\s*\}',
            text,
        )
    ]
    primary_match = re.search(r'PRIMARY_SERVER_KEY\s*=\s*"([^"]+)"', text)
    primary_key = primary_match.group(1) if primary_match else (presets[0].key if presets else "serverW")
    if not presets:
        presets = [
            ServerPreset(key="serverW", label="서버W", url="https://api4.govpress.cloud"),
            ServerPreset(key="serverH", label="서버H", url="https://api.govpress.cloud"),
            ServerPreset(key="serverV", label="서버V", url="https://api2.govpress.cloud"),
        ]
    return presets, primary_key


def _fetch_health(url: str, *, timeout: float = 5.0) -> dict[str, Any]:
    endpoint = url.rstrip("/") + "/health"
    try:
        request = __import__("urllib.request").request.Request(endpoint)
        request.add_header("User-Agent", "govpress-openclaw-healthcheck/1.0")
        request.add_header("Accept", "application/json")
        api_key = _load_deploy_env_value("GOVPRESS_API_KEY")
        if api_key:
            request.add_header("X-API-Key", api_key)
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {"ok": 200 <= response.status < 300, "status": response.status, "endpoint": endpoint, "body": body[:200]}
    except URLError as exc:
        return {"ok": False, "status": None, "endpoint": endpoint, "error": str(exc.reason)}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "status": None, "endpoint": endpoint, "error": str(exc)}


def build_server_status(*, dashboard_path: str = DEFAULT_DASHBOARD_PATH) -> dict[str, Any]:
    presets, primary_key = parse_server_presets()
    statuses = []
    for preset in presets:
        health = _fetch_health(preset.url)
        statuses.append(
            {
                "key": preset.key,
                "label": preset.label,
                "url": preset.url,
                "dashboard_url": preset.url.rstrip("/") + dashboard_path,
                **health,
            }
        )
    primary = next((item for item in statuses if item["key"] == primary_key), statuses[0])
    healthy_urls = [item["url"] for item in statuses if item["ok"]]
    fallback_candidates = [item["url"] for item in statuses if item["url"] != primary["url"] and item["ok"]]
    return {
        "primary_key": primary_key,
        "primary_url": primary["url"],
        "primary_healthy": primary["ok"],
        "fallback_candidates": fallback_candidates,
        "status": statuses,
        "mismatch": (not primary["ok"] and bool(fallback_candidates)),
        "recommended_url": primary["url"] if primary["ok"] else (fallback_candidates[0] if fallback_candidates else None),
        "healthy_urls": healthy_urls,
    }


def _shorten(value: Any, *, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def qc_status(export_root: Path, requested_date: str, *, dashboard_url: str | None = None) -> dict[str, Any]:
    report_path = resolve_report_path(export_root, requested_date)
    report = load_issue_report(report_path)
    payload = build_dashboard_payload(export_root)
    latest = payload.get("latest", {}) if isinstance(payload.get("latest"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    return {
        "command": "qc-status",
        "date": report.get("date"),
        "report_path": str(report_path),
        "summary": summary,
        "top_defects": payload.get("top_defects", []),
        "top_samples": payload.get("top_samples", []),
        "latest_review_required": latest.get("review_required", []),
        "latest_regression_failures": latest.get("regression_failures", []),
        "dashboard_url": dashboard_url,
    }


def qc_failures(export_root: Path, requested_date: str) -> dict[str, Any]:
    report_path = resolve_report_path(export_root, requested_date)
    report = load_issue_report(report_path)
    triage_entries = [item for item in _triage_entries(report) if item.get("review_required") is True]
    regression_failures = [item for item in _regression_entries(report) if item.get("passed") is False]
    proposals = _proposal_entries(report)
    return {
        "command": "qc-failures",
        "date": report.get("date"),
        "report_path": str(report_path),
        "review_required": triage_entries,
        "regression_failures": regression_failures,
        "proposals": proposals,
    }


def qc_issue(export_root: Path, requested_date: str) -> dict[str, Any]:
    report_path = resolve_report_path(export_root, requested_date)
    report = load_issue_report(report_path)
    summary_path = report_path.with_name("qc_summary.md")
    summary_markdown = summary_path.read_text(encoding="utf-8") if summary_path.exists() else build_markdown_summary(report)
    payload = build_issue_payload(report, summary_markdown=summary_markdown)
    issue_path = report_path.with_name("issue_payload.json")
    return {
        "command": "qc-issue",
        "date": report.get("date"),
        "report_path": str(report_path),
        "issue_path": str(issue_path),
        "title": payload["title"],
        "body_preview": _shorten(payload["body"], limit=700),
    }


def _run_subprocess(command: list[str], *, cwd: Path, extra_env: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, env=env)
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
        "command": command,
    }


def _run_hwpx_qc_inspect(sample_dir: Path, *, gov_md_root: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(gov_md_root / "scripts" / "run_hwpx_qc.py"),
        "inspect",
        str(sample_dir),
        "--json",
    ]
    result = _run_subprocess(command, cwd=gov_md_root)
    payload: dict[str, Any] = {}
    stdout = str(result.get("stdout", "")).strip()
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                payload = parsed
        except json.JSONDecodeError:
            payload = {"passed": False, "findings": [{"message": stdout[:500], "category": "inspect_parse"}]}
    return {
        "returncode": result["returncode"],
        "payload": payload,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "command": command,
    }


def _summarize_inspect_payload(payload: dict[str, Any]) -> str:
    if not payload:
        return "inspect 결과 없음"
    findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
    if payload.get("passed") is True:
        return "inspect=PASS findings=0"
    categories = []
    for item in findings[:3]:
        if isinstance(item, dict):
            category = str(item.get("category") or item.get("assertion_id") or item.get("message") or "").strip()
            if category:
                categories.append(category)
    suffix = f" top={','.join(categories)}" if categories else ""
    return f"inspect=FAIL findings={len(findings)}{suffix}"


def _inspect_finding_preview(payload: dict[str, Any], *, limit: int = 3) -> str:
    findings = payload.get("findings") if isinstance(payload.get("findings"), list) else []
    previews: list[str] = []
    for item in findings[:limit]:
        if not isinstance(item, dict):
            continue
        text = str(item.get("message") or item.get("category") or item.get("assertion_id") or "").strip()
        if text:
            previews.append(_shorten(text, limit=80))
    return " / ".join(previews)


def _load_sample_title(sample: SampleRecord) -> str:
    meta = _load_policy_meta(sample.sample_dir)
    return str(meta.get("title", "")).strip() or sample.sample_id


def _build_auto_fix_instruction(
    *,
    sample: SampleRecord,
    inspect_payload: dict[str, Any],
    next_fix_instruction: str = "",
) -> str:
    if next_fix_instruction.strip():
        return f"수정: {next_fix_instruction.strip()}"
    if inspect_payload.get("passed") is True:
        return (
            f"수정: {sample.sample_id}는 deterministic QC는 통과했지만 "
            "rendered/review를 다시 검토해 남은 구조적 결함이 없는지 확인하고 필요한 마무리 수정만 수행해."
        )
    findings = inspect_payload.get("findings") if isinstance(inspect_payload.get("findings"), list) else []
    hints: list[str] = []
    for item in findings[:3]:
        if isinstance(item, dict):
            message = str(item.get("message") or item.get("assertion_id") or item.get("category") or "").strip()
            if message:
                hints.append(message)
    hint_text = " / ".join(hints) if hints else "inspect findings를 반영"
    return (
        f"수정: {sample.sample_id}의 deterministic QC를 통과할 때까지 "
        f"현재 결함({hint_text})을 ground rule 기준으로 수정해줘."
    )


def _parse_auto_judge_output(text: str) -> AutoJudgeResult:
    payload: dict[str, Any] = {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            payload = parsed
    except json.JSONDecodeError:
        payload = {}
    decision = str(payload.get("decision", "retry")).strip() or "retry"
    if decision not in {"pass", "retry", "defer"}:
        decision = "retry"
    confidence = str(payload.get("confidence", "medium")).strip() or "medium"
    blocking = payload.get("blocking_findings")
    if not isinstance(blocking, list):
        blocking = []
    return AutoJudgeResult(
        decision=decision,
        confidence=confidence,
        blocking_findings=tuple(str(item).strip() for item in blocking if str(item).strip()),
        next_fix_instruction=str(payload.get("next_fix_instruction", "")).strip(),
        user_summary=str(payload.get("user_summary", "")).strip(),
    )


def _run_auto_judge(
    *,
    sample: SampleRecord,
    inspect_payload: dict[str, Any],
    worker_text: str,
    gov_md_root: Path,
) -> dict[str, Any]:
    rendered = _read_text(sample.sample_dir / "rendered.md")
    review = _read_text(sample.sample_dir / "review.md")
    template = _load_auto_judge_template()
    prompt = "\n\n".join(
        [
            template.strip(),
            f"sample_id: {sample.sample_id}",
            f"inspect_summary: {_summarize_inspect_payload(inspect_payload)}",
            f"worker_summary: {_shorten(worker_text, limit=1200)}",
            "rendered_excerpt:",
            rendered[:5000],
            "review_excerpt:",
            review[:4000],
            "inspect_json:",
            json.dumps(inspect_payload, ensure_ascii=False)[:4000],
        ]
    )
    with tempfile.NamedTemporaryFile(prefix="codex-auto-judge-", suffix=".json", delete=False) as tmp:
        output_path = Path(tmp.name)
    command = [
        "codex",
        "exec",
        "-m",
        DEFAULT_CODEX_MODEL,
        "-C",
        str(gov_md_root),
        "--json",
        "-o",
        str(output_path),
        prompt,
    ]
    try:
        result = _run_subprocess(command, cwd=gov_md_root)
        output = output_path.read_text(encoding="utf-8").strip() if output_path.exists() else ""
    finally:
        if output_path.exists():
            output_path.unlink()
    judge = _parse_auto_judge_output(output)
    return {
        "returncode": result["returncode"],
        "output": output,
        "judge": judge,
        "command": command,
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


def _format_codex_stream_line(line: str) -> str | None:
    text = line.strip()
    if not text:
        return None
    if text.startswith("codex event:"):
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}T.*\b(?:ERROR|WARN|INFO|DEBUG)\b", text):
        return None
    if any(
        marker in text
        for marker in (
            "codex_core::",
            "apply_patch verification failed",
            "Failed to find expected lines",
            "Command exited with code",
            "Process:",
            "Edit:",
            "Tool:",
        )
    ):
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    if str(payload.get("type", "")).strip() != "item.completed":
        return None
    item = payload.get("item")
    if not isinstance(item, dict):
        return None
    item_type = str(item.get("type", "")).strip()
    item_text = item.get("text")
    if item_type == "agent_message" and isinstance(item_text, str) and item_text.strip():
        return item_text.strip()[:3500]
    return None


def _run_codex_with_streaming(
    command: list[str],
    *,
    cwd: Path,
    on_update: Any | None = None,
) -> dict[str, Any]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert process.stdout is not None
    stdout_chunks: list[str] = []
    stream_buffer: list[str] = []

    def flush_stream_buffer() -> None:
        nonlocal stream_buffer
        if not stream_buffer:
            return
        message = "\n".join(stream_buffer).strip()
        stream_buffer = []
        if message and on_update is not None:
            on_update(message[:3500])

    while True:
        ready, _, _ = select.select([process.stdout], [], [], 0.2)
        if ready:
            line = process.stdout.readline()
            if line:
                stdout_chunks.append(line)
                formatted = _format_codex_stream_line(line)
                if formatted:
                    stream_buffer.append(formatted)
                    flush_stream_buffer()
        if process.poll() is not None:
            remainder = process.stdout.read()
            if remainder:
                stdout_chunks.append(remainder)
                for rem_line in remainder.splitlines():
                    formatted = _format_codex_stream_line(rem_line)
                    if formatted:
                        stream_buffer.append(formatted)
            break

    flush_stream_buffer()
    return {
        "returncode": int(process.returncode or 0),
        "stdout": "".join(stdout_chunks).strip(),
        "stderr": "",
        "command": command,
    }


def qc_rerun(target_date: str, *, output_root: Path, gov_md_root: Path, qc_root: Path) -> dict[str, Any]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_policy_briefing_qc_pipeline.py"),
        "--date",
        target_date,
        "--output-root",
        str(output_root),
        "--gov-md-converter-root",
        str(gov_md_root),
        "--qc-root",
        str(qc_root),
        "--json",
    ]
    result = _run_subprocess(command, cwd=PROJECT_ROOT)
    payload = json.loads(result["stdout"]) if result["stdout"] else {}
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    return {
        "command": "qc-rerun",
        "date": target_date,
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "summary": summary,
        "report_path": str(output_root / target_date / "pipeline_report.json"),
    }


def qc_promote(sample_id: str, *, qc_root: Path, gov_md_root: Path) -> dict[str, Any]:
    sample_dir = qc_root / sample_id
    if not sample_dir.exists():
        raise FileNotFoundError(f"QC sample directory not found: {sample_dir}")
    command = [
        sys.executable,
        str(gov_md_root / "scripts" / "run_hwpx_qc.py"),
        "promote-sample",
        str(sample_dir),
        "--sample-status",
        "curated",
    ]
    result = _run_subprocess(command, cwd=gov_md_root)
    return {
        "command": "qc-promote",
        "sample_id": sample_id,
        "sample_dir": str(sample_dir),
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
    }


def server_failover_check() -> dict[str, Any]:
    status = build_server_status()
    if status["primary_healthy"]:
        message = f"Primary server {status['primary_key']} is healthy"
    elif status["recommended_url"]:
        message = f"Primary server {status['primary_key']} is unhealthy; recommend {status['recommended_url']}"
    else:
        message = f"Primary server {status['primary_key']} is unhealthy and no healthy fallback is available"
    return {
        "command": "server-failover-check",
        **status,
        "action_required": bool(status["mismatch"]),
        "message": message,
    }


def parse_telegram_command(message: str) -> tuple[str, list[str]]:
    tokens = message.strip().split()
    if not tokens:
        raise ValueError("Empty message")
    if tokens[:2] == ["/qc", "today"]:
        return "qc-status", ["latest"]
    if tokens[:2] == ["/qc", "failures"]:
        return "qc-failures", ["latest"]
    if tokens[:2] == ["/qc", "issue"]:
        return "qc-issue", ["latest"]
    if len(tokens) == 3 and tokens[:2] == ["/qc", "rerun"]:
        _valid_date(tokens[2])
        return "qc-rerun", [tokens[2]]
    if len(tokens) == 4 and tokens[:2] == ["/qc", "promote"]:
        _valid_date(tokens[2])
        _valid_sample_id(tokens[3])
        return "qc-promote", [tokens[2], tokens[3]]
    if tokens[:2] == ["/server", "status"]:
        return "server-status", []
    if tokens[:2] == ["/server", "failover-check"]:
        return "server-failover-check", []
    raise ValueError("Unsupported command. Use /qc today|rerun|failures|issue|promote or /server status|failover-check")


def _normalize_message(message: str) -> str:
    cleaned = message
    cleaned = re.sub(r"Conversation info \(untrusted metadata\):\s*```json.*?```", "", cleaned, flags=re.S)
    cleaned = re.sub(r"Sender \(untrusted metadata\):\s*```json.*?```", "", cleaned, flags=re.S)
    cleaned = re.sub(r'Conversation info \(untrusted metadata\):\s*\{.*?\}', "", cleaned, flags=re.S)
    cleaned = re.sub(r'Sender \(untrusted metadata\):\s*\{.*?\}', "", cleaned, flags=re.S)
    cleaned = re.sub(r"\[media attached:.*?\]", "", cleaned, flags=re.S)
    cleaned = re.sub(r"To send an image back,.*", "", cleaned)
    return cleaned.strip()


def _extract_sample_id_from_text(text: str) -> str | None:
    match = re.search(r"\b(storage_job_[A-Za-z0-9]+|policy_briefing_\d{4}_\d{2}_\d{2}_[A-Za-z0-9]+)\b", text)
    return match.group(1) if match else None


def _extract_title_query_from_text(text: str) -> str | None:
    direct_patterns = [
        r"국정브리핑\s+보도자료\s+(.+?)\s+를\s+job으로\s+열어줘",
        r"국정브리핑\s+보도자료\s+(.+?)\s+job으로\s+열어줘",
    ]
    for pattern in direct_patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                return candidate.strip("'\"“”‘’ ").strip()

    quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", text)
    parts = [left or right for left, right in quoted if (left or right)]
    if parts:
        return " ".join(part.strip() for part in parts if part.strip()).strip() or None

    cleaned = text.strip()
    cleaned = re.sub(r"\b(job|샘플)\b", " ", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.replace("국정브리핑", " ")
    cleaned = cleaned.replace("보도자료", " ")
    cleaned = cleaned.replace("열어줘", " ")
    cleaned = cleaned.replace("로", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


def _should_try_implicit_title_open(text: str) -> bool:
    normalized = text.strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    if normalized.startswith("/"):
        return False
    if _extract_sample_id_from_text(normalized):
        return False
    if any(token in lowered for token in ("review", "rendered", "source", "golden")):
        return False
    if _is_pass_message(normalized) or _is_defer_message(normalized) or _is_fix_message(normalized):
        return False
    if _wants_job_list(normalized) or _wants_review_queue(normalized) or _wants_next_job(normalized):
        return False
    if _wants_golden_upload_fix(normalized):
        return False
    return len(normalized) >= 8


def _is_pass_message(text: str) -> bool:
    normalized = text.strip()
    return normalized == "통과" or normalized.endswith(" 통과")


def _is_defer_message(text: str) -> bool:
    normalized = text.strip()
    return normalized == "보류" or normalized.endswith(" 보류")


def _is_fix_message(text: str) -> bool:
    normalized = text.strip()
    return normalized.startswith("수정")


def _wants_golden_upload_fix(text: str) -> bool:
    normalized = text.strip().lower()
    return (
        "golden.md 업로드" in normalized
        or "golden 업로드" in normalized
        or normalized == "golden.md"
        or normalized == "golden"
    )


def _wants_job_list(text: str) -> bool:
    return "job 목록" in text or "샘플 목록" in text or "목록 보여줘" in text


def _wants_review_queue(text: str) -> bool:
    return "review 필요한" in text or "검토할" in text


def _requested_recent_job_count(text: str) -> int | None:
    if not ("job" in text.lower() and "생성" in text):
        return None
    if "국정브리핑" not in text and "보도자료" not in text:
        return None
    match = re.search(r"최근\s*(\d+)\s*건", text)
    if match:
        try:
            return max(1, min(50, int(match.group(1))))
        except ValueError:
            return None
    if "최근" in text:
        return 10
    return None


def _requested_auto_qc_count(text: str) -> int | None:
    lowered = text.lower()
    if "qc" not in lowered or "시작" not in text:
        return None
    match = re.search(r"최근\s*(\d+)\s*건", text)
    if match:
        try:
            return max(1, min(50, int(match.group(1))))
        except ValueError:
            return None
    return 10 if "최근" in text or "자동 시작" in text else None


def _wants_next_job(text: str) -> bool:
    return "다음 job" in text or "다음 샘플" in text


def _wants_auto_status(text: str) -> bool:
    return "현재 qc 상태" in text


def _wants_auto_stop(text: str) -> bool:
    return "현재 batch 중지" in text


def _wants_current_job_defer(text: str) -> bool:
    return "현재 job 보류" in text or "현재 job 건너뛰기" in text


def _wants_open_sample(text: str) -> bool:
    return "열어줘" in text or bool(_extract_sample_id_from_text(text.strip()))


def _wants_open_storage_title(text: str) -> bool:
    lowered = text.lower()
    return "열어줘" in text and "storage_job_" not in lowered and ("국정브리핑" in text or "보도자료" in text)


def _resolve_sample_id_from_text(
    text: str,
    *,
    storage_root: Path,
) -> str | None:
    del storage_root
    return _extract_sample_id_from_text(text)


def _require_sample_id_for_open_request(
    text: str,
    *,
    storage_root: Path,
) -> str | None:
    sample_id = _resolve_sample_id_from_text(text, storage_root=storage_root)
    if sample_id is not None:
        return sample_id
    if _wants_open_storage_title(text):
        title_query = _extract_title_query_from_text(text) or text.strip()
        raise ValueError(f"해당 제목으로 매칭되는 국정브리핑 문서를 찾지 못했습니다: {title_query}")
    return None


def _requested_file_keys(text: str) -> list[str]:
    lowered = text.lower()
    if "다운로드" in text or "다운받" in text or "파일 보내" in text:
        return ["review", "rendered", "source"]
    keys: list[str] = []
    if "source" in lowered or "원문" in text:
        keys.append("source")
    if "rendered" in lowered or "변환결과" in text:
        keys.append("rendered")
    if "review" in lowered or "리뷰" in text:
        keys.append("review")
    if "golden" in lowered:
        keys.append("golden")
    deduped: list[str] = []
    for key in keys:
        if key not in deduped:
            deduped.append(key)
    return deduped


def _refresh_remote_qc_sample(*, sample: SampleRecord, gov_md_root: Path) -> dict[str, Any]:
    if sample.sample_id.startswith("policy_briefing_"):
        # Policy briefing samples may come from cached export artifacts that are
        # already scaffolded; reopening should not force a fresh re-download.
        return {
            "returncode": 0,
            "stdout": "skip refresh for policy_briefing sample",
            "stderr": "",
            "command": ["skip-policy-briefing-refresh", sample.sample_id],
        }
    meta_path = sample.sample_dir / "meta.json"
    sample_status = sample.status
    if meta_path.exists():
        try:
            meta = _load_json(meta_path)
            sample_status = str(meta.get("sample_status", sample.status))
        except Exception:
            sample_status = sample.status
    command = [
        sys.executable,
        str(gov_md_root / "scripts" / "run_hwpx_qc.py"),
        "scaffold-local",
        str(sample.sample_dir / "source.hwpx"),
        "--root",
        str(sample.sample_dir.parent),
        "--sample-id",
        sample.sample_id,
        "--sample-status",
        sample_status,
        "--force",
        "--autofill",
    ]
    source_pdf = sample.sample_dir / "source.pdf"
    if source_pdf.exists():
        command.extend(["--pdf", str(source_pdf)])
    result = _run_subprocess(command, cwd=gov_md_root)
    return {
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "command": command,
    }


def _select_sample(sample: SampleRecord, *, sender_id: str, state_root: Path, gov_md_root: Path) -> dict[str, Any]:
    refresh = _refresh_remote_qc_sample(sample=sample, gov_md_root=gov_md_root)
    refreshed = _sample_record(sample.sample_dir)
    previous = _load_session_state(state_root, sender_id)
    state = {
        **previous,
        "selected_sample_id": refreshed.sample_id,
        "selected_sample_dir": str(refreshed.sample_dir),
        "updated_from": "telegram-selection",
    }
    state_path = _save_session_state(state_root, sender_id, state)
    return {
        "command": "remote-qc-open",
        "sample_id": refreshed.sample_id,
        "sample_dir": str(refreshed.sample_dir),
        "status": refreshed.status,
        "state_path": str(state_path),
        "has_golden": refreshed.has_golden,
        "has_review": refreshed.has_review,
        "refresh": refresh,
    }


def _send_policy_briefing_open_telegram(*, sample: SampleRecord, export_root: Path, gov_md_root: Path, qc_root: Path) -> dict[str, Any]:
    match = _POLICY_SAMPLE_ID_RE.fullmatch(sample.sample_id)
    if match is None:
        return {"ok": False, "reason": "not_policy_briefing_sample"}

    target_date = f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    news_item_id = match.group(4)
    policy_service_key = _load_deploy_env_value("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY")
    telegram_bot_token = _load_deploy_env_value("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = _load_deploy_env_value("TELEGRAM_CHAT_ID")
    if not policy_service_key:
        return {"ok": False, "reason": "missing_policy_service_key"}
    if not telegram_bot_token or not telegram_chat_id:
        return {"ok": False, "reason": "missing_telegram_credentials"}

    report_path = export_root / target_date / "pipeline_report.json"
    pipeline_command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "run_policy_briefing_qc_pipeline.py"),
        "--date",
        target_date,
        "--news-item-id",
        news_item_id,
        "--output-root",
        str(export_root),
        "--gov-md-converter-root",
        str(gov_md_root),
        "--qc-root",
        str(qc_root),
        "--force",
        "--output",
        str(report_path),
    ]
    pipeline_result = _run_subprocess(
        pipeline_command,
        cwd=PROJECT_ROOT,
        extra_env={"GOVPRESS_POLICY_BRIEFING_SERVICE_KEY": policy_service_key},
    )
    if pipeline_result["returncode"] != 0:
        return {
            "ok": False,
            "reason": "pipeline_failed",
            "pipeline": pipeline_result,
            "report_path": str(report_path),
        }

    telegram_command = [
        sys.executable,
        str(gov_md_root / "scripts" / "send_policy_briefing_qc_telegram.py"),
        str(report_path),
        "--json",
    ]
    telegram_result = _run_subprocess(
        telegram_command,
        cwd=gov_md_root,
        extra_env={"TELEGRAM_BOT_TOKEN": telegram_bot_token, "TELEGRAM_CHAT_ID": telegram_chat_id},
    )
    telegram_payload: dict[str, Any] | None = None
    stdout = str(telegram_result.get("stdout", "")).strip()
    if stdout:
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                telegram_payload = parsed
        except json.JSONDecodeError:
            telegram_payload = None
    return {
        "ok": telegram_result["returncode"] == 0,
        "report_path": str(report_path),
        "pipeline": pipeline_result,
        "telegram": telegram_result,
        "telegram_payload": telegram_payload,
    }


def _build_job_list_payload(
    *,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    storage_root: Path,
    review_only: bool,
    limit: int = 20,
) -> dict[str, Any]:
    entries = _scaffold_latest_policy_queue(
        export_root=export_root,
        gov_md_root=gov_md_root,
        remote_qc_root=remote_qc_root,
        storage_root=storage_root,
        limit=limit,
    )
    if review_only:
        entries = [entry for entry in entries if entry.review_required]
    return {
        "command": "remote-qc-list",
        "review_only": review_only,
        "sample_count": len(entries),
        "source_kind": "policy_briefing_latest",
        "samples": [
            {
                "sample_id": entry.sample.sample_id,
                "status": entry.sample.status,
                "has_golden": entry.sample.has_golden,
                "source_name": entry.sample.source_name,
                "title": entry.title,
                "approve_date": entry.approve_date,
                "review_required": entry.review_required,
                "risk_score": entry.risk_score,
                "finding_count": entry.finding_count,
                "hard_finding_count": entry.hard_finding_count,
                "defect_classes": list(entry.defect_classes),
            }
            for entry in entries[:12]
        ],
    }


def _build_recent_storage_jobs_payload(
    *,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    storage_root: Path,
    limit: int,
) -> dict[str, Any]:
    entries = _scaffold_latest_policy_queue(
        export_root=export_root,
        gov_md_root=gov_md_root,
        remote_qc_root=remote_qc_root,
        storage_root=storage_root,
        limit=limit,
    )
    return {
        "command": "remote-qc-generate-recent-jobs",
        "limit": limit,
        "selected_count": len(entries),
        "scaffolded_count": len(entries),
        "source_kind": "policy_briefing_latest",
        "items": [
            {
                "news_item_id": entry.news_item_id,
                "title": entry.title,
                "approve_date": entry.approve_date,
                "sample_id": entry.sample.sample_id,
                "scaffold_sample_dir": str(entry.sample.sample_dir),
                "review_required": entry.review_required,
                "risk_score": entry.risk_score,
            }
            for entry in entries
        ],
    }


def _build_next_sample_payload(
    *,
    export_root: Path,
    remote_qc_root: Path,
    storage_root: Path,
    sender_id: str,
    state_root: Path,
    gov_md_root: Path,
) -> dict[str, Any]:
    entries = _scaffold_latest_policy_queue(
        export_root=export_root,
        gov_md_root=gov_md_root,
        remote_qc_root=remote_qc_root,
        storage_root=storage_root,
        limit=20,
    )
    review_entries = [entry for entry in entries if entry.review_required]
    if not review_entries:
        return {
            "command": "remote-qc-next",
            "message": "검토할 review queue 샘플이 없습니다.",
        }
    state = _load_session_state(state_root, sender_id)
    current_id = str(state.get("selected_sample_id", "")).strip()
    if current_id:
        for index, entry in enumerate(review_entries):
            if entry.sample.sample_id == current_id and index + 1 < len(review_entries):
                return _select_sample(review_entries[index + 1].sample, sender_id=sender_id, state_root=state_root, gov_md_root=gov_md_root)
    return _select_sample(review_entries[0].sample, sender_id=sender_id, state_root=state_root, gov_md_root=gov_md_root)


def _build_sample_summary(sample: SampleRecord) -> dict[str, Any]:
    review_path = sample.sample_dir / "review.md"
    preview = ""
    if review_path.exists():
        preview = "\n".join(review_path.read_text(encoding="utf-8").splitlines()[:18]).strip()
    return {
        "command": "remote-qc-summary",
        "sample_id": sample.sample_id,
        "sample_dir": str(sample.sample_dir),
        "status": sample.status,
        "has_golden": sample.has_golden,
        "review_preview": preview,
    }


def _handle_golden_upload(
    *,
    ctx: TelegramContext,
    sender_id: str,
    sample: SampleRecord,
    gov_md_root: Path,
) -> dict[str, Any]:
    media_paths = [path for path in ctx.media_paths if path.suffix.lower() == ".md"]
    if not media_paths:
        raise ValueError("golden 업로드는 markdown 파일(.md)만 지원합니다.")
    uploaded = media_paths[0]
    target = sample.sample_dir / "golden.md"
    target.write_bytes(uploaded.read_bytes())
    _rewrite_sample_review(gov_md_root, sample.sample_dir)
    _append_sample_note(
        gov_md_root=gov_md_root,
        sample=sample,
        title="golden upload",
        body=f"uploaded_from: {uploaded}\n\ngolden.md updated and review.md regenerated.",
    )
    return {
        "command": "remote-qc-upload-golden",
        "sample_id": sample.sample_id,
        "golden_path": str(target),
        "uploaded_from": str(uploaded),
        "review_path": str(sample.sample_dir / "review.md"),
    }


def _build_default_fix_message_after_golden(sample: SampleRecord) -> str:
    return (
        "수정: 업로드한 golden.md를 기준으로 "
        f"{sample.sample_id}의 rendered.md와 review.md를 비교해 차이를 반영해줘. "
        "샘플 보정이 아니라 ground rule 기준으로 처리하고, 필요한 코드/테스트/샘플 재생성까지 수행해."
    )


def _handle_pass(
    *,
    sender_id: str,
    sample: SampleRecord,
    state_root: Path,
    gov_md_root: Path,
) -> dict[str, Any]:
    payload = qc_promote(sample.sample_id, qc_root=sample.sample_dir.parent, gov_md_root=gov_md_root)
    payload["command"] = "remote-qc-pass"
    payload["selected_sample_id"] = sample.sample_id
    state = _load_session_state(state_root, sender_id)
    state["selected_sample_id"] = sample.sample_id
    state["selected_sample_dir"] = str(sample.sample_dir)
    state["last_action"] = "pass"
    state["last_sample_outcome"] = "pass"
    _save_session_state(state_root, sender_id, state)
    batch_id = str(state.get("active_batch_id") or _default_batch_id(sample.sample_dir.parent))
    _update_active_batch_memory(
        gov_md_root=gov_md_root,
        batch_id=batch_id,
        state=state,
        sample=sample,
        action="pass",
        detail="promote-sample executed",
    )
    _append_sample_note(
        gov_md_root=gov_md_root,
        sample=sample,
        title="pass",
        body="sample accepted and promoted to curated.",
    )
    return payload


def _handle_defer(*, sender_id: str, sample: SampleRecord, state_root: Path, gov_md_root: Path) -> dict[str, Any]:
    state = _load_session_state(state_root, sender_id)
    state["selected_sample_id"] = sample.sample_id
    state["selected_sample_dir"] = str(sample.sample_dir)
    state["last_action"] = "defer"
    state["last_sample_outcome"] = "defer"
    _save_session_state(state_root, sender_id, state)
    batch_id = str(state.get("active_batch_id") or _default_batch_id(sample.sample_dir.parent))
    _update_active_batch_memory(
        gov_md_root=gov_md_root,
        batch_id=batch_id,
        state=state,
        sample=sample,
        action="defer",
        detail="sample deferred for later review",
    )
    _append_sample_note(
        gov_md_root=gov_md_root,
        sample=sample,
        title="defer",
        body="sample deferred for later review.",
    )
    return {
        "command": "remote-qc-defer",
        "sample_id": sample.sample_id,
        "message": f"{sample.sample_id} 보류로 기록했습니다.",
    }


def _build_fix_prompt(*, sample: SampleRecord, user_text: str) -> str:
    raise NotImplementedError


def _default_batch_id(remote_qc_root: Path) -> str:
    return f"{date.today().isoformat()}:{remote_qc_root.name}"


def _should_reset_batch(state: dict[str, Any], sample: SampleRecord) -> bool:
    if not state.get("codex_thread_id"):
        return True
    if int(state.get("batch_turn_count", 0) or 0) >= MAX_BATCH_TURNS:
        return True
    sample_ids = [str(item) for item in state.get("batch_sample_ids", []) if isinstance(item, str)]
    if sample.sample_id not in sample_ids and len(sample_ids) >= MAX_BATCH_SAMPLES:
        return True
    return False


def _extract_section(text: str, header: str) -> str:
    match = re.search(
        rf"(?ims)^\s*{re.escape(header)}\s*$\n(.*?)(?=^\s*(?:ground rule|scope|implementation result|remaining diff)\s*$|\Z)",
        text,
    )
    return match.group(1).strip() if match else ""


def _parse_codex_thread_id(stdout: str) -> str | None:
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and payload.get("type") == "thread.started":
            thread_id = payload.get("thread_id")
            if isinstance(thread_id, str) and thread_id.strip():
                return thread_id.strip()
    return None


def _update_active_batch_memory(
    *,
    gov_md_root: Path,
    batch_id: str,
    state: dict[str, Any],
    sample: SampleRecord,
    action: str,
    detail: str = "",
) -> None:
    _ensure_qc_memory_files(gov_md_root)
    path = _active_batch_path(gov_md_root)
    sample_ids = [str(item) for item in state.get("batch_sample_ids", []) if isinstance(item, str)]
    lines = [
        "# Active QC Batch",
        "",
        f"- batch_id: {batch_id}",
        f"- codex_thread_id: {state.get('codex_thread_id', '')}",
        f"- turn_count: {state.get('batch_turn_count', 0)}",
        f"- current_sample: {sample.sample_id}",
        "",
        "## Samples",
    ]
    for sample_id in sample_ids:
        marker = "current" if sample_id == sample.sample_id else "seen"
        lines.append(f"- {sample_id} ({marker})")
    lines.extend(["", "## Last Action", f"- action: {action}"])
    if detail.strip():
        lines.append(f"- detail: {detail.strip()}")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _append_sample_note(
    *,
    gov_md_root: Path,
    sample: SampleRecord,
    title: str,
    body: str,
) -> None:
    _ensure_qc_memory_files(gov_md_root)
    path = _sample_note_path(gov_md_root, sample.sample_id)
    existing = _read_text(path).strip()
    lines = [existing] if existing else [f"# {sample.sample_id}", ""]
    lines.extend([f"## {title}", "", body.strip(), ""])
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def _append_global_ground_rules(gov_md_root: Path, worker_text: str) -> None:
    section = _extract_section(worker_text, "ground rule")
    if not section:
        return
    _ensure_qc_memory_files(gov_md_root)
    path = _global_rules_path(gov_md_root)
    existing = _read_text(path)
    if section in existing:
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"## {date.today().isoformat()}\n\n{section}\n\n")


def _build_fix_prompt(
    *,
    sample: SampleRecord,
    user_text: str,
    gov_md_root: Path,
    batch_id: str,
    state: dict[str, Any],
) -> str:
    review_path = sample.sample_dir / "review.md"
    rendered_path = sample.sample_dir / "rendered.md"
    golden_path = sample.sample_dir / "golden.md"
    storage_rendered_path = sample.sample_dir / "storage_rendered.md"
    memory = _ensure_qc_memory_files(gov_md_root)
    sample_note = _sample_note_path(gov_md_root, sample.sample_id)
    lines = [
        "선택된 remote QC sample에 대한 수정 요청입니다.",
        f"active_batch_id: {batch_id}",
        f"existing_codex_thread_id: {state.get('codex_thread_id', '')}",
        f"sample_id: {sample.sample_id}",
        f"sample_dir: {sample.sample_dir}",
        f"global_ground_rules_md: {memory['global_rules']}",
        f"active_qc_batch_md: {memory['active_batch']}",
        f"sample_note_md: {sample_note if sample_note.exists() else sample_note}",
        f"review_md: {review_path if review_path.exists() else 'missing'}",
        f"rendered_md: {rendered_path if rendered_path.exists() else 'missing'}",
        f"golden_md: {golden_path if golden_path.exists() else 'missing'}",
        f"storage_rendered_md: {storage_rendered_path if storage_rendered_path.exists() else 'missing'}",
        "",
        "작업 규칙:",
        "- 샘플 보정 금지",
        "- 먼저 ground rule로 추상화",
        "- scope는 press_release/report/full_report 중 명시",
        "- 가능하면 코드/테스트를 수정하고 sample rendered도 갱신",
        "- 응답 형식은 정확히 ground rule / scope / implementation result / remaining diff",
        "- gov-md-converter에서 실제 코드 작업을 수행하고 필요한 테스트를 실행",
        "- review.md와 rendered.md를 최신 상태로 갱신",
        "- 먼저 global_ground_rules.md, active_qc_batch.md, sample_note_md가 있으면 읽고 현재 판단과 충돌하는지 확인",
        "",
        f"사용자 지시: {user_text.strip()}",
    ]
    return "\n".join(lines)


def _parse_worker_reply(stdout: str) -> str:
    text = stdout.strip()
    if not text:
        return ""
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict):
        for key in ("message", "output", "text", "reply"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        result = payload.get("result")
        if isinstance(result, dict):
            payloads = result.get("payloads")
            if isinstance(payloads, list):
                texts: list[str] = []
                for item in payloads:
                    if isinstance(item, dict):
                        value = item.get("text")
                        if isinstance(value, str) and value.strip():
                            texts.append(value.strip())
                if texts:
                    return "\n\n".join(texts)
    return text


def _handle_fix_request(
    *,
    sender_id: str,
    message_id: str | None,
    sample: SampleRecord,
    user_text: str,
    gov_md_root: Path,
    remote_qc_root: Path,
    state_root: Path,
    announce_start: bool = True,
    send_result_files: bool = True,
) -> dict[str, Any]:
    state = _load_session_state(state_root, sender_id)
    reset_batch = _should_reset_batch(state, sample)
    batch_id = str(state.get("active_batch_id") or _default_batch_id(remote_qc_root))
    if reset_batch:
        batch_id = _default_batch_id(remote_qc_root)
        state["batch_sample_ids"] = []
        state["batch_turn_count"] = 0
        state["codex_thread_id"] = ""
        state["batch_started_at"] = date.today().isoformat()
    if announce_start:
        _send_telegram_text(
            sender_id=sender_id,
            message_id=message_id,
            message=(
                f"수정 작업 시작: {sample.sample_id}\n"
                f"batch={batch_id} mode={'resume' if state.get('codex_thread_id') and not reset_batch else 'new'}"
            ),
        )
    prompt = _build_fix_prompt(sample=sample, user_text=user_text, gov_md_root=gov_md_root, batch_id=batch_id, state=state)
    with tempfile.NamedTemporaryFile(prefix="codex-qc-fix-", suffix=".txt", delete=False) as tmp:
        output_path = Path(tmp.name)
    try:
        if state.get("codex_thread_id"):
            command = [
                "codex",
                "exec",
                "resume",
                str(state["codex_thread_id"]),
                "-m",
                DEFAULT_CODEX_MODEL,
                "--dangerously-bypass-approvals-and-sandbox",
                "--json",
                "-o",
                str(output_path),
                prompt,
            ]
        else:
            command = [
                "codex",
                "exec",
                "-m",
                DEFAULT_CODEX_MODEL,
                "-C",
                str(gov_md_root),
                "--add-dir",
                str(PROJECT_ROOT),
                "--dangerously-bypass-approvals-and-sandbox",
                "--json",
                "-o",
                str(output_path),
                prompt,
            ]
        progress_chunks_sent = 0

        def send_progress_update(chunk: str) -> None:
            nonlocal progress_chunks_sent
            lines = [line.strip() for line in chunk.splitlines()]
            lines = [line for line in lines if line and not line.startswith("codex event:")]
            if not lines:
                return
            progress_chunks_sent += 1
            _send_telegram_text(
                sender_id=sender_id,
                message_id=message_id,
                message="\n".join(lines)[:3500],
            )
        result = _run_codex_with_streaming(command, cwd=gov_md_root, on_update=send_progress_update)
        worker_text = output_path.read_text(encoding="utf-8").strip() if output_path.exists() else ""
    finally:
        if output_path.exists():
            output_path.unlink()
    thread_id = state.get("codex_thread_id") or _parse_codex_thread_id(result.get("stdout", ""))
    sample_ids = [str(item) for item in state.get("batch_sample_ids", []) if isinstance(item, str)]
    if sample.sample_id not in sample_ids:
        sample_ids.append(sample.sample_id)
    state.update(
        {
            "active_batch_id": batch_id,
            "codex_thread_id": thread_id or "",
            "codex_last_sample_id": sample.sample_id,
            "selected_sample_id": sample.sample_id,
            "selected_sample_dir": str(sample.sample_dir),
            "batch_started_at": str(state.get("batch_started_at") or date.today().isoformat()),
            "batch_turn_count": int(state.get("batch_turn_count", 0) or 0) + 1,
            "batch_sample_ids": sample_ids,
            "last_action": "fix",
        }
    )
    _save_session_state(state_root, sender_id, state)
    _update_active_batch_memory(
        gov_md_root=gov_md_root,
        batch_id=batch_id,
        state=state,
        sample=sample,
        action="fix",
        detail=user_text,
    )
    if worker_text:
        _append_sample_note(
            gov_md_root=gov_md_root,
            sample=sample,
            title="fix request",
            body=worker_text,
        )
        _append_global_ground_rules(gov_md_root, worker_text)
    sent_files: list[dict[str, Any]] = []
    if send_result_files and result["returncode"] == 0:
        try:
            sent_files = _send_requested_files(
                sender_id=sender_id,
                message_id=message_id,
                sample=sample,
                file_keys=["rendered", "review"],
            )
            ok_count = len([item for item in sent_files if item.get("ok")])
            if ok_count:
                _send_telegram_text(
                    sender_id=sender_id,
                    message_id=message_id,
                    message=f"최종 결과 파일 전송: {ok_count}/2\n- rendered.md\n- review.md",
                )
        except Exception as exc:
            sent_files = [{"file": "rendered/review", "ok": False, "error": str(exc)}]
            _send_telegram_text(
                sender_id=sender_id,
                message_id=message_id,
                message=f"최종 결과 파일 전송 실패: {exc}",
            )
    return {
        "command": "remote-qc-fix-handoff",
        "sample_id": sample.sample_id,
        "returncode": result["returncode"],
        "stdout": result["stdout"],
        "stderr": result["stderr"],
        "worker_text": worker_text,
        "worker": "codex-cli",
        "model": DEFAULT_CODEX_MODEL,
        "thread_id": thread_id,
        "batch_id": batch_id,
        "resumed": bool(not reset_batch and state.get("batch_turn_count", 0) > 1),
        "sent_files": sent_files,
    }


def _run_fix_subcommand(
    *,
    sender_id: str,
    message_id: str | None,
    sample_id: str,
    user_text: str,
    gov_md_root: Path,
    remote_qc_root: Path,
    state_root: Path,
) -> dict[str, Any]:
    sample = _find_sample(sample_id, remote_qc_root)
    return _handle_fix_request(
        sender_id=sender_id,
        message_id=message_id,
        sample=sample,
        user_text=user_text,
        gov_md_root=gov_md_root,
        remote_qc_root=remote_qc_root,
        state_root=state_root,
    )


def _background_auto_log_dir(state_root: Path) -> Path:
    path = state_root / "background_auto_logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _spawn_background_auto_run(
    *,
    sender_id: str,
    message_id: str | None,
    export_root: Path,
    gov_md_root: Path,
    qc_root: Path,
    remote_qc_root: Path,
    state_root: Path,
) -> dict[str, Any]:
    log_path = _background_auto_log_dir(state_root) / f"auto-{sender_id}-{int(time.time())}.log"
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "openclaw_ops.py"),
        "--export-root",
        str(export_root),
        "--gov-md-root",
        str(gov_md_root),
        "--qc-root",
        str(qc_root),
        "--remote-qc-root",
        str(remote_qc_root),
        "--state-root",
        str(state_root),
        "remote-qc-auto-run-current",
        "--sender-id",
        sender_id,
    ]
    if message_id:
        command.extend(["--message-id", message_id])
    log_handle = log_path.open("ab")
    process = subprocess.Popen(
        command,
        cwd=str(PROJECT_ROOT),
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    log_handle.close()
    return {
        "command": "remote-qc-auto-queued",
        "ok": True,
        "pid": process.pid,
        "log_path": str(log_path),
    }


def _build_auto_start_payload(
    *,
    sender_id: str,
    message_id: str | None,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    state_root: Path,
    limit: int,
) -> dict[str, Any]:
    entries = _auto_queue_entries(
        export_root=export_root,
        gov_md_root=gov_md_root,
        remote_qc_root=remote_qc_root,
        storage_root=DEFAULT_STORAGE_ROOT,
        limit=limit,
    )
    candidate_ids = [entry.news_item_id for entry in entries]
    queue = [entry.sample.sample_id for entry in entries]
    state = _apply_auto_state(
        _load_session_state(state_root, sender_id),
        auto_mode=bool(queue),
        auto_batch_id=f"{date.today().isoformat()}:{sender_id}:policy_briefing",
        auto_source="policy_briefing",
        auto_requested_count=limit,
        auto_candidate_news_ids=candidate_ids,
        auto_queue_sample_ids=queue,
        auto_queue_index=0,
        auto_current_sample_id=queue[0] if queue else "",
        auto_current_attempt=0,
        auto_current_status="queued" if queue else "idle",
        auto_pass_gate="code+ai",
        auto_max_attempts=AUTO_MAX_ATTEMPTS,
        auto_results=[],
        auto_batch_started_at=_now_iso(),
        auto_batch_finished_at="",
        auto_batch_metrics={"sample_count": len(queue), "completed_count": 0},
        auto_sample_metrics={},
        last_action="auto-start",
    )
    if queue:
        state["selected_sample_id"] = queue[0]
    _save_session_state(state_root, sender_id, state)
    _write_auto_batch_report(state_root, sender_id, state)
    payload: dict[str, Any] = {
        "command": "remote-qc-auto-start",
        "ok": True,
        "requested_count": limit,
        "candidate_count": len(candidate_ids),
        "queue_count": len(queue),
        "queue_sample_ids": queue,
        "current_sample_id": queue[0] if queue else "",
        "queue_preview": [
            {
                "sample_id": entry.sample.sample_id,
                "title": entry.title,
                "risk_score": entry.risk_score,
                "finding_count": entry.finding_count,
                "hard_finding_count": entry.hard_finding_count,
                "defect_classes": list(entry.defect_classes[:3]),
            }
            for entry in entries[:5]
        ],
    }
    if queue:
        payload["runner"] = _spawn_background_auto_run(
            sender_id=sender_id,
            message_id=message_id,
            export_root=export_root,
            gov_md_root=gov_md_root,
            qc_root=DEFAULT_QC_ROOT,
            remote_qc_root=remote_qc_root,
            state_root=state_root,
        )
    return payload


def _auto_status_payload(*, sender_id: str, state_root: Path) -> dict[str, Any]:
    state = _load_session_state(state_root, sender_id)
    state = _apply_auto_state(state)
    queue = [str(item) for item in state.get("auto_queue_sample_ids", []) if isinstance(item, str)]
    current_sample_id = _current_auto_sample_id(state)
    current_title = ""
    if current_sample_id:
        try:
            current_title = _load_sample_title(_find_sample(current_sample_id, DEFAULT_REMOTE_QC_ROOT, DEFAULT_CURATED_QC_ROOT))
        except FileNotFoundError:
            current_title = current_sample_id
    counts = _auto_result_counts(state)
    return {
        "command": "remote-qc-auto-status",
        "ok": True,
        "auto_mode": bool(state.get("auto_mode")),
        "batch_id": state.get("auto_batch_id", ""),
        "queue_count": len(queue),
        "queue_index": int(state.get("auto_queue_index", 0) or 0),
        "current_sample_id": current_sample_id,
        "current_title": current_title,
        "current_attempt": int(state.get("auto_current_attempt", 0) or 0),
        "current_status": str(state.get("auto_current_status", "")),
        "results": list(state.get("auto_results", [])),
        "result_counts": counts,
        "auto_batch_started_at": str(state.get("auto_batch_started_at", "")),
        "auto_batch_finished_at": str(state.get("auto_batch_finished_at", "")),
        "auto_batch_metrics": dict(state.get("auto_batch_metrics", {})),
        "auto_batch_report_path": str(state.get("auto_batch_report_path", "")),
    }


def _auto_stop_payload(*, sender_id: str, state_root: Path) -> dict[str, Any]:
    state = _apply_auto_state(
        _load_session_state(state_root, sender_id),
        auto_mode=False,
        auto_current_status="stopped",
        auto_batch_finished_at=_now_iso(),
        last_action="auto-stop",
    )
    _save_session_state(state_root, sender_id, state)
    _write_auto_batch_report(state_root, sender_id, state)
    return {
        "command": "remote-qc-auto-stop",
        "ok": True,
        "message": "현재 자동 QC batch를 중지했습니다.",
    }


def _complete_auto_result(
    *,
    sender_id: str,
    message_id: str | None,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    state_root: Path,
    outcome: str,
) -> dict[str, Any]:
    state = _apply_auto_state(_load_session_state(state_root, sender_id))
    sample_id = _current_auto_sample_id(state)
    if not sample_id:
        return {
            "command": "remote-qc-auto-advance",
            "ok": True,
            "message": "진행 중인 자동 QC sample이 없습니다.",
        }
    sample = _find_sample(sample_id, remote_qc_root, DEFAULT_CURATED_QC_ROOT)
    if outcome == "pass":
        qc_promote(sample.sample_id, qc_root=sample.sample_dir.parent, gov_md_root=gov_md_root)
    _append_auto_result(
        state,
        sample_id=sample.sample_id,
        outcome=outcome,
        attempts=int(state.get("auto_current_attempt", 0) or 0),
    )
    _finalize_auto_sample_metric(state, sample_id=sample.sample_id, outcome=outcome)
    _advance_auto_queue(state)
    if _auto_batch_finished(state):
        state["auto_mode"] = False
        state["auto_current_status"] = "finished"
        state["auto_batch_finished_at"] = _now_iso()
        counts = _auto_result_counts(state)
        message = (
            "[QC Auto Complete]\n"
            f"last={sample.sample_id} outcome={outcome}\n"
            f"user_approved_pass={counts['pass']} auto_deferred={counts['defer']} total={len(state.get('auto_results', []))}"
        )
        runner = None
    else:
        state["auto_mode"] = True
        runner = _spawn_background_auto_run(
            sender_id=sender_id,
            message_id=message_id,
            export_root=export_root,
            gov_md_root=gov_md_root,
            qc_root=DEFAULT_QC_ROOT,
            remote_qc_root=remote_qc_root,
            state_root=state_root,
        )
        counts = _auto_result_counts(state)
        message = (
            f"[QC Auto Advance] {sample.sample_id} {('사용자승인 통과' if outcome == 'pass' else '자동보류')}\n"
            f"progress={int(state.get('auto_queue_index', 0)) + 1}/{len(state.get('auto_queue_sample_ids', []))}\n"
            f"user_approved_pass={counts['pass']} auto_deferred={counts['defer']}\n"
            f"next={_current_auto_sample_id(state) or '-'}"
        )
    state["last_action"] = f"auto-{outcome}"
    _save_session_state(state_root, sender_id, state)
    _write_auto_batch_report(state_root, sender_id, state)
    payload = {
        "command": "remote-qc-auto-advance",
        "ok": True,
        "outcome": outcome,
        "sample_id": sample.sample_id,
        "message": message,
    }
    if runner:
        payload["runner"] = runner
    return payload


def _run_auto_current(
    *,
    sender_id: str,
    message_id: str | None,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    state_root: Path,
) -> dict[str, Any]:
    state = _apply_auto_state(_load_session_state(state_root, sender_id))
    if not state.get("auto_mode"):
        return {"command": "remote-qc-auto-run-current", "ok": False, "message": "auto batch가 활성화되어 있지 않습니다."}
    while state.get("auto_mode") and not _auto_batch_finished(state):
        sample_id = _current_auto_sample_id(state)
        try:
            sample = _resolve_remote_sample(
                sample_id,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                storage_root=DEFAULT_STORAGE_ROOT,
            )
        except FileNotFoundError:
            _append_auto_result(
                state,
                sample_id=sample_id,
                outcome="deferred",
                attempts=int(state.get("auto_current_attempt", 0) or 0),
                note="sample missing",
            )
            _send_telegram_text(
                sender_id=sender_id,
                message_id=message_id,
                message=(
                    f"[QC Auto Deferred] sample={sample_id}\n"
                    "status=자동보류\n"
                    "reason=QC sample을 찾지 못해 다음 job으로 진행합니다."
                ),
            )
            _advance_auto_queue(state)
            _save_session_state(state_root, sender_id, state)
            _write_auto_batch_report(state_root, sender_id, state)
            continue
        sample_title = _load_sample_title(sample)
        queue_total = len([str(item) for item in state.get("auto_queue_sample_ids", []) if isinstance(item, str)])
        queue_index = int(state.get("auto_queue_index", 0) or 0) + 1
        sample_metric = _ensure_auto_sample_metric(
            state,
            sample_id=sample.sample_id,
            title=sample_title,
            queue_position=queue_index,
        )
        _write_auto_batch_report(state_root, sender_id, state)
        _select_sample(sample, sender_id=sender_id, state_root=state_root, gov_md_root=gov_md_root)
        attempt = int(state.get("auto_current_attempt", 0) or 0)
        next_fix_instruction = ""
        while attempt < int(state.get("auto_max_attempts", AUTO_MAX_ATTEMPTS) or AUTO_MAX_ATTEMPTS):
            attempt += 1
            state["auto_current_attempt"] = attempt
            state["auto_current_status"] = "running"
            _save_session_state(state_root, sender_id, state)
            _write_auto_batch_report(state_root, sender_id, state)
            attempt_metric: dict[str, Any] = {
                "attempt": attempt,
                "started_at": _now_iso(),
                "finished_at": "",
                "inspect_before_ms": 0,
                "fix_ms": 0,
                "inspect_after_ms": 0,
                "judge_ms": 0,
                "decision": "",
                "decision_summary": "",
            }
            _send_telegram_text(
                sender_id=sender_id,
                message_id=message_id,
                message=(
                    f"[QC Auto] {queue_index}/{queue_total}\n"
                    f"sample={sample.sample_id}\n"
                    f"title={_shorten(sample_title, limit=120)}\n"
                    f"iteration={attempt}/{state.get('auto_max_attempts', AUTO_MAX_ATTEMPTS)}"
                ),
            )
            inspect_before_started = time.perf_counter()
            pre_inspect = _run_hwpx_qc_inspect(sample.sample_dir, gov_md_root=gov_md_root)
            inspect_before_ms = max(int((time.perf_counter() - inspect_before_started) * 1000), 0)
            attempt_metric["inspect_before_ms"] = inspect_before_ms
            fix_result = _handle_fix_request(
                sender_id=sender_id,
                message_id=message_id,
                sample=sample,
                user_text=_build_auto_fix_instruction(
                    sample=sample,
                    inspect_payload=pre_inspect.get("payload", {}),
                    next_fix_instruction=next_fix_instruction,
                ),
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
                announce_start=False,
                send_result_files=False,
            )
            fix_ms = max(int((time.perf_counter() - inspect_before_started) * 1000), 0) - inspect_before_ms
            attempt_metric["fix_ms"] = max(fix_ms, 0)
            inspect_after_started = time.perf_counter()
            inspect_result = _run_hwpx_qc_inspect(sample.sample_dir, gov_md_root=gov_md_root)
            inspect_after_ms = max(int((time.perf_counter() - inspect_after_started) * 1000), 0)
            attempt_metric["inspect_after_ms"] = inspect_after_ms
            inspect_payload = inspect_result.get("payload", {})
            _send_telegram_text(
                sender_id=sender_id,
                message_id=message_id,
                message=(
                    f"[QC Auto] deterministic gate: {_summarize_inspect_payload(inspect_payload)}\n"
                    f"top={_inspect_finding_preview(inspect_payload) or '-'}"
                ),
            )
            if inspect_result["returncode"] != 0 or inspect_payload.get("passed") is not True:
                next_fix_instruction = _build_auto_fix_instruction(sample=sample, inspect_payload=inspect_payload)
                attempt_metric["decision"] = "retry"
                attempt_metric["decision_summary"] = _summarize_inspect_payload(inspect_payload)
                attempt_metric["finished_at"] = _now_iso()
                sample_metric["attempts"] = attempt
                sample_metric["inspect_total_ms"] = int(sample_metric.get("inspect_total_ms", 0) or 0) + inspect_before_ms + inspect_after_ms
                sample_metric["fix_total_ms"] = int(sample_metric.get("fix_total_ms", 0) or 0) + int(attempt_metric["fix_ms"])
                sample_metric["latest_decision"] = "retry"
                sample_metric.setdefault("attempt_metrics", []).append(attempt_metric)
                _write_auto_batch_report(state_root, sender_id, state)
                _send_telegram_text(
                    sender_id=sender_id,
                    message_id=message_id,
                    message=(
                        "[QC Auto] retry scheduled\n"
                        f"reason={_summarize_inspect_payload(inspect_payload)}\n"
                        f"next={_shorten(next_fix_instruction.removeprefix('수정:').strip(), limit=220)}"
                    ),
                )
                continue
            judge_started = time.perf_counter()
            judge_result = _run_auto_judge(
                sample=sample,
                inspect_payload=inspect_payload,
                worker_text=str(fix_result.get("worker_text", "")),
                gov_md_root=gov_md_root,
            )
            judge_ms = max(int((time.perf_counter() - judge_started) * 1000), 0)
            attempt_metric["judge_ms"] = judge_ms
            judge: AutoJudgeResult = judge_result["judge"]
            attempt_metric["decision"] = judge.decision
            attempt_metric["decision_summary"] = judge.user_summary or judge.next_fix_instruction or _summarize_inspect_payload(inspect_payload)
            attempt_metric["finished_at"] = _now_iso()
            sample_metric["attempts"] = attempt
            sample_metric["inspect_total_ms"] = int(sample_metric.get("inspect_total_ms", 0) or 0) + inspect_before_ms + inspect_after_ms
            sample_metric["fix_total_ms"] = int(sample_metric.get("fix_total_ms", 0) or 0) + int(attempt_metric["fix_ms"])
            sample_metric["judge_total_ms"] = int(sample_metric.get("judge_total_ms", 0) or 0) + judge_ms
            sample_metric["latest_decision"] = judge.decision
            sample_metric.setdefault("attempt_metrics", []).append(attempt_metric)
            _write_auto_batch_report(state_root, sender_id, state)
            _send_telegram_text(
                sender_id=sender_id,
                message_id=message_id,
                message=(
                    f"[QC Auto] ai judge={judge.decision} confidence={judge.confidence}\n"
                    f"blocking={len(judge.blocking_findings)}\n"
                    f"summary={_shorten(judge.user_summary or '요약 없음', limit=500)}\n"
                    f"next={_shorten(judge.next_fix_instruction or '-', limit=220)}"
                ),
            )
            if judge.decision == "pass":
                state["auto_current_status"] = "awaiting_user"
                state["auto_current_attempt"] = attempt
                _finalize_auto_sample_metric(state, sample_id=sample.sample_id, outcome="awaiting_user")
                _save_session_state(state_root, sender_id, state)
                _write_auto_batch_report(state_root, sender_id, state)
                _send_requested_files(
                    sender_id=sender_id,
                    message_id=message_id,
                    sample=sample,
                    file_keys=["rendered", "review"],
                )
                _send_telegram_text(
                    sender_id=sender_id,
                    message_id=message_id,
                    message=(
                        f"[QC Auto Ready] sample={sample.sample_id}\n"
                        f"title={_shorten(sample_title, limit=120)}\n"
                        f"attempts={attempt}/{state.get('auto_max_attempts', AUTO_MAX_ATTEMPTS)}\n"
                        "status=AI self-check PASS / 사용자 승인 대기\n"
                        f"{judge.user_summary or 'AI self-check 통과'}\n"
                        "응답: `통과` 또는 `보류`"
                    ),
                )
                return {
                    "command": "remote-qc-auto-run-current",
                    "ok": True,
                    "sample_id": sample.sample_id,
                    "status": "awaiting_user",
                }
            if judge.decision == "defer":
                break
            next_fix_instruction = judge.next_fix_instruction
        _append_auto_result(
            state,
            sample_id=sample.sample_id,
            outcome="deferred",
            attempts=attempt,
            note="max attempts reached" if attempt >= int(state.get("auto_max_attempts", AUTO_MAX_ATTEMPTS) or AUTO_MAX_ATTEMPTS) else "ai defer",
        )
        _finalize_auto_sample_metric(state, sample_id=sample.sample_id, outcome="deferred")
        _send_telegram_text(
            sender_id=sender_id,
            message_id=message_id,
            message=(
                f"[QC Auto Deferred] sample={sample.sample_id}\n"
                f"title={_shorten(sample_title, limit=120)}\n"
                f"attempts={attempt}\n"
                "status=자동보류\n"
                f"reason={next_fix_instruction or 'ai defer / max attempts'}"
            ),
        )
        _advance_auto_queue(state)
        _save_session_state(state_root, sender_id, state)
        _write_auto_batch_report(state_root, sender_id, state)
    state["auto_mode"] = False
    state["auto_current_status"] = "finished"
    state["auto_batch_finished_at"] = _now_iso()
    _save_session_state(state_root, sender_id, state)
    _write_auto_batch_report(state_root, sender_id, state)
    _send_telegram_text(
        sender_id=sender_id,
        message_id=message_id,
        message=(
            "[QC Auto Complete]\n"
            f"user_approved_pass={_auto_result_counts(state)['pass']} auto_deferred={_auto_result_counts(state)['defer']} "
            f"total={len(state.get('auto_results', []))}"
        ),
    )
    return {"command": "remote-qc-auto-run-current", "ok": True, "status": "finished"}


def _dispatch_remote_qc_message(
    *,
    message: str,
    ctx: TelegramContext,
    export_root: Path,
    gov_md_root: Path,
    remote_qc_root: Path,
    state_root: Path,
) -> dict[str, Any]:
    sender_id = ctx.sender_id
    if not sender_id:
        raise ValueError("Telegram sender_id를 찾지 못했습니다.")
    text = _normalize_message(message)
    title_open_requested = _wants_open_storage_title(text)
    implicit_title_open = False
    title_query = _extract_title_query_from_text(text) if title_open_requested else None
    if title_query is None and _should_try_implicit_title_open(text):
        title_query = text.strip()
        implicit_title_open = True
    sample_id = _resolve_sample_id_from_text(text, storage_root=DEFAULT_STORAGE_ROOT)
    recent_job_count = _requested_recent_job_count(text)
    auto_qc_count = _requested_auto_qc_count(text)

    if auto_qc_count is not None:
        return _build_auto_start_payload(
            sender_id=sender_id,
            message_id=ctx.message_id,
            export_root=export_root,
            gov_md_root=gov_md_root,
            remote_qc_root=remote_qc_root,
            state_root=state_root,
            limit=auto_qc_count,
        )

    if _wants_auto_status(text):
        return _auto_status_payload(sender_id=sender_id, state_root=state_root)

    if _wants_auto_stop(text):
        return _auto_stop_payload(sender_id=sender_id, state_root=state_root)

    if recent_job_count is not None:
        return _build_recent_storage_jobs_payload(
            export_root=export_root,
            gov_md_root=gov_md_root,
            remote_qc_root=remote_qc_root,
            storage_root=DEFAULT_STORAGE_ROOT,
            limit=recent_job_count,
        )

    if sample_id is None and title_query:
        policy_sample = _maybe_export_policy_briefing_sample(
            title_query,
            export_root=export_root,
            gov_md_root=gov_md_root,
            remote_qc_root=remote_qc_root,
            storage_root=DEFAULT_STORAGE_ROOT,
        )
        if policy_sample is not None:
            return _select_sample(
                policy_sample,
                sender_id=sender_id,
                state_root=state_root,
                gov_md_root=gov_md_root,
            )
        if title_open_requested or implicit_title_open:
            raise ValueError(f"해당 제목으로 매칭되는 국정브리핑 문서를 찾지 못했습니다: {title_query}")

    if sample_id and (_wants_open_sample(text) or text.strip() == sample_id):
        return _select_sample(
            _resolve_remote_sample(
                sample_id,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                storage_root=DEFAULT_STORAGE_ROOT,
            ),
            sender_id=sender_id,
            state_root=state_root,
            gov_md_root=gov_md_root,
        )
    if _wants_review_queue(text):
        return _build_job_list_payload(
            export_root=export_root,
            gov_md_root=gov_md_root,
            remote_qc_root=remote_qc_root,
            storage_root=DEFAULT_STORAGE_ROOT,
            review_only=True,
        )
    if _wants_job_list(text):
        return _build_job_list_payload(
            export_root=export_root,
            gov_md_root=gov_md_root,
            remote_qc_root=remote_qc_root,
            storage_root=DEFAULT_STORAGE_ROOT,
            review_only=False,
        )
    if _wants_next_job(text):
        auto_state = _apply_auto_state(_load_session_state(state_root, sender_id))
        if auto_state.get("auto_mode") and str(auto_state.get("auto_current_status", "")) == "awaiting_user":
            return _complete_auto_result(
                sender_id=sender_id,
                message_id=ctx.message_id,
                export_root=export_root,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
                outcome="defer",
            )
    if _wants_next_job(text):
        auto_state = _apply_auto_state(_load_session_state(state_root, sender_id))
        if auto_state.get("auto_mode"):
            return {
                "command": "remote-qc-auto-advance",
                "ok": False,
                "message": "현재 자동 QC가 승인 대기 상태가 아닙니다.",
            }
    if _wants_next_job(text):
        return _build_next_sample_payload(
            export_root=export_root,
            remote_qc_root=remote_qc_root,
            storage_root=DEFAULT_STORAGE_ROOT,
            sender_id=sender_id,
            state_root=state_root,
            gov_md_root=gov_md_root,
        )

    if _is_pass_message(text):
        auto_state = _apply_auto_state(_load_session_state(state_root, sender_id))
        if auto_state.get("auto_mode") and str(auto_state.get("auto_current_status", "")) == "awaiting_user":
            return _complete_auto_result(
                sender_id=sender_id,
                message_id=ctx.message_id,
                export_root=export_root,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
                outcome="pass",
            )
        sample = (
            _resolve_remote_sample(
                sample_id,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                storage_root=DEFAULT_STORAGE_ROOT,
            )
            if sample_id
            else _ensure_selected_sample(state_root, sender_id, remote_qc_root)
        )
        payload = _handle_pass(sender_id=sender_id, sample=sample, state_root=state_root, gov_md_root=gov_md_root)
        _reconcile_manual_auto_result(
            state_root=state_root,
            sender_id=sender_id,
            sample_id=sample.sample_id,
            outcome="pass",
            note="manually approved after batch completion",
        )
        return payload
    if _is_defer_message(text):
        auto_state = _apply_auto_state(_load_session_state(state_root, sender_id))
        if auto_state.get("auto_mode") and str(auto_state.get("auto_current_status", "")) == "awaiting_user":
            return _complete_auto_result(
                sender_id=sender_id,
                message_id=ctx.message_id,
                export_root=export_root,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
                outcome="defer",
            )
        sample = (
            _resolve_remote_sample(
                sample_id,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                storage_root=DEFAULT_STORAGE_ROOT,
            )
            if sample_id
            else _ensure_selected_sample(state_root, sender_id, remote_qc_root)
        )
        payload = _handle_defer(sender_id=sender_id, sample=sample, state_root=state_root, gov_md_root=gov_md_root)
        _reconcile_manual_auto_result(
            state_root=state_root,
            sender_id=sender_id,
            sample_id=sample.sample_id,
            outcome="defer",
            note="manually deferred after batch completion",
        )
        return payload
    if _wants_current_job_defer(text):
        auto_state = _apply_auto_state(_load_session_state(state_root, sender_id))
        if auto_state.get("auto_mode") and str(auto_state.get("auto_current_status", "")) == "awaiting_user":
            return _complete_auto_result(
                sender_id=sender_id,
                message_id=ctx.message_id,
                export_root=export_root,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
                outcome="defer",
            )
        return {
            "command": "remote-qc-auto-advance",
            "ok": False,
                "message": "현재 건너뛸 자동 QC job이 없습니다.",
            }

    sample = (
        _resolve_remote_sample(
            sample_id,
            gov_md_root=gov_md_root,
            remote_qc_root=remote_qc_root,
            storage_root=DEFAULT_STORAGE_ROOT,
        )
        if sample_id
        else _ensure_selected_sample(state_root, sender_id, remote_qc_root)
    )

    effective_media_paths = ctx.media_paths
    if not effective_media_paths and _wants_golden_upload_fix(text):
        effective_media_paths = _find_recent_inbound_markdown()

    if effective_media_paths:
        upload_payload = _handle_golden_upload(
            ctx=TelegramContext(
                sender_id=ctx.sender_id,
                message_id=ctx.message_id,
                media_paths=effective_media_paths,
            ),
            sender_id=sender_id,
            sample=sample,
            gov_md_root=gov_md_root,
        )
        fix_text = text.strip() if text.strip() else _build_default_fix_message_after_golden(sample)
        fix_payload = _spawn_background_fix(
            sender_id=sender_id,
            message_id=ctx.message_id,
            sample=sample,
            user_text=fix_text,
            export_root=export_root,
            gov_md_root=gov_md_root,
            qc_root=DEFAULT_QC_ROOT,
            remote_qc_root=remote_qc_root,
            state_root=state_root,
        )
        fix_payload["golden_upload"] = upload_payload
        return fix_payload
    if _is_fix_message(text):
        return _spawn_background_fix(
            sender_id=sender_id,
            message_id=ctx.message_id,
            sample=sample,
            user_text=text,
            export_root=export_root,
            gov_md_root=gov_md_root,
            qc_root=DEFAULT_QC_ROOT,
            remote_qc_root=remote_qc_root,
            state_root=state_root,
        )
    if _wants_golden_upload_fix(text):
        golden_path = sample.sample_dir / "golden.md"
        if not golden_path.exists():
            raise ValueError("현재 선택된 job에 golden.md가 없습니다. md 파일을 첨부해서 먼저 golden을 업로드해주세요.")
        fix_payload = _spawn_background_fix(
            sender_id=sender_id,
            message_id=ctx.message_id,
            sample=sample,
            user_text=_build_default_fix_message_after_golden(sample),
            export_root=export_root,
            gov_md_root=gov_md_root,
            qc_root=DEFAULT_QC_ROOT,
            remote_qc_root=remote_qc_root,
            state_root=state_root,
        )
        fix_payload["used_existing_golden"] = True
        return fix_payload

    file_keys = _requested_file_keys(text)
    if file_keys:
        results = _send_requested_files(
            sender_id=sender_id,
            message_id=ctx.message_id,
            sample=sample,
            file_keys=file_keys,
        )
        return {
            "command": "remote-qc-send-files",
            "sample_id": sample.sample_id,
            "results": results,
        }
    if "요약" in text or "차이" in text or "review" in text:
        return _build_sample_summary(sample)

    return {
        "command": "remote-qc-unsupported",
        "ok": False,
        "message": "지원: 최근 10건 job 뽑아서 qc 시작 | 현재 qc 상태 | 현재 batch 중지 | job 목록 보여줘 | review 필요한 job만 보여줘 | <sample-id> 열어줘 | 국정브리핑 보도자료 '<제목>' 열어줘 | source/rendered/review/golden 보내줘 | golden.md 업로드 | 통과 | 보류 | 수정: ...",
    }


def dispatch_telegram_message(
    message: str,
    *,
    chat_scope: str,
    export_root: Path,
    gov_md_root: Path,
    qc_root: Path,
    remote_qc_root: Path,
    state_root: Path,
) -> dict[str, Any]:
    if chat_scope != "dm":
        return {
            "command": "telegram-dispatch",
            "ok": False,
            "message": "GovPress QC commands are allowed only in direct Telegram DMs.",
        }
    normalized = _normalize_message(message)
    if normalized.startswith("/"):
        command, args = parse_telegram_command(normalized)
    else:
        ctx = build_telegram_context(message, state_root=state_root)
        payload = _dispatch_remote_qc_message(
            message=normalized,
            ctx=ctx,
            export_root=export_root,
            gov_md_root=gov_md_root,
            remote_qc_root=remote_qc_root,
            state_root=state_root,
        )
        if payload.get("command") == "remote-qc-open" and ctx.sender_id:
            sample = _find_sample(str(payload.get("sample_id")), remote_qc_root, DEFAULT_CURATED_QC_ROOT)
            file_keys = [key for key in ["review", "rendered", "source"] if (sample.sample_dir / {"review": "review.md", "rendered": "rendered.md", "source": "source.hwpx"}[key]).exists()]
            if sample.has_golden:
                file_keys.append("golden")
            payload["results"] = _send_requested_files(
                sender_id=ctx.sender_id,
                message_id=ctx.message_id,
                sample=sample,
                file_keys=file_keys,
            )
            if sample.sample_id.startswith("policy_briefing_"):
                payload["telegram_notification"] = _send_policy_briefing_open_telegram(
                    sample=sample,
                    export_root=export_root,
                    gov_md_root=gov_md_root,
                    qc_root=DEFAULT_QC_ROOT,
                )
        payload["ok"] = payload.get("ok", True)
        return payload
    if command == "qc-status":
        server_status = build_server_status()
        dashboard_url = next(
            (item["dashboard_url"] for item in server_status["status"] if item["key"] == server_status["primary_key"]),
            None,
        )
        payload = qc_status(export_root, args[0], dashboard_url=dashboard_url)
    elif command == "qc-failures":
        payload = qc_failures(export_root, args[0])
    elif command == "qc-issue":
        payload = qc_issue(export_root, args[0])
    elif command == "qc-rerun":
        payload = qc_rerun(args[0], output_root=export_root, gov_md_root=gov_md_root, qc_root=qc_root)
    elif command == "qc-promote":
        payload = qc_promote(args[1], qc_root=qc_root, gov_md_root=gov_md_root)
    elif command == "server-status":
        payload = {"command": "server-status", **build_server_status()}
    elif command == "server-failover-check":
        payload = server_failover_check()
    else:  # pragma: no cover
        raise ValueError(f"Unsupported command: {command}")
    payload["ok"] = True
    return payload


def format_human(payload: dict[str, Any]) -> str:
    command = payload.get("command")
    if command == "qc-status":
        summary = payload.get("summary", {})
        top_defects = payload.get("top_defects", [])
        top_samples = payload.get("top_samples", [])
        regression_failures = payload.get("latest_regression_failures", [])
        lines = [
            f"[QC] {payload.get('date')}",
            f"exported={summary.get('exported_count', 0)} review_required={summary.get('review_required_count', 0)} regression_failures={len(regression_failures)} proposals={summary.get('proposal_count', 0)} drafts={summary.get('draft_count', 0)}",
            f"report={payload.get('report_path')}",
        ]
        if payload.get("dashboard_url"):
            lines.append(f"dashboard={payload['dashboard_url']}")
        if not regression_failures and summary.get("review_required_count", 0):
            lines.append("note=review_required counts scratch samples pending human review, not current conversion failures")
        if top_defects:
            defect = top_defects[0]
            lines.append(f"top_defect={defect.get('defect_class')} ({defect.get('count')})")
        if top_samples:
            sample = top_samples[0]
            lines.append(f"top_sample={sample.get('sample_id')} ({sample.get('count')})")
        return "\n".join(lines)
    if command == "qc-failures":
        review_required = payload.get("review_required", [])
        regression_failures = payload.get("regression_failures", [])
        proposals = payload.get("proposals", [])
        lines = [
            f"[QC Failures] {payload.get('date')}",
            f"review_required={len(review_required)} regression_failures={len(regression_failures)} proposals={len(proposals)}",
            f"report={payload.get('report_path')}",
        ]
        if not regression_failures:
            lines.append("note=no current regression failures; remaining review queue is scratch-sample review")
        if review_required:
            sample = review_required[0]
            lines.append(f"first_review_sample={sample.get('sample_id')} risk={sample.get('risk_score')}")
        if proposals:
            proposal = proposals[0]
            first_file = (proposal.get("suggested_files") or ["-"])[0]
            lines.append(f"first_fix_target={proposal.get('defect_class')} file={first_file}")
        return "\n".join(lines)
    if command == "qc-issue":
        return "\n".join(
            [
                f"[QC Issue] {payload.get('date')}",
                f"title={payload.get('title')}",
                f"issue_payload={payload.get('issue_path')}",
                payload.get("body_preview", ""),
            ]
        ).strip()
    if command == "qc-rerun":
        summary = payload.get("summary", {})
        status = "ok" if payload.get("returncode") == 0 else "failed"
        return "\n".join(
            [
                f"[QC Rerun] {payload.get('date')} status={status}",
                f"exported={summary.get('exported_count', 0)} review_required={summary.get('review_required_count', 0)} proposals={summary.get('proposal_count', 0)} drafts={summary.get('draft_count', 0)}",
                f"report={payload.get('report_path')}",
                _shorten(payload.get("stderr") or payload.get("stdout"), limit=500),
            ]
        ).strip()
    if command == "qc-promote":
        status = "ok" if payload.get("returncode") == 0 else "failed"
        return "\n".join(
            [
                f"[QC Promote] sample={payload.get('sample_id')} status={status}",
                f"sample_dir={payload.get('sample_dir')}",
                _shorten(payload.get("stderr") or payload.get("stdout"), limit=500),
            ]
        ).strip()
    if command == "remote-qc-list":
        lines = [
            f"[QC Jobs] count={payload.get('sample_count', 0)} source=policy_briefing_latest20",
        ]
        for item in payload.get("samples", []):
            golden = "golden" if item.get("has_golden") else "no-golden"
            review = "review" if item.get("review_required") else "self-ok"
            defects = ",".join(item.get("defect_classes") or []) or "-"
            lines.append(
                f"- {item.get('sample_id')} risk={item.get('risk_score')} findings={item.get('finding_count')} "
                f"{review} {golden} title={item.get('title')} defects={defects}"
            )
        return "\n".join(lines)
    if command == "remote-qc-generate-recent-jobs":
        lines = [
            f"[QC Jobs Generated] recent={payload.get('limit')}",
            f"scaffolded={payload.get('scaffolded_count', 0)}",
            "source=국정브리핑 latest corpus (fresh scaffold)",
        ]
        for item in payload.get("items", [])[:10]:
            sample_dir = str(item.get("scaffold_sample_dir") or "")
            lines.append(
                f"- {item.get('sample_id')} risk={item.get('risk_score')} review={item.get('review_required')} "
                f"title={item.get('title')} sample={Path(sample_dir).name if sample_dir else '-'}"
            )
        lines.append("다음: `review 필요한 job만 보여줘` 또는 `<sample-id> 열어줘`")
        return "\n".join(lines)
    if command == "remote-qc-auto-start":
        lines = [
            f"[QC Auto Start] requested={payload.get('requested_count')}",
            f"review_queue={payload.get('queue_count', 0)} candidates={payload.get('candidate_count', 0)}",
            "note=`통과`는 사용자 승인 후만 집계됩니다. `iteration 5/5`는 통과가 아니라 마지막 자동 수정 시도입니다.",
        ]
        if payload.get("current_sample_id"):
            lines.append(f"current={payload.get('current_sample_id')}")
        for item in payload.get("queue_preview", [])[:3]:
            if not isinstance(item, dict):
                continue
            defects = ",".join(item.get("defect_classes") or []) or "-"
            lines.append(
                f"- {item.get('sample_id')} risk={item.get('risk_score')} findings={item.get('finding_count')} "
                f"hard={item.get('hard_finding_count')} title={_shorten(item.get('title'), limit=60)} defects={defects}"
            )
        if payload.get("queue_sample_ids"):
            lines.append("queue=" + ", ".join(payload.get("queue_sample_ids", [])[:5]))
        if payload.get("runner"):
            lines.append(f"pid={payload['runner'].get('pid')}")
        return "\n".join(lines)
    if command == "remote-qc-auto-status":
        lines = [
            f"[QC Auto Status] active={payload.get('auto_mode')}",
            f"batch={payload.get('batch_id')}",
            f"queue={payload.get('queue_index')}/{payload.get('queue_count')}",
            f"current={payload.get('current_sample_id')} status={payload.get('current_status')} attempt={payload.get('current_attempt')}",
        ]
        if payload.get("current_title"):
            lines.append(f"title={_shorten(payload.get('current_title'), limit=80)}")
        counts = payload.get("result_counts") or {}
        if isinstance(counts, dict):
            lines.append(
                f"user_approved_pass={counts.get('pass', 0)} auto_deferred={counts.get('defer', 0)} other={counts.get('other', 0)}"
            )
        results = payload.get("results", [])
        if results:
            last = results[-1]
            lines.append(f"last={last.get('sample_id')} outcome={last.get('outcome')} attempts={last.get('attempts')}")
        return "\n".join(lines)
    if command == "remote-qc-auto-stop":
        return str(payload.get("message", "")).strip()
    if command == "remote-qc-auto-advance":
        return str(payload.get("message", "")).strip()
    if command == "remote-qc-open":
        return "\n".join(
            [
                f"[QC Job Open] {payload.get('sample_id')}",
                f"status={payload.get('status')} golden={payload.get('has_golden')} review={payload.get('has_review')}",
                f"sample_dir={payload.get('sample_dir')}",
                "다음: `review 보내줘` 또는 `source 보내줘` 또는 `통과` 또는 `수정: ...`",
            ]
        )
    if command == "remote-qc-summary":
        lines = [
            f"[QC Summary] {payload.get('sample_id')}",
            f"status={payload.get('status')} golden={payload.get('has_golden')}",
        ]
        preview = str(payload.get("review_preview", "")).strip()
        if preview:
            lines.append(preview)
        return "\n".join(lines).strip()
    if command == "remote-qc-send-files":
        ok_count = len([item for item in payload.get("results", []) if item.get("ok")])
        lines = [
            f"[QC Files] {payload.get('sample_id')}",
            f"sent={ok_count}/{len(payload.get('results', []))}",
        ]
        for item in payload.get("results", []):
            status = "ok" if item.get("ok") else "failed"
            lines.append(f"- {item.get('file')}: {status}")
        return "\n".join(lines)
    if command == "remote-qc-upload-golden":
        return "\n".join(
            [
                f"[QC Golden Uploaded] {payload.get('sample_id')}",
                f"golden={payload.get('golden_path')}",
                f"review={payload.get('review_path')}",
                "다음: `review 보내줘` 또는 `통과` 또는 `수정: ...`",
            ]
        )
    if command == "remote-qc-pass":
        status = "ok" if payload.get("returncode") == 0 else "failed"
        return "\n".join(
            [
                f"[QC Pass] sample={payload.get('selected_sample_id')} status={status}",
                _shorten(payload.get("stderr") or payload.get("stdout"), limit=500),
            ]
        ).strip()
    if command == "remote-qc-defer":
        return str(payload.get("message", "")).strip()
    if command == "remote-qc-fix-queued":
        lines = [f"[QC Fix Queued] sample={payload.get('sample_id')}"]
        if payload.get("golden_upload"):
            lines.append("golden.md 저장 및 review 갱신 완료")
        if payload.get("used_existing_golden"):
            lines.append("기존 golden.md 기준으로 바로 수정 작업을 시작했습니다.")
        lines.append(f"pid={payload.get('pid')}")
        lines.append("수정 진행/완료 메시지는 이어서 전송됩니다.")
        return "\n".join(lines).strip()
    if command in {"remote-qc-fix-handoff", "remote-qc-upload-golden-and-fix", "remote-qc-use-existing-golden-and-fix"}:
        if payload.get("returncode") == 0 and payload.get("worker_text"):
            return str(payload.get("worker_text")).strip()
        return "\n".join(
            [
                f"[QC Fix Handoff Failed] sample={payload.get('sample_id')}",
                _shorten(payload.get("stderr") or payload.get("stdout"), limit=700),
            ]
        ).strip()
    if command == "remote-qc-next":
        if payload.get("sample_id"):
            return format_human(payload)
        return str(payload.get("message", "")).strip()
    if command in {"server-status", "server-failover-check"}:
        lines = [
            f"[Server Status] primary={payload.get('primary_key')} healthy={payload.get('primary_healthy')}",
            f"recommended={payload.get('recommended_url')}",
        ]
        for item in payload.get("status", [])[:3]:
            lines.append(f"{item.get('key')} status={item.get('status')} ok={item.get('ok')} url={item.get('url')}")
        if payload.get("message"):
            lines.append(payload["message"])
        return "\n".join(lines)
    if command == "telegram-dispatch" and payload.get("ok") is False:
        return str(payload.get("message"))
    return json.dumps(payload, ensure_ascii=False, indent=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpenClaw wrapper for GovPress QC and server health operations")
    parser.add_argument("--export-root", default=str(DEFAULT_EXPORT_ROOT))
    parser.add_argument("--gov-md-root", default=str(DEFAULT_GOV_MD_ROOT))
    parser.add_argument("--qc-root", default=str(DEFAULT_QC_ROOT))
    parser.add_argument("--remote-qc-root", default=str(DEFAULT_REMOTE_QC_ROOT))
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT))
    parser.add_argument("--json", action="store_true")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    status_parser = subparsers.add_parser("qc-status")
    status_parser.add_argument("--date", default="latest", type=_valid_date)
    status_parser.add_argument("--dashboard-url")

    failures_parser = subparsers.add_parser("qc-failures")
    failures_parser.add_argument("--date", default="latest", type=_valid_date)

    issue_parser = subparsers.add_parser("qc-issue")
    issue_parser.add_argument("--date", default="latest", type=_valid_date)

    rerun_parser = subparsers.add_parser("qc-rerun")
    rerun_parser.add_argument("--date", required=True, type=_valid_date)

    promote_parser = subparsers.add_parser("qc-promote")
    promote_parser.add_argument("--date", required=True, type=_valid_date)
    promote_parser.add_argument("--sample-id", required=True, type=_valid_sample_id)

    subparsers.add_parser("server-status")
    subparsers.add_parser("server-failover-check")

    dispatch_parser = subparsers.add_parser("telegram-dispatch")
    dispatch_parser.add_argument("--message", required=True)
    dispatch_parser.add_argument("--chat-scope", default="dm", choices=["dm", "group"])

    fix_runner = subparsers.add_parser("remote-qc-run-fix")
    fix_runner.add_argument("--sender-id", required=True)
    fix_runner.add_argument("--sample-id", required=True, type=_valid_sample_id)
    fix_runner.add_argument("--user-text", required=True)
    fix_runner.add_argument("--message-id")

    auto_start = subparsers.add_parser("remote-qc-auto-start")
    auto_start.add_argument("--sender-id", required=True)
    auto_start.add_argument("--limit", type=int, default=10)
    auto_start.add_argument("--message-id")

    auto_status = subparsers.add_parser("remote-qc-auto-status")
    auto_status.add_argument("--sender-id", required=True)

    auto_run = subparsers.add_parser("remote-qc-auto-run-current")
    auto_run.add_argument("--sender-id", required=True)
    auto_run.add_argument("--message-id")

    auto_advance = subparsers.add_parser("remote-qc-auto-advance")
    auto_advance.add_argument("--sender-id", required=True)
    auto_advance.add_argument("--outcome", choices=["pass", "defer"], required=True)
    auto_advance.add_argument("--message-id")

    auto_stop = subparsers.add_parser("remote-qc-auto-stop")
    auto_stop.add_argument("--sender-id", required=True)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    export_root = Path(args.export_root).resolve()
    gov_md_root = Path(args.gov_md_root).resolve()
    qc_root = Path(args.qc_root).resolve()
    remote_qc_root = Path(args.remote_qc_root).resolve()
    state_root = Path(args.state_root).resolve()
    try:
        if args.subcommand == "qc-status":
            payload = qc_status(export_root, args.date, dashboard_url=args.dashboard_url)
        elif args.subcommand == "qc-failures":
            payload = qc_failures(export_root, args.date)
        elif args.subcommand == "qc-issue":
            payload = qc_issue(export_root, args.date)
        elif args.subcommand == "qc-rerun":
            payload = qc_rerun(args.date, output_root=export_root, gov_md_root=gov_md_root, qc_root=qc_root)
        elif args.subcommand == "qc-promote":
            payload = qc_promote(args.sample_id, qc_root=qc_root, gov_md_root=gov_md_root)
            payload["date"] = args.date
        elif args.subcommand == "server-status":
            payload = {"command": "server-status", **build_server_status()}
        elif args.subcommand == "server-failover-check":
            payload = server_failover_check()
        elif args.subcommand == "telegram-dispatch":
            payload = dispatch_telegram_message(
                args.message,
                chat_scope=args.chat_scope,
                export_root=export_root,
                gov_md_root=gov_md_root,
                qc_root=qc_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
            )
        elif args.subcommand == "remote-qc-run-fix":
            payload = _run_fix_subcommand(
                sender_id=args.sender_id,
                message_id=args.message_id,
                sample_id=args.sample_id,
                user_text=args.user_text,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
            )
        elif args.subcommand == "remote-qc-auto-start":
            payload = _build_auto_start_payload(
                sender_id=args.sender_id,
                message_id=args.message_id,
                export_root=export_root,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
                limit=args.limit,
            )
        elif args.subcommand == "remote-qc-auto-status":
            payload = _auto_status_payload(sender_id=args.sender_id, state_root=state_root)
        elif args.subcommand == "remote-qc-auto-run-current":
            payload = _run_auto_current(
                sender_id=args.sender_id,
                message_id=args.message_id,
                export_root=export_root,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
            )
        elif args.subcommand == "remote-qc-auto-advance":
            payload = _complete_auto_result(
                sender_id=args.sender_id,
                message_id=args.message_id,
                export_root=export_root,
                gov_md_root=gov_md_root,
                remote_qc_root=remote_qc_root,
                state_root=state_root,
                outcome=args.outcome,
            )
        elif args.subcommand == "remote-qc-auto-stop":
            payload = _auto_stop_payload(sender_id=args.sender_id, state_root=state_root)
        else:  # pragma: no cover
            raise AssertionError(f"Unhandled subcommand {args.subcommand}")
    except Exception as exc:
        payload = {"command": args.subcommand, "ok": False, "message": str(exc)}
        if args.subcommand == "remote-qc-run-fix":
            try:
                _send_telegram_text(
                    sender_id=args.sender_id,
                    message_id=args.message_id,
                    message=f"[QC Fix Handoff Failed] sample={args.sample_id}\n{str(exc).strip()}",
                )
            except Exception:
                pass
        if args.subcommand == "remote-qc-auto-run-current":
            try:
                _send_telegram_text(
                    sender_id=args.sender_id,
                    message_id=args.message_id,
                    message=f"[QC Auto Failed]\n{str(exc).strip()}",
                )
            except Exception:
                pass
        print(json.dumps(payload, ensure_ascii=False, indent=2) if args.json else payload["message"])
        return 1

    human_text = format_human(payload)
    if args.subcommand == "telegram-dispatch" and args.chat_scope == "dm":
        try:
            ctx = build_telegram_context(args.message, state_root=state_root)
            if ctx.sender_id:
                _send_telegram_text(
                    sender_id=ctx.sender_id,
                    message_id=ctx.message_id,
                    message=human_text,
                )
        except Exception:
            pass

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(human_text)
    if payload.get("returncode") not in (None, 0):
        return int(payload["returncode"])
    if payload.get("ok") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
