from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile_token(secret_key: str, token: str, remote_ip: str | None = None) -> tuple[bool, dict]:
    payload = {
        "secret": secret_key,
        "response": token,
    }
    if remote_ip:
        payload["remoteip"] = remote_ip

    request = Request(
        TURNSTILE_VERIFY_URL,
        data=urlencode(payload).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        result = json.loads(response.read().decode("utf-8"))
    return bool(result.get("success")), result
