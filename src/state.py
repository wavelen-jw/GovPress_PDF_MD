from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DocumentState:
    current_pdf_path: Path | None = None
    current_markdown: str = ""
    save_path: Path | None = None
    is_dirty: bool = False

    def load_markdown(self, markdown: str, pdf_path: Path | None = None) -> None:
        self.current_pdf_path = pdf_path
        self.current_markdown = markdown
        self.save_path = None
        self.is_dirty = False

    def update_markdown(self, markdown: str) -> None:
        if markdown != self.current_markdown:
            self.current_markdown = markdown
            self.is_dirty = True

    def mark_saved(self, save_path: Path) -> None:
        self.save_path = save_path
        self.is_dirty = False

    @property
    def display_name(self) -> str:
        if self.save_path:
            return self.save_path.name
        if self.current_pdf_path:
            return self.current_pdf_path.name
        return "새 문서"
