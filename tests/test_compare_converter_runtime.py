from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "compare_converter_runtime.py"
SPEC = importlib.util.spec_from_file_location("compare_converter_runtime", SCRIPT_PATH)
assert SPEC and SPEC.loader
runtime = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime)


class CompareConverterRuntimeTests(unittest.TestCase):
    def test_request_json_sends_cloudflare_compatible_headers(self) -> None:
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'{"ok": true}'

        with patch.object(runtime.urllib.request, "urlopen", return_value=response) as mocked_open:
            payload = runtime._request_json(
                "https://api.example/health",
                headers={"X-API-Key": "secret"},
            )

        request = mocked_open.call_args.args[0]
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(
            request.get_header("User-agent"),
            "GovPress-Converter-Diagnostics/1.0",
        )
        self.assertEqual(request.get_header("Accept"), "application/json")
        self.assertEqual(request.get_header("X-api-key"), "secret")
        mocked_open.assert_called_once_with(request, timeout=120)


if __name__ == "__main__":
    unittest.main()
