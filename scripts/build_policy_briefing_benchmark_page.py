#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


OUTPUT_DEFAULT = Path("ui/benchmark-policy-briefing-data.js")
CORPUS_DEFAULT = Path("artifacts/policy_briefing_benchmark/corpus_latest100")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a static page payload for the policy briefing benchmark."
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=CORPUS_DEFAULT,
        help="Policy briefing benchmark corpus root.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_DEFAULT,
        help="Output JS file path.",
    )
    return parser.parse_args()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_float(value):
    return None if value is None else float(value)


def clean_title(title: str) -> str:
    return re.sub(r"^\[[^\]]+\]\s*", "", title).strip()


def markdown_excerpt(path: Path, limit: int = 12000) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")[:limit]


def merge_rows(manifest: dict, readhim_eval: dict, opendataloader_eval: dict) -> list[dict]:
    manifest_rows = {item["news_item_id"]: item for item in manifest["documents"]}
    readhim_rows = {item["document_id"]: item for item in readhim_eval["documents"]}
    opendataloader_rows = {item["document_id"]: item for item in opendataloader_eval["documents"]}

    rows: list[dict] = []
    for doc_id, meta in sorted(
        manifest_rows.items(),
        key=lambda item: item[1]["approve_date"],
        reverse=True,
    ):
        readhim = readhim_rows.get(doc_id, {})
        opendataloader = opendataloader_rows.get(doc_id, {})
        readhim_scores = readhim.get("scores", {})
        opendataloader_scores = opendataloader.get("scores", {})
        readhim_overall = readhim_scores.get("overall")
        opendataloader_overall = opendataloader_scores.get("overall")
        rows.append(
            {
                "document_id": doc_id,
                "title": clean_title(meta["title"]),
                "department": meta["department"],
                "approve_date": meta["approve_date"],
                "readhim": {
                    "overall": safe_float(readhim_overall),
                    "nid": safe_float(readhim_scores.get("nid")),
                    "teds": safe_float(readhim_scores.get("teds")),
                    "mhs": safe_float(readhim_scores.get("mhs")),
                    "prediction_available": bool(readhim.get("prediction_available")),
                    "table_timed_out": bool(readhim.get("table_timed_out")),
                },
                "opendataloader": {
                    "overall": safe_float(opendataloader_overall),
                    "nid": safe_float(opendataloader_scores.get("nid")),
                    "teds": safe_float(opendataloader_scores.get("teds")),
                    "mhs": safe_float(opendataloader_scores.get("mhs")),
                    "prediction_available": bool(opendataloader.get("prediction_available")),
                },
                "delta_overall": (
                    safe_float(readhim_overall) - safe_float(opendataloader_overall)
                    if readhim_overall is not None and opendataloader_overall is not None
                    else None
                ),
            }
        )
    return rows


def choose_example_ids(rows: list[dict]) -> list[str]:
    paired = [row for row in rows if row["delta_overall"] is not None]
    biggest_delta = sorted(
        paired,
        key=lambda row: abs(row["delta_overall"]),
        reverse=True,
    )[:4]
    best_readhim = sorted(
        [row for row in rows if row["readhim"]["overall"] is not None],
        key=lambda row: row["readhim"]["overall"],
        reverse=True,
    )[:2]
    best_odl = sorted(
        [row for row in rows if row["opendataloader"]["overall"] is not None],
        key=lambda row: row["opendataloader"]["overall"],
        reverse=True,
    )[:2]
    ordered = []
    for row in biggest_delta + best_readhim + best_odl:
        if row["document_id"] not in ordered:
            ordered.append(row["document_id"])
    return ordered[:6]


def build_examples(corpus_dir: Path, rows: list[dict]) -> list[dict]:
    gt_dir = corpus_dir / "ground-truth"
    readhim_dir = corpus_dir / "prediction" / "readhim" / "markdown"
    opendataloader_dir = corpus_dir / "prediction" / "opendataloader" / "markdown"
    by_id = {row["document_id"]: row for row in rows}
    examples: list[dict] = []
    for doc_id in choose_example_ids(rows):
        row = by_id[doc_id]
        examples.append(
            {
                "document_id": doc_id,
                "title": row["title"],
                "department": row["department"],
                "approve_date": row["approve_date"],
                "readhim": row["readhim"],
                "opendataloader": row["opendataloader"],
                "ground_truth_markdown": markdown_excerpt(gt_dir / f"{doc_id}.md"),
                "readhim_markdown": markdown_excerpt(readhim_dir / f"{doc_id}.md")
                if (readhim_dir / f"{doc_id}.md").exists()
                else "",
                "opendataloader_markdown": markdown_excerpt(opendataloader_dir / f"{doc_id}.md")
                if (opendataloader_dir / f"{doc_id}.md").exists()
                else "",
            }
        )
    return examples


def build_payload(corpus_dir: Path) -> dict:
    manifest = load_json(corpus_dir / "manifest.json")
    readhim_eval = load_json(corpus_dir / "prediction" / "readhim" / "evaluation.json")
    opendataloader_eval = load_json(corpus_dir / "prediction" / "opendataloader" / "evaluation.json")
    rows = merge_rows(manifest, readhim_eval, opendataloader_eval)

    payload = {
        "title": "정책브리핑 99건 벤치마크",
        "subtitle": "정책브리핑 보도자료를 기준으로 Ground Truth를 직접 만들고, 읽힘(HWPX->MD)과 OpenDataLoader(PDF->MD)를 같은 지표로 비교한 결과",
        "corpus": {
            "document_count": manifest["document_count"],
            "ground_truth_count": len(manifest["documents"]),
            "failure_count": len(manifest.get("failures", [])),
            "generated_at": manifest["generated_at"],
            "note": "최신 정책브리핑 보도자료 중 PDF와 HWPX가 모두 있는 문서를 대상으로 docViewer HTML을 Markdown으로 정규화해 ground truth를 생성했습니다.",
        },
        "metrics": {
            "readhim": readhim_eval["metrics"],
            "opendataloader": opendataloader_eval["metrics"],
        },
        "summary": {
            "readhim": readhim_eval.get("summary", {}),
            "opendataloader": opendataloader_eval.get("summary", {}),
        },
        "documents": rows,
        "examples": build_examples(corpus_dir, rows),
        "source_notes": [
            {
                "label": "OpenDataLoader Benchmark 문서",
                "url": "https://opendataloader.org/docs/benchmark",
                "description": "NID, TEDS, MHS 정의와 공식 벤치 재현 방법의 기준 문서.",
            },
            {
                "label": "opendataloader-bench 저장소",
                "url": "https://github.com/opendataloader-project/opendataloader-bench",
                "description": "이번 비교에서 사용한 evaluator의 원본 저장소. 지표 구현과 출력 형식의 출처입니다.",
            },
            {
                "label": "GovPress_PDF_MD",
                "url": "https://github.com/wavelen-jw/GovPress_PDF_MD",
                "description": "정책브리핑 ground truth 생성, 읽힘/ODL 실행, 정적 리포트 생성 코드를 추가한 실행 리포지토리.",
            },
        ],
        "metric_help": [
            {
                "label": "Overall",
                "description": "문서별 NID, TEDS, MHS의 평균입니다. 표가 없는 문서는 있는 지표만으로 평균합니다.",
                "source_url": "https://opendataloader.org/docs/benchmark",
            },
            {
                "label": "NID",
                "description": "본문 읽기 순서와 텍스트 보존 정도를 보는 지표입니다.",
                "source_url": "https://opendataloader.org/docs/benchmark",
            },
            {
                "label": "TEDS",
                "description": "표 구조와 셀 내용을 함께 비교하는 지표입니다.",
                "source_url": "https://opendataloader.org/docs/benchmark",
            },
            {
                "label": "MHS",
                "description": "제목 계층과 섹션 구조 보존 정도를 보는 지표입니다.",
                "source_url": "https://opendataloader.org/docs/benchmark",
            },
        ],
        "failure_notes": manifest.get("failures", []),
    }
    return payload


def main() -> int:
    args = parse_args()
    payload = build_payload(args.corpus_dir.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "window.BENCHMARK_POLICY_BRIEFING_DATA = "
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + ";\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
