from __future__ import annotations

from pathlib import Path


class StorageService:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.originals_dir = self.root / "originals"
        self.results_dir = self.root / "results"
        self.edits_dir = self.root / "edited"
        for directory in (self.originals_dir, self.results_dir, self.edits_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def save_original_pdf(self, job_id: str, file_name: str, content: bytes) -> Path:
        path = self.originals_dir / f"{job_id}-{file_name}"
        path.write_bytes(content)
        return path

    def save_generated_markdown(self, job_id: str, markdown: str) -> Path:
        path = self.results_dir / f"{job_id}.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def save_edited_markdown(self, job_id: str, markdown: str) -> Path:
        path = self.edits_dir / f"{job_id}.md"
        path.write_text(markdown, encoding="utf-8")
        return path

    def delete_job_files(self, job_id: str, file_name: str | None = None) -> None:
        candidates = [
            self.results_dir / f"{job_id}.md",
            self.edits_dir / f"{job_id}.md",
        ]
        if file_name:
            candidates.append(self.originals_dir / f"{job_id}-{file_name}")
        for path in candidates:
            if path.exists():
                path.unlink()
