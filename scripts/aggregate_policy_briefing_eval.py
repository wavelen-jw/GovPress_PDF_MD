#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from multiprocessing import Process, Queue
from pathlib import Path
from statistics import fmean


BENCH_SRC = Path("/home/wavel/opendataloader-bench/src")
if str(BENCH_SRC) not in sys.path:
    sys.path.insert(0, str(BENCH_SRC))

from evaluator_heading_level import evaluate_heading_level
from evaluator_reading_order import evaluate_reading_order
from evaluator_table import evaluate_table


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def safe_mean(values: list[float]) -> float | None:
    return fmean(values) if values else None


def _evaluate_table_worker(gt_markdown: str, pred_markdown: str, queue: Queue) -> None:
    try:
        queue.put(("ok", evaluate_table(gt_markdown, pred_markdown)))
    except Exception as exc:  # pragma: no cover - defensive guard
        queue.put(("err", repr(exc)))


def evaluate_table_with_timeout(
    gt_markdown: str, pred_markdown: str, timeout_seconds: float
) -> tuple[float | None, float | None, bool]:
    queue: Queue = Queue()
    proc = Process(
        target=_evaluate_table_worker,
        args=(gt_markdown, pred_markdown, queue),
        daemon=True,
    )
    proc.start()
    proc.join(timeout_seconds)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        return None, None, True
    if queue.empty():
        return None, None, False
    status, payload = queue.get()
    if status == "err":
        raise RuntimeError(f"table evaluation failed: {payload}")
    return payload[0], payload[1], False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ground-truth-dir", required=True)
    parser.add_argument("--prediction-dir", required=True)
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--table-timeout-seconds", type=float, default=10.0)
    args = parser.parse_args()

    gt_dir = Path(args.ground_truth_dir)
    prediction_dir = Path(args.prediction_dir)
    summary = json.loads(Path(args.summary).read_text())

    documents = []
    overall_values = []
    nid_values = []
    nid_s_values = []
    teds_values = []
    teds_s_values = []
    mhs_values = []
    mhs_s_values = []
    missing_predictions = 0
    table_timeouts = 0

    for gt_path in sorted(gt_dir.glob("*.md")):
        doc_id = gt_path.stem
        pred_path = prediction_dir / f"{doc_id}.md"
        gt_markdown = read_text(gt_path)
        pred_markdown = read_text(pred_path)
        prediction_available = pred_path.exists()
        if not prediction_available:
            missing_predictions += 1

        nid, nid_s = evaluate_reading_order(gt_markdown, pred_markdown)
        teds, teds_s, table_timed_out = evaluate_table_with_timeout(
            gt_markdown,
            pred_markdown,
            args.table_timeout_seconds,
        )
        mhs, mhs_s = evaluate_heading_level(gt_markdown, pred_markdown)
        vals = [v for v in [nid, teds, mhs] if v is not None]
        overall = fmean(vals) if vals else None
        if table_timed_out:
            table_timeouts += 1

        if overall is not None:
            overall_values.append(overall)
        if nid is not None:
            nid_values.append(nid)
        if nid_s is not None:
            nid_s_values.append(nid_s)
        if teds is not None:
            teds_values.append(teds)
        if teds_s is not None:
            teds_s_values.append(teds_s)
        if mhs is not None:
            mhs_values.append(mhs)
        if mhs_s is not None:
            mhs_s_values.append(mhs_s)

        documents.append(
            {
                "document_id": doc_id,
                "scores": {
                    "overall": overall,
                    "nid": nid,
                    "nid_s": nid_s,
                    "teds": teds,
                    "teds_s": teds_s,
                    "mhs": mhs,
                    "mhs_s": mhs_s,
                },
                "prediction_available": prediction_available,
                "table_timed_out": table_timed_out,
            }
        )

    payload = {
        "summary": summary,
        "metrics": {
            "score": {
                "overall_mean": safe_mean(overall_values),
                "nid_mean": safe_mean(nid_values),
                "nid_s_mean": safe_mean(nid_s_values),
                "teds_mean": safe_mean(teds_values),
                "teds_s_mean": safe_mean(teds_s_values),
                "mhs_mean": safe_mean(mhs_values),
                "mhs_s_mean": safe_mean(mhs_s_values),
            },
            "nid_count": len(nid_values),
            "teds_count": len(teds_values),
            "mhs_count": len(mhs_values),
            "missing_predictions": missing_predictions,
            "table_timeouts": table_timeouts,
        },
        "documents": documents,
    }
    Path(args.output).write_text(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
