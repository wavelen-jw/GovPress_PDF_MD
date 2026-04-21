#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def _request_json(url: str, *, headers: dict[str, str], data: bytes | None = None) -> dict[str, object]:
    request = urllib.request.Request(url, headers=headers, data=data)
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.load(response)


def _runtime_probe(base_url: str, *, admin_key: str) -> dict[str, object]:
    try:
        return _request_json(
            f"{base_url}/v1/admin/runtime/converter",
            headers={"X-Admin-Key": admin_key},
        )
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {
            "available": False,
            "probe_error": f"HTTP {exc.code}",
            "probe_body": detail[:500],
        }


def _multipart_body(sample_path: Path, *, boundary: str) -> tuple[bytes, str]:
    content = sample_path.read_bytes()
    lines: list[bytes] = [
        f"--{boundary}\r\n".encode(),
        (
            'Content-Disposition: form-data; name="file"; filename="%s"\r\n'
            % sample_path.name
        ).encode(),
        b"Content-Type: application/octet-stream\r\n\r\n",
        content,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    body = b"".join(lines)
    return body, f"multipart/form-data; boundary={boundary}"


def _upload_and_fetch_result(base_url: str, *, api_key: str, sample_path: Path) -> dict[str, object]:
    boundary = f"govpress-boundary-{int(time.time() * 1000)}"
    body, content_type = _multipart_body(sample_path, boundary=boundary)
    created = _request_json(
        f"{base_url}/v1/jobs",
        headers={
            "X-API-Key": api_key,
            "Content-Type": content_type,
        },
        data=body,
    )
    job_id = str(created["job_id"])
    edit_token = str(created["edit_token"])
    poll_headers = {"X-API-Key": api_key, "X-Edit-Token": edit_token}
    for _ in range(60):
        status_payload = _request_json(f"{base_url}/v1/jobs/{job_id}", headers=poll_headers)
        status = str(status_payload.get("status", "unknown"))
        if status == "completed":
            result_payload = _request_json(f"{base_url}/v1/jobs/{job_id}/result", headers=poll_headers)
            return {
                "job_id": job_id,
                "edit_token": edit_token,
                "status": status,
                "result": result_payload,
            }
        if status == "failed":
            raise SystemExit(f"{base_url} job failed: {json.dumps(status_payload, ensure_ascii=False)}")
        time.sleep(2)
    raise SystemExit(f"{base_url} job did not complete within timeout")


def _hash_text(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare converter runtime and conversion hashes across servers")
    parser.add_argument("--sample", required=True, help="Path to sample HWPX/PDF file")
    parser.add_argument("--api-key", required=True, help="GovPress API key")
    parser.add_argument("--admin-key", required=True, help="GovPress admin key")
    parser.add_argument(
        "--require-equal-hashes",
        action="store_true",
        help="Exit non-zero when text/html hashes differ across servers",
    )
    parser.add_argument(
        "--server",
        action="append",
        required=True,
        help="Server definition in the form name=https://host",
    )
    args = parser.parse_args()

    sample_path = Path(args.sample).resolve()
    if not sample_path.is_file():
        raise SystemExit(f"sample file not found: {sample_path}")

    results: list[dict[str, object]] = []
    for item in args.server:
        if "=" not in item:
            raise SystemExit(f"invalid --server value: {item}")
        name, base_url = item.split("=", 1)
        runtime = _runtime_probe(base_url, admin_key=args.admin_key)
        upload = _upload_and_fetch_result(base_url, api_key=args.api_key, sample_path=sample_path)
        result_payload = upload["result"]
        assert isinstance(result_payload, dict)
        text_markdown = str(result_payload["table_variants"]["text"]["markdown"])
        html_markdown = str(result_payload["table_variants"]["html"]["markdown"])
        results.append(
            {
                "name": name,
                "base_url": base_url,
                "runtime": runtime,
                "job_id": upload["job_id"],
                "text_sha256": _hash_text(text_markdown),
                "html_sha256": _hash_text(html_markdown),
                "title": result_payload.get("meta", {}).get("title"),
            }
        )

    if args.require_equal_hashes:
        text_hashes = {str(row["text_sha256"]) for row in results}
        html_hashes = {str(row["html_sha256"]) for row in results}
        if len(text_hashes) != 1 or len(html_hashes) != 1:
            raise SystemExit("converter output hash mismatch across servers")

    print(json.dumps({"sample": str(sample_path), "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
