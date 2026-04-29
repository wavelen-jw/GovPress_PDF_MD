#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path


QC_DOC = Path("/home/wavel/projects/gov-md-converter/docs/qc-v2-hardest-curated-press-releases.md")
QC_ROOT = Path("/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2")
OUTPUT_ROOT = Path("artifacts/hardest_policy_briefings")
DATA_OUTPUT = Path("ui/hardest-policy-briefings-data.js")

ENGINES = [
    {"key": "readhim", "label": "읽힘"},
    {"key": "kordoc", "label": "Kordoc"},
    {"key": "opendataloader", "label": "OpenDataLoader PDF"},
    {"key": "docling", "label": "Docling"},
    {"key": "chatgpt-5.4-medium", "label": "ChatGPT 5.4 medium"},
    {"key": "gemini", "label": "Gemini"},
]

DIFFICULTY_NOTES = {
    "156759031": "통계 보고서처럼 긴 문서입니다. 목차, 설명문, 수백 개의 표, 부록이 이어져서 제목과 표를 끝까지 일관되게 구분해야 합니다.",
    "156754934": "수출입 수치와 품목별 표가 매우 많습니다. 비슷한 표 제목과 숫자가 반복되어 표의 경계와 증감률 표기를 흐트러뜨리기 쉽습니다.",
    "156756008": "피해자 현황과 지원 건수 표가 길게 이어지고, 별표·쌍별표·참고 문장이 많습니다. 설명문이 표나 목록 안으로 섞이지 않게 분리해야 합니다.",
    "156757632": "본문은 보도자료 형식이지만 뒤쪽에는 조사 개요와 지역별 통계표가 이어집니다. 본문 설명, 그림 제목, 붙임 표의 구조를 각각 다르게 보존해야 합니다.",
    "156757541": "법률별 요약표와 11개 법안 설명이 이어집니다. 표 안의 긴 문장과 목록을 본문 목록으로 잘못 빼내지 않고 셀 안에 유지해야 합니다.",
    "156448349": "외국인 토지 보유 현황 표가 본문과 붙임에 반복됩니다. 예시 번호처럼 보이는 문장과 실제 번호 목록을 구분하고, 넓은 다단 표를 보존해야 합니다.",
    "156757495": "지가 변동률과 토지 거래량 표가 번갈아 나오고, 그림을 대신하는 표도 섞여 있습니다. 그림 설명과 실제 데이터 표를 구분해야 합니다.",
    "156757844": "행사 일정, 참여 기관, 인물 명단이 큰 표로 들어 있습니다. 표 셀 안에 긴 소개문과 줄바꿈이 많아 표 형태가 무너지기 쉽습니다.",
    "156755997": "보도자료 뒤에 정책 설명서에 가까운 긴 붙임이 이어집니다. 본문, 로드맵, 해외 사례, 담당부서 표를 각각 다른 구조로 읽어야 합니다.",
    "156757801": "본문은 짧지만 참고자료가 제도 설명서처럼 길게 이어집니다. 카드뉴스, 신청 기준, 법령 인용, 별표 설명을 서로 섞지 않는 것이 중요합니다.",
}


def table_rows(markdown: str) -> list[dict]:
    rows: list[dict] = []
    in_table = False
    for line in markdown.splitlines():
        if line.startswith("| 순위 |"):
            in_table = True
            continue
        if in_table and line.startswith("| ---"):
            continue
        if in_table and not line.startswith("|"):
            break
        if not in_table or not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) < 6:
            continue
        rows.append(
            {
                "rank": int(cells[0]),
                "sample_id": cells[1].strip("`"),
                "title": cells[2],
                "source_url": cells[3],
                "qc_status": cells[4],
                "difficulty_reason": cells[5],
            }
        )
    return rows


def details_by_sample(markdown: str) -> dict[str, dict]:
    sections = re.split(r"\n##\s+\d+\.\s+", "\n" + markdown)
    details: dict[str, dict] = {}
    for section in sections[1:]:
        lines = section.strip().splitlines()
        title = lines[0].strip() if lines else ""
        body = "\n".join(lines[1:]).strip()
        sample_match = re.search(r"sample id:\s*`([^`]+)`", body)
        if not sample_match:
            continue
        sample_id = sample_match.group(1)
        feature = ""
        qc_point = ""
        deferred_reason = ""
        for line in body.splitlines():
            if line.startswith("- 특징:"):
                feature = line.removeprefix("- 특징:").strip()
            elif line.startswith("- QC 포인트:"):
                qc_point = line.removeprefix("- QC 포인트:").strip()
            elif line.startswith("- 보류 사유:"):
                deferred_reason = line.removeprefix("- 보류 사유:").strip()
        details[sample_id] = {
            "section_title": title,
            "feature": feature,
            "qc_point": qc_point,
            "deferred_reason": deferred_reason,
        }
    return details


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def sample_for(sample_id: str) -> Path | None:
    path = QC_ROOT / sample_id
    return path if path.exists() else None


def news_id_from_sample(sample_id: str) -> str:
    match = re.search(r"(\d{9})$", sample_id)
    return match.group(1) if match else sample_id


def load_statuses(output_root: Path, engine: str) -> dict[str, dict]:
    status_path = output_root / "outputs" / engine / "status.json"
    if not status_path.exists():
        return {}
    payload = load_json(status_path)
    return {str(item["news_id"]): item for item in payload.get("documents", []) if "news_id" in item}


def copy_manual_outputs(output_root: Path, engine: str, source_engine: str | None = None) -> dict[str, dict]:
    source_engine = source_engine or engine
    source_dir = output_root / "manual" / source_engine
    target_dir = output_root / "outputs" / engine
    target_dir.mkdir(parents=True, exist_ok=True)
    statuses: dict[str, dict] = {}
    for md_path in source_dir.glob("*.md"):
        news_id = md_path.stem
        shutil.copyfile(md_path, target_dir / f"{news_id}.md")
        statuses[news_id] = {"news_id": news_id, "status": "available"}
    status_payload = {
        "engine": engine,
        "documents": list(statuses.values()),
    }
    (target_dir / "status.json").write_text(json.dumps(status_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return statuses


def build_payload() -> dict:
    markdown = QC_DOC.read_text(encoding="utf-8")
    rows = table_rows(markdown)
    details = details_by_sample(markdown)

    output_root = OUTPUT_ROOT.resolve()
    manual_chatgpt = copy_manual_outputs(output_root, "chatgpt-5.4-medium")
    manual_gemini = copy_manual_outputs(output_root, "gemini")
    status_by_engine = {
        engine["key"]: {
            **load_statuses(output_root, engine["key"]),
            **({"__manual__": {"status": "available"}} if engine["key"] == "chatgpt-5.4-medium" and manual_chatgpt else {}),
            **({"__manual__": {"status": "available"}} if engine["key"] == "gemini" and manual_gemini else {}),
        }
        for engine in ENGINES
    }

    documents: list[dict] = []
    for row in rows:
        sample_id = row["sample_id"]
        news_id = news_id_from_sample(sample_id)
        sample_dir = sample_for(sample_id)
        meta = load_json(sample_dir / "meta.json") if sample_dir else {}
        document_metadata = meta.get("document_metadata") if isinstance(meta.get("document_metadata"), dict) else {}
        title = row["title"] or meta.get("title") or document_metadata.get("title") or sample_id
        department = meta.get("department") or document_metadata.get("issuer_agency") or ""
        engine_results = []
        for engine in ENGINES:
            key = engine["key"]
            status = status_by_engine.get(key, {}).get(news_id, {})
            md_path = output_root / "outputs" / key / f"{news_id}.md"
            if md_path.exists():
                state = "available"
                relative_path = f"outputs/{key}/{news_id}.md"
            else:
                state = status.get("status") or ("manual_missing" if key in {"chatgpt-5.4-medium", "gemini"} else "missing")
                relative_path = ""
            engine_results.append(
                {
                    "key": key,
                    "label": engine["label"],
                    "status": state,
                    "path": relative_path,
                    "error": "" if state == "available" else status.get("error", ""),
                }
            )
        documents.append(
            {
                "rank": row["rank"],
                "title": title,
                "source_url": row["source_url"],
                "department": department,
                "difficulty_note": DIFFICULTY_NOTES.get(news_id, row["difficulty_reason"]),
                "engines": engine_results,
            }
        )

    return {
        "title": "AI가 고른 어려운 보도자료 10선",
        "subtitle": "표, 붙임, 각주가 복잡하게 섞인 정책브리핑 문서를 여러 변환 도구로 비교합니다.",
        "generated_at": "2026-04-29",
        "engines": ENGINES,
        "documents": documents,
    }


def main() -> int:
    payload = build_payload()
    DATA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    DATA_OUTPUT.write_text(
        "window.HARDEST_POLICY_BRIEFINGS_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
