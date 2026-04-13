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


class ProxyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        self._proxy()

    def do_POST(self) -> None:
        self._proxy()

    def do_PATCH(self) -> None:
        self._proxy()

    def do_DELETE(self) -> None:
        self._proxy()

    def do_OPTIONS(self) -> None:
        self._proxy()

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
            if key.lower() in HOP_BY_HOP_HEADERS:
                continue
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if payload:
            self.wfile.write(payload)

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - - [{self.log_date_time_string()}] {fmt % args}", flush=True)


def main() -> None:
    server = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), ProxyHandler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
