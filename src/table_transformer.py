from __future__ import annotations

import re


_CIRCLED_NUMBER_MAP = {
    "①": "1.",
    "②": "2.",
    "③": "3.",
    "④": "4.",
    "⑤": "5.",
    "⑥": "6.",
    "⑦": "7.",
    "⑧": "8.",
    "⑨": "9.",
    "⑩": "10.",
    "⑪": "11.",
    "⑫": "12.",
    "⑬": "13.",
    "⑭": "14.",
    "⑮": "15.",
    "⑯": "16.",
    "⑰": "17.",
    "⑱": "18.",
    "⑲": "19.",
    "⑳": "20.",
}


def split_checkmark_payload(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\s*√\s*", text) if part.strip()]
    return [f"√ {part}" for part in parts]


def expand_reference_compare_payload(line: str) -> list[str] | None:
    if "현재는(As-Is)" not in line or "앞으로는(To-Be)" not in line:
        return None
    labels = ["(관리대상)", "(정보수집)", "(품질관리)", "(운영방식)"]
    if not all(label in line for label in labels):
        return None

    parts = [part.strip() for part in line.split("<br>") if part.strip()]
    bullets = [part for part in parts if not any(token in part for token in ("현재는(As-Is)", "앞으로는(To-Be)", "(관리대상)"))]
    payload = next((part for part in parts if "현재는(As-Is)" in part and "앞으로는(To-Be)" in part), line)

    compact = payload.replace(" ", "")
    if "현재는(As-Is)" not in compact or "앞으로는(To-Be)" not in compact:
        return None
    left_title = "현재는(As-Is)"
    right_title = "앞으로는(To-Be)"

    rows: list[tuple[str, str, str, str]] = []
    for pos, label in enumerate(labels):
        start = compact.find(label)
        if start == -1:
            return None
        start += len(label)
        next_positions = [compact.find(next_label, start) for next_label in labels[pos + 1 :] if compact.find(next_label, start) != -1]
        end = min(next_positions) if next_positions else len(compact)
        segment = compact[start:end]
        if segment.startswith(left_title):
            segment = segment[len(left_title):]
        if segment.startswith(right_title):
            segment = segment[len(right_title):]
        values = split_checkmark_payload(segment)
        if len(values) != 2:
            return None
        rows.append((label, values[0], "➜", values[1]))

    rendered: list[str] = []
    for bullet in bullets:
        bullet = re.sub(r"^[-○ㅇ]\s+", "", bullet)
        rendered.append(f"> - {bullet}")
    if bullets:
        rendered.append("")
    rendered.append(f"> | | {left_title} | | {right_title} |")
    rendered.append("> | --- | --- | --- | --- |")
    for label, left, arrow, right in rows:
        rendered.append(f"> | {label} | {left} | {arrow} | {right} |")
    return rendered


def collect_single_column_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    index = start
    while index < len(lines) and not lines[index].strip():
        index += 1

    rows: list[str] = []
    saw_table = False
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            if saw_table:
                break
            index += 1
            continue
        if not stripped.startswith("|"):
            break
        saw_table = True
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 1:
            return None, start
        cell = cells[0]
        if cell and not set(cell) <= {"-", ":"}:
            rows.append(cell)
        index += 1
    return (rows or None), index


def rewrite_labeled_arrow_compare_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    heading_line = lines[start].strip()
    if not re.fullmatch(r">?\s*<\s*.+\s*>", heading_line):
        return None, start

    heading = heading_line.lstrip(">").strip()
    index = start + 1
    rows: list[tuple[str, str, str]] = []

    while index < len(lines):
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            break

        label_line = lines[index].strip()
        m = re.fullmatch(r"\|\s*(.+?)\s*\|\s*\|", label_line)
        if not m:
            break
        label = m.group(1).replace("<br>", " ").strip()
        index += 1

        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            return None, start
        left_line = lines[index].strip()
        left_match = re.fullmatch(r"(.+?)\s*\|\s*➜\s*\|", left_line)
        if not left_match:
            return None, start
        left = left_match.group(1).strip()
        index += 1

        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            return None, start
        right_line = lines[index].strip()
        if right_line.startswith("|"):
            return None, start
        right = right_line.strip()
        index += 1

        rows.append((label, left, right))

        while index < len(lines) and not lines[index].strip():
            index += 1
        if index < len(lines) and re.fullmatch(r"\|\s*[-:| ]+\|", lines[index].strip()):
            index += 1

    if len(rows) < 2:
        return None, start

    rendered = [f"##### {heading}", ""]
    first_label, first_left, first_right = rows[0]
    rendered.append(f"| {first_label} | {first_left} | ➜ | {first_right} |")
    rendered.append("| --- | --- | --- | --- |")
    for label, left, right in rows[1:]:
        rendered.append(f"| {label} | {left} | ➜ | {right} |")
    return rendered, index


def rewrite_split_compare_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    heading_line = lines[start].strip()
    if not re.fullmatch(r">?\s*<\s*.+\s*>", heading_line):
        return None, start

    heading = heading_line.lstrip(">").strip()
    index = start + 1
    labels: list[str] = []
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            if labels:
                index += 1
                break
            index += 1
            continue
        if stripped.startswith("|") or stripped == "➜":
            break
        labels.append(stripped)
        index += 1

    table_rows, next_index = collect_single_column_table(lines, index)
    if not labels or not table_rows:
        return None, start

    index = next_index
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines) or lines[index].strip() != "➜":
        return None, start
    index += 1

    right_rows, next_index = collect_single_column_table(lines, index)
    if right_rows:
        left_rows = table_rows
        if len(labels) != len(left_rows) or len(labels) != len(right_rows):
            return None, start
    else:
        if len(table_rows) != len(labels) * 2:
            return None, start
        left_rows = table_rows[: len(labels)]
        right_rows = table_rows[len(labels) :]
        next_index = index

    rendered = [f"##### {heading}", ""]
    rendered.append(f"| {labels[0]} | {left_rows[0]} | ➜ | {right_rows[0]} |")
    rendered.append("| --- | --- | --- | --- |")
    for label, left, right in zip(labels[1:], left_rows[1:], right_rows[1:]):
        rendered.append(f"| {label} | {left} | ➜ | {right} |")
    return rendered, next_index


def rewrite_split_reference_compare_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    if lines[start].strip() != "| 현재는(As-Is) |":
        return None, start

    if start + 4 >= len(lines):
        return None, start
    if lines[start + 1].strip() != "| --- |":
        return None, start
    left_payload = lines[start + 2].strip()
    if not left_payload.startswith("|"):
        return None, start
    if lines[start + 3].strip() != "| 앞으로는(To-Be) |":
        return None, start
    if lines[start + 4].strip() != "| --- |":
        return None, start
    if start + 5 >= len(lines):
        return None, start
    right_payload = lines[start + 5].strip()
    if not right_payload.startswith("|"):
        return None, start

    left_cells = [cell.strip() for cell in left_payload.strip("|").split("|")]
    right_cells = [cell.strip() for cell in right_payload.strip("|").split("|")]
    if len(left_cells) != 1 or len(right_cells) != 1:
        return None, start

    left_items = split_checkmark_payload(left_cells[0])
    right_items = split_checkmark_payload(right_cells[0])

    index = start + 6
    while index < len(lines) and not lines[index].strip():
        index += 1

    labels: list[str] = []
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            break
        if not re.fullmatch(r"\(.+\)", stripped):
            break
        labels.append(stripped)
        index += 1

    if not labels or len(labels) != len(left_items) or len(labels) != len(right_items):
        return None, start

    rendered = [
        "> | | 현재는(As-Is) | | 앞으로는(To-Be) |",
        "> | --- | --- | --- | --- |",
    ]
    for label, left, right in zip(labels, left_items, right_items):
        rendered.append(f"> | {label} | {left} | ➜ | {right} |")
    return rendered, index


def rewrite_reference_compare_bullets(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    if not lines[start].strip().startswith("- "):
        return None, start
    index = start
    bullets: list[str] = []
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            index += 1
            break
        if not stripped.startswith("- "):
            break
        bullets.append(stripped[2:].strip())
        index += 1
    if not bullets:
        return None, start

    lookahead = index
    while lookahead < len(lines) and not lines[lookahead].strip():
        lookahead += 1
    if lookahead >= len(lines):
        return None, start
    marker = lines[lookahead].strip()
    if marker not in {"| 현재는(As-Is) |", "> | | 현재는(As-Is) |"}:
        return None, start

    return ([f"> - {bullet}" for bullet in bullets] + [""]), index


def rewrite_compact_year_matrix(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    stripped = lines[start].strip()
    plain = stripped[2:].strip() if stripped.startswith("> ") else stripped.lstrip(">").strip()
    if "최근 5개년 누적" not in plain or "구 분2018년2019년개수예산개수예산" not in plain:
        return None, start

    matrix = plain.replace("최근 5개년 누적 (단위 : 개, 억원)", "").strip()
    prefix_pattern = r"^구\s*분2018년2019년개수예산개수예산"
    if not re.match(prefix_pattern, matrix):
        return None, start
    payload = re.sub(prefix_pattern, "", matrix)
    labels = ["정보화사업", "정보시스템", "하드웨어", "소프트웨어"]
    value_pattern = re.compile(r"\d{1,3},\d{3}(?:[▲▼])?")
    rows: list[tuple[str, str, str, str, str]] = []
    for pos, label in enumerate(labels):
        if not payload.startswith(label):
            return None, start
        payload = payload[len(label):]
        next_labels = labels[pos + 1 :]
        next_index = min(
            [payload.find(next_label) for next_label in next_labels if payload.find(next_label) != -1] or [len(payload)]
        )
        segment = payload[:next_index]
        values = value_pattern.findall(segment)
        if len(values) != 4:
            return None, start
        rows.append((label, values[0], values[1], values[2], values[3]))
        payload = payload[next_index:]

    prefix = "> " if stripped.startswith(">") else ""
    rendered = [
        f"{prefix}최근 5개년 누적 (단위 : 개, 억원)",
        "",
        f"{prefix}| 구 분 | 2018년 | | 2019년 | |",
        f"{prefix}| --- | --- | --- | --- | --- |",
        f"{prefix}| 구 분 | 개수 | 예산 | 개수 | 예산 |",
    ]
    for label, c1, b1, c2, b2 in rows:
        rendered.append(f"{prefix}| {label} | {c1} | {b1} | {c2} | {b2} |")
    return rendered, start + 1


def normalize_table_row_trailing_empty_cells(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            normalized.append(line)
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) >= 5 and cells[-1] == "":
            cells = cells[:-1]
            indent = line[: len(line) - len(line.lstrip())]
            normalized.append(f"{indent}| " + " | ".join(cells) + " |")
            continue
        normalized.append(line)
    return normalized


def rewrite_role_assignment_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    if start + 1 >= len(lines):
        return None, start
    header = lines[start].strip()
    separator = lines[start + 1].strip()
    if header != "| 구 분 | 구성 및 역할 |":
        return None, start
    if not re.fullmatch(r"\|\s*[-: ]+\|\s*[-: ]+\|", separator):
        return None, start

    def _is_structure_boundary(text: str) -> bool:
        stripped = text.strip()
        if not stripped:
            return False
        if stripped.startswith(("## ", "### ", "##### ", "|", "> ")):
            return True
        if re.match(r"^(?:[ⅠⅡⅢⅣⅤ]\.|\d+\.|□\s|○\s|◇\s|붙임\d+|참고\d+|별첨\d+)", stripped):
            return True
        return False

    def _finalize_row(row: str) -> tuple[str, str] | None:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        if len(cells) != 2 or cells[0] == "구 분":
            return None
        return cells[0], cells[1]

    index = start + 2
    rows: list[tuple[str, str]] = []
    current_row: str | None = None
    while index < len(lines):
        stripped = lines[index].strip()
        if not stripped:
            if current_row:
                lookahead = index + 1
                while lookahead < len(lines) and not lines[lookahead].strip():
                    lookahead += 1
                if lookahead < len(lines) and not _is_structure_boundary(lines[lookahead]):
                    index += 1
                    continue
                finalized = _finalize_row(current_row)
                if finalized:
                    rows.append(finalized)
                current_row = None
            break
        if stripped.startswith("|"):
            if current_row:
                finalized = _finalize_row(current_row)
                if finalized:
                    rows.append(finalized)
            current_row = stripped
            index += 1
            continue
        if current_row:
            if _is_structure_boundary(stripped):
                finalized = _finalize_row(current_row)
                if finalized:
                    rows.append(finalized)
                current_row = None
                break
            current_row = f"{current_row} {stripped}"
            index += 1
            continue
        break

    if current_row:
        finalized = _finalize_row(current_row)
        if finalized:
            rows.append(finalized)

    if len(rows) < 2:
        return None, start

    merged_rows: list[tuple[str, str]] = []
    for title, payload in rows:
        clean_title = re.sub(r"\s+", " ", title.replace("<br>", " ")).strip()
        if clean_title in {"•", "·", "▪", "◦", "-", "※"} and merged_rows:
            prev_title, prev_payload = merged_rows[-1]
            merged_rows[-1] = (prev_title, f"{prev_payload} {payload}".strip())
            continue
        merged_rows.append((title, payload))

    def _normalize_payload(payload: str) -> tuple[list[str], list[str]]:
        clean_payload = payload.replace("ž", "•").replace("", "•").replace("<br>", "\n")
        clean_payload = clean_payload.replace("\r", "\n")
        parts = [re.sub(r"\s+", " ", part).strip(" |") for part in clean_payload.split("\n") if part.strip()]
        bullets: list[str] = []
        notes: list[str] = []
        for part in parts:
            part = part.lstrip("•·▪◦- ").strip()
            if not part:
                continue
            if part.startswith("※"):
                note = part[1:].strip()
                if note:
                    notes.append(note)
                continue
            if bullets and not part.startswith(("(", "•", "▪", "◦")):
                bullets[-1] = f"{bullets[-1]} {part}".strip()
                continue
            bullets.append(part)

        normalized_bullets: list[str] = []
        for bullet in bullets:
            if any(marker in bullet for marker in ("(구성)", "(역할)")):
                chunks = [chunk.strip() for chunk in re.split(r"(?=\((?:구성|역할)\))", bullet) if chunk.strip()]
                normalized_bullets.extend(chunks)
            else:
                normalized_bullets.append(bullet)
        return normalized_bullets, notes

    rendered: list[str] = []
    for title, payload in merged_rows:
        clean_title = re.sub(r"\s+", " ", title.replace("<br>", " ")).strip()
        if clean_title in {"•", "·", "▪", "◦", "-", "※"}:
            continue
        rendered.append(f"- {clean_title}")
        bullets, notes = _normalize_payload(payload)
        for bullet in bullets:
            rendered.append(f"  - {bullet}")
        for note in notes:
            rendered.append(f"  > {note}")
        rendered.append("")
    if rendered and rendered[-1] == "":
        rendered.pop()
    return rendered, index


def _normalize_strategy_task_payload(payload: str) -> list[str]:
    text = payload.replace("<br>", "\n")
    for src, dst in _CIRCLED_NUMBER_MAP.items():
        text = text.replace(src, f"\n{dst} ")
    text = re.sub(r"(?<!\d)(\d{1,2})\.\s*", lambda m: f"\n{m.group(1)}. ", text)
    lines = [re.sub(r"\s+", " ", part).strip() for part in text.splitlines()]
    return [line for line in lines if line and line != "추진과제"]


def rewrite_grouped_strategy_matrix(lines: list[str], start: int) -> tuple[list[str] | None, int]:
    stripped = lines[start].strip()
    if stripped not in {"- 추진분야 및 과제", "### 추진분야 및 과제"}:
        return None, start

    index = start + 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines) or not lines[index].strip().startswith("|"):
        return None, start

    table_lines: list[str] = []
    current_row: str | None = None
    while index < len(lines):
        current = lines[index].strip()
        if not current:
            lookahead = index + 1
            while lookahead < len(lines) and not lines[lookahead].strip():
                lookahead += 1
            if lookahead < len(lines) and lines[lookahead].strip().startswith("|"):
                index += 1
                continue
            if current_row:
                table_lines.append(current_row)
                current_row = None
            if table_lines:
                index = lookahead
                break
            index += 1
            continue
        if current.startswith("|"):
            if current_row:
                table_lines.append(current_row)
            current_row = current
            index += 1
            continue
        if current_row and (
            current.startswith(("분야", "대국민", "추진과제"))
            or re.match(r"^(?:\d+\.\s+|[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳])", current)
        ):
            current_row = f"{current_row} {current}"
            index += 1
            continue
        if current_row:
            table_lines.append(current_row)
            current_row = None
        if not current.startswith("|"):
            break
        index += 1

    if current_row:
        table_lines.append(current_row)

    if len(table_lines) < 3:
        return None, start

    detailed_titles: list[str] = []
    heading_re = re.compile(r"^###\s+\d+\.\s+(.+)$")
    lookahead = index
    while lookahead < len(lines) and len(detailed_titles) < 6:
        stripped = lines[lookahead].strip()
        match = heading_re.match(stripped)
        if not match:
            lookahead += 1
            continue
        next_nonempty = lookahead + 1
        while next_nonempty < len(lines) and not lines[next_nonempty].strip():
            next_nonempty += 1
        if next_nonempty < len(lines):
            follower = lines[next_nonempty].strip()
            if follower and not follower.startswith(("-", ">", "<그림>", "|", "###", "##")):
                detailed_titles.append(match.group(1).strip())
        lookahead += 1
    if len(detailed_titles) >= 2:
        rendered = ["### 추진분야 및 과제", ""]
        for title in detailed_titles:
            rendered.append(f"- {title}")
        return rendered, index

    parsed_rows: list[list[str]] = []
    for row in table_lines:
        if set(row.replace("|", "").replace("-", "").replace(":", "").replace(" ", "").replace("\n", "")) == set():
            continue
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        parsed_rows.append(cells)
    if len(parsed_rows) < 2:
        return None, start

    group_titles: list[str] = []
    for row in parsed_rows:
        candidates: list[str] = []
        for cell in row:
            cleaned = re.sub(r"\s+", " ", cell.replace("\n", " ")).strip()
            if not cleaned or "추진" in cleaned or re.fullmatch(r"열\s*\d+", cleaned):
                continue
            candidates.append(cleaned)
        if len(candidates) >= 2:
            group_titles = candidates
            break
    if len(group_titles) < 2:
        return None, start

    groups: list[tuple[str, list[str]]] = []
    group_cursor = 0
    for row in parsed_rows[1:]:
        candidates = []
        for cell in row:
            cleaned = re.sub(r"\s+", " ", cell.replace("\n", " ")).strip()
            if not cleaned or cleaned == "추진과제":
                continue
            if re.fullmatch(r"\d+|열 \d+|추진 분야", cleaned):
                continue
            candidates.append(cell)
        if not candidates:
            continue
        payload_cell = max(candidates, key=lambda value: len(value.strip()))
        tasks = _normalize_strategy_task_payload(payload_cell)
        if not tasks:
            continue
        if len(tasks) == 1 and not re.match(r"^\d+\.\s+", tasks[0]):
            continue
        if group_cursor >= len(group_titles):
            break
        groups.append((group_titles[group_cursor], tasks))
        group_cursor += 1

    if len(groups) < 2:
        return None, start

    if groups and len(groups[0][1]) == 1:
        first_task = re.sub(r"\s+", " ", groups[0][1][0]).strip()
        first_title = re.sub(r"\s+", " ", groups[0][0]).strip()
        if first_task == first_title:
            groups = groups[1:]

    if all(re.fullmatch(r"열\s*\d+", title) for title, _ in groups):
        detailed_titles = detailed_titles[: len(groups)]
        if len(detailed_titles) == len(groups):
            groups = [(detailed_titles[idx], tasks) for idx, (_, tasks) in enumerate(groups)]

    rendered = ["### 추진분야 및 과제", ""]
    for title, tasks in groups:
        rendered.append(f"- {title}")
        for task in tasks:
            if re.match(r"^\d+\.\s+", task):
                rendered.append(f"  - {task}")
            else:
                rendered.append(f"  - {task}")
        rendered.append("")
    if rendered[-1] == "":
        rendered.pop()
    return rendered, index
