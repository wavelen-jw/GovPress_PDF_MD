"""Markdown post-processor – routes raw PDF-extracted text to the right formatter.

Responsibility map
------------------
postprocess_markdown()          Public entry point; detects document type and dispatches.
_is_press_release()             Detects 보도자료 stamp in first 10 lines.
_is_government_report()         Detects Roman-numeral sections / 요약 / 참고 headers.
_is_service_guide()             Detects Arabic-numbered section guides (안내문).

_postprocess_press_release()    Formats 보도자료: title → metadata → subtitle → body.
_postprocess_generic_markdown() Formats annual plans, white papers, and other docs.
postprocess_report()            Formats government reports (imported from report_postprocessor).

Internal helpers (press release body):
  _render_body()                Stateful line-by-line rendering of the body section.
  _normalize_body_line()        Maps a single raw line to rendered Markdown lines.
  _join_body_lines()            Joins lines broken mid-sentence by the PDF extractor.
  _post_clean()                 Final blank-line and formatting cleanup pass.

Internal helpers (shared / pre-cleaning):
  _preclean_lines()             Strips table noise, TOC, images before routing.
  _split_lines()                Expands <br>, inline service-table bundles, etc.
"""
from __future__ import annotations

import re
from typing import Iterable

from .document_template import DEFAULT_TEMPLATE, PressReleaseTemplate
from .parser_rules import clean_line, extract_sections, is_reference_line, split_contact_chunks
from .report_postprocessor import postprocess_report, postprocess_service_guide


# ── Patterns & constants ─────────────────────────────────────────────────────

IMAGE_PATTERN = re.compile(r"!\[[^\]]*\]\((?:[^()]|\([^)]*\))*\)")
TABLE_NOISE_PATTERN = re.compile(r"^\|[\|\-·.\u2024\u2025\u2026\u22ef\d\s]*\|?$|^\|?(?:[-·.\u2024\u2025\u2026\u22ef]{3,}|\d+|\s)*\|?$")
TOC_DOTS_PATTERN = re.compile(r"[·\.]{4,}\s*\d+\s*$")
DATE_ONLY_PATTERN = re.compile(r"^\d{4}\.\s*\d{1,2}\.?$")
HEADING_BULLET_PATTERN = re.compile(r"^(#{1,6})\s*([□○ㅇ￭▸※-])\s*(.+)$")
TOPIC_BULLET_PATTERN = re.compile(r"^[■◆]\s*(.+)$")
NUMBERED_HEADING_PATTERN = re.compile(r"^\d+\.\s+.+$")
PLAIN_HEADING_PATTERN = re.compile(r"^(#{2,6})\s*(.+)$")
HTML_BREAK_PATTERN = re.compile(r"<br\s*/?>", re.IGNORECASE)
HTML_TABLE_TAG_PATTERN = re.compile(r"^</?(?:table|tr|th|td)\b", re.IGNORECASE)
CONTACT_LABELS = {"담당 부서", "담당부서", "책임자", "담당자"}
IMAGE_ARTIFACT_PATTERN = re.compile(r"\S+_images/\S+\.(?:png|jpg|jpeg)\)?")
PRESS_PARAGRAPH_ENDINGS = (
    "밝혔다.",
    "말했다.",
    "전했다.",
    "강조했다.",
    "강조하며,",
    "설명했다.",
    "예정이다.",
    "기대된다.",
    "된다.",
    "있다.",
)
INLINE_SPLIT_MARKERS = ("￭", "▲")
APPENDIX_FIELD_PATTERN = re.compile(r"^[○ㅇ]\s*([^:：]+)\s*[:：]\s*(.+)$")
PRESS_CALLOUT_MARKER_PATTERN = re.compile(r"\s+(?=▴\()")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=다\.)\s+(?=[가-힣])")
TRAILING_ANGLE_LABEL_PATTERN = re.compile(r"^(.*?[.!?])\s*(<[^>]+>)$")
ANGLE_LABEL_WITH_TRIANGLE_PATTERN = re.compile(r"^(<[^>]+>)\s*(△.+)$")
CASE_STUDY_HEADING_PATTERN = re.compile(r"^####\s*<\s*20\d{2}.*추진 사례\s*>$")
MARKDOWN_TABLE_SEPARATOR_PATTERN = re.compile(r"^\|\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|$")
INLINE_SERVICE_TABLE_BUNDLE_PATTERN = re.compile(r"(\|[^|]+\|[^|]+\|[^|]+\|)")
APPENDIX_COUNT_ONLY_PATTERN = re.compile(r"^\(\d+개\)$")


# ── Line splitting & pre-cleaning ────────────────────────────────────────────

def _split_inline_service_table_bundle(text: str) -> list[str]:
    if "|서비스|주요내용|신청방법|" not in text:
        return [text]

    prefix, _, remainder = text.partition("|서비스|주요내용|신청방법|")
    lines: list[str] = []
    prefix = clean_line(prefix)
    if prefix:
        lines.append(prefix)

    bundle = f"|서비스|주요내용|신청방법|{remainder}"
    rows = [clean_line(match.group(1)) for match in INLINE_SERVICE_TABLE_BUNDLE_PATTERN.finditer(bundle)]
    if rows:
        lines.extend(rows)
        return lines

    lines.append(clean_line(bundle))
    return lines


def _join_title(lines: Iterable[str]) -> str:
    return " ".join(clean_line(line) for line in lines if clean_line(line)).strip()


def _split_lines(raw_text: str) -> list[str]:
    expanded: list[str] = []
    in_html_table = False
    for raw_line in raw_text.splitlines():
        stripped = raw_line.strip()
        if HTML_TABLE_TAG_PATTERN.match(stripped):
            if stripped.lower().startswith("<table"):
                in_html_table = True
            if in_html_table:
                expanded.append(stripped)
                if stripped.lower().startswith("</table"):
                    in_html_table = False
                continue

        service_parts = _split_inline_service_table_bundle(raw_line)
        if len(service_parts) > 1 or service_parts[0] != raw_line:
            for part in service_parts:
                if part:
                    expanded.append(part)
            continue

        if raw_line.strip().startswith("|") and raw_line.strip().endswith("|"):
            line = IMAGE_ARTIFACT_PATTERN.sub("", raw_line).strip()
            if not line:
                expanded.append("")
                continue
            if TABLE_NOISE_PATTERN.fullmatch(line):
                if MARKDOWN_TABLE_SEPARATOR_PATTERN.fullmatch(line):
                    expanded.append(clean_line(line))
                continue
            expanded.append(clean_line(IMAGE_PATTERN.sub("", line)))
            continue

        normalized_line = HTML_BREAK_PATTERN.sub("\n", raw_line)
        for raw_line in normalized_line.splitlines():
            if "![image" in raw_line:
                continue
            line = IMAGE_ARTIFACT_PATTERN.sub("", raw_line).strip()
            if not line:
                expanded.append("")
                continue

            if line.startswith("|") and line.endswith("|"):
                inner = line.strip("|")
                if "|" in inner:
                    expanded.append(clean_line(line))
                    continue
                cells = [
                    clean_line(IMAGE_ARTIFACT_PATTERN.sub("", IMAGE_PATTERN.sub("", cell)))
                    for cell in line.strip("|").split("|")
                ]
                cells = [cell for cell in cells if cell]
                if not cells:
                    continue
                if all(set(cell) <= {"-"} for cell in cells):
                    continue
                if len(cells) % 2 == 0 and any(cell in CONTACT_LABELS for cell in cells[::2]):
                    pairs = [f"{cells[index]}: {cells[index + 1]}" for index in range(0, len(cells), 2)]
                    expanded.append(" ".join(pairs))
                    continue
                expanded.extend(cells)
                continue

            expanded.append(clean_line(IMAGE_PATTERN.sub("", line)))

    return [clean_line(line) for line in expanded]


def _is_meaningful_line(line: str) -> bool:
    text = clean_line(line)
    if not text:
        return False
    if IMAGE_PATTERN.search(text):
        return False
    if TABLE_NOISE_PATTERN.fullmatch(text):
        return False
    return True


def _preclean_lines(raw_text: str) -> list[str]:
    lines = _split_lines(raw_text)
    cleaned: list[str] = []
    in_toc = False

    for line in lines:
        text = clean_line(IMAGE_PATTERN.sub("", line))
        if text.startswith("|") and text.endswith("|") and "|" in text.strip("|"):
            cleaned.append(text)
            continue
        text = text.lstrip("| ").rstrip("| ").strip()
        if text.startswith("- □"):
            text = "□ " + text[3:].strip()
        elif text.startswith("- ○"):
            text = "○ " + text[3:].strip()
        elif text.startswith("- ㅇ"):
            text = "ㅇ " + text[3:].strip()
        if not text:
            continue
        if TABLE_NOISE_PATTERN.fullmatch(text):
            continue
        if text in {"|", "||", "|---|"}:
            continue
        if text == "# 순 서" or text == "순 서":
            in_toc = True
            continue
        if in_toc:
            if TOC_DOTS_PATTERN.search(text) or text.startswith("- "):
                continue
            if text.startswith("## ") or text.startswith("### ") or text.startswith("#### "):
                in_toc = False
            else:
                continue
        cleaned.append(text)

    return cleaned


# ── Document type detection ───────────────────────────────────────────────────

_PRESS_STAMP_RE = re.compile(r'^(?:.+\s+)?보도자료\s*$')

# 보고서 구조 지표: 로마자 섹션 또는 요약/참고 헤더
_REPORT_SECTION_RE = re.compile(
    r'^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ|I{1,3}V?|VI{0,3}|IX|IV)\s*[.．]'
    r'|^요\s*약\s*$'
    r'|^[<＜]\s*참고',
    re.MULTILINE,
)

# 서비스 안내문: 짧은 아라비아 숫자 섹션 제목이 3개 이상 있고 로마자 섹션이 없는 문서
_SG_SECTION_TITLE_RE = re.compile(
    r'^[1-9]\d*[.．]\s+(?!.*(?:다\.|요\.|습니다\.|니다\.))[가-힣A-Za-z ()·\-&]{1,25}\s*$',
    re.MULTILINE,
)
_SG_SENTENCE_ENDINGS = re.compile(r'다\.|요\.|습니다\.|니다\.')


def _is_government_report(raw_text: str) -> bool:
    """로마자 섹션(I. II. III.), 요약, 또는 <참고> 섹션이 있으면 보고서 형식."""
    return bool(_REPORT_SECTION_RE.search(raw_text))


def _is_service_guide(raw_text: str) -> bool:
    """서비스 안내문 감지.

    조건:
      1. 짧은 아라비아 숫자 섹션 제목(N. 짧은제목)이 3개 이상
      2. 로마자 섹션 없음 (보고서와 구분)
      3. 보도자료 스탬프 없음
    """
    if _is_press_release(raw_text):
        return False
    if _REPORT_SECTION_RE.search(raw_text):
        return False
    matches = _SG_SECTION_TITLE_RE.findall(raw_text)
    return len(matches) >= 3


def _is_press_release(raw_text: str) -> bool:
    """문서 최상단(첫 10줄)에 '보도자료'가 독립 스탬프로 있는지로 판단.

    '행정안전부 보도자료' 같은 짧은 스탬프 줄만 인정.
    '행안부 보도자료·홈페이지 개선 방안' 처럼 제목에 포함된 경우는 제외.
    """
    for line in raw_text.splitlines()[:10]:
        if _PRESS_STAMP_RE.match(line.strip()):
            return True
    return False


# ── Metadata & section rendering ─────────────────────────────────────────────

def _render_metadata(lines: list[str], plain_metadata: bool = False) -> list[str]:
    if not lines:
        return []

    def normalize_metadata_text(value: str) -> str:
        normalized = re.sub(r"\)\s+\(", ") / (", value)
        normalized = re.sub(r"(\d{1,2}:\d{2})\s+\(", r"\1 / (", normalized)
        return normalized

    rendered = ["행정안전부 보도자료"]
    briefing_values: list[str] = []
    for line in lines:
        text = clean_line(line)
        if text.startswith("보도시점"):
            suffix = text[len("보도시점") :].strip(" :")
            suffix = normalize_metadata_text(suffix)
            if suffix:
                briefing_values.append(suffix)
        else:
            normalized = normalize_metadata_text(text)
            if normalized and normalized != "보도자료":
                briefing_values.append(normalized)
    if briefing_values:
        rendered.append(f"보도시점: {' / '.join(briefing_values)}")
    return rendered


def _should_render_press_heading(content: str) -> bool:
    text = clean_line(content)
    if len(text) <= 32:
        return True
    if text.startswith(("이번 과정은", "실습 과정에서는", "현장학습은")):
        return True
    if text.startswith(
        (
            "행정안전부는",
            "행정안전부 윤호중 장관은",
            "행정안전부",
            "정부는",
            "김민재 차관은",
            "김광용",
            "향후,",
            "협력국에",
            "이번에 제정된",
            "먼저,",
            "현장에서는",
            "화재 진압 후에는",
            "이번 보고서에는",
            "이번 개선 방안은",
        )
    ):
        return False
    if any(text.endswith(ending) for ending in PRESS_PARAGRAPH_ENDINGS):
        return False
    return len(text) <= 70


def _split_press_callout_items(text: str) -> list[str]:
    return [clean_line(part) for part in PRESS_CALLOUT_MARKER_PATTERN.split(text) if clean_line(part)]


# ── Press release body rendering ─────────────────────────────────────────────
# _render_body() and its helpers form a self-contained rendering pipeline.
# Next step: extract this block into press_body_renderer.py once patterns are
# consolidated into a shared _md_patterns module.

_STRUCTURAL_STARTS = frozenset("#>|-*◆■□○\u20dd§※▴▲△＜<￭▸ㅇ(▪\uf0a7")


def _join_body_lines(lines: list[str]) -> list[str]:
    """PDF에서 문장 중간에 끊긴 줄을 이어 붙임.

    1) 이전 줄이 마침표로 끝나지 않고 구조 요소가 아닌 경우 → 다음 줄과 합침.
    2) ◆/■ 소제목 직후 줄도 마침표 없이 끝나면 합침 (◆ 뒤 본문 연결).
    """
    joined: list[str] = []
    for line in lines:
        text = clean_line(line)
        if not text:
            joined.append(text)
            continue
        is_structural = text[0] in _STRUCTURAL_STARTS
        prev = joined[-1] if joined else ""
        prev_is_structural = bool(prev and prev[0] in _STRUCTURAL_STARTS)
        if (
            prev
            and not prev.rstrip().endswith(".")
            and not prev_is_structural
            and not is_structural
        ):
            # 일반 연속 줄 합치기
            joined[-1] = f"{prev.rstrip()} {text}"
        elif (
            prev
            and not prev.rstrip().endswith(".")
            and prev_is_structural
            and prev.lstrip()[0] in "◆■"
            and not is_structural
        ):
            # ◆/■ 소제목 뒤 이어지는 본문 줄도 합침
            joined[-1] = f"{prev.rstrip()} {text}"
        else:
            joined.append(text)
    return joined


def _join_continuation_rendered(lines: list[str]) -> list[str]:
    """렌더링 후에도 문장이 끊긴 경우 이어 붙임 (예: ◆ 분리 후 나머지 줄)."""
    joined: list[str] = []
    for line in lines:
        if not line:
            joined.append(line)
            continue
        is_html_table = HTML_TABLE_TAG_PATTERN.match(line.lstrip())
        is_structural = is_html_table or line.lstrip()[:1] in "#>|-" or line.startswith(("  -", "  >"))
        prev = joined[-1] if joined else ""
        prev_is_html_table = HTML_TABLE_TAG_PATTERN.match(prev.lstrip()) if prev else None
        prev_is_structural = not prev or prev_is_html_table or prev.lstrip()[:1] in "#>|-" or prev.startswith(("  -", "  >"))
        if (
            prev
            and not prev.rstrip().endswith(".")
            and not prev_is_structural
            and not is_structural
        ):
            joined[-1] = f"{prev.rstrip()} {line}"
        else:
            joined.append(line)
    return joined


def _split_topic_heading(content: str) -> tuple[str, str]:
    """◆/■ 뒤 content를 (제목, 본문)으로 분리.

    전략 1: 앞 2-4 단어가 뒤에서 반복되면 반복 직전에서 분리.
    전략 2: 누적 길이 6-24 내의 마지막 공백에서 분리.
    """
    if len(content) <= 22:
        return content, ""
    words = content.split()
    for n in range(2, min(5, len(words))):
        prefix_with_space = " ".join(words[:n]) + " "
        remainder = content[len(prefix_with_space):]
        if prefix_with_space in remainder:
            split_pos = len(prefix_with_space) + remainder.index(prefix_with_space)
            return content[:split_pos].strip(), content[split_pos:].strip()
    best_pos = -1
    for i, ch in enumerate(content):
        if ch == " " and 6 <= i <= 24:
            best_pos = i
    if best_pos == -1:
        return content, ""
    return content[:best_pos].strip(), content[best_pos + 1:].strip()


def _normalize_body_line(text: str, template: PressReleaseTemplate) -> list[str]:
    if HTML_TABLE_TAG_PATTERN.match(text):
        return [text]
    angle_triangle_match = ANGLE_LABEL_WITH_TRIANGLE_PATTERN.match(text)
    if angle_triangle_match:
        label = clean_line(angle_triangle_match.group(1))
        remainder = clean_line(angle_triangle_match.group(2))
        return [f"> {label}", ">", f"> {remainder}"]
    trailing_label_match = TRAILING_ANGLE_LABEL_PATTERN.match(text)
    if trailing_label_match:
        sentence = clean_line(trailing_label_match.group(1)).lstrip("□ ").strip()
        label = clean_line(trailing_label_match.group(2))
        return [sentence, "", f"#### {label}", ""]
    if text.startswith("<") and text.endswith(">") and "개요" in text:
        return [f">{text}"]
    if text.startswith("▴("):
        items = _split_press_callout_items(text)
        return [f">{item}" for item in items]
    if is_reference_line(text):
        return [f"> {text}"]
    if text.startswith("<") and text.endswith(">"):
        return [f"#### {text}", ""]

    heading_match = PLAIN_HEADING_PATTERN.match(text)
    if heading_match:
        content = heading_match.group(2).strip()
        if content.startswith("<") and content.endswith(">"):
            return [f"#### {content}", ""]
        if content.startswith("□"):
            inner = content[1:].strip()
            return [inner]
        if content.startswith(("○", "ㅇ")):
            return [f"- {content[1:].strip()}"]
        if content.startswith("※"):
            note = content[1:].strip()
            if note.startswith("(주요 중대범죄)"):
                return [f"  > {note}"]
            return [f"> {content}"]
        if _should_render_press_heading(content):
            level = min(max(len(heading_match.group(1)), 2), 3)
            return [f"{'#' * level} {content}", ""]
        return [content]

    if any(text.startswith(marker) for marker in template.top_level_bullets):
        content = text[1:].strip()
        if content.startswith("<") and content.endswith(">"):
            return [f"#### {content}", ""]
        return [content]
    if any(text.startswith(marker) for marker in template.second_level_bullets):
        return [f"- {text[1:].strip()}"]
    if any(text.startswith(marker) for marker in template.third_level_bullets):
        if "민‧관합동 현장지원단 구성:" in text:
            return [f"  >{text[1:].strip()}"]
        if text.startswith("*") and (
            "20% 표본점검" in text or text[1:].strip().startswith("(주요 점검항목)")
        ):
            return [f"  > {text[1:].strip()}"]
        if (
            "*" in template.third_level_bullets
            and text.startswith("*")
            and len(text) > 1
            and "일정(안)" not in text
        ):
            return [f"> {text[1:].strip()}", ""]
        return [f"  - {text[1:].strip('-* ').strip()}"]
    if text.startswith("※"):
        note = text[1:].strip()
        if note.startswith("(붙임") or note.startswith("(참고"):
            return [f"- {note}"]
        return [f"> {note}"]
    if text.startswith("* "):
        return [f"  - {text[2:].strip()}"]
    topic_match = TOPIC_BULLET_PATTERN.match(text)
    if topic_match:
        content = topic_match.group(1).strip()
        heading, body = _split_topic_heading(content)
        if not body:
            return [f"#### {heading}", ""]
        body_result: list[str] = []
        for part in _SENTENCE_SPLIT_RE.split(body):
            body_result.append(part)
            if part.endswith("다."):
                body_result.append("")
        return [f"#### {heading}", ""] + body_result
    parts = _SENTENCE_SPLIT_RE.split(text)
    result: list[str] = []
    for part in parts:
        result.append(part)
        if part.endswith("다."):
            result.append("")
    return result


def _expand_inline_bullets(lines: list[str]) -> list[str]:
    expanded: list[str] = []
    for line in lines:
        if line.lstrip().startswith(">"):
            expanded.append(line.rstrip())
            continue
        leading = line[: len(line) - len(line.lstrip(" "))]
        text = clean_line(line)
        if text.startswith(("#", ">", "- ", "  - ")):
            if leading and (text.startswith("-") or text.startswith(">")):
                expanded.append(f"{leading}{text}")
            else:
                expanded.append(text)
            continue
        marker = next((item for item in INLINE_SPLIT_MARKERS if item in text), None)
        if not marker:
            expanded.append(f"{leading}{text}" if leading and text.startswith("-") else text)
            continue

        parts = [clean_line(part) for part in re.split(r"[￭▲]", text) if clean_line(part)]
        if len(parts) <= 1:
            expanded.append(f"{leading}{text}" if leading and text.startswith("-") else text)
            continue
        expanded.extend(f"- {part}" for part in parts)
    return expanded


def _quote_indent_for_context(rendered: list[str]) -> str:
    previous_nonblank = next((line for line in reversed(rendered) if line.strip()), "")
    if not previous_nonblank:
        return ""

    leading = previous_nonblank[: len(previous_nonblank) - len(previous_nonblank.lstrip(" "))]
    stripped = previous_nonblank.lstrip()
    if stripped.startswith("-"):
        return f"{leading}  "
    if stripped.startswith(">"):
        return leading
    return leading


def _starts_new_body_block(text: str, template: PressReleaseTemplate) -> bool:
    if not text:
        return False
    if HTML_TABLE_TAG_PATTERN.match(text):
        return True
    if is_reference_line(text):
        return True
    if text.startswith(("<", "※", "* ")):
        return True
    if any(
        text.startswith(marker)
        for marker in (
            template.top_level_bullets
            + template.second_level_bullets
            + template.third_level_bullets
            + ("ㅇ ", "￭", "▸", "- ", "- - ", "n ")
        )
    ):
        return True
    if HEADING_BULLET_PATTERN.match(text) or PLAIN_HEADING_PATTERN.match(text):
        return True
    if DATE_ONLY_PATTERN.fullmatch(text):
        return True
    return False


def _starts_main_press_body(text: str, template: PressReleaseTemplate) -> bool:
    if any(text.startswith(marker) for marker in template.top_level_bullets):
        return True
    if any(text.startswith(marker) for marker in template.second_level_bullets):
        return True
    if text.startswith(("<", "※", "* ", "- ", "ㅇ ", "▸", "￭")):
        return True
    if is_reference_line(text):
        return True
    return False


def _is_case_study_bullet(text: str) -> bool:
    return text.startswith(("§", "- ", "○ ", "△", "※", "\uf0a7", "", "▪"))


def _is_case_study_intro(text: str) -> bool:
    return text.startswith("(") and ")" in text[:20]


def _render_body(lines: list[str], template: PressReleaseTemplate) -> list[str]:
    lines = _join_body_lines(lines)
    rendered: list[str] = []
    inside_reference_block = False
    reference_block_mode: str | None = None
    note_quote_indent: str | None = None
    intro_quote_mode = False
    main_body_started = False
    case_study_mode = False
    previous_case_study_bullet_was_split = False
    reference_breakers = (
        "- 먼저",
        "- 특히",
        "- 이후",
        "- 이어서",
        "- 한편",
        "○ 먼저",
        "○ 특히",
        "○ 이후",
        "○ 이어서",
        "□ 한편",
    )
    for line in lines:
        text = clean_line(line)
        if not text:
            continue
        if case_study_mode:
            if text.startswith("□"):
                if rendered and rendered[-1] != "":
                    rendered.append("")
                case_study_mode = False
                main_body_started = True
            elif _is_case_study_intro(text):
                if rendered and rendered[-1] != "":
                    rendered.append("")
                rendered.append(f"> {text}")
                previous_case_study_bullet_was_split = False
                continue
            elif _is_case_study_bullet(text):
                bullet_text = text
                if text.startswith(("§", "※", "\uf0a7", "", "▪")):
                    bullet_text = text[1:].strip()
                elif text.startswith("○ "):
                    bullet_text = text[1:].strip()

                if text.startswith(("○ ", "§", "※", "\uf0a7", "", "▪")):
                    if text.startswith("§") and "§" in bullet_text:
                        parts = [clean_line(part) for part in bullet_text.split("§") if clean_line(part)]
                        for index, part in enumerate(parts):
                            prefix = "> - "
                            rendered.append(f"{prefix}{part}")
                        previous_case_study_bullet_was_split = True
                    else:
                        prefix = ">   - " if text.startswith("※") else "> - "
                        rendered.append(f"{prefix}{bullet_text}")
                        previous_case_study_bullet_was_split = False
                else:
                    if text.startswith("△"):
                        rendered.append(f">    - {text[1:].strip()}")
                    elif text.startswith("- "):
                        prefix = ">    - " if previous_case_study_bullet_was_split else "> - "
                        rendered.append(f"{prefix}{text[1:].strip()}")
                    else:
                        rendered.append(f"> {text}")
                    previous_case_study_bullet_was_split = False
                continue
            elif text and not text.startswith("□"):
                rendered.append(f"> - {text}")
                previous_case_study_bullet_was_split = False
                continue
            else:
                rendered.append(f"> {text}")
                previous_case_study_bullet_was_split = False
                continue
        if not main_body_started:
            if text.startswith("# "):
                intro_quote_mode = True
                rendered.append(f"> ## {text[2:].strip()}")
                continue
            if intro_quote_mode and not _starts_main_press_body(text, template):
                rendered.append(f"> {text}")
                continue
            if intro_quote_mode:
                if rendered and rendered[-1] != "":
                    rendered.append("")
                intro_quote_mode = False
            if _starts_main_press_body(text, template):
                main_body_started = True
        if note_quote_indent is not None:
            if _starts_new_body_block(text, template):
                note_quote_indent = None
            else:
                rendered.append(f"{note_quote_indent}> {text}")
                continue
        if inside_reference_block and text.startswith(reference_breakers):
            if rendered and rendered[-1] != "":
                rendered.append("")
            inside_reference_block = False
            reference_block_mode = None

        if inside_reference_block:
            if reference_block_mode == "education_plan":
                if text.startswith("△"):
                    if rendered and rendered[-1] != ">":
                        rendered.append(">")
                    rendered.append(f"> {text}")
                    continue
                if (
                    rendered
                    and rendered[-1].lstrip().startswith("> △")
                    and not text.startswith(("#", "-", ">", "<", "□", "○", "ㅇ"))
                ):
                    rendered[-1] = f"{rendered[-1]} {text}"
                    continue
                if rendered and rendered[-1] != "":
                    rendered.append("")
                inside_reference_block = False
                reference_block_mode = None
            else:
                rendered.append(f"> {text}")
                continue

        normalized = _normalize_body_line(text, template)
        if normalized and CASE_STUDY_HEADING_PATTERN.match(normalized[0]):
            case_study_mode = True
        if text.startswith("※") and normalized:
            note_quote_indent = _quote_indent_for_context(rendered)
            normalized = [
                f"{note_quote_indent}{line}" if line.startswith(">") else line for line in normalized
            ]
        if text.startswith("*") and normalized and normalized[0].startswith(">"):
            previous_nonblank = next((line for line in reversed(rendered) if line), "")
            if previous_nonblank.lstrip().startswith("-"):
                normalized = [f"  {line}" if line.startswith(">") else line for line in normalized]
        elif normalized and normalized[0].startswith(">"):
            previous_nonblank = next((line for line in reversed(rendered) if line), "")
            if (
                (normalized[0].startswith("> <") and previous_nonblank.lstrip().startswith("-"))
                or previous_nonblank.startswith("  >")
            ):
                normalized = [f"  {line}" if line.startswith(">") else line for line in normalized]
        if (
            any(text.startswith(marker) for marker in template.top_level_bullets)
            and rendered
            and normalized
            and not normalized[0].startswith("## ")
            and rendered[-1] != ""
        ):
            rendered.append("")
        rendered.extend(normalized)
        if normalized and normalized[0].startswith(">") and is_reference_line(text) and "연혁" in text:
            inside_reference_block = True
            reference_block_mode = "reference"
        elif (
            normalized
            and normalized[0].startswith("> <")
            and "교육계획" in normalized[0]
            and not text.startswith(">")
        ):
            inside_reference_block = True
            reference_block_mode = "education_plan"
    return _expand_inline_bullets(rendered)


def _render_appendix(lines: list[str]) -> list[str]:
    cleaned = [clean_line(line) for line in lines if clean_line(line)]
    if not cleaned:
        return []

    rendered: list[str] = []
    index = 0

    if cleaned[0] == "참고":
        if len(cleaned) > 1 and not cleaned[1].startswith(("□", "○", "※", "*", "〈", "<")):
            rendered.extend([f"## 참고: {cleaned[1]}", ""])
            index = 2
        else:
            rendered.extend(["## 참고", ""])
            index = 1

    if index < len(cleaned) and not cleaned[index].startswith(("□", "○", "※", "*", "〈", "<")):
        rendered.extend([f"### {cleaned[index]}", ""])
        index += 1

    while index < len(cleaned):
        text = cleaned[index]

        if text == "영역" and index + 1 < len(cleaned) and cleaned[index + 1] == "평가지표":
            rows: list[tuple[str, str]] = []
            cursor = index + 2
            while cursor + 1 < len(cleaned):
                label = cleaned[cursor]
                if label.startswith(("○ ", "□ ", "※ ", "* ", "참고")):
                    break
                value = cleaned[cursor + 1]
                if value.startswith(("○ ", "□ ")):
                    break
                items = [clean_line(part) for part in re.split(r"\s*▴", value) if clean_line(part)]
                rows.append((label, "<br>".join(items)))
                cursor += 2
            if rows:
                rendered.append("| 영역 | 평가지표 |")
                rendered.append("| --- | --- |")
                for label, value in rows:
                    rendered.append(f"| {label} | {value} |")
                rendered.append("")
                index = cursor
                continue

        if text == "구 분 (기관수)" and index + 5 < len(cleaned):
            headers = cleaned[index : index + 6]
            cursor = index + 6
            rows: list[list[str]] = []

            while cursor < len(cleaned):
                label = cleaned[cursor]
                if label.startswith(("□ ", "○ ", "※ ", "* ")):
                    break
                if "(" not in label:
                    break
                cursor += 1
                cells: list[str] = []
                while cursor < len(cleaned) and len(cells) < 5:
                    token = cleaned[cursor]
                    if cells and _looks_like_appendix_summary_label(token):
                        break
                    if APPENDIX_COUNT_ONLY_PATTERN.fullmatch(token) and cells:
                        cells[-1] = f"{cells[-1]} {token}"
                    else:
                        cells.append(token[2:].strip() if token.startswith("- ") else token)
                    cursor += 1
                while len(cells) < 5:
                    cells.append("-")
                rows.append([label, *cells[:5]])

            if rows:
                rendered.append("| " + " | ".join(headers) + " |")
                rendered.append("| " + " | ".join("---" for _ in headers) + " |")
                for row in rows:
                    rendered.append("| " + " | ".join(row) + " |")
                rendered.append("")
                index = cursor
                continue

        if text.startswith("□ "):
            rendered.extend([f"### {text[2:].strip()}", ""])
            index += 1
            continue
        if text.startswith("○ "):
            rendered.append(f"- {text[2:].strip()}")
            index += 1
            continue
        if text.startswith("※ "):
            rendered.append(f"> {text[2:].strip()}")
            index += 1
            continue
        if text.startswith("* "):
            rendered.append(f"> {text[2:].strip()}")
            index += 1
            continue
        if text.startswith(("▪", "", "\uf0a7", "▴")):
            rendered.append(f"- {text[1:].strip()}")
            index += 1
            continue
        if text.startswith("〈 <"):
            rendered.extend([f"#### {text[text.find('<'):].strip()}", ""])
            index += 1
            continue
        if text.startswith(("〈", "<")):
            rendered.extend([f"#### {text}", ""])
            index += 1
            continue

        rendered.append(text)
        index += 1

    return rendered


def _looks_like_appendix_summary_label(text: str) -> bool:
    stripped = clean_line(text)
    return (
        "(" in stripped
        and ")" in stripped
        and any(keyword in stripped for keyword in ("기관", "단체", "교육청", "공기업"))
    )


def _render_contacts(lines: list[str]) -> list[str]:
    chunks = split_contact_chunks(lines)
    if not chunks:
        return []

    rendered = ["## 담당부서", ""]
    current_department = ""
    for chunk in chunks:
        if chunk.startswith(("담당 부서", "담당부서")):
            current_department = chunk.split(":", 1)[1].strip() if ":" in chunk else chunk
        else:
            if current_department:
                rendered.append(f"- {current_department} {chunk}")
            else:
                rendered.append(f"- {chunk}")
    return rendered


def _normalize_generic_line(text: str) -> list[str]:
    if HTML_TABLE_TAG_PATTERN.match(text):
        return [text]
    if text.startswith("< 핵심 정책과제 >") or text.startswith("<핵심 정책과제>"):
        suffix = text.split(">", 1)[1].strip() if ">" in text else ""
        lines = ["> <핵심 정책과제>"]
        if suffix:
            lines.extend(_normalize_generic_line(suffix))
        return lines

    heading_match = HEADING_BULLET_PATTERN.match(text)
    if heading_match:
        marker = heading_match.group(2)
        content = heading_match.group(3).strip()
        if marker == "□":
            return [f"## {content}", ""]
        if marker in {"○", "ㅇ", "￭", "▸", "-"}:
            return [f"- {content}"]
        if marker in {"", "※"}:
            return [f"## {content}", ""]

    topic_match = TOPIC_BULLET_PATTERN.match(text)
    if topic_match:
        return [f"## {topic_match.group(1).strip()}", ""]

    plain_heading_match = PLAIN_HEADING_PATTERN.match(text)
    if plain_heading_match:
        content = plain_heading_match.group(2).strip()
        if DATE_ONLY_PATTERN.fullmatch(content):
            return [f"> {content}"]
        if content.startswith("<") and content.endswith(">"):
            return [f"> {content}"]
        if len(content) < 100:
            level = min(max(len(plain_heading_match.group(1)), 2), 3)
            return [f"{'#' * level} {content}", ""]
        return [content]

    if text.startswith("<") and text.endswith(">"):
        return [f"> {text}"]

    if text.startswith("※"):
        return [f"> {text}"]

    if text.startswith("* "):
        return [f"- {text[2:].strip()}"]

    if text.startswith("- ㅇ "):
        return [f"- {text[4:].strip()}"]

    if text.startswith("- * "):
        return [f"- {text[4:].strip()}"]

    if text.startswith("- ** "):
        return [f"- {text[5:].strip()}"]

    if text.startswith("n "):
        return [f"- {text[2:].strip()}"]

    if text.startswith("￭"):
        return [f"- {text[1:].strip()}"]

    if text.startswith("▸"):
        return [f"- {text[1:].strip()}"]

    if text.startswith("ㅇ "):
        return [f"- {text[1:].strip()}"]

    if text.startswith("- - "):
        return [f"  - {text[4:].strip()}"]

    if text.startswith("- "):
        return [text]

    if NUMBERED_HEADING_PATTERN.match(text) and len(text) < 80:
        return [f"## {text}", ""]

    if DATE_ONLY_PATTERN.fullmatch(text):
        return [f"> {text}"]

    return [text]


def _collapse_wrapped_lines(lines: list[str]) -> list[str]:
    collapsed: list[str] = []
    for text in lines:
        if not text:
            continue
        if not collapsed:
            collapsed.append(text)
            continue

        previous = collapsed[-1]
        if previous.endswith((".", ":", ">", ")")):
            collapsed.append(text)
            continue
        if text.startswith("〈") or previous.startswith("〈"):
            collapsed.append(text)
            continue
        if text.startswith(("#", "-", ">", "|")) or HTML_TABLE_TAG_PATTERN.match(text):
            collapsed.append(text)
            continue
        if previous.startswith(("#", "-", ">", "|")):
            collapsed.append(text)
            continue
        if len(previous) < 35:
            collapsed[-1] = f"{previous} {text}"
            continue
        collapsed.append(text)
    return collapsed


def _post_clean(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    previous_blank = False
    for line in lines:
        stripped_leading = line[: len(line) - len(line.lstrip(" "))]
        if line.lstrip().startswith(">"):
            text = line.rstrip()
        else:
            text = clean_line(line)
        if stripped_leading and text.startswith(("-", ">")):
            text = f"{stripped_leading}{text}"
        if not text:
            if not previous_blank:
                cleaned.append("")
            previous_blank = True
            continue
        if text.startswith("▴") and cleaned and cleaned[-1].lstrip().startswith("-"):
            cleaned[-1] = f"{cleaned[-1].rstrip()} {text}"
            previous_blank = False
            continue
        if (
            text.startswith("△")
            and cleaned
            and cleaned[-1].lstrip().startswith(("-", "△"))
        ):
            if cleaned[-1].lstrip().startswith("-") and cleaned[-1].rstrip().endswith(","):
                cleaned[-1] = f"{cleaned[-1].rstrip()}   {text}"
                previous_blank = False
                continue
            cleaned.append(f"  {text}")
            previous_blank = False
            continue
        if text.startswith("-") and cleaned and cleaned[-1].lstrip().startswith("△"):
            cleaned.append("")
        if text.startswith("|"):
            if cleaned and cleaned[-1] != "" and not cleaned[-1].startswith("|"):
                cleaned.append("")
            cleaned.append(text)
            previous_blank = False
            continue
        if text.startswith("〈"):
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            cleaned.append(text)
            previous_blank = False
            continue
        if "현장지원단 구성:" in text:
            if cleaned and cleaned[-1] != "":
                cleaned.append("")
            cleaned.append(text)
            cleaned.append("")
            previous_blank = True
            continue
        if (
            cleaned
            and cleaned[-1]
            and cleaned[-1].lstrip().startswith("-")
            and text.startswith("(")
        ):
            cleaned[-1] = f"{cleaned[-1].rstrip()} {text}"
            previous_blank = False
            continue
        if (
            cleaned
            and cleaned[-1]
            and cleaned[-1].lstrip().startswith("-")
            and not text.lstrip().startswith(("#", "-", ">", "---", "|"))
            and not HTML_TABLE_TAG_PATTERN.match(text.lstrip())
        ):
            if text.lstrip().startswith("△"):
                cleaned.append("")
            else:
                cleaned[-1] = f"{cleaned[-1].rstrip()} {text}"
                previous_blank = False
                continue
        previous_blank = False
        cleaned.append(text)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return cleaned


def _nest_schedule_subitems(lines: list[str]) -> list[str]:
    nested: list[str] = []
    inside_schedule = False
    for line in lines:
        raw = line.rstrip()
        text = clean_line(line)
        if not text:
            nested.append(line)
            continue

        if raw.startswith("  - ") and text.endswith("일정(안)"):
            inside_schedule = True
            nested.append(line)
            continue

        if inside_schedule and raw.startswith("  - ") and "접수:" in text:
            nested.append(f"    - {raw[4:].strip()}")
            continue

        if inside_schedule and not raw.startswith("  - "):
            inside_schedule = False

        nested.append(line)
    return nested


# ── Generic document processing ──────────────────────────────────────────────

def _postprocess_generic_markdown(raw_text: str) -> str:
    lines = _preclean_lines(raw_text)
    meaningful = [line for line in lines if _is_meaningful_line(line)]
    if not meaningful:
        return ""

    title = meaningful[0].lstrip("# ").strip()
    body_lines = meaningful[1:]

    rendered: list[str] = [f"# {title}", ""]
    if body_lines and DATE_ONLY_PATTERN.fullmatch(body_lines[0].lstrip("# ").strip()):
        rendered.append(f"> {body_lines[0].lstrip('# ').strip()}")
        rendered.append("")
        body_lines = body_lines[1:]
    for line in body_lines:
        rendered.extend(_normalize_generic_line(line))

    cleaned = _collapse_wrapped_lines(rendered)
    return "\n".join(_post_clean(cleaned)).strip() + "\n"


def _postprocess_press_release(
    raw_text: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE
) -> str:
    sections = extract_sections(raw_text, template)
    blocks: list[str] = []
    subtitle_items: list[str] = []
    seen_subtitles: set[str] = set()
    for line in sections.subtitle_lines:
        item = clean_line(line).lstrip("- ").strip()
        if not item:
            continue
        key = re.sub(r"\s+", "", item)
        if key in seen_subtitles:
            continue
        seen_subtitles.add(key)
        subtitle_items.append(item)
    use_quote_subtitles = any("실태점검" in item for item in subtitle_items)

    title = _join_title(sections.title_lines)
    if title:
        blocks.append(f"# {title}")

    metadata = _render_metadata(sections.metadata_lines)
    if metadata:
        blocks.append("\n".join(metadata))

    if sections.subtitle_lines:
        subtitles = "\n".join(f"> {item}" for item in subtitle_items)
        blocks.append(subtitles)

    if sections.body_lines:
        blocks.append("---")

    body = _render_body(sections.body_lines, template)
    if body:
        blocks.append("\n".join(_nest_schedule_subitems(_post_clean(body))).strip())

    contacts = _render_contacts(sections.contact_lines)
    if contacts:
        blocks.append("\n".join(_post_clean(contacts)).strip())

    appendix = _render_appendix(sections.appendix_lines)
    if appendix:
        blocks.append("\n".join(_post_clean(appendix)).strip())

    output = "\n\n".join(block for block in blocks if block).strip() + "\n"
    return output.replace("\n\n---\n\n", "\n---\n")


# ── Public API ───────────────────────────────────────────────────────────────

def postprocess_markdown(
    raw_text: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE
) -> str:
    raw_text = raw_text.replace("\x00", "")
    if _is_press_release(raw_text):
        cleaned_lines = _preclean_lines(raw_text)
        return _postprocess_press_release("\n".join(cleaned_lines), template)
    if _is_government_report(raw_text):
        return postprocess_report(raw_text)
    if _is_service_guide(raw_text):
        return postprocess_service_guide(raw_text)
    return _postprocess_generic_markdown(raw_text)
