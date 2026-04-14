from __future__ import annotations

import unittest
from unittest import mock

from scripts.check_cloudflare_tunnel_connectors import inspect_tunnel, parse_tunnel_info, stale_connector_ids


SAMPLE_INFO = """
NAME:     govpress-api
ID:       b73b8bf8-453e-427d-ad76-02dcb3c7448c
CREATED:  2026-03-29 12:21:33.70577 +0000 UTC

CONNECTOR ID                         CREATED              ARCHITECTURE VERSION  ORIGIN IP      EDGE
fd50bf4d-03af-4e44-82e4-46846ac8b40a 2026-04-13T22:56:31Z linux_amd64  2026.3.0 49.168.117.124 1xicn06
89acc957-bb4d-485b-bf39-b8524edf551e 2026-04-14T07:38:35Z linux_amd64  2026.3.0 49.168.117.124 2xicn05, 2xicn06
""".strip()

SAMPLE_INFO_CLEAN = """
NAME:     govpress-api
ID:       b73b8bf8-453e-427d-ad76-02dcb3c7448c
CREATED:  2026-03-29 12:21:33.70577 +0000 UTC

CONNECTOR ID                         CREATED              ARCHITECTURE VERSION  ORIGIN IP      EDGE
89acc957-bb4d-485b-bf39-b8524edf551e 2026-04-14T07:38:35Z linux_amd64  2026.3.0 49.168.117.124 2xicn05, 2xicn06
""".strip()


class CloudflareTunnelConnectorTests(unittest.TestCase):
    def test_parse_tunnel_info_extracts_connectors(self) -> None:
        payload = parse_tunnel_info(SAMPLE_INFO)
        self.assertEqual(payload["name"], "govpress-api")
        self.assertEqual(payload["id"], "b73b8bf8-453e-427d-ad76-02dcb3c7448c")
        self.assertEqual(len(payload["connectors"]), 2)
        self.assertEqual(payload["connectors"][0]["connector_id"], "fd50bf4d-03af-4e44-82e4-46846ac8b40a")

    def test_stale_connector_ids_keeps_newest_only(self) -> None:
        payload = parse_tunnel_info(SAMPLE_INFO)
        self.assertEqual(stale_connector_ids(payload["connectors"]), ["fd50bf4d-03af-4e44-82e4-46846ac8b40a"])

    def test_inspect_tunnel_reports_stale_connector_without_cleanup(self) -> None:
        with mock.patch(
            "scripts.check_cloudflare_tunnel_connectors.run_cloudflared",
            return_value=SAMPLE_INFO,
        ) as mocked:
            payload = inspect_tunnel("serverH", "b73", cleanup_stale=False)
        self.assertEqual(payload["stale_connector_ids"], ["fd50bf4d-03af-4e44-82e4-46846ac8b40a"])
        mocked.assert_called_once_with("tunnel", "info", "b73")

    def test_inspect_tunnel_cleans_stale_connector_and_reloads_info(self) -> None:
        with mock.patch(
            "scripts.check_cloudflare_tunnel_connectors.run_cloudflared",
            side_effect=[SAMPLE_INFO, "", SAMPLE_INFO_CLEAN],
        ) as mocked:
            payload = inspect_tunnel("serverH", "b73", cleanup_stale=True)
        self.assertEqual(payload["stale_connector_ids"], [])
        self.assertEqual(payload["cleaned_connector_ids"], ["fd50bf4d-03af-4e44-82e4-46846ac8b40a"])
        self.assertEqual(
            mocked.mock_calls[1].args,
            ("tunnel", "cleanup", "--connector-id", "fd50bf4d-03af-4e44-82e4-46846ac8b40a", "b73"),
        )
