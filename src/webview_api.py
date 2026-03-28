"""Python API exposed to the JavaScript frontend via pywebview."""
from __future__ import annotations

import json
import logging
import threading
from html import escape
from pathlib import Path

try:
    import markdown as markdown_lib
except ImportError:
    markdown_lib = None  # type: ignore[assignment]

import webview

# webview.FileDialog는 pywebview 일부 버전/PyInstaller 빌드에서 누락될 수 있음.
# 호환성을 위해 정수 상수를 직접 정의한다.
_OPEN_DIALOG = getattr(webview, 'OPEN_DIALOG', None) or 10
_SAVE_DIALOG = getattr(webview, 'SAVE_DIALOG', None) or 20

from .converter import convert_pdf_to_markdown
from .preview_widget import normalize_preview_markdown, decorate_preview_html, inject_cursor_highlight
from .state import DocumentState
from .utils import configure_logging, ensure_utf8_text, save_markdown_file
from .app_metadata import APP_NAME, APP_VERSION


_MAX_CONTENT_CHARS = 2_000_000   # 2 MB hard cap on editor content
_MAX_RENDER_CHARS  =   500_000   # 500 KB soft cap on markdown-to-HTML rendering


class GovPressAPI:
    """All public methods are callable from JavaScript as `pywebview.api.<method>()`."""

    def __init__(self) -> None:
        self.window = None
        self._state = DocumentState()
        self._lock = threading.Lock()  # guards _state across the bg conversion thread and JS callbacks
        self._logger = configure_logging(Path.home() / f".{APP_NAME}" / "app.log")
        self._logger.info("GovPressAPI 초기화 완료 (v%s)", APP_VERSION)

    def set_window(self, window) -> None:
        self.window = window

    # ── PDF conversion ─────────────────────────────────────────────────────

    def open_pdf_dialog(self) -> None:
        """Open a native file dialog and start conversion if a PDF is chosen."""
        self._logger.info("open_pdf_dialog: Python 호출됨")
        try:
            result = self.window.create_file_dialog(
                _OPEN_DIALOG,
                file_types=("PDF Files (*.pdf)",),
            )
        except Exception as exc:
            self._logger.error("파일 선택 창 오류: %s", exc, exc_info=True)
            self._js(f"onConversionError({json.dumps('파일 선택 창을 열 수 없습니다.')})")
            return
        if result:
            self._logger.info("open_pdf_dialog: 선택=%s", result[0])
            self._start_conversion(Path(result[0]))
        else:
            self._js("onPdfDialogCancelled()")

    def open_md_dialog(self) -> None:
        """Open a native file dialog to load an existing Markdown file."""
        self._logger.info("open_md_dialog: Python 호출됨")
        try:
            result = self.window.create_file_dialog(
                _OPEN_DIALOG,
                file_types=("Markdown Files (*.md)",),
            )
        except Exception as exc:
            self._logger.error("MD 파일 선택 창 오류: %s", exc, exc_info=True)
            self._js(f"onConversionError({json.dumps('파일 선택 창을 열 수 없습니다.')})")
            return
        if not result:
            self._js("onPdfDialogCancelled()")
            return
        md_path = Path(result[0])
        try:
            content = ensure_utf8_text(md_path.read_text(encoding="utf-8", errors="replace"))
        except OSError as exc:
            self._logger.error("MD 파일 읽기 오류: %s", exc)
            self._js(f"onConversionError({json.dumps('MD 파일을 읽을 수 없습니다.')})")
            return
        with self._lock:
            self._state.load_markdown(content, md_path)
        payload = json.dumps({"markdown": content, "filename": md_path.name, "path": str(md_path)})
        self._js(f"onMdLoaded({payload})")

    def get_version(self) -> str:
        """Return the application version string."""
        return APP_VERSION

    def convert_pdf(self, path: str) -> None:
        """Start PDF conversion for the given absolute file path (drag-and-drop)."""
        if not isinstance(path, str) or not path.lower().endswith(".pdf"):
            self._js(f"onConversionError({json.dumps('PDF 파일만 변환할 수 있습니다.')})")
            return
        self._start_conversion(Path(path))

    def _start_conversion(self, pdf_path: Path) -> None:
        if not pdf_path.exists():
            self._js(f"onConversionError({json.dumps('선택한 PDF 파일을 찾을 수 없습니다.')})")
            return
        threading.Thread(target=self._do_convert, args=(pdf_path,), daemon=True).start()

    def _do_convert(self, pdf_path: Path) -> None:
        try:
            markdown = convert_pdf_to_markdown(pdf_path)
            clean = ensure_utf8_text(markdown)
            with self._lock:
                self._state.load_markdown(clean, pdf_path)
            payload = json.dumps({"markdown": clean, "filename": pdf_path.name})
            self._js(f"onConversionSuccess({payload})")
        except Exception as exc:
            self._logger.error("Conversion failed for %s: %s", pdf_path, exc)
            error_msg = json.dumps(self._user_message(str(exc)))
            self._js(f"onConversionError({error_msg})")

    # ── Markdown rendering ──────────────────────────────────────────────────

    def render_markdown(self, content: str, cursor_line: str | None = None) -> str:
        """Return rendered HTML body for the given Markdown content."""
        if len(content) > _MAX_RENDER_CHARS:
            content = content[:_MAX_RENDER_CHARS]
        normalized = normalize_preview_markdown(content)
        if cursor_line:
            normalized = inject_cursor_highlight(normalized, cursor_line)
        if markdown_lib is None:
            return f"<pre>{escape(normalized)}</pre>"
        body = markdown_lib.markdown(
            normalized,
            extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
        )
        return decorate_preview_html(body)

    # ── Save ────────────────────────────────────────────────────────────────

    def save_markdown(self, content: str) -> dict:
        """Open a save dialog and write the Markdown file. Returns status dict."""
        self._logger.info("save_markdown: Python 호출됨")
        with self._lock:
            suggested = (
                self._state.save_path.name
                if self._state.save_path
                else f"{self._state.current_pdf_path.stem if self._state.current_pdf_path else 'document'}.md"
            )
        result = self.window.create_file_dialog(
            _SAVE_DIALOG,
            save_filename=suggested,
            file_types=("Markdown Files (*.md)",),
        )
        if not result:
            return {"saved": False}
        save_path = Path(result if isinstance(result, str) else result[0])
        try:
            save_markdown_file(save_path, content)
            with self._lock:
                self._state.mark_saved(save_path)
            return {"saved": True, "path": str(save_path), "name": save_path.name}
        except OSError as exc:
            self._logger.error("Save failed: %s", exc)
            return {"saved": False, "error": str(exc)}

    # ── Content state sync ──────────────────────────────────────────────────

    def update_content(self, content: str) -> None:
        """Called on every editor change to keep dirty-state in sync."""
        if len(content) > _MAX_CONTENT_CHARS:
            return  # silently ignore; UI already has the oversized content
        with self._lock:
            self._state.update_markdown(content)

    # ── Misc ────────────────────────────────────────────────────────────────

    def show_error(self, message: str) -> None:
        """Display a native error dialog."""
        if self.window:
            self.window.create_confirmation_dialog("오류", message)

    # ── Internal helpers ────────────────────────────────────────────────────

    def _js(self, code: str) -> None:
        if self.window:
            self.window.evaluate_js(code)

    @staticmethod
    def _user_message(detail: str) -> str:
        if "java=명령을 찾을 수 없습니다." in detail:
            return "Java 11+가 설치되어 있지 않아 PDF 변환을 진행할 수 없습니다."
        if "지원되지 않는 Java 버전입니다" in detail:
            return "설치된 Java 버전이 낮아 PDF 변환을 진행할 수 없습니다. Java 11 이상이 필요합니다."
        return f"PDF 변환에 실패했습니다.\n\n{detail}"
