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
from urllib.parse import unquote, urlparse


LOGGER = logging.getLogger("read_shortener")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve file-backed shortlink redirects.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    parser.add_argument("--map-file", required=True)
    parser.add_argument("--log-level", default="INFO")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def _validate_slug(slug: str) -> str:
    normalized = slug.strip().strip("/")
    if not normalized:
        raise ValueError("slug must not be empty")
    if "/" in normalized:
        raise ValueError(f"slug must be a single path segment: {slug}")
    for char in normalized:
        if char.isalnum() or char in "-_":
            continue
        raise ValueError(f"slug contains unsupported character: {char!r}")
    return normalized


def _validate_target(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"target must be an absolute http(s) URL: {url}")
    return url


def load_redirect_map(path: Path) -> dict[str, str]:
    if not path.exists():
        raise FileNotFoundError(f"shortlink map not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("shortlink map must be a JSON object")

    redirects: dict[str, str] = {}
    for raw_slug, raw_target in data.items():
        if not isinstance(raw_slug, str) or not isinstance(raw_target, str):
            raise ValueError("shortlink map keys and values must be strings")
        slug = _validate_slug(raw_slug)
        target = _validate_target(raw_target)
        redirects[slug] = target
    return redirects


@dataclass
class RedirectStore:
    path: Path

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._mtime_ns = -1
        self._redirects: dict[str, str] = {}
        self.reload_if_needed(force=True)

    def reload_if_needed(self, *, force: bool = False) -> None:
        stat = self.path.stat()
        if not force and stat.st_mtime_ns == self._mtime_ns:
            return
        redirects = load_redirect_map(self.path)
        with self._lock:
            self._redirects = redirects
            self._mtime_ns = stat.st_mtime_ns
        LOGGER.info("loaded %s shortlinks from %s", len(redirects), self.path)

    def resolve(self, slug: str) -> str | None:
        self.reload_if_needed()
        with self._lock:
            return self._redirects.get(slug)

    def count(self) -> int:
        self.reload_if_needed()
        with self._lock:
            return len(self._redirects)


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
        raw_path = self.path.split("?", 1)[0]
        path = unquote(raw_path)
        if path == "/health":
            return self._handle_health(include_body=include_body)
        slug = path.lstrip("/")
        if not slug:
            return self._not_found(include_body=include_body)
        try:
            slug = _validate_slug(slug)
        except ValueError:
            return self._not_found(include_body=include_body)

        target = self.redirect_store.resolve(slug)
        if not target:
            return self._not_found(include_body=include_body)

        self.send_response(HTTPStatus.FOUND)
        self.send_header("Location", target)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if include_body:
            self.wfile.write(f"Redirecting to {target}\n".encode("utf-8"))

    def _handle_health(self, *, include_body: bool) -> None:
        payload = json.dumps({"status": "ok", "shortlinks": self.redirect_store.count()}).encode("utf-8")
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
    map_file = Path(args.map_file)
    store = RedirectStore(map_file)
    if args.validate_only:
        print(json.dumps({"status": "ok", "shortlinks": store.count(), "map_file": str(map_file)}))
        return 0

    server = RedirectHTTPServer((args.host, args.port), store)
    LOGGER.info("starting read shortener on http://%s:%s using %s", args.host, args.port, map_file)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("shutting down")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
