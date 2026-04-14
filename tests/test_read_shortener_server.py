from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from http.client import HTTPConnection
from pathlib import Path

from scripts.read_shortener_server import RedirectHTTPServer, RedirectStore, load_redirect_config


class ReadShortenerServerTests(unittest.TestCase):
    def test_load_redirect_config_validates_default_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "redirect.json"
            path.write_text(json.dumps({"default_target": "https://example.com/doc"}), encoding="utf-8")
            config = load_redirect_config(path)
        self.assertEqual(config["default_target"], "https://example.com/doc")

    def test_load_redirect_config_rejects_missing_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "redirect.json"
            path.write_text(json.dumps({}), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_redirect_config(path)

    def test_store_reloads_after_file_change(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "redirect.json"
            path.write_text(json.dumps({"default_target": "https://example.com/a"}), encoding="utf-8")
            store = RedirectStore(path)
            self.assertEqual(store.target(), "https://example.com/a")
            time.sleep(0.01)
            path.write_text(json.dumps({"default_target": "https://example.com/b"}), encoding="utf-8")
            self.assertEqual(store.target(), "https://example.com/b")

    def test_http_server_redirects_root_and_reports_health(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "redirect.json"
            path.write_text(json.dumps({"default_target": "https://example.com/doc"}), encoding="utf-8")
            store = RedirectStore(path)
            server = RedirectHTTPServer(("127.0.0.1", 0), store)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/")
                response = conn.getresponse()
                self.assertEqual(response.status, 302)
                self.assertEqual(response.getheader("Location"), "https://example.com/doc")
                response.read()
                conn.close()

                conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/health")
                response = conn.getresponse()
                body = response.read().decode("utf-8")
                self.assertEqual(response.status, 200)
                self.assertIn('"status": "ok"', body)
                conn.close()

                conn = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn.request("GET", "/nope")
                response = conn.getresponse()
                self.assertEqual(response.status, 404)
                response.read()
                conn.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
