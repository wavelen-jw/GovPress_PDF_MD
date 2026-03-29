from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    cors_allow_origins: list[str]
    max_upload_bytes: int


def _parse_origins(raw: str | None) -> list[str]:
    if not raw:
        return ["*"]
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_settings() -> Settings:
    raw_upload_bytes = os.environ.get("GOVPRESS_MAX_UPLOAD_BYTES", "25000000")
    return Settings(
        api_key=os.environ.get("GOVPRESS_API_KEY") or None,
        cors_allow_origins=_parse_origins(os.environ.get("GOVPRESS_CORS_ALLOW_ORIGINS")),
        max_upload_bytes=max(int(raw_upload_bytes), 1),
    )
