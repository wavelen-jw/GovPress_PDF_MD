from __future__ import annotations

from datetime import datetime
import sqlite3
import threading
from pathlib import Path
from typing import Protocol

from .models import HwpxTableMode, JobArtifacts, JobRecord, JobResult, JobStatus, utcnow


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _fromisoformat(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _row_to_record(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        job_id=row["job_id"],
        edit_token=row["edit_token"],
        file_name=row["file_name"],
        source=row["source"],
        status=row["status"],
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        progress=row["progress"],
        error_code=row["error_code"],
        error_message=row["error_message"],
        client_request_id=row["client_request_id"],
        result_version=row["result_version"],
        hwpx_table_mode=row["hwpx_table_mode"] or "text",
        result=JobResult(
            markdown=row["markdown"],
            html_preview=row["html_preview"],
            title=row["title"],
            department=row["department"],
            edited_markdown=row["edited_markdown"],
            saved_at=_fromisoformat(row["saved_at"]),
        ),
        artifacts=JobArtifacts(
            original_file_path=Path(row["original_pdf_path"]),
            final_markdown_path=Path(row["final_markdown_path"]) if row["final_markdown_path"] else None,
            edited_markdown_path=Path(row["edited_markdown_path"]) if row["edited_markdown_path"] else None,
        ),
    )


class JobRepository(Protocol):
    def create(
        self,
        *,
        job_id: str,
        edit_token: str,
        file_name: str,
        source: str,
        hwpx_table_mode: HwpxTableMode,
        client_request_id: str | None,
        original_file_path: Path,
    ) -> JobRecord: ...

    def get_by_client_request_id(self, client_request_id: str) -> JobRecord | None: ...

    def get(self, job_id: str) -> JobRecord | None: ...

    def list_page(
        self,
        *,
        limit: int = 20,
        status: JobStatus | None = None,
        cursor: str | None = None,
    ) -> tuple[list[JobRecord], str | None]: ...

    def update_status(
        self,
        job_id: str,
        *,
        status: JobStatus,
        progress: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> JobRecord: ...

    def save_result(
        self,
        job_id: str,
        *,
        markdown: str,
        html_preview: str,
        title: str | None,
        department: str | None,
        final_markdown_path: Path | None,
    ) -> JobRecord: ...

    def save_edited_markdown(
        self,
        job_id: str,
        *,
        markdown: str,
        edited_markdown_path: Path | None,
    ) -> JobRecord: ...

    def recover_incomplete_jobs(self) -> int: ...

    def count_queued_jobs(self) -> int: ...

    def claim_next_queued_job(self, worker_id: str) -> JobRecord | None: ...

    def delete(self, job_id: str) -> JobRecord | None: ...

    def cleanup_old_jobs(
        self,
        *,
        older_than_days: int,
        statuses: tuple[JobStatus, ...] | None = None,
    ) -> list[JobRecord]: ...


class SQLiteJobRepository:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path, check_same_thread=False)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    edit_token TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0,
                    error_code TEXT,
                    error_message TEXT,
                    client_request_id TEXT UNIQUE,
                    result_version INTEGER NOT NULL DEFAULT 0,
                    hwpx_table_mode TEXT NOT NULL DEFAULT 'text',
                    original_pdf_path TEXT NOT NULL,
                    final_markdown_path TEXT,
                    edited_markdown_path TEXT,
                    markdown TEXT,
                    html_preview TEXT,
                    title TEXT,
                    department TEXT,
                    edited_markdown TEXT,
                    saved_at TEXT,
                    claimed_by TEXT
                )
                """
            )
            columns = {
                row["name"]
                for row in conn.execute("PRAGMA table_info(jobs)").fetchall()
            }
            if "claimed_by" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN claimed_by TEXT")
            if "edit_token" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN edit_token TEXT")
            if "hwpx_table_mode" not in columns:
                conn.execute("ALTER TABLE jobs ADD COLUMN hwpx_table_mode TEXT NOT NULL DEFAULT 'text'")
            conn.execute(
                """
                UPDATE jobs
                SET edit_token = 'legacy-' || job_id
                WHERE edit_token IS NULL OR edit_token = ''
                """
            )
            conn.execute(
                """
                UPDATE jobs
                SET hwpx_table_mode = 'text'
                WHERE hwpx_table_mode IS NULL OR hwpx_table_mode = ''
                """
            )
            conn.commit()

    def create(
        self,
        *,
        job_id: str,
        edit_token: str,
        file_name: str,
        source: str,
        hwpx_table_mode: HwpxTableMode,
        client_request_id: str | None,
        original_file_path: Path,
    ) -> JobRecord:
        with self._lock, self._connect() as conn:
            if client_request_id:
                existing = self.get_by_client_request_id(client_request_id)
                if existing is not None:
                    return existing

            now = utcnow()
            conn.execute(
                """
                INSERT INTO jobs (
                    job_id, edit_token, file_name, source, status, created_at, updated_at,
                    progress, error_code, error_message, client_request_id, hwpx_table_mode,
                    result_version, original_pdf_path, final_markdown_path,
                    edited_markdown_path, markdown, html_preview, title,
                    department, edited_markdown, saved_at
                    , claimed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    edit_token,
                    file_name,
                    source,
                    "queued",
                    now.isoformat(),
                    now.isoformat(),
                    0,
                    None,
                    None,
                    client_request_id,
                    hwpx_table_mode,
                    0,
                    str(original_file_path),
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ),
            )
            conn.commit()
        record = self.get(job_id)
        assert record is not None
        return record

    def get_by_client_request_id(self, client_request_id: str) -> JobRecord | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM jobs WHERE client_request_id = ?",
                (client_request_id,),
            ).fetchone()
        return _row_to_record(row) if row else None

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
        return _row_to_record(row) if row else None

    def list_page(
        self,
        *,
        limit: int = 20,
        status: JobStatus | None = None,
        cursor: str | None = None,
    ) -> tuple[list[JobRecord], str | None]:
        clauses: list[str] = []
        params: list[object] = []

        if status:
            clauses.append("status = ?")
            params.append(status)

        if cursor:
            cursor_created_at, cursor_job_id = cursor.split("|", 1)
            clauses.append("(created_at < ? OR (created_at = ? AND job_id < ?))")
            params.extend([cursor_created_at, cursor_created_at, cursor_job_id])

        query = "SELECT * FROM jobs"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC, job_id DESC LIMIT ?"
        params.append(limit + 1)

        with self._lock, self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()

        records = [_row_to_record(row) for row in rows[:limit]]
        next_cursor: str | None = None
        if len(rows) > limit and records:
            last = records[-1]
            next_cursor = f"{last.created_at.isoformat()}|{last.job_id}"
        return records, next_cursor

    def update_status(
        self,
        job_id: str,
        *,
        status: JobStatus,
        progress: int | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> JobRecord:
        current = self.get(job_id)
        if current is None:
            raise KeyError(job_id)

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET status = ?, progress = ?, error_code = ?, error_message = ?, updated_at = ?,
                    claimed_by = CASE WHEN ? = 'queued' THEN NULL ELSE claimed_by END
                WHERE job_id = ?
                """,
                (
                    status,
                    current.progress if progress is None else progress,
                    error_code,
                    error_message,
                    utcnow().isoformat(),
                    status,
                    job_id,
                ),
            )
            conn.commit()
        updated = self.get(job_id)
        assert updated is not None
        return updated

    def save_result(
        self,
        job_id: str,
        *,
        markdown: str,
        html_preview: str,
        title: str | None,
        department: str | None,
        final_markdown_path: Path | None,
    ) -> JobRecord:
        current = self.get(job_id)
        if current is None:
            raise KeyError(job_id)

        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET markdown = ?, html_preview = ?, title = ?, department = ?,
                    final_markdown_path = ?, result_version = ?, progress = 100,
                    status = 'completed', error_code = NULL, error_message = NULL,
                    updated_at = ?, claimed_by = NULL
                WHERE job_id = ?
                """,
                (
                    markdown,
                    html_preview,
                    title,
                    department,
                    str(final_markdown_path) if final_markdown_path else None,
                    current.result_version + 1,
                    utcnow().isoformat(),
                    job_id,
                ),
            )
            conn.commit()
        updated = self.get(job_id)
        assert updated is not None
        return updated

    def save_edited_markdown(
        self,
        job_id: str,
        *,
        markdown: str,
        edited_markdown_path: Path | None,
    ) -> JobRecord:
        current = self.get(job_id)
        if current is None:
            raise KeyError(job_id)

        saved_at = utcnow()
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                UPDATE jobs
                SET edited_markdown = ?, edited_markdown_path = ?, saved_at = ?,
                    result_version = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (
                    markdown,
                    str(edited_markdown_path) if edited_markdown_path else None,
                    saved_at.isoformat(),
                    current.result_version + 1,
                    saved_at.isoformat(),
                    job_id,
                ),
            )
            conn.commit()
        updated = self.get(job_id)
        assert updated is not None
        return updated

    def recover_incomplete_jobs(self) -> int:
        with self._lock, self._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE jobs
                SET status = 'queued',
                    progress = 0,
                    error_code = CASE
                        WHEN status = 'processing' THEN 'RECOVERED_AFTER_RESTART'
                        ELSE error_code
                    END,
                    error_message = CASE
                        WHEN status = 'processing' THEN 'Server restarted while the job was processing.'
                        ELSE error_message
                    END,
                    updated_at = ?,
                    claimed_by = NULL
                WHERE status IN ('queued', 'processing')
                """,
                (utcnow().isoformat(),),
            )
            conn.commit()
        return int(cursor.rowcount or 0)

    def count_queued_jobs(self) -> int:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM jobs WHERE status = 'queued'").fetchone()
        return int(row[0]) if row else 0

    def claim_next_queued_job(self, worker_id: str) -> JobRecord | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT job_id FROM jobs
                WHERE status = 'queued'
                ORDER BY created_at ASC, job_id ASC
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                return None
            job_id = row["job_id"]
            updated = conn.execute(
                """
                UPDATE jobs
                SET status = 'processing',
                    progress = 25,
                    claimed_by = ?,
                    updated_at = ?
                WHERE job_id = ? AND status = 'queued'
                """,
                (worker_id, utcnow().isoformat(), job_id),
            )
            conn.commit()
            if updated.rowcount == 0:
                return None
        return self.get(job_id)

    def delete(self, job_id: str) -> JobRecord | None:
        existing = self.get(job_id)
        if existing is None:
            return None
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            conn.commit()
        return existing

    def cleanup_old_jobs(
        self,
        *,
        older_than_days: int,
        statuses: tuple[JobStatus, ...] | None = None,
    ) -> list[JobRecord]:
        threshold = utcnow().timestamp() - (older_than_days * 86400)
        clauses = ["strftime('%s', updated_at) < ?"]
        params: list[object] = [str(int(threshold))]
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            clauses.append(f"status IN ({placeholders})")
            params.extend(statuses)
        where_clause = " AND ".join(clauses)
        with self._lock, self._connect() as conn:
            rows = conn.execute(f"SELECT * FROM jobs WHERE {where_clause}", tuple(params)).fetchall()
            records = [_row_to_record(row) for row in rows]
            conn.execute(f"DELETE FROM jobs WHERE {where_clause}", tuple(params))
            conn.commit()
        return records


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._job_order: list[str] = []
        self._client_request_ids: dict[str, str] = {}
        self._lock = threading.Lock()

    def create(
        self,
        *,
        job_id: str,
        edit_token: str,
        file_name: str,
        source: str,
        client_request_id: str | None,
        original_file_path: Path,
    ) -> JobRecord:
        with self._lock:
            if client_request_id and client_request_id in self._client_request_ids:
                existing_id = self._client_request_ids[client_request_id]
                return self._jobs[existing_id]

            now = utcnow()
            record = JobRecord(
                job_id=job_id,
                edit_token=edit_token,
                file_name=file_name,
                source=source,
                status="queued",
                created_at=now,
                updated_at=now,
                progress=0,
                client_request_id=client_request_id,
                artifacts=JobArtifacts(original_file_path=original_file_path),
            )
            self._jobs[job_id] = record
            self._job_order.append(job_id)
            if client_request_id:
                self._client_request_ids[client_request_id] = job_id
            return record

    def get_by_client_request_id(self, client_request_id: str) -> JobRecord | None:
        with self._lock:
            job_id = self._client_request_ids.get(client_request_id)
            return self._jobs.get(job_id) if job_id else None

    def get(self, job_id: str) -> JobRecord | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_page(
        self,
        *,
        limit: int = 20,
        status: JobStatus | None = None,
        cursor: str | None = None,
    ) -> tuple[list[JobRecord], str | None]:
        with self._lock:
            start_index = 0
            if cursor:
                _, cursor_job_id = cursor.split("|", 1)
                if cursor_job_id in self._job_order:
                    start_index = self._job_order.index(cursor_job_id) + 1
            items: list[JobRecord] = []
            ordered = list(reversed(self._job_order))
            if start_index:
                ordered = ordered[start_index:]
            for job_id in ordered:
                record = self._jobs[job_id]
                if status and record.status != status:
                    continue
                items.append(record)
                if len(items) >= limit:
                    break
            next_cursor = None
            remaining = [job_id for job_id in ordered if not status or self._jobs[job_id].status == status]
            if len(remaining) > limit and items:
                last = items[-1]
                next_cursor = f"{last.created_at.isoformat()}|{last.job_id}"
            return items, next_cursor

    def update_status(self, job_id: str, *, status: JobStatus, progress: int | None = None, error_code: str | None = None, error_message: str | None = None) -> JobRecord:
        with self._lock:
            record = self._jobs[job_id]
            record.status = status
            record.progress = record.progress if progress is None else progress
            record.error_code = error_code
            record.error_message = error_message
            record.updated_at = utcnow()
            return record

    def save_result(self, job_id: str, *, markdown: str, html_preview: str, title: str | None, department: str | None, final_markdown_path: Path | None) -> JobRecord:
        with self._lock:
            record = self._jobs[job_id]
            record.result.markdown = markdown
            record.result.html_preview = html_preview
            record.result.title = title
            record.result.department = department
            record.result_version += 1
            record.progress = 100
            record.status = "completed"
            record.error_code = None
            record.error_message = None
            record.updated_at = utcnow()
            if record.artifacts:
                record.artifacts.final_markdown_path = final_markdown_path
            return record

    def save_edited_markdown(self, job_id: str, *, markdown: str, edited_markdown_path: Path | None) -> JobRecord:
        with self._lock:
            record = self._jobs[job_id]
            record.result.edited_markdown = markdown
            record.result.saved_at = utcnow()
            record.result_version += 1
            record.updated_at = utcnow()
            if record.artifacts:
                record.artifacts.edited_markdown_path = edited_markdown_path
            return record

    def recover_incomplete_jobs(self) -> int:
        recovered = 0
        with self._lock:
            for record in self._jobs.values():
                if record.status not in {"queued", "processing"}:
                    continue
                if record.status == "processing":
                    record.error_code = "RECOVERED_AFTER_RESTART"
                    record.error_message = "Server restarted while the job was processing."
                record.status = "queued"
                record.progress = 0
                record.updated_at = utcnow()
                recovered += 1
        return recovered

    def claim_next_queued_job(self, worker_id: str) -> JobRecord | None:
        with self._lock:
            for job_id in self._job_order:
                record = self._jobs[job_id]
                if record.status != "queued":
                    continue
                record.status = "processing"
                record.progress = 25
                record.updated_at = utcnow()
                return record
        return None

    def delete(self, job_id: str) -> JobRecord | None:
        with self._lock:
            record = self._jobs.pop(job_id, None)
            if record is None:
                return None
            if job_id in self._job_order:
                self._job_order.remove(job_id)
            if record.client_request_id:
                self._client_request_ids.pop(record.client_request_id, None)
            return record

    def cleanup_old_jobs(
        self,
        *,
        older_than_days: int,
        statuses: tuple[JobStatus, ...] | None = None,
    ) -> list[JobRecord]:
        threshold = utcnow().timestamp() - (older_than_days * 86400)
        with self._lock:
            records = [
                record for record in self._jobs.values()
                if record.updated_at.timestamp() < threshold and (not statuses or record.status in statuses)
            ]
            for record in records:
                self._jobs.pop(record.job_id, None)
                if record.job_id in self._job_order:
                    self._job_order.remove(record.job_id)
                if record.client_request_id:
                    self._client_request_ids.pop(record.client_request_id, None)
            return records
