"""HWPX 전용 후처리기.

PDF 아티팩트(페이지 노이즈, TOC 점선, 이미지 참조 등) 제거 로직을 적용하지 않는다.
HWPX에서 추출된 텍스트는 구조적으로 깔끔하므로, 단락 스타일 정보를 활용해
Markdown으로 변환한다.

처리 흐름
----------
postprocess_hwpx(paragraphs)
  └─ 문서 타입 감지 (_is_press_release / _is_government_report / 기타)
       ├─ 보도자료  → _render_press_release()  (parser_rules.extract_sections 재사용)
       ├─ 보고서    → _render_generic()
       └─ 기타      → _render_generic()
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .parser_rules import (
    clean_line,
    extract_sections,
    is_reference_line,
    split_contact_chunks,
)


# ── 데이터 모델 ──────────────────────────────────────────────────────────────────

@dataclass
class HwpxParagraph:
    """HWPX 단락 하나를 표현하는 중간 표현."""
    style_id: str   # 한글 스타일 이름 (예: "제목 1", "본문", "목록")
    text: str       # 정제된 텍스트
    level: int = 0  # 들여쓰기 수준 (0이 최상위)


# ── 스타일 분류 ──────────────────────────────────────────────────────────────────

# 제목 스타일 → Markdown 헤딩 레벨
_HEADING_STYLE_PATTERNS: list[tuple[re.Pattern[str], int]] = [
    (re.compile(r"^제목\s*1$"), 1),
    (re.compile(r"^제목\s*2$"), 2),
    (re.compile(r"^제목\s*3$"), 3),
    (re.compile(r"^제목\s*4$"), 4),
    (re.compile(r"^제목\s*5$"), 5),
    (re.compile(r"^제목\s*6$"), 6),
    (re.compile(r"^제목\s*[7-9]$"), 6),
    # 영문 스타일명 (일부 템플릿)
    (re.compile(r"^Heading\s*1$", re.IGNORECASE), 1),
    (re.compile(r"^Heading\s*2$", re.IGNORECASE), 2),
    (re.compile(r"^Heading\s*3$", re.IGNORECASE), 3),
]

_LIST_STYLE_RE = re.compile(r"^(목록|글머리표|리스트|List|번호\s*목록|순서\s*목록)", re.IGNORECASE)
_NUMBERED_LIST_STYLE_RE = re.compile(r"^(번호\s*목록|순서\s*목록|NumberedList)", re.IGNORECASE)


def _heading_level(style_id: str) -> int | None:
    """스타일 이름에서 Markdown 헤딩 레벨을 반환. 해당 없으면 None."""
    for pattern, level in _HEADING_STYLE_PATTERNS:
        if pattern.match(style_id.strip()):
            return level
    return None


def _is_list_item(style_id: str) -> bool:
    return bool(_LIST_STYLE_RE.match(style_id.strip()))


def _is_numbered_list(style_id: str) -> bool:
    return bool(_NUMBERED_LIST_STYLE_RE.match(style_id.strip()))


# ── 문서 타입 감지 ────────────────────────────────────────────────────────────────

_PRESS_STAMP_RE = re.compile(r'^(?:.+\s+)?보도자료\s*$')
_REPORT_SECTION_RE = re.compile(
    r'^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ|I{1,3}V?|VI{0,3}|IX|IV)\s*[.．]'
    r'|^요\s*약\s*$'
    r'|^[<＜]\s*참고',
    re.MULTILINE,
)


def _is_press_release(paragraphs: list[HwpxParagraph]) -> bool:
    """첫 10개 단락 내에 '보도자료' 스탬프가 있으면 True."""
    for para in paragraphs[:10]:
        if _PRESS_STAMP_RE.match(para.text.strip()):
            return True
    return False


def _is_government_report(text: str) -> bool:
    return bool(_REPORT_SECTION_RE.search(text))


# ── 번호 목록 카운터 ─────────────────────────────────────────────────────────────

class _NumberedListCounter:
    def __init__(self) -> None:
        self._counters: dict[int, int] = {}

    def next(self, level: int) -> int:
        # 더 깊은 레벨 카운터 초기화
        for k in list(self._counters.keys()):
            if k > level:
                del self._counters[k]
        self._counters[level] = self._counters.get(level, 0) + 1
        return self._counters[level]


# ── 제네릭 렌더러 ─────────────────────────────────────────────────────────────────

def _render_generic(paragraphs: list[HwpxParagraph]) -> str:
    """보도자료 외 문서: 스타일 기반 Markdown 변환."""
    lines: list[str] = []
    numbered = _NumberedListCounter()
    prev_was_heading = False

    for para in paragraphs:
        text = clean_line(para.text)
        if not text:
            if lines and lines[-1] != "":
                lines.append("")
            prev_was_heading = False
            continue

        style = para.style_id
        level = _heading_level(style)
        indent = "  " * max(para.level, 0)

        if level is not None:
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(f"{'#' * level} {text}")
            lines.append("")
            prev_was_heading = True
            continue

        if _is_numbered_list(style):
            n = numbered.next(para.level)
            lines.append(f"{indent}{n}. {text}")
            prev_was_heading = False
            continue

        if _is_list_item(style):
            numbered._counters.clear()
            lines.append(f"{indent}- {text}")
            prev_was_heading = False
            continue

        # 일반 본문
        numbered._counters.clear()
        if prev_was_heading:
            lines.append(text)
        else:
            lines.append(text)
        prev_was_heading = False

    # 후처리: 연속 빈 줄 제거
    result: list[str] = []
    for line in lines:
        if line == "" and result and result[-1] == "":
            continue
        result.append(line)

    return "\n".join(result).strip()


# ── 보도자료 렌더러 ───────────────────────────────────────────────────────────────

def _render_press_release(paragraphs: list[HwpxParagraph]) -> str:
    """보도자료 형식: parser_rules.extract_sections()를 활용해 구조화."""
    # 단락 리스트를 평문 텍스트로 변환해 기존 섹션 추출기에 전달
    raw_lines = [para.text for para in paragraphs]
    raw_text = "\n".join(raw_lines)

    sections = extract_sections(raw_text)

    out: list[str] = []

    # 헤더 (보도자료 스탬프)
    for line in sections.metadata_lines[:1]:
        text = clean_line(line)
        if text:
            out.append(f"# {text}")
            out.append("")

    # 브리핑 정보 (날짜, 담당부서 등)
    meta = [clean_line(l) for l in sections.metadata_lines[1:] if clean_line(l)]
    if meta:
        for m in meta:
            out.append(f"> {m}")
        out.append("")

    # 제목
    title_lines = [clean_line(l) for l in sections.title_lines if clean_line(l)]
    if title_lines:
        title = " ".join(title_lines)
        out.append(f"## {title}")
        out.append("")

    # 부제목
    for line in sections.subtitle_lines:
        text = clean_line(line)
        if text:
            out.append(f"### {text}")
    if sections.subtitle_lines:
        out.append("")

    # 본문
    for line in sections.body_lines:
        text = clean_line(line)
        if not text:
            if out and out[-1] != "":
                out.append("")
            continue
        if is_reference_line(text):
            out.append(f"> {text}")
        elif text.startswith(("○", "ㅇ")):
            out.append(f"- {text[1:].strip()}")
        elif text.startswith("□"):
            out.append(f"### {text[1:].strip()}")
        elif text.startswith("-"):
            out.append(text)
        else:
            out.append(text)

    # 붙임/부록
    if sections.appendix_lines:
        out.append("")
        out.append("---")
        out.append("")
        for line in sections.appendix_lines:
            text = clean_line(line)
            if text:
                out.append(text)

    # 담당자
    if sections.contact_lines:
        out.append("")
        out.append("---")
        out.append("")
        chunks = split_contact_chunks(sections.contact_lines)
        for chunk in chunks:
            for line in chunk:
                text = clean_line(line)
                if text:
                    out.append(f"- {text}")
            out.append("")

    # 연속 빈 줄 정리
    result: list[str] = []
    for line in out:
        if line == "" and result and result[-1] == "":
            continue
        result.append(line)

    return "\n".join(result).strip()


# ── 공개 진입점 ──────────────────────────────────────────────────────────────────

def postprocess_hwpx(paragraphs: list[HwpxParagraph]) -> str:
    """HWPX 단락 목록을 최종 Markdown 문자열로 변환한다.

    Args:
        paragraphs: hwpx_converter가 추출한 단락 목록.

    Returns:
        정규화된 Markdown 문자열.
    """
    if not paragraphs:
        return ""

    if _is_press_release(paragraphs):
        return _render_press_release(paragraphs)

    return _render_generic(paragraphs)
