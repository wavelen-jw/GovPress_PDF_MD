from __future__ import annotations

import re
from pathlib import Path
from typing import Protocol


def _safe_filename(file_name: str) -> str:
    """파일명에서 경로 구분자 및 위험 문자를 제거해 path traversal을 방지."""
    name = Path(file_name).name  # 디렉터리 컴포넌트 제거
    name = re.sub(r"[^\w\s.\-()]", "_", name)  # 허용 문자 외 치환
    return name or "document"


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

    def save_original_file(self, job_id: str, file_name: str, content: bytes) -> Path:
        path = self.originals_dir / f"{job_id}-{_safe_filename(file_name)}"
        path.write_bytes(content)
        return path

    def save_original_pdf(self, job_id: str, file_name: str, content: bytes) -> Path:
        return self.save_original_file(job_id, file_name, content)

    async def save_original_pdf_stream(
        self,
        job_id: str,
        file_name: str,
        upload: AsyncReadableUpload,
        *,
        max_bytes: int,
        chunk_size: int = 1024 * 1024,
    ) -> Path:
        path = self.originals_dir / f"{job_id}-{_safe_filename(file_name)}"
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
        for path in candidates:
            if path.exists():
                path.unlink()
        for path in self.originals_dir.glob(f"{job_id}-*"):
            if path.is_file():
                path.unlink()
