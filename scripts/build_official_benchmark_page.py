#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


BENCHMARK_REPO_DEFAULT = Path("/home/wavel/opendataloader-bench")
OUTPUT_DEFAULT = Path("ui/benchmark-official-data.js")

ENGINE_META = {
    "opendataloader-hybrid": {
        "label": "OpenDataLoader [hybrid]",
        "license": "Apache-2.0",
        "kind": "official",
        "speed_s_per_page": 0.463,
    },
    "docling": {"label": "Docling", "license": "MIT", "kind": "official", "speed_s_per_page": 0.762},
    "nutrient": {"label": "Nutrient", "license": "Proprietary", "kind": "official", "speed_s_per_page": 0.230},
    "marker": {"label": "Marker", "license": "GPL-3.0", "kind": "official", "speed_s_per_page": 53.932},
    "unstructured-hires": {
        "label": "Unstructured [hi_res]",
        "license": "Apache-2.0",
        "kind": "official",
        "speed_s_per_page": 3.008,
    },
    "edgeparse": {"label": "EdgeParse", "license": "Apache-2.0", "kind": "official", "speed_s_per_page": 0.036},
    "opendataloader": {
        "label": "OpenDataLoader",
        "license": "Apache-2.0",
        "kind": "official",
        "speed_s_per_page": 0.015,
    },
    "mineru": {"label": "MinerU", "license": "AGPL-3.0", "kind": "official", "speed_s_per_page": 5.962},
    "pymupdf4llm": {
        "label": "PyMuPDF4LLM",
        "license": "AGPL-3.0",
        "kind": "official",
        "speed_s_per_page": 0.091,
    },
    "unstructured": {
        "label": "Unstructured",
        "license": "Apache-2.0",
        "kind": "official",
        "speed_s_per_page": 0.077,
    },
    "markitdown": {"label": "MarkItDown", "license": "MIT", "kind": "official", "speed_s_per_page": 0.114},
    "liteparse": {
        "label": "LiteParse",
        "license": "Apache-2.0",
        "kind": "official",
        "speed_s_per_page": 1.061,
    },
    "readhim": {"label": "읽힘", "license": "Proprietary", "kind": "local"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a static page for official opendataloader-bench style comparison."
    )
    parser.add_argument(
        "--benchmark-repo",
        type=Path,
        default=BENCHMARK_REPO_DEFAULT,
        help="Local clone of opendataloader-bench.",
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


def extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return re.sub(r"^#+\s*", "", stripped).strip() or fallback
    return fallback


def safe_float(value):
    return None if value is None else float(value)


def engine_row(engine_name: str, payload: dict) -> dict:
    metrics = payload["metrics"]["score"]
    summary = payload.get("summary") or {}
    meta = ENGINE_META.get(
        engine_name,
        {"label": engine_name, "license": "Unknown", "kind": "local"},
    )
    return {
        "engine": engine_name,
        "label": meta["label"],
        "license": meta["license"],
        "kind": meta["kind"],
        "overall": safe_float(metrics.get("overall_mean")),
        "nid": safe_float(metrics.get("nid_mean")),
        "teds": safe_float(metrics.get("teds_mean")),
        "mhs": safe_float(metrics.get("mhs_mean")),
        "speed_s_per_page": safe_float(meta.get("speed_s_per_page", summary.get("elapsed_per_doc"))),
        "processor": summary.get("processor"),
        "document_count": summary.get("document_count"),
        "date": summary.get("date"),
        "missing_predictions": payload["metrics"].get("missing_predictions"),
    }


def build_examples(benchmark_repo: Path, readhim_eval: dict, opendataloader_eval: dict) -> list[dict]:
    gt_root = benchmark_repo / "ground-truth" / "markdown"
    prediction_root = benchmark_repo / "prediction"

    readhim_docs = {
        item["document_id"]: item["scores"]
        for item in readhim_eval["documents"]
        if item.get("prediction_available")
    }
    odl_docs = {
        item["document_id"]: item["scores"]
        for item in opendataloader_eval["documents"]
        if item.get("prediction_available")
    }

    examples: list[dict] = []
    ranked_doc_ids = sorted(
        set(readhim_docs) & set(odl_docs),
        key=lambda doc_id: abs(
            float(readhim_docs[doc_id].get("overall") or 0.0)
            - float(odl_docs[doc_id].get("overall") or 0.0)
        ),
        reverse=True,
    )[:6]

    for doc_id in ranked_doc_ids:
        gt_path = gt_root / f"{doc_id}.md"
        readhim_path = prediction_root / "readhim" / "markdown" / f"{doc_id}.md"
        odl_path = prediction_root / "opendataloader" / "markdown" / f"{doc_id}.md"
        gt_markdown = gt_path.read_text(encoding="utf-8", errors="ignore")
        readhim_markdown = readhim_path.read_text(encoding="utf-8", errors="ignore")
        odl_markdown = odl_path.read_text(encoding="utf-8", errors="ignore")
        examples.append(
            {
                "document_id": doc_id,
                "title": extract_title(gt_markdown, doc_id),
                "readhim_scores": readhim_docs[doc_id],
                "opendataloader_scores": odl_docs[doc_id],
                "ground_truth_markdown": gt_markdown[:12000],
                "readhim_markdown": readhim_markdown[:12000],
                "opendataloader_markdown": odl_markdown[:12000],
            }
        )
    return examples


def build_payload(benchmark_repo: Path) -> dict:
    prediction_root = benchmark_repo / "prediction"
    repo_head = (
        __import__("subprocess")
        .run(
            ["git", "-C", str(benchmark_repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        .stdout.strip()
    )

    rows = []
    for engine_name, meta in ENGINE_META.items():
        evaluation_path = prediction_root / engine_name / "evaluation.json"
        if not evaluation_path.exists():
            continue
        rows.append(engine_row(engine_name, load_json(evaluation_path)))

    rows.sort(key=lambda item: (item["overall"] is None, -(item["overall"] or 0.0)))

    readhim_eval = load_json(prediction_root / "readhim" / "evaluation.json")
    opendataloader_eval = load_json(prediction_root / "opendataloader" / "evaluation.json")
    top_row = next((row for row in rows if row["engine"] == "readhim"), None)

    payload = {
        "title": "공식 벤치 방식으로 본 읽힘 PDF 성능",
        "subtitle": "OpenDataLoader 공식 벤치 코퍼스와 동일한 ground truth, 동일한 evaluator 위에서 읽힘을 하나의 PDF 변환 엔진으로 추가 비교",
        "repo": {
            "url": "https://github.com/opendataloader-project/opendataloader-bench",
            "commit": repo_head,
            "docs_url": "https://opendataloader.org/docs/benchmark",
        },
        "corpus": {
            "pdf_count": len(list((benchmark_repo / "pdfs").glob("*.pdf"))),
            "ground_truth_count": len(list((benchmark_repo / "ground-truth" / "markdown").glob("*.md"))),
            "ground_truth_path": "ground-truth/markdown",
            "pdf_path": "pdfs",
        },
        "readhim_adapter": {
            "engine_name": "readhim",
            "display_name": "읽힘",
            "adapter_note": "읽힘 행은 local clone의 opendataloader-bench에 readhim 엔진을 추가하고, govpress_converter.convert_pdf()를 통해 prediction/readhim/markdown 을 생성한 뒤 src/evaluator.py로 평가했습니다.",
            "run_environment": "WSL Ubuntu on server W",
        },
        "leaderboard": rows,
        "readhim": top_row,
        "examples": build_examples(benchmark_repo, readhim_eval, opendataloader_eval),
        "metric_help": [
            {
                "label": "Overall",
                "description": "문서별 NID, TEDS, MHS 평균입니다. 공식 벤치의 문서별 집계 규칙을 그대로 따릅니다.",
            },
            {
                "label": "NID",
                "description": "읽기 순서 유사도입니다. 본문 텍스트의 순서와 내용이 ground truth에 얼마나 가까운지 봅니다.",
            },
            {
                "label": "TEDS",
                "description": "표 구조 유사도입니다. 테이블 DOM 구조와 셀 내용을 함께 비교합니다.",
            },
            {
                "label": "MHS",
                "description": "제목 계층 유사도입니다. heading 레벨과 구조 보존 정도를 봅니다.",
            },
        ],
        "source_notes": [
            {
                "label": "공식 벤치 문서",
                "url": "https://opendataloader.org/docs/benchmark",
                "description": "지표 정의, 공식 리더보드, 재현 방법.",
            },
            {
                "label": "벤치 구현 저장소",
                "url": "https://github.com/opendataloader-project/opendataloader-bench",
                "description": f"이번 비교가 기반한 로컬 clone의 원격 저장소. 사용한 commit: {repo_head}",
            },
            {
                "label": "이번 실행 방식",
                "url": "https://github.com/wavelen-jw/GovPress_PDF_MD",
                "description": "이 리포지토리에서 readhim 어댑터와 정적 페이지를 추가하고, 공식 코퍼스 위에서 읽힘을 별도 엔진으로 실행.",
            },
        ],
    }
    return payload


def main() -> int:
    args = parse_args()
    payload = build_payload(args.benchmark_repo.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    text = "window.BENCHMARK_OFFICIAL_DATA = " + json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
    ) + ";\n"
    args.output.write_text(text, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
