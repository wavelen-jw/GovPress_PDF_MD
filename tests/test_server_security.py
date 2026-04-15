from __future__ import annotations

import unittest

from fastapi import HTTPException

from server.app.core.config import Settings
from server.app.core.security import verify_api_key


class ServerSecurityTests(unittest.TestCase):
    def test_verify_api_key_rejects_missing_server_key(self) -> None:
        settings = Settings(
            api_key=None,
            admin_api_key=None,
            cors_allow_origins=[],
            max_upload_bytes=1,
            turnstile_secret_key=None,
            upload_rate_limit_count=1,
            upload_rate_limit_window_seconds=60,
            job_ttl_hours=72,
            policy_briefing_service_key=None,
            using_policy_briefing_service_key_fallback=False,
        )
        with self.assertRaises(HTTPException) as context:
            verify_api_key(settings, None)

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(context.exception.detail, "Server is not properly configured")

    def test_verify_api_key_accepts_matching_key(self) -> None:
        settings = Settings(
            api_key="secret",
            admin_api_key=None,
            cors_allow_origins=[],
            max_upload_bytes=1,
            turnstile_secret_key=None,
            upload_rate_limit_count=1,
            upload_rate_limit_window_seconds=60,
            job_ttl_hours=72,
            policy_briefing_service_key=None,
            using_policy_briefing_service_key_fallback=False,
        )
        self.assertIsNone(verify_api_key(settings, "secret"))

    def test_verify_api_key_rejects_invalid_key(self) -> None:
        settings = Settings(
            api_key="secret",
            admin_api_key=None,
            cors_allow_origins=[],
            max_upload_bytes=1,
            turnstile_secret_key=None,
            upload_rate_limit_count=1,
            upload_rate_limit_window_seconds=60,
            job_ttl_hours=72,
            policy_briefing_service_key=None,
            using_policy_briefing_service_key_fallback=False,
        )
        with self.assertRaises(HTTPException) as context:
            verify_api_key(settings, "wrong")

        self.assertEqual(context.exception.status_code, 401)
        self.assertEqual(context.exception.detail, "Invalid API key")
