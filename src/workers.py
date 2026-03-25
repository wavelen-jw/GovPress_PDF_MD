from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, Signal, Slot

from .converter import convert_pdf_to_markdown


class ConversionWorkerSignals(QObject):
    finished = Signal(Path, str)
    failed = Signal(Path, str, str)


class ConversionWorker(QRunnable):
    def __init__(self, pdf_path: Path) -> None:
        super().__init__()
        self.pdf_path = pdf_path
        self.signals = ConversionWorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            markdown = convert_pdf_to_markdown(self.pdf_path)
        except Exception as exc:  # pragma: no cover
            self.signals.failed.emit(
                self.pdf_path,
                "PDF 변환에 실패했습니다. OpenDataLoader PDF 또는 Java 설치 상태를 확인하세요.",
                str(exc),
            )
            return
        self.signals.finished.emit(self.pdf_path, markdown)
