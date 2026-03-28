"""PyWebView window entry point (replaces PySide6 main_window)."""
from __future__ import annotations

import logging
import os
from pathlib import Path

import webview

# Edge WebView2 접근성 폴링 노이즈 억제
logging.getLogger("pywebview").setLevel(logging.CRITICAL)
os.environ.setdefault("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS", "--disable-features=msSmartScreenProtection")

from .webview_api import GovPressAPI
from .app_metadata import APP_DISPLAY_NAME, APP_NAME
from .utils import resolve_resource_path


def run() -> None:
    api = GovPressAPI()

    html_path = resolve_resource_path("ui", "index.html")

    window = webview.create_window(
        APP_DISPLAY_NAME,
        url=str(html_path),
        js_api=api,
        width=1440,
        height=900,
        min_size=(900, 600),
        background_color="#ffffff",
    )
    api.set_window(window)

    webview.start(gui="edgechromium", debug=False)
