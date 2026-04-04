from __future__ import annotations

from pathlib import Path
from typing import Protocol


class AsyncReadableUpload(Protocol):
    async def read(self, size: int = -1) -> bytes: ...


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

    async def save_original_pdf_stream(
        self,
        job_id: str,
        file_name: str,
        upload: AsyncReadableUpload,
        *,
        max_bytes: int,
        chunk_size: int = 1024 * 1024,
    ) -> Path:
        path = self.originals_dir / f"{job_id}-{file_name}"
        total = 0
        with path.open("wb") as handle:
            while True:
                chunk = await upload.read(chunk_size)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    handle.close()
                    if path.exists():
                        path.unlink()
                    raise ValueError("Uploaded file exceeds the maximum allowed size")
                handle.write(chunk)
        if total == 0:
            if path.exists():
                path.unlink()
            raise ValueError("Uploaded file is empty")
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
