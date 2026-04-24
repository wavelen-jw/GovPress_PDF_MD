from __future__ import annotations

import importlib
import os
import unittest


class HostProxyTests(unittest.TestCase):
    def test_proxy_filters_upstream_content_length(self) -> None:
        previous_upstream = os.environ.get("GOVPRESS_HOST_PROXY_UPSTREAM")
        os.environ["GOVPRESS_HOST_PROXY_UPSTREAM"] = "http://127.0.0.1:8013"
        try:
            import deploy.wsl.bin.host_proxy as host_proxy

            host_proxy = importlib.reload(host_proxy)
            self.assertIn("content-length", host_proxy.RESPONSE_SKIP_HEADERS)
            self.assertNotIn("content-length", host_proxy.CORS_RESPONSE_HEADERS)
            self.assertNotIn("content-length", host_proxy.HOP_BY_HOP_HEADERS)
        finally:
            if previous_upstream is None:
                os.environ.pop("GOVPRESS_HOST_PROXY_UPSTREAM", None)
            else:
                os.environ["GOVPRESS_HOST_PROXY_UPSTREAM"] = previous_upstream


if __name__ == "__main__":
    unittest.main()
