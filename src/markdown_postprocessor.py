from __future__ import annotations

import re
from typing import Iterable

from .document_template import DEFAULT_TEMPLATE, PressReleaseTemplate
from .parser_rules import clean_line, extract_sections, is_reference_line, split_contact_chunks


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
TRAILING_ANGLE_LABEL_PATTERN = re.compile(r"^(.*?[.!?])\s*(<[^>]+>)$")
ANGLE_LABEL_WITH_TRIANGLE_PATTERN = re.compile(r"^(<[^>]+>)\s*(△.+)$")
CASE_STUDY_HEADING_PATTERN = re.compile(r"^####\s*<\s*20\d{2}.*추진 사례\s*>$")
MARKDOWN_TABLE_SEPARATOR_PATTERN = re.compile(r"^\|\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)+\|$")
INLINE_SERVICE_TABLE_BUNDLE_PATTERN = re.compile(r"(\|[^|]+\|[^|]+\|[^|]+\|)")


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
    for raw_line in raw_text.splitlines():
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


def _has_press_release_markers(lines: list[str]) -> bool:
    joined = "\n".join(lines)
    markers = ("보도자료", "보도시점", "담당 부서", "담당부서")
    return sum(1 for marker in markers if marker in joined) >= 2


def _render_metadata(lines: list[str], plain_metadata: bool = False) -> list[str]:
    if not lines:
        return []

    def normalize_metadata_text(value: str) -> str:
        normalized = re.sub(r"\)\s+\(", ") / (", value)
        normalized = re.sub(r"(\d{1,2}:\d{2})\s+\(", r"\1 / (", normalized)
        return normalized

    rendered = ["행정안전부 보도자료"] if plain_metadata else ["> 행정안전부 보도자료"]
    for line in lines:
        text = clean_line(line)
        if text.startswith("보도시점"):
            suffix = text[len("보도시점") :].strip(" :")
            suffix = normalize_metadata_text(suffix)
            if suffix:
                rendered.append(f"보도시점: {suffix}" if plain_metadata else f"> 보도시점: {suffix}")
        else:
            normalized = normalize_metadata_text(text)
            rendered.append(f"보도시점: {normalized}" if plain_metadata else f"> 보도시점: {normalized}")
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
            return [f"> {text[1:].strip()}"]
        return [f"  - {text[1:].strip('-* ').strip()}"]
    if text.startswith("※"):
        note = text[1:].strip()
        return [f"> {note}"]
    if text.startswith("* "):
        return [f"  - {text[2:].strip()}"]
    return [text]


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
    return text.startswith(("§", "- ", "○ ", "△", "※"))


def _is_case_study_intro(text: str) -> bool:
    return text.startswith("(") and ")" in text[:20]


def _render_body(lines: list[str], template: PressReleaseTemplate) -> list[str]:
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
                bullet_text = text[1:].strip() if text.startswith(("§", "※")) else text.lstrip("○").strip()
                if text.startswith(("○ ", "§", "※")):
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
    return []


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
        if text.startswith(("#", "-", ">", "|")):
            collapsed.append(text)
            continue
        if previous.startswith(("#", "-", ">")):
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
    subtitle_items = [clean_line(line).lstrip("- ").strip() for line in sections.subtitle_lines]
    use_quote_subtitles = any("실태점검" in item for item in subtitle_items)

    title = _join_title(sections.title_lines)
    if title:
        blocks.append(f"# {title}")

    metadata = _render_metadata(sections.metadata_lines, plain_metadata=use_quote_subtitles)
    if metadata:
        blocks.append("\n".join(metadata))

    if sections.subtitle_lines:
        subtitles = "\n".join(
            f"> {item}" if use_quote_subtitles else f"- {item}" for item in subtitle_items
        )
        if sections.body_lines:
            blocks.append(f"{subtitles}\n---")
        else:
            blocks.append(subtitles)

    body = _render_body(sections.body_lines, template)
    if body:
        blocks.append("\n".join(_nest_schedule_subitems(_post_clean(body))).strip())

    appendix = _render_appendix(sections.appendix_lines)
    if appendix:
        blocks.append("\n".join(_post_clean(appendix)).strip())

    contacts = _render_contacts(sections.contact_lines)
    if contacts:
        blocks.append("\n".join(_post_clean(contacts)).strip())

    output = "\n\n".join(block for block in blocks if block).strip() + "\n"
    return output.replace("\n\n---\n\n", "\n---\n")


def postprocess_markdown(
    raw_text: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE
) -> str:
    cleaned_lines = _preclean_lines(raw_text)
    if _has_press_release_markers(cleaned_lines):
        return _postprocess_press_release("\n".join(cleaned_lines), template)
    return _postprocess_generic_markdown("\n".join(cleaned_lines))
