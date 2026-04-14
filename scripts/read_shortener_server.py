from __future__ import annotations

import argparse
import json
import logging
import threading
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


LOGGER = logging.getLogger("read_shortener")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a single file-backed redirect target.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--config-file", required=True)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def _validate_target(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"default_target must be an absolute http(s) URL: {url}")
    return url


def load_redirect_config(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"redirect config not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("redirect config must be a JSON object")

    raw_target = data.get("default_target", "")
    if not isinstance(raw_target, str) or not raw_target.strip():
        raise ValueError("redirect config requires non-empty default_target")
    return {"default_target": _validate_target(raw_target.strip())}


@dataclass
class RedirectStore:
    path: Path

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._mtime_ns = -1
        self._config: dict[str, str] = {}
        self.reload_if_needed(force=True)

    def reload_if_needed(self, *, force: bool = False) -> None:
        stat = self.path.stat()
        if not force and stat.st_mtime_ns == self._mtime_ns:
            return
        config = load_redirect_config(self.path)
        with self._lock:
            self._config = config
            self._mtime_ns = stat.st_mtime_ns
        LOGGER.info("loaded redirect target from %s", self.path)

    def target(self) -> str:
        self.reload_if_needed()
        with self._lock:
            return self._config["default_target"]


class RedirectHandler(BaseHTTPRequestHandler):
    server_version = "GovPressReadShortener/1.0"

    def do_GET(self) -> None:
        self._handle_request(include_body=True)

    def do_HEAD(self) -> None:
        self._handle_request(include_body=False)

    def log_message(self, format: str, *args: Any) -> None:
        LOGGER.info("%s - %s", self.address_string(), format % args)

    @property
    def redirect_store(self) -> RedirectStore:
        return self.server.redirect_store  # type: ignore[attr-defined]

    def _handle_request(self, *, include_body: bool) -> None:
        path = self.path.split("?", 1)[0]
        if path == "/health":
            return self._handle_health(include_body=include_body)
        if path not in {"", "/"}:
            return self._not_found(include_body=include_body)

        target = self.redirect_store.target()
        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", target)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if include_body:
            self.wfile.write(f"Redirecting to {target}\n".encode("utf-8"))

    def _handle_health(self, *, include_body: bool) -> None:
        payload = json.dumps({"status": "ok", "default_target": self.redirect_store.target()}).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if include_body:
            self.wfile.write(payload)

    def _not_found(self, *, include_body: bool) -> None:
        payload = b"Not found\n"
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if include_body:
            self.wfile.write(payload)


class RedirectHTTPServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], redirect_store: RedirectStore):
        super().__init__(server_address, RedirectHandler)
        self.redirect_store = redirect_store


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(message)s")
    config_file = Path(args.config_file)
    store = RedirectStore(config_file)
    if args.validate_only:
        print(json.dumps({"status": "ok", "default_target": store.target(), "config_file": str(config_file)}))
        return 0

    server = RedirectHTTPServer((args.host, args.port), store)
    LOGGER.info("starting read shortener on http://%s:%s using %s", args.host, args.port, config_file)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("shutting down")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
