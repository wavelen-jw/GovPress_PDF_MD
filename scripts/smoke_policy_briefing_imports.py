from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


USER_AGENT = "GovPress-Policy-Briefing-Smoke/1.0"


class ApiRequestError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


def parse_server(value: str) -> tuple[str, str]:
    name, separator, base_url = value.partition("=")
    if not separator or not name.strip() or not base_url.strip().startswith(("http://", "https://")):
        raise argparse.ArgumentTypeError("server must be NAME=http(s)://host")
    return name.strip(), base_url.rstrip("/")


def request_json(
    base_url: str,
    path: str,
    api_key: str,
    *,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    edit_token: str | None = None,
    timeout: float = 90,
    attempts: int = 3,
) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": USER_AGENT, "X-API-Key": api_key}
    data = None
    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")
    if edit_token:
        headers["X-Edit-Token"] = edit_token
    for attempt in range(1, attempts + 1):
        request = Request(f"{base_url}{path}", data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(raw).get("detail", raw)
            except json.JSONDecodeError:
                detail = raw
            error = ApiRequestError(exc.code, str(detail).strip() or f"HTTP {exc.code}")
            if attempt == attempts or not (exc.code >= 500 or exc.code in {408, 429}):
                raise error from exc
        except (TimeoutError, URLError) as exc:
            if attempt == attempts:
                raise
        time.sleep(attempt)
    raise RuntimeError("request retry loop ended unexpectedly")


def wait_for_result(
    base_url: str,
    api_key: str,
    job_id: str,
    edit_token: str,
    *,
    poll_timeout: float,
    request_timeout: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    deadline = time.monotonic() + poll_timeout
    while True:
        job = request_json(
            base_url,
            f"/v1/jobs/{job_id}",
            api_key,
            edit_token=edit_token,
            timeout=request_timeout,
        )
        status = job.get("status")
        if status == "completed":
            result = request_json(
                base_url,
                f"/v1/jobs/{job_id}/result",
                api_key,
                edit_token=edit_token,
                timeout=request_timeout,
            )
            markdown = result.get("markdown")
            if not isinstance(markdown, str) or not markdown.strip():
                raise RuntimeError("completed job returned empty markdown")
            return job, result
        if status == "failed":
            raise RuntimeError(f"conversion failed: {job.get('error_code') or 'unknown'}: {job.get('error_message') or ''}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"job did not complete within {poll_timeout:g}s")
        time.sleep(1)


def smoke_item(
    server: tuple[str, str],
    item: dict[str, Any],
    target_date: str,
    api_key: str,
    *,
    poll_timeout: float,
    request_timeout: float,
) -> dict[str, Any]:
    name, base_url = server
    news_item_id = str(item["news_item_id"])
    started = time.monotonic()
    try:
        imported = request_json(
            base_url,
            "/v1/policy-briefings/import",
            api_key,
            method="POST",
            body={
                "news_item_id": news_item_id,
                "date": target_date,
                "converter_engine": "govpress-hwpx-md",
            },
            timeout=request_timeout,
        )
        job_id = str(imported["job_id"])
        edit_token = str(imported["edit_token"])
        _, result = wait_for_result(
            base_url,
            api_key,
            job_id,
            edit_token,
            poll_timeout=poll_timeout,
            request_timeout=request_timeout,
        )
        markdown = result["markdown"]
        return {
            "server": name,
            "news_item_id": news_item_id,
            "status": "passed",
            "markdown_chars": len(markdown),
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }
    except Exception as exc:
        return {
            "server": name,
            "news_item_id": news_item_id,
            "status": "failed",
            "error": f"{exc.__class__.__name__}: {exc}",
            "elapsed_seconds": round(time.monotonic() - started, 3),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import and verify every primary HWPX for a policy-briefing date.")
    parser.add_argument("--server", action="append", type=parse_server, required=True, help="NAME=http(s)://host")
    parser.add_argument("--date", dest="target_date", help="YYYY-MM-DD; defaults to the current Asia/Seoul date")
    parser.add_argument("--api-key", default=os.environ.get("GOVPRESS_API_KEY", ""))
    parser.add_argument("--jobs", type=int, default=2, choices=range(1, 5))
    parser.add_argument("--request-timeout-seconds", type=float, default=90)
    parser.add_argument("--poll-timeout-seconds", type=float, default=300)
    parser.add_argument("--require-equal-inventory", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.api_key.strip():
        raise SystemExit("GOVPRESS_API_KEY or --api-key is required")
    target_date = args.target_date or datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()

    inventories: dict[str, list[dict[str, Any]]] = {}
    catalog_rows: list[dict[str, Any]] = []
    for name, base_url in args.server:
        query = urlencode({"date": target_date})
        catalog = request_json(
            base_url,
            f"/v1/policy-briefings/today?{query}",
            args.api_key,
            timeout=args.request_timeout_seconds,
        )
        items = [item for item in catalog.get("items", []) if item.get("has_hwpx")]
        inventories[name] = items
        catalog_rows.append(
            {
                "server": name,
                "total_items": len(catalog.get("items", [])),
                "hwpx_items": len(items),
                "served_stale": bool(catalog.get("served_stale", False)),
            }
        )

    inventory_sets = {name: {str(item["news_item_id"]) for item in items} for name, items in inventories.items()}
    inventory_equal = len({frozenset(values) for values in inventory_sets.values()}) <= 1
    results: list[dict[str, Any]] = []
    for server in args.server:
        name, _ = server
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = [
                executor.submit(
                    smoke_item,
                    server,
                    item,
                    target_date,
                    args.api_key,
                    poll_timeout=args.poll_timeout_seconds,
                    request_timeout=args.request_timeout_seconds,
                )
                for item in inventories[name]
            ]
            for future in as_completed(futures):
                row = future.result()
                results.append(row)
                print(
                    f"[{row['server']}] {row['news_item_id']} {row['status']} ({row['elapsed_seconds']}s)",
                    file=sys.stderr,
                    flush=True,
                )

    failures = [row for row in results if row["status"] != "passed"]
    payload = {
        "date": target_date,
        "catalogs": catalog_rows,
        "inventory_equal": inventory_equal,
        "inventory_differences": {
            name: sorted(set().union(*inventory_sets.values()) - values)
            for name, values in inventory_sets.items()
        },
        "summary": {"checked": len(results), "passed": len(results) - len(failures), "failed": len(failures)},
        "failures": failures,
        "results": sorted(results, key=lambda row: (row["server"], row["news_item_id"])),
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if failures or (args.require_equal_inventory and not inventory_equal):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
