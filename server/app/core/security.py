from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(settings, api_key: str | None = Security(API_KEY_HEADER)) -> None:
    expected = settings.api_key
    if not expected:
        return
    if api_key == expected:
        return
    raise HTTPException(status_code=401, detail="Invalid API key")
