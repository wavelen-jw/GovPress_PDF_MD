#!/usr/bin/env python3
from __future__ import annotations

import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import socket
from urllib.parse import urlsplit


LISTEN_HOST = os.environ.get("GOVPRESS_HOST_PROXY_LISTEN_HOST", "127.0.0.1")
LISTEN_PORT = int(os.environ.get("GOVPRESS_HOST_PROXY_LISTEN_PORT", "8080"))
UPSTREAM_BASE = os.environ.get("GOVPRESS_HOST_PROXY_UPSTREAM", "http://127.0.0.1:8013")
UPSTREAM = urlsplit(UPSTREAM_BASE)
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


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key, X-Admin-Key, X-Edit-Token")

    def do_GET(self) -> None:
        if self.path == "/health":
            self._health(include_body=True)
            return
        self._proxy()

    def do_HEAD(self) -> None:
        if self.path == "/health":
            self._health(include_body=False)
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
            self.send_response(204, "No Content")
            self._send_cors_headers()
            self.end_headers()
            return
        self._proxy()

    def _health(self, *, include_body: bool) -> None:
        conn_cls = http.client.HTTPSConnection if UPSTREAM.scheme == "https" else http.client.HTTPConnection
        conn = conn_cls(UPSTREAM.hostname, UPSTREAM.port, timeout=5)
        payload = b""
        status = 200
        reason = "OK"
        content_type = "application/json"
        try:
            conn.request("GET" if include_body else "HEAD", "/health", headers={"Host": UPSTREAM.netloc})
            upstream_response = conn.getresponse()
            payload = upstream_response.read() if include_body else b""
            status = upstream_response.status
            reason = upstream_response.reason
            content_type = upstream_response.getheader("Content-Type", "application/json")
        except (OSError, socket.timeout) as exc:
            self.send_error(502, f"upstream unavailable: {exc}")
            return
        finally:
            conn.close()

        self.send_response(status, reason)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def _proxy(self) -> None:
        body = b""
        length = self.headers.get("Content-Length")
        if length:
            body = self.rfile.read(int(length))

        upstream_headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS and key.lower() != "host"
        }
        upstream_headers["Host"] = UPSTREAM.netloc
        upstream_headers["X-Forwarded-For"] = self.client_address[0]
        upstream_headers["X-Forwarded-Proto"] = "http"

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
            if lower in HOP_BY_HOP_HEADERS or lower in CORS_RESPONSE_HEADERS:
                continue
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        if self.command != "HEAD" and payload:
            self.wfile.write(payload)

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
