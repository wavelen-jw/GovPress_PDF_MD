from __future__ import annotations

from pathlib import Path
import re

import fitz

from .parser_rules import clean_line


CONTACT_LABELS = ("담당 부서", "담당부서", "책임자", "담당자")
PAGE_NUMBER_PATTERN = re.compile(r"^-\s*\d+\s*-$")
CONTACT_LABEL_PATTERN = re.compile(r"(담당\s*부서|담당부서|책임자|담당자)\s*")
PHONE_PATTERN = re.compile(r"\(\d{2,4}-\d{3,4}-\d{4}\)")
METADATA_TITLE_SPLIT_PATTERN = re.compile(
    r"^(?P<meta>.*?(?:조간|석간|\d{1,2}:\d{2}))\s+(?P<title>.+)$"
)
BRIEFING_DETAIL_PATTERN = re.compile(
    r"^(?:\(.+\)|.+\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?.*|.*조간.*|.*석간.*)$"
)
NOISE_PREFIXES = {"광"}
ORG_SUFFIXES = ("실", "과", "단", "센터", "담당관")
MINISTRY_SUFFIXES = ("부", "처", "청")
CONTACT_BLOCK_LABELS = set(CONTACT_LABELS)
POSITION_TOKENS = ("과 장", "사무관", "주무관", "연구관", "서기관", "기술서기관")
APPENDIX_PREFIXES = ("붙임", "붙 임", "별첨", "<참고", "< 참고")
NEW_LOGICAL_LINE_PREFIXES = (
    "보도자료",
    "보도시점",
    "담당 부서",
    "담당부서",
    "책임자",
    "담당자",
    "□",
    "○",
    "ㅇ",
    "- ",
    "* ",
    "<",
    "※",
    "◆",
    "◇",
    "▶",
    "▣",
)
HARD_BREAK_PREFIXES = (
    "보도자료",
    "보도시점",
    "담당 부서",
    "담당부서",
    "책임자",
    "담당자",
    "◆",
    "◇",
    "▶",
    "▣",
    "<",
    "* ",
)
TABLE_HEADER_SKIP_VALUES = {"", None}


def _normalize_contact_block(text: str) -> str:
    normalized = CONTACT_LABEL_PATTERN.sub(lambda match: f"{match.group(1)}: ", text)
    return re.sub(r"(:\s+)+", ": ", normalized).strip()


def _normalize_phone_spacing(text: str) -> str:
    return PHONE_PATTERN.sub(lambda match: f" {match.group(0)}", text).replace("  ", " ").strip()


def _split_metadata_tail(line: str) -> list[str]:
    if not line.startswith("("):
        return [line]

    match = METADATA_TITLE_SPLIT_PATTERN.match(line)
    if not match:
        return [line]

    meta = clean_line(match.group("meta"))
    title = clean_line(match.group("title"))
    if not title or title.startswith("("):
        return [line]
    return [meta, title]


def _looks_like_department_continuation(text: str) -> bool:
    normalized = text.strip()
    if any(char.isdigit() for char in normalized):
        return False
    if normalized in CONTACT_BLOCK_LABELS:
        return False
    if normalized in POSITION_TOKENS:
        return False
    if normalized.startswith("<") and normalized.endswith(">"):
        return False
    if normalized.endswith(ORG_SUFFIXES):
        return len(normalized) >= 4
    if normalized.endswith(MINISTRY_SUFFIXES):
        return len(normalized) >= 3
    if normalized.endswith("연구원"):
        return len(normalized) >= 4
    return False


def _parse_contact_entries(block_lines: list[str]) -> list[str]:
    tokens = [clean_line(line) for line in block_lines if clean_line(line) and clean_line(line) not in {"<총괄>"}]
    entries: list[str] = []
    current_department = ""
    index = 0

    while index < len(tokens):
        token = tokens[index]
        if token in {"담당 부서", "담당부서"}:
            dept_parts: list[str] = []
            index += 1
            while index < len(tokens):
                candidate = tokens[index]
                if candidate in {"담당 부서", "담당부서", "책임자", "담당자"}:
                    break
                if _looks_like_department_continuation(candidate) or not dept_parts:
                    dept_parts.append(candidate)
                    index += 1
                    continue
                break
            current_department = " ".join(dept_parts).strip()
            continue

        if _looks_like_department_continuation(token):
            dept_parts = [token]
            index += 1
            while index < len(tokens) and _looks_like_department_continuation(tokens[index]):
                dept_parts.append(tokens[index])
                index += 1
            current_department = " ".join(dept_parts).strip()
            continue

        if token in {"책임자", "담당자"}:
            role = token
            role_parts: list[str] = []
            dept_suffix: list[str] = []
            phone_seen = False
            index += 1
            while index < len(tokens):
                candidate = tokens[index]
                if candidate in {"담당 부서", "담당부서", "책임자", "담당자"}:
                    break
                if phone_seen and _looks_like_department_continuation(candidate):
                    if role == "책임자":
                        dept_suffix.append(candidate)
                        index += 1
                        continue
                    break
                if role == "책임자" and _looks_like_department_continuation(candidate) and phone_seen:
                    dept_suffix.append(candidate)
                    index += 1
                    continue
                role_parts.append(candidate)
                if PHONE_PATTERN.search(candidate):
                    phone_seen = True
                index += 1

            if dept_suffix:
                current_department = " ".join(part for part in (current_department, " ".join(dept_suffix).strip()) if part).strip()
            if current_department and role_parts:
                detail = _normalize_phone_spacing(" ".join(role_parts))
                entries.append(f"담당 부서: {current_department} {role}: {detail}")
            continue

        index += 1

    if entries:
        return entries

    return [_normalize_contact_block(" ".join(tokens))]


def _starts_new_logical_line(text: str) -> bool:
    return text.startswith(NEW_LOGICAL_LINE_PREFIXES)


def _starts_hard_break_line(text: str) -> bool:
    return text.startswith(HARD_BREAK_PREFIXES)


def _looks_like_briefing_detail(text: str) -> bool:
    return bool(BRIEFING_DETAIL_PATTERN.match(text))


def _ends_paragraph(text: str) -> bool:
    stripped = text.rstrip()
    if stripped.startswith("- ") and stripped.endswith("-"):
        return True
    return stripped.endswith((".", "!", "?", ".”", '."', "다.", "다”", "다.”", "다!"))


def _looks_like_noise(text: str) -> bool:
    return len(text) == 1 and text in NOISE_PREFIXES


def _is_table_row_text(text: str) -> bool:
    return text.count(" | ") >= 1


def _coalesce_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        text = clean_line(line)
        if not text:
            continue
        if not merged:
            merged.append(text)
            continue

        previous = merged[-1]
        if _is_table_row_text(previous) or _is_table_row_text(text):
            merged.append(text)
            continue
        if previous in {"보도자료", "보도시점"}:
            merged.append(text)
            continue
        if _looks_like_briefing_detail(previous):
            merged.append(text)
            continue
        if _starts_hard_break_line(previous):
            merged.append(text)
            continue
        if _starts_new_logical_line(text):
            merged.append(text)
            continue
        if _ends_paragraph(previous):
            merged.append(text)
            continue

        merged[-1] = f"{previous} {text}".strip()
    return merged


def _normalize_briefing_lines(lines: list[str]) -> list[str]:
    expanded: list[str] = []
    for line in lines:
        expanded.extend(_split_metadata_tail(line))

    if "보도시점" not in expanded:
        return expanded

    briefing_index = expanded.index("보도시점")
    metadata_before: list[str] = []
    move_start = briefing_index
    while move_start > 0:
        candidate = expanded[move_start - 1]
        if candidate == "보도자료":
            break
        if not _looks_like_briefing_detail(candidate):
            break
        metadata_before.insert(0, candidate)
        move_start -= 1

    if not metadata_before:
        normalized = expanded
    else:
        normalized = expanded[:move_start] + expanded[briefing_index:]
        insert_at = normalized.index("보도시점") + 1
        normalized = normalized[:insert_at] + metadata_before + normalized[insert_at:]

    merged_metadata: list[str] = []
    index = 0
    while index < len(normalized):
        token = normalized[index]
        if token == "보도시점":
            details: list[str] = []
            index += 1
            while index < len(normalized) and _looks_like_briefing_detail(normalized[index]):
                details.append(normalized[index])
                index += 1
            merged_metadata.append("보도시점")
            if details:
                merged_metadata.append(" ".join(details))
            continue
        merged_metadata.append(token)
        index += 1
    return merged_metadata


def _coalesce_block_lines(block_lines: list[str]) -> list[str]:
    merged: list[str] = []
    for block_line in block_lines:
        text = clean_line(block_line)
        if not text:
            continue
        if not merged:
            merged.append(text)
            continue
        previous = merged[-1]
        if _is_table_row_text(previous) or _is_table_row_text(text):
            merged.append(text)
            continue
        if _starts_hard_break_line(previous) or _starts_new_logical_line(text) or _ends_paragraph(previous):
            merged.append(text)
            continue
        merged[-1] = f"{previous} {text}".strip()
    return merged


def _is_contact_continuation_block(block_lines: list[str]) -> bool:
    if not block_lines:
        return False
    return all(
        line in CONTACT_BLOCK_LABELS
        or line in POSITION_TOKENS
        or line == "<총괄>"
        or PHONE_PATTERN.search(line)
        or _looks_like_department_continuation(line)
        or (not any(char.isdigit() for char in line) and len(line) <= 6)
        for line in block_lines
    )


def _normalize_table_cell(cell: object) -> str:
    if cell is None:
        return ""
    normalized = clean_line(str(cell).replace("\n", " "))
    normalized = re.sub(r"\s*§\s*", " • ", normalized).strip()
    return re.sub(r"\s{2,}", " ", normalized)


def _render_table_lines(table: fitz.table.Table) -> list[str]:
    rendered: list[str] = []
    for row in table.extract():
        cells = [_normalize_table_cell(cell) for cell in row]
        non_empty = [cell for cell in cells if cell not in TABLE_HEADER_SKIP_VALUES]
        if len(non_empty) < 2:
            continue
        rendered.append(" | ".join(non_empty))
    return rendered


def _is_contact_table(table: fitz.table.Table) -> bool:
    extracted = table.extract()
    return any(
        _normalize_table_cell(cell) in {"담당 부서", "담당부서"}
        for row in extracted
        for cell in row
    )


def _is_supported_content_table(table: fitz.table.Table) -> bool:
    return table.row_count >= 2 and table.col_count >= 2 and not _is_contact_table(table)


def _bbox_overlaps(left: tuple[float, float, float, float], right: tuple[float, float, float, float]) -> bool:
    left_x0, left_y0, left_x1, left_y1 = left
    right_x0, right_y0, right_x1, right_y1 = right
    return not (
        left_x1 <= right_x0
        or right_x1 <= left_x0
        or left_y1 <= right_y0
        or right_y1 <= left_y0
    )


def extract_text_from_pdf_with_pymupdf(pdf_path: str | Path) -> str:
    document = fitz.open(str(pdf_path))
    try:
        lines: list[str] = []
        stop_after_contact_appendix = False
        for page in document:
            if stop_after_contact_appendix:
                break
            contact_buffer: list[str] = []
            contact_seen = False

            def flush_contact_buffer() -> None:
                nonlocal contact_buffer, contact_seen
                if not contact_buffer:
                    return
                lines.extend(_parse_contact_entries(contact_buffer))
                contact_buffer = []
                contact_seen = True

            table_blocks: list[tuple[float, float, tuple[float, float, float, float], list[str]]] = []
            try:
                found_tables = page.find_tables()
                tables = found_tables.tables if found_tables else []
            except Exception:
                tables = []

            for table in tables:
                if not _is_supported_content_table(table):
                    continue
                table_lines = _render_table_lines(table)
                if not table_lines:
                    continue
                bbox = tuple(float(value) for value in table.bbox)
                table_blocks.append((bbox[1], bbox[0], bbox, table_lines))

            text_blocks: list[tuple[float, float, tuple[float, float, float, float], list[str]]] = []
            for block in page.get_text("dict").get("blocks", []):
                if block.get("type") != 0:
                    continue

                block_lines: list[str] = []
                for line in block.get("lines", []):
                    text = clean_line(
                        "".join(span.get("text", "") for span in line.get("spans", []))
                    )
                    if text:
                        block_lines.append(text)

                if block_lines:
                    bbox = tuple(float(value) for value in block.get("bbox", (0, 0, 0, 0)))
                    text_blocks.append((bbox[1], bbox[0], bbox, block_lines))

            content_blocks = sorted(
                [("text", *item) for item in text_blocks] + [("table", *item) for item in table_blocks],
                key=lambda item: (item[1], item[2]),
            )

            for block_type, _, _, bbox, block_lines in content_blocks:
                if block_type == "text" and any(
                    _bbox_overlaps(bbox, table_bbox) for _, _, table_bbox, _ in table_blocks
                ):
                    continue
                if len(block_lines) == 1 and PAGE_NUMBER_PATTERN.match(block_lines[0]):
                    continue
                if len(block_lines) == 1 and _looks_like_noise(block_lines[0]):
                    continue
                if contact_seen and block_lines[0].startswith(APPENDIX_PREFIXES):
                    flush_contact_buffer()
                    stop_after_contact_appendix = True
                    break

                if block_lines[0] == "보도시점" and len(block_lines) > 1:
                    flush_contact_buffer()
                    lines.append("보도시점")
                    metadata_lines = []
                    for detail_line in block_lines[1:]:
                        metadata_lines.extend(_split_metadata_tail(detail_line))
                    lines.extend(metadata_lines)
                    continue

                if any(label in block_lines for label in CONTACT_BLOCK_LABELS) or (
                    contact_buffer and _is_contact_continuation_block(block_lines)
                ):
                    contact_buffer.extend(block_lines)
                    continue

                flush_contact_buffer()
                expanded_lines: list[str] = []
                for block_line in _coalesce_block_lines(block_lines):
                    expanded_lines.extend(_split_metadata_tail(block_line))
                for expanded_line in expanded_lines:
                    joined = expanded_line
                    if any(label in joined for label in CONTACT_LABELS):
                        joined = _normalize_contact_block(joined)
                    lines.append(joined)

            flush_contact_buffer()

        return "\n".join(_normalize_briefing_lines(_coalesce_lines(lines)))
    finally:
        document.close()
