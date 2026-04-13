#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_eval(path: Path) -> dict:
    return json.loads(path.read_text())


def fmt(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "n/a"


def top_docs(payload: dict, limit: int = 5, reverse: bool = True) -> list[dict]:
    docs = [doc for doc in payload["documents"] if doc["scores"]["overall"] is not None]
    return sorted(docs, key=lambda doc: doc["scores"]["overall"], reverse=reverse)[:limit]


def paired_deltas(
    readhim: dict, opendataloader: dict, limit: int = 5
) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    readhim_scores = {
        doc["document_id"]: doc["scores"]["overall"]
        for doc in readhim["documents"]
        if doc["scores"]["overall"] is not None
    }
    opendataloader_scores = {
        doc["document_id"]: doc["scores"]["overall"]
        for doc in opendataloader["documents"]
        if doc["scores"]["overall"] is not None
    }
    deltas = []
    for doc_id in sorted(set(readhim_scores) | set(opendataloader_scores)):
        readhim_score = readhim_scores.get(doc_id)
        opendataloader_score = opendataloader_scores.get(doc_id)
        if readhim_score is None or opendataloader_score is None:
            continue
        deltas.append((doc_id, readhim_score - opendataloader_score))
    best_for_readhim = sorted(deltas, key=lambda item: item[1], reverse=True)[:limit]
    best_for_opendataloader = sorted(deltas, key=lambda item: item[1])[:limit]
    return best_for_readhim, best_for_opendataloader


def build_table_section(title: str, docs: list[dict]) -> list[str]:
    lines = [
        f"## {title}",
        "",
        "| 문서 ID | overall | nid | teds | mhs |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for doc in docs:
        scores = doc["scores"]
        lines.append(
            f"| {doc['document_id']} | {fmt(scores['overall'])} | {fmt(scores['nid'])} | {fmt(scores['teds'])} | {fmt(scores['mhs'])} |"
        )
    lines.append("")
    return lines


def build_summary(readhim: dict, opendataloader: dict) -> str:
    r_metrics = readhim["metrics"]["score"]
    o_metrics = opendataloader["metrics"]["score"]
    best_for_readhim, best_for_opendataloader = paired_deltas(readhim, opendataloader)
    lines = [
        "# 정책브리핑 99건 벤치마크 요약",
        "",
        "## 개요",
        "",
        "- Ground-truth: 정책브리핑 `docViewer` HTML을 정규화한 Markdown",
        "- 읽힘: `HWPX -> Markdown`",
        "- OpenDataLoader: `PDF -> Markdown`",
        "- 평가: `opendataloader-bench`의 `NID`, `TEDS`, `MHS`",
        "",
        "## 평균 점수",
        "",
        "| 엔진 | overall | nid | teds | mhs | missing_predictions |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| 읽힘 | {fmt(r_metrics['overall_mean'])} | {fmt(r_metrics['nid_mean'])} | {fmt(r_metrics['teds_mean'])} | {fmt(r_metrics['mhs_mean'])} | {readhim['metrics']['missing_predictions']} |",
        f"| OpenDataLoader | {fmt(o_metrics['overall_mean'])} | {fmt(o_metrics['nid_mean'])} | {fmt(o_metrics['teds_mean'])} | {fmt(o_metrics['mhs_mean'])} | {opendataloader['metrics']['missing_predictions']} |",
        "",
        "## 집계 메모",
        "",
        f"- Ground-truth 문서 수: {len(readhim['documents'])}건",
        f"- 읽힘 TEDS 집계 건수: {readhim['metrics']['teds_count']}건",
        f"- OpenDataLoader TEDS 집계 건수: {opendataloader['metrics']['teds_count']}건",
        f"- 읽힘 표 평가 timeout: {readhim['metrics'].get('table_timeouts', 0)}건",
        "",
    ]
    lines.extend(build_table_section("읽힘 상위 5건", top_docs(readhim, 5, reverse=True)))
    lines.extend(build_table_section("읽힘 하위 5건", top_docs(readhim, 5, reverse=False)))
    lines.extend(
        [
            "## 엔진 간 차이",
            "",
            "### 읽힘 우세 상위 5건",
            "",
            "| 문서 ID | overall 차이 (읽힘 - ODL) |",
            "| --- | ---: |",
        ]
    )
    for doc_id, delta in best_for_readhim:
        lines.append(f"| {doc_id} | {delta:.4f} |")
    lines.extend(
        [
            "",
            "### OpenDataLoader 우세 상위 5건",
            "",
            "| 문서 ID | overall 차이 (읽힘 - ODL) |",
            "| --- | ---: |",
        ]
    )
    for doc_id, delta in best_for_opendataloader:
        lines.append(f"| {doc_id} | {delta:.4f} |")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readhim", required=True)
    parser.add_argument("--opendataloader", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    summary = build_summary(
        load_eval(Path(args.readhim)),
        load_eval(Path(args.opendataloader)),
    )
    Path(args.output).write_text(summary)


if __name__ == "__main__":
    main()
