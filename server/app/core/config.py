from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_POLICY_BRIEFING_SERVICE_KEY = (
    "QBvXfTPVvBtw48ic0JvU5iKcvMHFDRZ5Svr/zyzqpUhl+VsJP8vr2uFnX0+XmgqCpHS9sXbI6TYugGmwAvEl8w=="
)


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    admin_api_key: str | None
    cors_allow_origins: list[str]
    max_upload_bytes: int
    turnstile_secret_key: str | None
    upload_rate_limit_count: int
    upload_rate_limit_window_seconds: int
    job_ttl_hours: int
    policy_briefing_service_key: str | None


def _parse_origins(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_settings() -> Settings:
    raw_upload_bytes = os.environ.get("GOVPRESS_MAX_UPLOAD_BYTES", "25000000")
    raw_rate_limit_count = os.environ.get("GOVPRESS_UPLOAD_RATE_LIMIT_COUNT", "12")
    raw_rate_limit_window_seconds = os.environ.get("GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS", "60")
    raw_job_ttl_hours = os.environ.get("GOVPRESS_JOB_TTL_HOURS", "72")
    return Settings(
        api_key=os.environ.get("GOVPRESS_API_KEY") or None,
        admin_api_key=os.environ.get("GOVPRESS_ADMIN_API_KEY") or None,
        cors_allow_origins=_parse_origins(os.environ.get("GOVPRESS_CORS_ALLOW_ORIGINS")),
        max_upload_bytes=max(int(raw_upload_bytes), 1),
        turnstile_secret_key=os.environ.get("GOVPRESS_TURNSTILE_SECRET_KEY") or None,
        upload_rate_limit_count=max(int(raw_rate_limit_count), 1),
        upload_rate_limit_window_seconds=max(int(raw_rate_limit_window_seconds), 1),
        job_ttl_hours=max(int(raw_job_ttl_hours), 1),
        policy_briefing_service_key=(
            os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY")
            or DEFAULT_POLICY_BRIEFING_SERVICE_KEY
        ),
    )
