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
                _user_message_from_exception(str(exc)),
                str(exc),
            )
            return
        self.signals.finished.emit(self.pdf_path, markdown)


def _user_message_from_exception(detail: str) -> str:
    if "java=명령을 찾을 수 없습니다." in detail:
        return "Java 11+가 설치되어 있지 않아 PDF 변환을 진행할 수 없습니다."
    if "지원되지 않는 Java 버전입니다" in detail:
        return "설치된 Java 버전이 낮아 PDF 변환을 진행할 수 없습니다."
    return "PDF 변환에 실패했습니다. OpenDataLoader PDF 또는 Java 설치 상태를 확인하세요."
