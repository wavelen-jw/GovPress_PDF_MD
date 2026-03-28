"""Python API exposed to the JavaScript frontend via pywebview."""
from __future__ import annotations

import json
import logging
import threading
from html import escape
from pathlib import Path

try:
    import webview
except ImportError:
    webview = None  # type: ignore[assignment]

try:
    import markdown as markdown_lib
except ImportError:
    markdown_lib = None  # type: ignore[assignment]

from .converter import convert_pdf_to_markdown
from .preview_widget import normalize_preview_markdown, decorate_preview_html, inject_cursor_highlight
from .state import DocumentState
from .utils import configure_logging, ensure_utf8_text, save_markdown_file
from .app_metadata import APP_NAME


_MAX_CONTENT_CHARS = 2_000_000   # 2 MB hard cap on editor content
_MAX_RENDER_CHARS  =   500_000   # 500 KB soft cap on markdown-to-HTML rendering


class GovPressAPI:
    """All public methods are callable from JavaScript as `pywebview.api.<method>()`."""

    def __init__(self) -> None:
        self.window = None
        self._state = DocumentState()
        self._lock = threading.Lock()  # guards _state across the bg conversion thread and JS callbacks
        self._logger = configure_logging(Path.home() / f".{APP_NAME}" / "app.log")

    def set_window(self, window) -> None:
        self.window = window

    # ── PDF conversion ─────────────────────────────────────────────────────

    def open_pdf_dialog(self) -> None:
        """Open a native file dialog and start conversion if a PDF is chosen.

        pywebview calls JS API methods in a worker thread, but
        ``create_file_dialog`` requires the GUI thread on Windows
        (EdgeChromium / MSHTML).  Calling it directly from the JS-bridge
        thread can silently fail — the dialog never appears.

        We work around this by spawning a short-lived thread so that the
        JS-bridge thread is released immediately, then attempting the
        pywebview dialog.  If that still fails we fall back to a tkinter
        file dialog which always works on Windows.
        """

        def _show():
            result = self._open_file_dialog_safe()
            if result:
                self._start_conversion(Path(result[0]))
            else:
                self._js("onPdfDialogCancelled()")

        threading.Thread(target=_show, daemon=True).start()

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
        with self._lock:
            suggested = (
                self._state.save_path.name
                if self._state.save_path
                else f"{self._state.current_pdf_path.stem if self._state.current_pdf_path else 'document'}.md"
            )
        result = self._save_file_dialog_safe(suggested)
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

    # ── File-dialog helpers (thread-safe) ───────────────────────────────────

    def _open_file_dialog_safe(self):
        """Try pywebview native dialog first, fall back to tkinter."""
        try:
            result = self.window.create_file_dialog(
                webview.FileDialog.OPEN,
                file_types=("PDF Files (*.pdf)",),
            )
            if result is not None:
                return result
        except Exception as exc:
            self._logger.warning("pywebview 파일 열기 다이얼로그 실패, tkinter로 전환: %s", exc)
        return self._tk_open_dialog()

    def _save_file_dialog_safe(self, suggested: str):
        """Try pywebview native save dialog first, fall back to tkinter."""
        try:
            result = self.window.create_file_dialog(
                webview.FileDialog.SAVE,
                save_filename=suggested,
                file_types=("Markdown Files (*.md)",),
            )
            if result is not None:
                return result
        except Exception as exc:
            self._logger.warning("pywebview 저장 다이얼로그 실패, tkinter로 전환: %s", exc)
        return self._tk_save_dialog(suggested)

    @staticmethod
    def _tk_open_dialog():
        """Tkinter-based fallback open-file dialog (always works on Windows)."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            root.focus_force()
            path = filedialog.askopenfilename(
                title="PDF 파일 선택",
                filetypes=[("PDF Files", "*.pdf"), ("All Files", "*.*")],
            )
            root.destroy()
            return [path] if path else None
        except Exception:
            return None

    @staticmethod
    def _tk_save_dialog(suggested: str):
        """Tkinter-based fallback save-file dialog."""
        try:
            import tkinter as tk
            from tkinter import filedialog

            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            root.focus_force()
            path = filedialog.asksaveasfilename(
                title="마크다운 저장",
                initialfile=suggested,
                defaultextension=".md",
                filetypes=[("Markdown Files", "*.md"), ("All Files", "*.*")],
            )
            root.destroy()
            return path if path else None
        except Exception:
            return None

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
