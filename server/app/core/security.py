from __future__ import annotations

from hmac import compare_digest

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader


API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False, scheme_name="XApiKey")
ADMIN_KEY_HEADER = APIKeyHeader(name="X-Admin-Key", auto_error=False, scheme_name="XAdminKey")
EDIT_TOKEN_HEADER = APIKeyHeader(name="X-Edit-Token", auto_error=False, scheme_name="XEditToken")


def verify_api_key(settings, api_key: str | None = Security(API_KEY_HEADER)) -> None:
    expected = settings.api_key
    if not expected:
        raise HTTPException(status_code=503, detail="Server is not properly configured")
    if api_key and compare_digest(api_key, expected):
        return
    raise HTTPException(status_code=401, detail="Invalid API key")


def verify_admin_api_key(settings, admin_key: str | None = Security(ADMIN_KEY_HEADER)) -> None:
    expected = settings.admin_api_key
    if not expected:
        raise HTTPException(status_code=503, detail="Admin API key is not configured")
    if admin_key and compare_digest(admin_key, expected):
        return
    raise HTTPException(status_code=403, detail="Invalid admin key")


def require_edit_token(edit_token: str | None = Security(EDIT_TOKEN_HEADER)) -> str:
    if edit_token:
        return edit_token
    raise HTTPException(status_code=401, detail="Missing edit token")
