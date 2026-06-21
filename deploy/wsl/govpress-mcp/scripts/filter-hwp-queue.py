#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Filter GovPress HWP queue JSONL by approve_date.")
    parser.add_argument("--input", default="data/fetch-log/hwp-queue.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    seen = set()
    rows = []

    if src.exists():
        with src.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                approve_date = str(item.get("approve_date") or "")
                if approve_date < args.start_date or approve_date > args.end_date:
                    continue
                key = (item.get("news_item_id"), item.get("hwp_path"))
                if key in seen:
                    continue
                seen.add(key)
                rows.append(item)

    dst.parent.mkdir(parents=True, exist_ok=True)
    with dst.open("w", encoding="utf-8") as f:
        for item in rows:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"wrote_hwp_queue={dst} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
