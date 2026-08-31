from __future__ import annotations

import importlib
import io
import os
import unittest
from unittest import mock


class HostProxyTests(unittest.TestCase):
    def test_options_allows_pages_preview_origin(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "GOVPRESS_CORS_ALLOW_ORIGINS": "https://govpress.cloud",
                "GOVPRESS_CORS_ALLOW_ORIGIN_REGEX": (
                    r"^https://(?:[a-z0-9-]+\.)?readhim-web\.pages\.dev$"
                ),
            },
        ):
            import deploy.wsl.bin.host_proxy as host_proxy

            host_proxy = importlib.reload(host_proxy)
            handler = object.__new__(host_proxy.ProxyHandler)
            handler.path = "/v1/jobs"
            handler.headers = {
                "Origin": "https://preview-04d7ae780de1.readhim-web.pages.dev",
            }
            handler.send_response = mock.Mock()
            handler.send_header = mock.Mock()
            handler.end_headers = mock.Mock()

            handler.do_OPTIONS()

        handler.send_response.assert_called_once_with(204, "No Content")
        self.assertIn(
            mock.call(
                "Access-Control-Allow-Origin",
                "https://preview-04d7ae780de1.readhim-web.pages.dev",
            ),
            handler.send_header.call_args_list,
        )
        self.assertIn(mock.call("Vary", "Origin"), handler.send_header.call_args_list)

    def test_options_rejects_lookalike_pages_origin(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "GOVPRESS_CORS_ALLOW_ORIGINS": "https://govpress.cloud",
                "GOVPRESS_CORS_ALLOW_ORIGIN_REGEX": (
                    r"^https://(?:[a-z0-9-]+\.)?readhim-web\.pages\.dev$"
                ),
            },
        ):
            import deploy.wsl.bin.host_proxy as host_proxy

            host_proxy = importlib.reload(host_proxy)
            handler = object.__new__(host_proxy.ProxyHandler)
            handler.path = "/v1/jobs"
            handler.headers = {
                "Origin": "https://preview.readhim-web.pages.dev.example.com",
            }
            handler.send_response = mock.Mock()
            handler.send_header = mock.Mock()
            handler.end_headers = mock.Mock()

            handler.do_OPTIONS()

        handler.send_response.assert_called_once_with(403, "Forbidden")
        self.assertNotIn(
            "Access-Control-Allow-Origin",
            [call.args[0] for call in handler.send_header.call_args_list],
        )

    def test_static_routes_resolve_only_public_service_files(self) -> None:
        import deploy.wsl.bin.host_proxy as host_proxy

        host_proxy = importlib.reload(host_proxy)
        self.assertEqual(
            host_proxy.static_file_for_path("/").name,
            "landing.html",
        )
        self.assertEqual(
            host_proxy.static_file_for_path("/app/").name,
            "index.html",
        )
        self.assertEqual(
            host_proxy.static_file_for_path(
                "/GovPress_PDF_MD/app/_expo/static/js/web/AppEntry-45b8351326937a39cc38d9987793d220.js"
            ).name,
            "AppEntry-45b8351326937a39cc38d9987793d220.js",
        )
        self.assertIsNone(
            host_proxy.static_file_for_path("/app/%2e%2e/ui/landing.html")
        )
    def test_proxy_decodes_chunked_post_body_from_edge(self) -> None:
        import deploy.wsl.bin.host_proxy as host_proxy

        host_proxy = importlib.reload(host_proxy)
        handler = object.__new__(host_proxy.ProxyHandler)
        handler.command = "POST"
        handler.path = "/v1/policy-briefings/import"
        handler.headers = {
            "Content-Type": "application/json",
            "Transfer-Encoding": "chunked",
            "X-API-Key": "test-key",
            "Host": "api4.example",
        }
        first = b'{"news_item_id":"156771197",'
        second = b'"date":"2026-07-16"}'
        payload = first + second
        handler.rfile = io.BytesIO(
            f"{len(first):X}\r\n".encode() + first + b"\r\n"
            + f"{len(second):X};edge=test\r\n".encode() + second + b"\r\n0\r\n\r\n"
        )
        handler.wfile = mock.Mock()
        handler.client_address = ("203.0.113.10", 12345)
        handler.send_response = mock.Mock()
        handler.send_header = mock.Mock()
        handler.end_headers = mock.Mock()

        response = mock.Mock(status=200, reason="OK")
        response.read.return_value = b'{"job_id":"job_test"}'
        response.getheaders.return_value = [("Content-Type", "application/json")]
        connection = mock.Mock()
        connection.getresponse.return_value = response

        with mock.patch.object(host_proxy, "UPSTREAM", mock.Mock(scheme="http", hostname="127.0.0.1", port=8013, netloc="127.0.0.1:8013")), mock.patch.object(
            host_proxy.http.client, "HTTPConnection", return_value=connection
        ):
            handler._proxy()

        forwarded = connection.request.call_args.kwargs
        self.assertEqual(forwarded["body"], payload)
        self.assertEqual(forwarded["headers"]["Content-Length"], str(len(payload)))
        self.assertNotIn("Transfer-Encoding", forwarded["headers"])

    def test_proxy_forwards_post_body_and_content_type(self) -> None:
        import deploy.wsl.bin.host_proxy as host_proxy

        host_proxy = importlib.reload(host_proxy)
        handler = object.__new__(host_proxy.ProxyHandler)
        handler.command = "POST"
        handler.path = "/v1/policy-briefings/import"
        payload = b'{"news_item_id":"156771197","date":"2026-07-16"}'
        handler.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(payload)),
            "X-API-Key": "test-key",
            "Host": "api4.example",
        }
        handler.rfile = io.BytesIO(payload)
        handler.wfile = mock.Mock()
        handler.client_address = ("203.0.113.10", 12345)
        handler.send_response = mock.Mock()
        handler.send_header = mock.Mock()
        handler.end_headers = mock.Mock()

        response = mock.Mock()
        response.status = 200
        response.reason = "OK"
        response.read.return_value = b'{"job_id":"job_test"}'
        response.getheaders.return_value = [("Content-Type", "application/json")]
        connection = mock.Mock()
        connection.getresponse.return_value = response

        with mock.patch.object(host_proxy, "UPSTREAM", mock.Mock(scheme="http", hostname="127.0.0.1", port=8013, netloc="127.0.0.1:8013")), mock.patch.object(
            host_proxy.http.client, "HTTPConnection", return_value=connection
        ):
            handler._proxy()

        connection.request.assert_called_once()
        method, path = connection.request.call_args.args
        forwarded = connection.request.call_args.kwargs
        self.assertEqual((method, path), ("POST", "/v1/policy-briefings/import"))
        self.assertEqual(forwarded["body"], payload)
        self.assertEqual(forwarded["headers"]["Content-Type"], "application/json")
        self.assertEqual(forwarded["headers"]["Content-Length"], str(len(payload)))
        self.assertEqual(forwarded["headers"]["X-API-Key"], "test-key")
        self.assertEqual(forwarded["headers"]["X-Forwarded-For"], "203.0.113.10")

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
