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
    if "PDF 텍스트 추출에 실패했습니다" in detail:
        return "PDF에서 텍스트를 추출하지 못했습니다. 파일이 손상되었거나 지원되지 않는 형식일 수 있습니다."
    return "PDF 변환에 실패했습니다. 입력 파일 상태를 확인하세요."
