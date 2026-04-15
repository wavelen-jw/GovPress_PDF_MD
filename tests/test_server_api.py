from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest

from server.app.core.config import DEFAULT_POLICY_BRIEFING_SERVICE_KEY
from server.app.main import create_app


class ServerApiContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.app = create_app(Path(self.temp_dir.name))

    def tearDown(self) -> None:
        self.app.state.worker.stop()

    def test_openapi_contains_expected_paths(self) -> None:
        schema = self.app.openapi()

        self.assertIn("/health", schema["paths"])
        self.assertIn("/v1/jobs", schema["paths"])
        self.assertIn("/v1/jobs/{job_id}", schema["paths"])
        self.assertIn("/v1/jobs/{job_id}/retry", schema["paths"])
        self.assertIn("/v1/jobs/{job_id}/result", schema["paths"])
        self.assertIn("/v1/policy-briefings/today", schema["paths"])
        self.assertIn("/v1/policy-briefings/import", schema["paths"])
        self.assertIn("/v1/policy-briefings/qc/dashboard", schema["paths"])
        self.assertIn("/v1/policy-briefings/qc/dashboard.json", schema["paths"])

    def test_openapi_contains_expected_job_operations(self) -> None:
        schema = self.app.openapi()
        jobs_ops = schema["paths"]["/v1/jobs"]

        self.assertIn("post", jobs_ops)
        self.assertEqual(jobs_ops["post"]["operationId"], "create_job_v1_jobs_post")
        self.assertIn("security", jobs_ops["post"])

    def test_openapi_contains_expected_result_operations(self) -> None:
        schema = self.app.openapi()
        result_ops = schema["paths"]["/v1/jobs/{job_id}/result"]

        self.assertIn("get", result_ops)
        self.assertIn("patch", result_ops)
        get_security_names = {key for entry in result_ops["get"]["security"] for key in entry}
        patch_security_names = {key for entry in result_ops["patch"]["security"] for key in entry}
        self.assertEqual(get_security_names, {"XApiKey", "XEditToken"})
        self.assertEqual(patch_security_names, {"XApiKey", "XEditToken"})

    def test_app_exposes_services_on_state(self) -> None:
        self.assertTrue(hasattr(self.app.state, "job_service"))
        self.assertTrue(hasattr(self.app.state, "result_service"))
        self.assertTrue(hasattr(self.app.state, "worker"))
        self.assertTrue(hasattr(self.app.state, "settings"))

    def test_app_uses_default_operational_settings(self) -> None:
        self.assertEqual(self.app.state.settings.max_upload_bytes, 25_000_000)
        self.assertEqual(self.app.state.settings.cors_allow_origins, [])
        self.assertEqual(self.app.state.settings.upload_rate_limit_count, 12)
        self.assertEqual(self.app.state.settings.upload_rate_limit_window_seconds, 60)
        self.assertEqual(self.app.state.settings.job_ttl_hours, 72)
        self.assertEqual(
            self.app.state.settings.policy_briefing_service_key,
            DEFAULT_POLICY_BRIEFING_SERVICE_KEY,
        )

    def test_app_reads_environment_operational_settings(self) -> None:
        previous = {
            "GOVPRESS_API_KEY": os.environ.get("GOVPRESS_API_KEY"),
            "GOVPRESS_CORS_ALLOW_ORIGINS": os.environ.get("GOVPRESS_CORS_ALLOW_ORIGINS"),
            "GOVPRESS_MAX_UPLOAD_BYTES": os.environ.get("GOVPRESS_MAX_UPLOAD_BYTES"),
            "GOVPRESS_UPLOAD_RATE_LIMIT_COUNT": os.environ.get("GOVPRESS_UPLOAD_RATE_LIMIT_COUNT"),
            "GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS": os.environ.get("GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS"),
            "GOVPRESS_JOB_TTL_HOURS": os.environ.get("GOVPRESS_JOB_TTL_HOURS"),
            "GOVPRESS_POLICY_BRIEFING_SERVICE_KEY": os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY"),
        }
        try:
            os.environ["GOVPRESS_API_KEY"] = "secret-key"
            os.environ["GOVPRESS_CORS_ALLOW_ORIGINS"] = "https://m.example.com, https://admin.example.com"
            os.environ["GOVPRESS_MAX_UPLOAD_BYTES"] = "1234"
            os.environ["GOVPRESS_UPLOAD_RATE_LIMIT_COUNT"] = "5"
            os.environ["GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS"] = "30"
            os.environ["GOVPRESS_JOB_TTL_HOURS"] = "24"
            os.environ["GOVPRESS_POLICY_BRIEFING_SERVICE_KEY"] = "policy-key"
            app = create_app(Path(self.temp_dir.name))
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.assertEqual(app.state.settings.api_key, "secret-key")
        self.assertEqual(
            app.state.settings.cors_allow_origins,
            ["https://m.example.com", "https://admin.example.com"],
        )
        self.assertEqual(app.state.settings.max_upload_bytes, 1234)
        self.assertEqual(app.state.settings.upload_rate_limit_count, 5)
        self.assertEqual(app.state.settings.upload_rate_limit_window_seconds, 30)
        self.assertEqual(app.state.settings.job_ttl_hours, 24)
        self.assertEqual(app.state.settings.policy_briefing_service_key, "policy-key")
