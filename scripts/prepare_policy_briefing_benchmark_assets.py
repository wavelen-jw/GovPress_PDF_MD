#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import requests


CATALOG_DIR = Path("deploy/wsl/data/storage/policy_briefing_catalog")


def load_catalog_items() -> dict[str, dict]:
    merged: dict[str, dict] = {}
    for path in sorted(CATALOG_DIR.glob("*.json")):
        merged.update(json.loads(path.read_text()).get("items", {}))
    return merged


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    manifest = json.loads(Path(args.manifest).read_text())
    items = load_catalog_items()
    output_dir = Path(args.output_dir)
    pdf_dir = output_dir / "pdfs"
    hwpx_dir = output_dir / "hwpxs"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    hwpx_dir.mkdir(parents=True, exist_ok=True)

    for doc in manifest.get("documents", []):
        news_id = doc["news_item_id"]
        item = items[news_id]
        pdf_attachment = None
        hwpx_attachment = None
        for attachment in item.get("attachments", []):
            file_name = attachment.get("file_name", "").lower()
            if file_name.endswith(".pdf") and pdf_attachment is None:
                pdf_attachment = attachment
            if file_name.endswith(".hwpx") and hwpx_attachment is None:
                hwpx_attachment = attachment
        if pdf_attachment is None or hwpx_attachment is None:
            print(f"skip {news_id} missing attachment")
            continue

        for attachment, target_dir, suffix in [
            (pdf_attachment, pdf_dir, "pdf"),
            (hwpx_attachment, hwpx_dir, "hwpx"),
        ]:
            target = target_dir / f"{news_id}.{suffix}"
            if target.exists():
                continue
            response = requests.get(attachment["file_url"], timeout=60)
            response.raise_for_status()
            target.write_bytes(response.content)
            print(f"downloaded {news_id}.{suffix}")


if __name__ == "__main__":
    main()
