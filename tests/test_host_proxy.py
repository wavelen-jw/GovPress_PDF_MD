from __future__ import annotations

import importlib
import os
import unittest
from unittest import mock


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

    def test_health_keeps_small_health_body_while_policy_probe_is_enabled(self) -> None:
        previous_api_key = os.environ.get("GOVPRESS_HOST_PROXY_HEALTH_API_KEY")
        os.environ["GOVPRESS_HOST_PROXY_HEALTH_API_KEY"] = "test-key"
        try:
            import deploy.wsl.bin.host_proxy as host_proxy

            host_proxy = importlib.reload(host_proxy)
            with mock.patch.object(host_proxy, "request_upstream") as mocked_request:
                mocked_request.side_effect = [
                    (200, "OK", "application/json", b'{"status":"ok","converter":{"version":"0.1.30"}}'),
                    (200, "OK", "application/json", b'{"items":[{"title":"large policy payload"}]}'),
                ]
                handler = object.__new__(host_proxy.ProxyHandler)
                handler.send_response = mock.Mock()
                handler.send_header = mock.Mock()
                handler.end_headers = mock.Mock()
                handler.wfile = mock.Mock()

                handler._health(include_body=True)

            mocked_request.assert_has_calls(
                [
                    mock.call("/health"),
                    mock.call(
                        mock.ANY,
                        {"X-API-Key": "test-key", "Accept": "application/json"},
                    ),
                ]
            )
            handler.send_response.assert_called_once_with(200, "OK")
            handler.wfile.write.assert_called_once_with(b'{"status":"ok","converter":{"version":"0.1.30"}}')
        finally:
            if previous_api_key is None:
                os.environ.pop("GOVPRESS_HOST_PROXY_HEALTH_API_KEY", None)
            else:
                os.environ["GOVPRESS_HOST_PROXY_HEALTH_API_KEY"] = previous_api_key


if __name__ == "__main__":
    unittest.main()
