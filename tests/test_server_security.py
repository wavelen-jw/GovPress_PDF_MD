from __future__ import annotations

import unittest

from fastapi import HTTPException

from server.app.core.config import Settings
from server.app.core.security import verify_api_key


class ServerSecurityTests(unittest.TestCase):
    def test_verify_api_key_allows_missing_key_when_auth_disabled(self) -> None:
        settings = Settings(
            api_key=None,
            cors_allow_origins=[],
            max_upload_bytes=1,
            turnstile_secret_key=None,
            upload_rate_limit_count=1,
            upload_rate_limit_window_seconds=60,
            job_ttl_hours=72,
        )
        self.assertIsNone(verify_api_key(settings, None))

    def test_verify_api_key_accepts_matching_key(self) -> None:
        settings = Settings(
            api_key="secret",
            cors_allow_origins=[],
            max_upload_bytes=1,
            turnstile_secret_key=None,
            upload_rate_limit_count=1,
            upload_rate_limit_window_seconds=60,
            job_ttl_hours=72,
        )
        self.assertIsNone(verify_api_key(settings, "secret"))

    def test_verify_api_key_rejects_invalid_key(self) -> None:
        settings = Settings(
            api_key="secret",
            cors_allow_origins=[],
            max_upload_bytes=1,
            turnstile_secret_key=None,
            upload_rate_limit_count=1,
            upload_rate_limit_window_seconds=60,
            job_ttl_hours=72,
        )
        with self.assertRaises(HTTPException) as context:
            verify_api_key(settings, "wrong")

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Invalid API key")
