from __future__ import annotations

from dataclasses import dataclass
import os


DEFAULT_CORS_ALLOW_ORIGINS = [
    "https://govpress.cloud",
    "https://www.govpress.cloud",
    "https://ai.govpress.cloud",
    "https://wavelen-jw.github.io",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "http://localhost:8013",
    "http://127.0.0.1:8013",
]

DEFAULT_CORS_ALLOW_ORIGIN_REGEX = r"^https://(?:[a-z0-9-]+\.)?readhim-web\.pages\.dev$"


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    admin_api_key: str | None
    cors_allow_origins: list[str]
    cors_allow_origin_regex: str | None
    max_upload_bytes: int
    turnstile_secret_key: str | None
    upload_rate_limit_count: int
    upload_rate_limit_window_seconds: int
    job_ttl_hours: int
    policy_briefing_service_key: str | None
    using_policy_briefing_service_key_fallback: bool


def _parse_origins(raw: str | None) -> list[str]:
    if not raw:
        return list(DEFAULT_CORS_ALLOW_ORIGINS)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_bool(raw: str | None, *, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _parse_origin_regex(raw: str | None) -> str | None:
    if raw is None:
        return DEFAULT_CORS_ALLOW_ORIGIN_REGEX
    normalized = raw.strip()
    return normalized or None


def load_settings() -> Settings:
    raw_upload_bytes = os.environ.get("GOVPRESS_MAX_UPLOAD_BYTES", "25000000")
    raw_rate_limit_count = os.environ.get("GOVPRESS_UPLOAD_RATE_LIMIT_COUNT", "12")
    raw_rate_limit_window_seconds = os.environ.get("GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS", "60")
    raw_job_ttl_hours = os.environ.get("GOVPRESS_JOB_TTL_HOURS", "72")
    configured_policy_briefing_service_key = os.environ.get("GOVPRESS_POLICY_BRIEFING_SERVICE_KEY") or None
    return Settings(
        api_key=os.environ.get("GOVPRESS_API_KEY") or None,
        admin_api_key=os.environ.get("GOVPRESS_ADMIN_API_KEY") or None,
        cors_allow_origins=_parse_origins(os.environ.get("GOVPRESS_CORS_ALLOW_ORIGINS")),
        cors_allow_origin_regex=_parse_origin_regex(
            os.environ.get("GOVPRESS_CORS_ALLOW_ORIGIN_REGEX")
        ),
        max_upload_bytes=max(int(raw_upload_bytes), 1),
        turnstile_secret_key=os.environ.get("GOVPRESS_TURNSTILE_SECRET_KEY") or None,
        upload_rate_limit_count=max(int(raw_rate_limit_count), 1),
        upload_rate_limit_window_seconds=max(int(raw_rate_limit_window_seconds), 1),
        job_ttl_hours=max(int(raw_job_ttl_hours), 1),
        policy_briefing_service_key=configured_policy_briefing_service_key,
        using_policy_briefing_service_key_fallback=False,
    )
