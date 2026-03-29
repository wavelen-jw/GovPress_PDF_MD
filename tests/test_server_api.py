from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest

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

    def test_openapi_contains_expected_job_operations(self) -> None:
        schema = self.app.openapi()
        jobs_ops = schema["paths"]["/v1/jobs"]

        self.assertIn("get", jobs_ops)
        self.assertIn("post", jobs_ops)
        self.assertEqual(jobs_ops["post"]["operationId"], "create_job_v1_jobs_post")
        parameters = jobs_ops["get"]["parameters"]
        parameter_names = {parameter["name"] for parameter in parameters}
        self.assertIn("cursor", parameter_names)
        self.assertIn("limit", parameter_names)
        self.assertIn("status", parameter_names)
        self.assertIn("security", jobs_ops["get"])

    def test_openapi_contains_expected_result_operations(self) -> None:
        schema = self.app.openapi()
        result_ops = schema["paths"]["/v1/jobs/{job_id}/result"]

        self.assertIn("get", result_ops)
        self.assertIn("patch", result_ops)

    def test_app_exposes_services_on_state(self) -> None:
        self.assertTrue(hasattr(self.app.state, "job_service"))
        self.assertTrue(hasattr(self.app.state, "result_service"))
        self.assertTrue(hasattr(self.app.state, "worker"))
        self.assertTrue(hasattr(self.app.state, "settings"))

    def test_app_uses_default_operational_settings(self) -> None:
        self.assertEqual(self.app.state.settings.max_upload_bytes, 25_000_000)
        self.assertEqual(self.app.state.settings.cors_allow_origins, ["*"])

    def test_app_reads_environment_operational_settings(self) -> None:
        previous = {
            "GOVPRESS_API_KEY": os.environ.get("GOVPRESS_API_KEY"),
            "GOVPRESS_CORS_ALLOW_ORIGINS": os.environ.get("GOVPRESS_CORS_ALLOW_ORIGINS"),
            "GOVPRESS_MAX_UPLOAD_BYTES": os.environ.get("GOVPRESS_MAX_UPLOAD_BYTES"),
        }
        try:
            os.environ["GOVPRESS_API_KEY"] = "secret-key"
            os.environ["GOVPRESS_CORS_ALLOW_ORIGINS"] = "https://m.example.com, https://admin.example.com"
            os.environ["GOVPRESS_MAX_UPLOAD_BYTES"] = "1234"
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
