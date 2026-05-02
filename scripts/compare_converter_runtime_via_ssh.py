#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
from dataclasses import dataclass


REMOTE_CODE = r"""
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request


def request_json(url, headers, data=None):
    retryable_statuses = {502, 503, 504}
    last_error = None
    for attempt in range(1, 7):
        request = urllib.request.Request(url, headers=headers, data=data)
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:1000]
            last_error = "HTTP %s for %s: %s" % (exc.code, url, body)
            if exc.code not in retryable_statuses or attempt == 6:
                raise RuntimeError(last_error) from exc
        except urllib.error.URLError as exc:
            last_error = "URL error for %s: %s" % (url, exc)
            if attempt == 6:
                raise RuntimeError(last_error) from exc
        print("request_retry attempt=%s url=%s error=%s" % (attempt, url, last_error), file=sys.stderr)
        time.sleep(5)
    raise RuntimeError(last_error or "request failed for %s" % url)


def runtime_probe(base_url, admin_key):
    try:
        return request_json(
            base_url + "/v1/admin/runtime/converter",
            headers={"X-Admin-Key": admin_key},
        )
    except Exception as exc:
        return {
            "available": False,
            "probe_error": str(exc)[:500],
        }


def main():
    config = json.loads(sys.stdin.read())
    base_url = config["base_url"].rstrip("/")
    api_key = config["api_key"]
    admin_key = config["admin_key"]
    news_item_id = config["news_item_id"]
    date = config.get("date")

    runtime = runtime_probe(base_url, admin_key)
    payload = {"news_item_id": news_item_id}
    if date:
        payload["date"] = date

    created = request_json(
        base_url + "/v1/policy-briefings/import",
        headers={"X-API-Key": api_key, "Content-Type": "application/json"},
        data=json.dumps(payload).encode("utf-8"),
    )
    job_id = str(created["job_id"])
    edit_token = str(created["edit_token"])
    result = request_json(
        base_url + "/v1/jobs/%s/result" % job_id,
        headers={"X-API-Key": api_key, "X-Edit-Token": edit_token},
    )
    text = str(result["table_variants"]["text"]["markdown"])
    html = str(result["table_variants"]["html"]["markdown"])
    print(json.dumps({
        "runtime": runtime,
        "job_id": job_id,
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "title": result.get("meta", {}).get("title"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
"""


@dataclass(frozen=True)
class Server:
    name: str
    ssh_target: str
    base_url: str


def _parse_server(raw: str) -> Server:
    parts = raw.split("=", 2)
    if len(parts) != 3:
        raise SystemExit(f"invalid --server value: {raw}")
    name, ssh_target, base_url = parts
    if not name or not ssh_target or not base_url:
        raise SystemExit(f"invalid --server value: {raw}")
    return Server(name=name, ssh_target=ssh_target, base_url=base_url.rstrip("/"))


def _run_remote(server: Server, *, api_key: str, admin_key: str, news_item_id: str, date: str | None) -> dict[str, object]:
    config = {
        "base_url": server.base_url,
        "api_key": api_key,
        "admin_key": admin_key,
        "news_item_id": news_item_id,
        "date": date,
    }
    proc = subprocess.run(
        ["ssh", server.ssh_target, "python3 -c " + shlex.quote(REMOTE_CODE)],
        input=json.dumps(config, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=180,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.strip()
        stdout = proc.stdout.strip()
        detail = stderr or stdout or f"exit {proc.returncode}"
        raise SystemExit(f"{server.name} {server.ssh_target} failed: {detail[:1000]}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{server.name} returned invalid JSON: {exc}: {proc.stdout[:1000]}") from exc
    payload["name"] = server.name
    payload["ssh_target"] = server.ssh_target
    payload["base_url"] = server.base_url
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare converter runtime and output hashes through server-local APIs over SSH")
    parser.add_argument("--policy-briefing-id", required=True, help="Policy briefing news_item_id to import on each server")
    parser.add_argument("--policy-briefing-date", help="Policy briefing date in YYYY-MM-DD format")
    parser.add_argument("--api-key", default=os.environ.get("API_KEY"), help="GovPress API key")
    parser.add_argument("--admin-key", default=os.environ.get("ADMIN_KEY"), help="GovPress admin key")
    parser.add_argument(
        "--require-equal-hashes",
        action="store_true",
        help="Exit non-zero when text/html hashes differ across servers",
    )
    parser.add_argument(
        "--server",
        action="append",
        required=True,
        help="Server definition in the form name=ssh-target=http://127.0.0.1:port",
    )
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("--api-key or API_KEY is required")
    if not args.admin_key:
        raise SystemExit("--admin-key or ADMIN_KEY is required")

    servers = [_parse_server(raw) for raw in args.server]
    results = [
        _run_remote(
            server,
            api_key=str(args.api_key),
            admin_key=str(args.admin_key),
            news_item_id=str(args.policy_briefing_id),
            date=args.policy_briefing_date,
        )
        for server in servers
    ]

    if args.require_equal_hashes:
        text_hashes = {str(row["text_sha256"]) for row in results}
        html_hashes = {str(row["html_sha256"]) for row in results}
        if len(text_hashes) != 1 or len(html_hashes) != 1:
            print(json.dumps({"sample": f"policy-briefing:{args.policy_briefing_id}", "results": results}, ensure_ascii=False, indent=2))
            raise SystemExit("converter output hash mismatch across servers")

    print(json.dumps({"sample": f"policy-briefing:{args.policy_briefing_id}", "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
