#!/usr/bin/env python3
from __future__ import annotations

import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
import os
from pathlib import Path
import re
import socket
from datetime import UTC, datetime, timedelta
from urllib.parse import unquote, urlsplit


LISTEN_HOST = os.environ.get("GOVPRESS_HOST_PROXY_LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("GOVPRESS_HOST_PROXY_LISTEN_PORT", "8080"))
UPSTREAM_BASE = os.environ.get("GOVPRESS_HOST_PROXY_UPSTREAM", "http://127.0.0.1:8013")
UPSTREAM = urlsplit(UPSTREAM_BASE)
HEALTHCHECK_API_KEY = (
    os.environ.get("GOVPRESS_HOST_PROXY_HEALTH_API_KEY", "").strip()
    or os.environ.get("GOVPRESS_API_KEY", "").strip()
)
DEFAULT_CORS_ALLOW_ORIGINS = {
    "https://govpress.cloud",
    "https://www.govpress.cloud",
    "https://wavelen-jw.github.io",
}
CORS_ALLOW_ORIGINS = {
    item.strip()
    for item in os.environ.get(
        "GOVPRESS_CORS_ALLOW_ORIGINS",
        ",".join(sorted(DEFAULT_CORS_ALLOW_ORIGINS)),
    ).split(",")
    if item.strip()
}
DEFAULT_CORS_ALLOW_ORIGIN_REGEX = r"^https://(?:[a-z0-9-]+\.)?readhim-web\.pages\.dev$"
_cors_allow_origin_regex = os.environ.get(
    "GOVPRESS_CORS_ALLOW_ORIGIN_REGEX",
    DEFAULT_CORS_ALLOW_ORIGIN_REGEX,
).strip()
CORS_ALLOW_ORIGIN_REGEX = (
    re.compile(_cors_allow_origin_regex) if _cors_allow_origin_regex else None
)
HOP_BY_HOP_HEADERS = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailers",
    "transfer-encoding",
    "upgrade",
}

CORS_RESPONSE_HEADERS = {
    "access-control-allow-origin",
    "access-control-allow-methods",
    "access-control-allow-headers",
    "access-control-allow-credentials",
    "access-control-expose-headers",
    "access-control-max-age",
}
RESPONSE_SKIP_HEADERS = HOP_BY_HOP_HEADERS | CORS_RESPONSE_HEADERS | {"content-length"}
SEOUL_UTC_OFFSET = timedelta(hours=9)
MAX_REQUEST_BODY_BYTES = int(os.environ.get("GOVPRESS_HOST_PROXY_MAX_BODY_BYTES", str(100 * 1024 * 1024)))
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
UI_ROOT = (REPOSITORY_ROOT / "ui").resolve()
APP_ROOT = (REPOSITORY_ROOT / "mobile" / "dist").resolve()
DIRECTORY_PAGES = frozenset({"benchmark-policy-briefing", "hardest-policy-briefings"})


def contained_file(root: Path, relative_path: str) -> Path | None:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def static_file_for_path(request_target: str) -> Path | None:
    path = unquote(urlsplit(request_target).path)
    if path in {"/", "/landing.html"}:
        return contained_file(UI_ROOT, "landing.html")
    for prefix in ("/app/", "/GovPress_PDF_MD/app/"):
        if path.startswith(prefix):
            return contained_file(APP_ROOT, path[len(prefix):] or "index.html")
    relative = path.lstrip("/")
    direct = contained_file(UI_ROOT, relative)
    if direct is not None:
        return direct
    parts = [part for part in relative.split("/") if part]
    if len(parts) == 1 and parts[0] in DIRECTORY_PAGES:
        return contained_file(UI_ROOT, f"{parts[0]}.html")
    if len(parts) == 2 and parts[0] in DIRECTORY_PAGES:
        return contained_file(UI_ROOT, parts[1])
    return None


class InvalidRequestBody(ValueError):
    pass


def cors_origin_allowed(origin: str) -> bool:
    if origin in CORS_ALLOW_ORIGINS:
        return True
    return bool(CORS_ALLOW_ORIGIN_REGEX and CORS_ALLOW_ORIGIN_REGEX.fullmatch(origin))


def read_chunked_body(stream, *, max_bytes: int = MAX_REQUEST_BODY_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        size_line = stream.readline(8192)
        if not size_line.endswith(b"\r\n"):
            raise InvalidRequestBody("malformed chunk size")
        try:
            size = int(size_line[:-2].split(b";", 1)[0], 16)
        except ValueError as exc:
            raise InvalidRequestBody("invalid chunk size") from exc
        if size == 0:
            while True:
                trailer = stream.readline(8192)
                if trailer == b"\r\n":
                    return b"".join(chunks)
                if not trailer or not trailer.endswith(b"\r\n"):
                    raise InvalidRequestBody("malformed chunk trailer")
        total += size
        if total > max_bytes:
            raise InvalidRequestBody("request body exceeds proxy limit")
        chunk = stream.read(size)
        if len(chunk) != size or stream.read(2) != b"\r\n":
            raise InvalidRequestBody("incomplete chunk")
        chunks.append(chunk)


def seoul_today_iso() -> str:
    return (datetime.now(UTC) + SEOUL_UTC_OFFSET).date().isoformat()


def request_upstream(path: str, headers: dict[str, str] | None = None, *, timeout: int = 5) -> tuple[int, str, str, bytes]:
    conn_cls = http.client.HTTPSConnection if UPSTREAM.scheme == "https" else http.client.HTTPConnection
    conn = conn_cls(UPSTREAM.hostname, UPSTREAM.port, timeout=timeout)
    request_headers = {"Host": UPSTREAM.netloc}
    if headers:
        request_headers.update(headers)
    try:
        conn.request("GET", path, headers=request_headers)
        upstream_response = conn.getresponse()
        payload = upstream_response.read()
        return (
            upstream_response.status,
            upstream_response.reason,
            upstream_response.getheader("Content-Type", "application/json"),
            payload,
        )
    finally:
        conn.close()


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _allowed_cors_origin(self) -> str | None:
        headers = getattr(self, "headers", {})
        origin = headers.get("Origin", "").strip()
        return origin if origin and cors_origin_allowed(origin) else None

    def _send_cors_headers(self, origin: str | None = None) -> bool:
        origin = origin or self._allowed_cors_origin()
        if origin is None:
            return False
        self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key, X-Admin-Key, X-Edit-Token")
        return True

    def do_GET(self) -> None:
        if self.path == "/health":
            self._health(include_body=True)
            return
        if self._serve_static(include_body=True):
            return
        self._proxy()

    def do_HEAD(self) -> None:
        if self.path == "/health":
            self._health(include_body=False)
            return
        if self._serve_static(include_body=False):
            return
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def do_PATCH(self) -> None:
        self._proxy()

    def do_DELETE(self) -> None:
        self._proxy()

    def do_OPTIONS(self) -> None:
        if self.path == "/health" or self.path.startswith("/v1/"):
            origin = self._allowed_cors_origin()
            if origin is None:
                self.send_response(403, "Forbidden")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(204, "No Content")
            self._send_cors_headers(origin)
            self.end_headers()
            return
        self._proxy()

    def _serve_static(self, *, include_body: bool) -> bool:
        if self.path == "/app":
            self.send_response(308, "Permanent Redirect")
            self.send_header("Location", "/app/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return True
        static_file = static_file_for_path(self.path)
        if static_file is None:
            return False
        try:
            payload = static_file.read_bytes()
        except OSError:
            self.send_error(500, "static file unavailable")
            return True
        content_type, _ = mimetypes.guess_type(static_file.name)
        self.send_response(200, "OK")
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if include_body:
            self.wfile.write(payload)
        return True

    def _health(self, *, include_body: bool) -> None:
        try:
            status, reason, content_type, payload = request_upstream("/health")
            if status == 200 and HEALTHCHECK_API_KEY:
                policy_status, policy_reason, _, policy_payload = request_upstream(
                    f"/v1/policy-briefings/today?date={seoul_today_iso()}",
                    {"X-API-Key": HEALTHCHECK_API_KEY, "Accept": "application/json"},
                )
                if policy_status != 200:
                    status = policy_status
                    reason = policy_reason
                    content_type = "application/json"
                    payload = (
                        b'{"status":"error","reason":"policy_probe_failed",'
                        + f'"upstream_status":{policy_status}'.encode("ascii")
                        + b"}"
                    )
                elif not policy_payload:
                    status = 502
                    reason = "Bad Gateway"
                    content_type = "application/json"
                    payload = b'{"status":"error","reason":"empty_policy_probe"}'
            if not include_body:
                payload = b""
        except (OSError, socket.timeout) as exc:
            self.send_error(502, f"upstream unavailable: {exc}")
            return

        self.send_response(status, reason)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def _proxy(self) -> None:
        try:
            body = self._read_request_body()
        except InvalidRequestBody as exc:
            self.send_error(400, str(exc))
            return

        upstream_headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
        }
        upstream_headers["Host"] = UPSTREAM.netloc
        upstream_headers["X-Forwarded-For"] = self.client_address[0]
        upstream_headers["X-Forwarded-Proto"] = "http"
        if body:
            upstream_headers["Content-Length"] = str(len(body))
        else:
            upstream_headers.pop("Content-Length", None)

        conn_cls = http.client.HTTPSConnection if UPSTREAM.scheme == "https" else http.client.HTTPConnection
        conn = conn_cls(UPSTREAM.hostname, UPSTREAM.port, timeout=30)
        try:
            conn.request(self.command, self.path, body=body, headers=upstream_headers)
            upstream_response = conn.getresponse()
            payload = upstream_response.read()
        except (OSError, socket.timeout) as exc:
            self.send_error(502, f"upstream unavailable: {exc}")
            return
        finally:
            conn.close()

        self.send_response(upstream_response.status, upstream_response.reason)
        for key, value in upstream_response.getheaders():
            lower = key.lower()
            if lower in RESPONSE_SKIP_HEADERS:
                continue
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        if self.command != "HEAD" and payload:
            self.wfile.write(payload)

    def _read_request_body(self) -> bytes:
        length = self.headers.get("Content-Length")
        if length:
            try:
                size = int(length)
            except ValueError as exc:
                raise InvalidRequestBody("invalid content length") from exc
            if size < 0 or size > MAX_REQUEST_BODY_BYTES:
                raise InvalidRequestBody("request body exceeds proxy limit")
            body = self.rfile.read(size)
            if len(body) != size:
                raise InvalidRequestBody("incomplete request body")
            return body
        transfer_encoding = self.headers.get("Transfer-Encoding", "")
        if "chunked" in {part.strip().lower() for part in transfer_encoding.split(",")}:
            return read_chunked_body(self.rfile)
        return b""

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - - [{self.log_date_time_string()}] {fmt % args}", flush=True)


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


def main() -> None:
    server = ReusableThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
