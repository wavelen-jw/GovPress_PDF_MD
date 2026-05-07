from __future__ import annotations

import subprocess
import unittest
from unittest.mock import patch

from server.app.adapters.policy_briefing import PolicyBriefingClient


class PolicyBriefingClientDownloadTests(unittest.TestCase):
    def test_curl_download_has_process_timeout(self) -> None:
        client = PolicyBriefingClient(service_key="test", timeout_seconds=8)

        with patch("server.app.adapters.policy_briefing.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout=b"PK\x03\x04", stderr=b"")

            content = client._download_attachment_with_curl("https://example.test/file.hwpx")

        self.assertEqual(content, b"PK\x03\x04")
        self.assertEqual(run.call_args.kwargs["timeout"], 11)


if __name__ == "__main__":
    unittest.main()
