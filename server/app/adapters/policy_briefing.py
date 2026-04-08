from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from html import unescape
import json
from pathlib import Path
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


PRESS_RELEASE_LIST_URL = "https://apis.data.go.kr/1371000/pressReleaseService/pressReleaseList"
_APPENDIX_PREFIXES = ("붙임", "별첨", "첨부")


@dataclass(frozen=True)
class PolicyBriefingAttachment:
    file_name: str
    file_url: str

    @property
    def extension(self) -> str:
        lower = self.file_name.lower()
        if "." not in lower:
            return ""
        return "." + lower.rsplit(".", 1)[-1]

    @property
    def is_hwpx(self) -> bool:
        return self.extension == ".hwpx"

    @property
    def is_appendix(self) -> bool:
        stripped = self.file_name.strip().lstrip("[").lstrip("<")
        return stripped.startswith(_APPENDIX_PREFIXES)


@dataclass(frozen=True)
class PolicyBriefingItem:
    news_item_id: str
    title: str
    department: str
    approve_date: str
    original_url: str
    attachments: tuple[PolicyBriefingAttachment, ...]

    @property
    def primary_hwpx(self) -> PolicyBriefingAttachment | None:
        hwpx_files = [attachment for attachment in self.attachments if attachment.is_hwpx]
        if not hwpx_files:
            return None
        primary = next((attachment for attachment in hwpx_files if not attachment.is_appendix), None)
        return primary or hwpx_files[0]


@dataclass(frozen=True)
class DownloadedPolicyBriefingFile:
    item: PolicyBriefingItem
    attachment: PolicyBriefingAttachment
    content: bytes

    @property
    def is_zip_container(self) -> bool:
        return self.content.startswith(b"PK\x03\x04")


@dataclass(frozen=True)
class PolicyBriefingCachedDocument:
    news_item_id: str
    file_name: str
    markdown_text: str
    markdown_html: str
    html_preview_text: str
    html_preview_html: str
    title: str | None
    department: str | None
    cached_at: str


class PolicyBriefingClient:
    def __init__(
        self,
        *,
        service_key: str | None,
        list_url: str = PRESS_RELEASE_LIST_URL,
        timeout_seconds: int = 30,
    ) -> None:
        self._service_key = (service_key or "").strip()
        self._list_url = list_url
        self._timeout_seconds = timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self._service_key)

    def list_items(self, target_date: date) -> list[PolicyBriefingItem]:
        if not self.configured:
            raise RuntimeError("정책브리핑 API 서비스키가 설정되지 않았습니다.")

        ymd = target_date.strftime("%Y%m%d")
        query = urllib.parse.urlencode(
            {
                "serviceKey": self._service_key,
                "startDate": ymd,
                "endDate": ymd,
            }
        )
        request = urllib.request.Request(
            f"{self._list_url}?{query}",
            headers={"User-Agent": "GovPress/1.0"},
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            payload = response.read()

        root = ET.fromstring(payload)
        result_code = (root.findtext("./header/resultCode") or "").strip()
        if result_code and result_code != "0":
            result_msg = (root.findtext("./header/resultMsg") or "API call failed").strip()
            raise RuntimeError(f"정책브리핑 API 호출 실패: {result_code} {result_msg}")

        items: list[PolicyBriefingItem] = []
        for node in root.findall("./body/NewsItem"):
            attachments = tuple(
                PolicyBriefingAttachment(file_name=file_name, file_url=file_url)
                for file_name, file_url in _extract_attachment_pairs(node)
                if file_name and file_url
            )
            items.append(
                PolicyBriefingItem(
                    news_item_id=(node.findtext("NewsItemId") or "").strip(),
                    title=unescape((node.findtext("Title") or "").strip()),
                    department=unescape((node.findtext("MinisterCode") or "").strip()),
                    approve_date=(node.findtext("ApproveDate") or "").strip(),
                    original_url=(node.findtext("OriginalUrl") or "").strip(),
                    attachments=attachments,
                )
            )
        return items

    def list_today_hwpx_items(self, target_date: date) -> list[PolicyBriefingItem]:
        return [item for item in self.list_items(target_date) if item.primary_hwpx is not None]

    def download_primary_hwpx(self, news_item_id: str, *, target_date: date) -> DownloadedPolicyBriefingFile:
        items = self.list_today_hwpx_items(target_date)
        item = next((entry for entry in items if entry.news_item_id == news_item_id), None)
        if item is None:
            raise KeyError(news_item_id)
        return self.download_item_hwpx(item)

    def download_item_hwpx(self, item: PolicyBriefingItem) -> DownloadedPolicyBriefingFile:
        attachment = item.primary_hwpx
        if attachment is None:
            raise ValueError("HWPX 첨부파일이 없는 기사입니다.")

        request = urllib.request.Request(
            attachment.file_url,
            headers={"User-Agent": "GovPress/1.0"},
        )
        with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
            content = response.read()
        if not content:
            raise ValueError("첨부파일 다운로드 결과가 비어 있습니다.")
        return DownloadedPolicyBriefingFile(item=item, attachment=attachment, content=content)


class PolicyBriefingCatalog:
    def __init__(self, *, client: PolicyBriefingClient, cache_path: Path) -> None:
        self._client = client
        self._cache_path = cache_path
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

    def list_cached_items(self, *, target_date: date, ensure_fresh: bool = True) -> list[PolicyBriefingItem]:
        store = self._load_store()
        if ensure_fresh and store["last_refreshed_on"] != target_date.isoformat():
            fetched_items = self._client.list_today_hwpx_items(target_date)
            merged_items = {
                **store["items"],
                **{item.news_item_id: _serialize_item(item) for item in fetched_items},
            }
            store = {
                "last_refreshed_on": target_date.isoformat(),
                "items": merged_items,
            }
            self._save_store(store)
        items = [_deserialize_item(payload) for payload in store["items"].values()]
        return sorted(items, key=_item_sort_key, reverse=True)

    def get_cached_item(self, news_item_id: str) -> PolicyBriefingItem | None:
        store = self._load_store()
        payload = store["items"].get(news_item_id)
        if payload is None:
            return None
        return _deserialize_item(payload)

    def refresh_today(self, target_date: date) -> list[PolicyBriefingItem]:
        return self.list_cached_items(target_date=target_date, ensure_fresh=True)

    def _load_store(self) -> dict[str, object]:
        if not self._cache_path.exists():
            return {"last_refreshed_on": "", "items": {}}
        payload = json.loads(self._cache_path.read_text())
        items = payload.get("items")
        if not isinstance(items, dict):
            items = {}
        last_refreshed_on = payload.get("last_refreshed_on")
        if not isinstance(last_refreshed_on, str):
            last_refreshed_on = ""
        return {"last_refreshed_on": last_refreshed_on, "items": items}

    def _save_store(self, store: dict[str, object]) -> None:
        self._cache_path.write_text(json.dumps(store, ensure_ascii=False, indent=2))


class PolicyBriefingCache:
    def __init__(self, *, client: PolicyBriefingClient, cache_dir: Path) -> None:
        self._client = client
        self._cache_dir = cache_dir
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._cache_dir / "index.json"

    def get(self, news_item_id: str) -> PolicyBriefingCachedDocument | None:
        payload = self._load_index().get(news_item_id)
        if not isinstance(payload, dict):
            return None
        return PolicyBriefingCachedDocument(
            news_item_id=news_item_id,
            file_name=str(payload.get("file_name", "")),
            markdown_text=str(payload.get("markdown_text", "")),
            markdown_html=str(payload.get("markdown_html", "")),
            html_preview_text=str(payload.get("html_preview_text", "")),
            html_preview_html=str(payload.get("html_preview_html", "")),
            title=str(payload.get("title")) if payload.get("title") is not None else None,
            department=str(payload.get("department")) if payload.get("department") is not None else None,
            cached_at=str(payload.get("cached_at", "")),
        )

    def save(
        self,
        *,
        item: PolicyBriefingItem,
        markdown_text: str,
        markdown_html: str,
        html_preview_text: str,
        html_preview_html: str,
        title: str | None,
        department: str | None,
    ) -> PolicyBriefingCachedDocument:
        cached = PolicyBriefingCachedDocument(
            news_item_id=item.news_item_id,
            file_name=item.primary_hwpx.file_name if item.primary_hwpx else "",
            markdown_text=markdown_text,
            markdown_html=markdown_html,
            html_preview_text=html_preview_text,
            html_preview_html=html_preview_html,
            title=title,
            department=department,
            cached_at=datetime.now(UTC).isoformat(),
        )
        index = self._load_index()
        index[item.news_item_id] = {
            "file_name": cached.file_name,
            "markdown_text": cached.markdown_text,
            "markdown_html": cached.markdown_html,
            "html_preview_text": cached.html_preview_text,
            "html_preview_html": cached.html_preview_html,
            "title": cached.title,
            "department": cached.department,
            "cached_at": cached.cached_at,
        }
        self._save_index(index)
        return cached

    def warm_item(self, item: PolicyBriefingItem) -> PolicyBriefingCachedDocument:
        cached = self.get(item.news_item_id)
        if cached is not None:
            return cached
        downloaded = self._client.download_item_hwpx(item)
        if not downloaded.is_zip_container:
            raise ValueError("첨부파일 확장자는 .hwpx 이지만 실제 파일 형식이 HWPX(zip) 가 아닙니다.")

        from . import hwpx_converter, opendataloader

        with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as handle:
            temp_path = Path(handle.name)
            handle.write(downloaded.content)
        try:
            markdown_text = hwpx_converter.convert_hwpx(str(temp_path), table_mode="text")
            markdown_html = hwpx_converter.convert_hwpx(str(temp_path), table_mode="html")
        finally:
            temp_path.unlink(missing_ok=True)

        html_preview_text = opendataloader.render_preview_html(markdown_text)
        html_preview_html = opendataloader.render_preview_html(markdown_html)
        title, department = opendataloader.extract_metadata(markdown_text)
        return self.save(
            item=item,
            markdown_text=markdown_text,
            markdown_html=markdown_html,
            html_preview_text=html_preview_text,
            html_preview_html=html_preview_html,
            title=title,
            department=department,
        )

    def warm_items(self, items: list[PolicyBriefingItem]) -> list[PolicyBriefingCachedDocument]:
        warmed: list[PolicyBriefingCachedDocument] = []
        for item in items:
            warmed.append(self.warm_item(item))
        return warmed

    def _load_index(self) -> dict[str, object]:
        if not self._index_path.exists():
            return {}
        payload = json.loads(self._index_path.read_text())
        return payload if isinstance(payload, dict) else {}

    def _save_index(self, index: dict[str, object]) -> None:
        self._index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2))


def _serialize_item(item: PolicyBriefingItem) -> dict[str, object]:
    return {
        "news_item_id": item.news_item_id,
        "title": item.title,
        "department": item.department,
        "approve_date": item.approve_date,
        "original_url": item.original_url,
        "attachments": [
            {"file_name": attachment.file_name, "file_url": attachment.file_url}
            for attachment in item.attachments
        ],
    }


def _deserialize_item(payload: dict[str, object]) -> PolicyBriefingItem:
    attachments = tuple(
        PolicyBriefingAttachment(
            file_name=str(attachment.get("file_name", "")),
            file_url=str(attachment.get("file_url", "")),
        )
        for attachment in payload.get("attachments", [])
        if isinstance(attachment, dict)
    )
    return PolicyBriefingItem(
        news_item_id=str(payload.get("news_item_id", "")),
        title=str(payload.get("title", "")),
        department=str(payload.get("department", "")),
        approve_date=str(payload.get("approve_date", "")),
        original_url=str(payload.get("original_url", "")),
        attachments=attachments,
    )


def _item_sort_key(item: PolicyBriefingItem) -> tuple[str, str]:
    try:
        approved_at = datetime.strptime(item.approve_date, "%m/%d/%Y %H:%M:%S")
        approved_key = approved_at.isoformat()
    except ValueError:
        approved_key = item.approve_date
    return (approved_key, item.news_item_id)


def _extract_attachment_pairs(node: ET.Element) -> list[tuple[str, str]]:
    file_names = [unescape((entry.text or "").strip()) for entry in node.findall("FileName")]
    file_urls = [(entry.text or "").strip() for entry in node.findall("FileUrl")]
    return list(zip(file_names, file_urls))
