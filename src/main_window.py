from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QThreadPool, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolBar,
    QWidget,
)

from .editor_widget import MarkdownEditor
from .preview_widget import MarkdownPreviewWidget
from .app_metadata import (
    APP_DISPLAY_NAME,
    APP_GITHUB_URL,
    APP_NAME,
    SETTINGS_APPLICATION,
    SETTINGS_ORGANIZATION,
    TEMURIN_17_URL,
)
from .state import DocumentState
from .utils import (
    configure_logging,
    ensure_utf8_text,
    resolve_resource_path,
    save_markdown_file,
)
from .workers import ConversionWorker


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_DISPLAY_NAME)
        self._resize_to_screen_ratio()
        self.setAcceptDrops(True)
        icon_path = resolve_resource_path("assets", "icons", "govpress.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.settings = QSettings(SETTINGS_ORGANIZATION, SETTINGS_APPLICATION)
        self.logger = configure_logging(Path.home() / f".{APP_NAME}" / "app.log")
        self.thread_pool = QThreadPool.globalInstance()
        self.state = DocumentState()
        self._last_cursor_block_number = 0
        self._follow_cursor_preview = False

        self.editor = MarkdownEditor(self)
        self.preview = MarkdownPreviewWidget(
            resolve_resource_path("assets", "styles", "preview.css"),
            self,
        )
        self.splitter = QSplitter(self)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.setCentralWidget(self.splitter)

        self.preview_timer = QTimer(self)
        self.preview_timer.setInterval(250)
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self._refresh_preview)
        self.editor.markdown_changed.connect(self._handle_markdown_changed)
        self.editor.cursorPositionChanged.connect(self._highlight_current_cursor_line)

        self._build_toolbar()
        self._build_status_bar()
        self._apply_drop_target_style(False)
        self._set_view_mode("split")
        self._refresh_preview()

    def _resize_to_screen_ratio(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1728, 972)
            return

        available = screen.availableGeometry()
        width = max(int(available.width() * 0.9), 1728)
        height = max(int(available.height() * 0.9), 972)
        width = min(width, available.width())
        height = min(height, available.height())
        self.resize(width, height)

    def _build_toolbar(self) -> None:
        """Create the main toolbar and actions."""
        toolbar = QToolBar("Main", self)
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_action = QAction("PDF 열기", self)
        open_action.triggered.connect(self.open_pdf_dialog)
        toolbar.addAction(open_action)

        save_action = QAction("저장", self)
        save_action.triggered.connect(self.save_markdown)
        toolbar.addAction(save_action)

        source_action = QAction("소스 모드", self)
        source_action.triggered.connect(lambda: self._set_view_mode("source"))
        toolbar.addAction(source_action)

        preview_action = QAction("미리보기 모드", self)
        preview_action.triggered.connect(lambda: self._set_view_mode("preview"))
        toolbar.addAction(preview_action)

        split_action = QAction("분할 보기", self)
        split_action.triggered.connect(lambda: self._set_view_mode("split"))
        toolbar.addAction(split_action)

        follow_cursor_action = QAction("커서 따라가기", self)
        follow_cursor_action.setCheckable(True)
        follow_cursor_action.setChecked(False)
        follow_cursor_action.toggled.connect(self._set_follow_cursor_preview)
        toolbar.addAction(follow_cursor_action)

        spacer = QWidget(self)
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        info_action = QAction("정보", self)
        info_action.triggered.connect(self._show_info_dialog)
        toolbar.addAction(info_action)

    def _build_status_bar(self) -> None:
        """Create the status bar widgets."""
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)
        self.status_file = QLabel("새 문서", self)
        self.statusBar().addPermanentWidget(self.status_file, 1)
        self.statusBar().showMessage("준비")

    def _set_follow_cursor_preview(self, enabled: bool) -> None:
        self._follow_cursor_preview = enabled
        self.statusBar().showMessage(
            "커서 따라가기 켜짐" if enabled else "커서 따라가기 꺼짐"
        )

    def _apply_drop_target_style(self, active: bool) -> None:
        """Highlight the main window while a valid PDF drag is active."""
        if active:
            self.setStyleSheet(
                "QMainWindow {"
                "border: 2px solid #0f766e;"
                "background-color: #f0fdfa;"
                "}"
            )
        else:
            self.setStyleSheet("")

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Accept PDF drags and surface a visible drop target state."""
        urls = event.mimeData().urls()
        if any(url.toLocalFile().lower().endswith(".pdf") for url in urls):
            event.acceptProposedAction()
            self._apply_drop_target_style(True)
            self.statusBar().showMessage("PDF를 놓으면 변환을 시작합니다.")
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """Clear drag highlight when the pointer leaves the window."""
        self._apply_drop_target_style(False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Start conversion when PDF files are dropped on the window."""
        self._apply_drop_target_style(False)
        pdf_files = [
            Path(url.toLocalFile())
            for url in event.mimeData().urls()
            if url.toLocalFile().lower().endswith(".pdf")
        ]
        if not pdf_files:
            self._show_warning("PDF 파일만 열 수 있습니다.")
            return

        if len(pdf_files) > 1:
            self.statusBar().showMessage("여러 파일 중 첫 번째 PDF만 편집기로 엽니다.")
        self.load_pdf(pdf_files[0])
        event.acceptProposedAction()

    def open_pdf_dialog(self) -> None:
        """Open a native file picker for PDF selection."""
        last_dir = self.settings.value("last_dir", str(Path.home()))
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "PDF 열기",
            last_dir,
            "PDF Files (*.pdf)",
        )
        if file_name:
            self.settings.setValue("last_dir", str(Path(file_name).parent))
            self.load_pdf(Path(file_name))

    def load_pdf(self, pdf_path: Path) -> None:
        """Queue PDF conversion on a background worker."""
        if not pdf_path.exists():
            self._show_warning("선택한 PDF 파일을 찾을 수 없습니다.")
            return
        if not self._confirm_discard_changes():
            return

        self.statusBar().showMessage(f"변환 중: {pdf_path.name}")
        worker = ConversionWorker(pdf_path)
        worker.signals.finished.connect(self._on_conversion_success)
        worker.signals.failed.connect(self._on_conversion_failure)
        self.thread_pool.start(worker)

    def _on_conversion_success(self, pdf_path: Path, markdown: str) -> None:
        """Load converted markdown into the editor and preview panes."""
        clean_markdown = ensure_utf8_text(markdown)
        self.state.load_markdown(clean_markdown, pdf_path)
        self.editor.set_markdown(clean_markdown)
        self._last_cursor_block_number = self.editor.get_current_block_number()
        self.preview.render_markdown(clean_markdown, self.editor.get_current_block_text())
        self._update_status_widgets("변환 완료")

    def _on_conversion_failure(
        self, pdf_path: Path, user_message: str, debug_detail: str
    ) -> None:
        """Record failure details and show a user-facing error dialog."""
        self.logger.error("Conversion failed for %s: %s", pdf_path, debug_detail)
        self._update_status_widgets("변환 실패")
        self._show_error(user_message, debug_detail)

    def _handle_markdown_changed(self, markdown: str) -> None:
        """Track dirty state and debounce preview updates."""
        self.state.update_markdown(markdown)
        self._update_status_widgets("편집 중")
        self.preview_timer.start()

    def _refresh_preview(self) -> None:
        """Render the current editor content in the preview pane."""
        self.preview.render_markdown(
            self.editor.get_markdown(),
            self.editor.get_current_block_text(),
            preserve_scroll=True,
        )

    def _highlight_current_cursor_line(self) -> None:
        current_block_number = self.editor.get_current_block_number()
        target_ratio = None
        if self._follow_cursor_preview and current_block_number != self._last_cursor_block_number:
            target_ratio = self.editor.get_cursor_scroll_ratio()
        self._last_cursor_block_number = current_block_number
        self.preview.render_markdown(
            self.editor.get_markdown(),
            self.editor.get_current_block_text(),
            preserve_scroll=target_ratio is None,
            target_ratio=target_ratio,
        )

    def _set_view_mode(self, mode: str) -> None:
        """Switch between source, preview, and split layouts."""
        if mode == "source":
            self.editor.show()
            self.preview.hide()
        elif mode == "preview":
            self.editor.hide()
            self.preview.show()
        else:
            self.editor.show()
            self.preview.show()
        self.statusBar().showMessage(f"보기 모드: {mode}")

    def save_markdown(self) -> None:
        """Save the current markdown to a chosen .md file."""
        suggested_name = (
            self.state.save_path.name
            if self.state.save_path
            else f"{self.state.current_pdf_path.stem if self.state.current_pdf_path else 'document'}.md"
        )
        last_dir = self.settings.value("last_dir", str(Path.home()))
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Markdown 저장",
            str(Path(last_dir) / suggested_name),
            "Markdown Files (*.md)",
        )
        if not file_name:
            return

        save_path = Path(file_name)
        try:
            save_markdown_file(save_path, self.editor.get_markdown())
        except OSError as exc:
            self.logger.error("Save failed for %s: %s", save_path, exc)
            self._show_error("Markdown 저장에 실패했습니다.", str(exc))
            return

        self.settings.setValue("last_dir", str(save_path.parent))
        self.state.mark_saved(save_path)
        self._update_status_widgets("저장 완료")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Prompt before closing when there are unsaved changes."""
        if self._confirm_discard_changes():
            event.accept()
        else:
            event.ignore()

    def _confirm_discard_changes(self) -> bool:
        """Return True if it is safe to replace or close the current document."""
        if not self.state.is_dirty:
            return True
        reply = QMessageBox.question(
            self,
            "미저장 변경 사항",
            "저장되지 않은 변경 사항이 있습니다. 계속 진행하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        return reply == QMessageBox.Yes

    def _update_status_widgets(self, message: str) -> None:
        """Refresh file name and save status in the status bar."""
        suffix = "미저장 변경" if self.state.is_dirty else "저장됨"
        self.status_file.setText(f"{self.state.display_name} | {suffix}")
        self.statusBar().showMessage(message)

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "경고", message)

    def _show_error(self, message: str, details: str) -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Critical)
        dialog.setWindowTitle("오류")
        dialog.setText(message)
        dialog.setTextFormat(Qt.RichText)
        dialog.setTextInteractionFlags(Qt.TextBrowserInteraction | Qt.TextSelectableByMouse)
        if "java=명령을 찾을 수 없습니다." in details:
            dialog.setInformativeText(
                "Java 11+ 설치가 필요합니다.<br>"
                "권장 배포본: <a href=\"{url}\">Eclipse Temurin 17 다운로드</a>".format(
                    url=TEMURIN_17_URL
                )
            )
        elif "지원되지 않는 Java 버전입니다" in details:
            dialog.setInformativeText(
                "Java 11 이상이 필요합니다.<br>"
                "권장 배포본: <a href=\"{url}\">Eclipse Temurin 17 다운로드</a>".format(
                    url=TEMURIN_17_URL
                )
            )
        dialog.setDetailedText(details)
        dialog.exec()

    def _show_info_dialog(self) -> None:
        dialog = QMessageBox(self)
        dialog.setWindowTitle("정보")
        dialog.setIcon(QMessageBox.Information)
        dialog.setText(f"만든이 : 행정안전부 정준우")
        dialog.setInformativeText(f"GitHub 주소 : {APP_GITHUB_URL}")
        dialog.setTextInteractionFlags(Qt.TextSelectableByMouse)
        dialog.exec()


def run() -> None:
    """Launch the application event loop."""
    app = QApplication.instance() or QApplication([])
    app.setApplicationName(APP_NAME)
    window = MainWindow()
    window.show()
    app.exec()
