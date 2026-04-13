#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from build_policy_briefing_ground_truth_example import CATALOG_DIR, build_document


def parse_approve_date(value: str) -> datetime:
    return datetime.strptime(value, "%m/%d/%Y %H:%M:%S")


def iter_eligible_items() -> list[dict]:
    merged: dict[str, dict] = {}
    for path in sorted(CATALOG_DIR.glob("*.json")):
        items = json.loads(path.read_text()).get("items", {})
        merged.update(items)
    eligible = []
    for news_id, item in merged.items():
        attachments = item.get("attachments", [])
        exts = {att.get("file_name", "").lower().split(".")[-1] for att in attachments if att.get("file_name")}
        if "pdf" in exts and "hwpx" in exts:
            eligible.append(item)
    eligible.sort(key=lambda item: (parse_approve_date(item["approve_date"]), item["news_item_id"]), reverse=True)
    return eligible


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    corpus_dir = output_dir / "ground-truth"
    corpus_dir.mkdir(parents=True, exist_ok=True)

    items = iter_eligible_items()[: args.limit]
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "document_count": len(items),
        "documents": [],
        "failures": [],
    }

    for item in items:
        news_id = item["news_item_id"]
        out_path = corpus_dir / f"{news_id}.md"
        try:
            content = build_document(news_id)
            out_path.write_text(content)
            manifest["documents"].append(
                {
                    "news_item_id": news_id,
                    "title": item["title"],
                    "department": item["department"],
                    "approve_date": item["approve_date"],
                    "path": str(out_path),
                }
            )
            print(f"ok {news_id} {item['title']}")
        except BaseException as exc:  # pragma: no cover - batch logging path
            if isinstance(exc, KeyboardInterrupt):
                raise
            manifest["failures"].append(
                {
                    "news_item_id": news_id,
                    "title": item["title"],
                    "error": repr(exc),
                }
            )
            print(f"fail {news_id} {item['title']} :: {exc}")

    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )


if __name__ == "__main__":
    main()
