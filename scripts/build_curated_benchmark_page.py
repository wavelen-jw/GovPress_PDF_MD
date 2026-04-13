#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build static benchmark page data for the curated OpenDataLoader comparison."
    )
    parser.add_argument(
        "--samples-root",
        type=Path,
        default=Path("/mnt/c/FTC_downloads/storage_batch_curated_hwpx_pdf"),
        help="Root containing per-document folders with rendered.md and source.pdf.",
    )
    parser.add_argument(
        "--results-root",
        type=Path,
        default=Path("artifacts/opendataloader_curated_bench/results"),
        help="Result folder containing evaluation-curated-final.json and prediction_markdown/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("ui/benchmark-curated-data.js"),
        help="Output JS file that assigns window.BENCHMARK_CURATED_DATA.",
    )
    return parser.parse_args()


def score_band(value: float) -> str:
    if value >= 0.6:
        return "strong"
    if value >= 0.45:
        return "mixed"
    return "weak"


def extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped).strip() or fallback
    return fallback


def metric_commentary(scores: dict[str, float | None]) -> list[str]:
    comments: list[str] = []
    nid = float(scores.get("nid") or 0.0)
    teds = scores.get("teds")
    mhs = float(scores.get("mhs") or 0.0)

    if nid >= 0.9:
        comments.append("본문 읽기 순서는 매우 안정적입니다.")
    elif nid >= 0.8:
        comments.append("본문 읽기 순서는 대체로 안정적입니다.")
    else:
        comments.append("본문 읽기 순서가 흔들려 사람이 다시 확인해야 합니다.")

    if teds is None:
        comments.append("표 구조 평가는 적용되지 않았습니다.")
    elif float(teds) >= 0.75:
        comments.append("표 구조 재현이 강한 편입니다.")
    elif float(teds) >= 0.4:
        comments.append("표는 일부 맞지만 셀 병합이나 정렬은 흔들립니다.")
    else:
        comments.append("표 구조가 크게 무너져 수동 정리가 필요합니다.")

    if mhs >= 0.3:
        comments.append("제목 계층도 비교적 유지됐습니다.")
    elif mhs > 0:
        comments.append("제목 계층은 일부만 보존됐습니다.")
    else:
        comments.append("제목 계층은 golden과 거의 맞지 않습니다.")

    return comments


def build_payload(samples_root: Path, results_root: Path) -> dict:
    evaluation_path = results_root / "evaluation-curated-final.json"
    prediction_root = results_root / "prediction_markdown"
    evaluation = json.loads(evaluation_path.read_text(encoding="utf-8"))
    score_metrics = evaluation["metrics"]["score"]

    documents = []
    for item in sorted(
        evaluation["documents"],
        key=lambda entry: entry["scores"]["overall"],
        reverse=True,
    ):
        doc_id = item["document_id"]
        sample_dir = samples_root / doc_id
        golden_path = sample_dir / "rendered.md"
        prediction_path = prediction_root / f"{doc_id}.md"
        golden_text = golden_path.read_text(encoding="utf-8", errors="ignore")
        prediction_text = prediction_path.read_text(encoding="utf-8", errors="ignore")
        title = extract_title(golden_text, doc_id)
        scores = item["scores"]
        documents.append(
            {
                "document_id": doc_id,
                "title": title,
                "band": score_band(float(scores["overall"])),
                "scores": scores,
                "commentary": metric_commentary(scores),
                "golden_markdown": golden_text,
                "prediction_markdown": prediction_text,
                "golden_preview": golden_text[:4000],
                "prediction_preview": prediction_text[:4000],
                "golden_length": len(golden_text),
                "prediction_length": len(prediction_text),
            }
        )

    top_documents = [doc["document_id"] for doc in documents[:3]]
    bottom_documents = [doc["document_id"] for doc in documents[-3:]]
    excluded = ["storage_job_23c81b8c21fd"]

    return {
        "title": "OpenDataLoader 정적 비교 리포트",
        "subtitle": "PDF를 Markdown으로 변환한 결과를 curated golden Markdown과 비교",
        "engine": "opendataloader",
        "input_root": str(samples_root),
        "golden_source": "rendered.md",
        "excluded_documents": excluded,
        "document_count": len(documents),
        "aggregate_metrics": {
            "overall_mean": score_metrics["overall_mean"],
            "nid_mean": score_metrics["nid_mean"],
            "nid_s_mean": score_metrics["nid_s_mean"],
            "teds_mean": score_metrics["teds_mean"],
            "teds_s_mean": score_metrics["teds_s_mean"],
            "mhs_mean": score_metrics["mhs_mean"],
            "mhs_s_mean": score_metrics["mhs_s_mean"],
            "missing_predictions": evaluation["metrics"]["missing_predictions"],
        },
        "metric_help": [
            {
                "name": "overall",
                "label": "Overall 점수",
                "description": "읽기 순서, 표 구조, 제목 계층을 합쳐 본 최종 지표입니다.",
            },
            {
                "name": "nid",
                "label": "읽기 순서 (NID)",
                "description": "본문 텍스트가 올바른 순서로 추출됐는지 봅니다. 높을수록 문맥 손상이 적습니다.",
            },
            {
                "name": "teds",
                "label": "표 구조 (TEDS)",
                "description": "표의 행·열·병합 구조가 golden과 얼마나 비슷한지 봅니다.",
            },
            {
                "name": "mhs",
                "label": "제목 계층 (MHS)",
                "description": "제목 레벨과 문서 계층이 golden Markdown과 얼마나 일치하는지 봅니다.",
            },
        ],
        "top_documents": top_documents,
        "bottom_documents": bottom_documents,
        "documents": documents,
    }


def main() -> int:
    args = parse_args()
    payload = build_payload(args.samples_root.resolve(), args.results_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    js_text = "window.BENCHMARK_CURATED_DATA = " + json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    ) + ";\n"
    args.output.write_text(js_text, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
