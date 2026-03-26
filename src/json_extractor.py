from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .parser_rules import clean_line


IGNORED_NODE_TYPES = {"image", "footer"}
CONTACT_LABELS = {"담당 부서", "담당부서", "책임자", "담당자"}
TABLE_LIST_MARKERS = ("§", "•", "‧")


def _collect_text(node: dict[str, Any]) -> list[str]:
    node_type = node.get("type")
    if node_type in IGNORED_NODE_TYPES:
        return []

    if node_type in {"paragraph", "heading", "caption"}:
        content = clean_line(str(node.get("content") or ""))
        return [content] if content else []

    if node_type == "list":
        lines: list[str] = []
        for item in node.get("list items", []):
            lines.extend(_collect_text(item))
        return lines

    if node_type == "list item":
        lines: list[str] = []
        content = clean_line(str(node.get("content") or ""))
        if content:
            lines.append(content)
        for child in node.get("kids", []):
            lines.extend(_collect_text(child))
        return lines

    if node_type == "table":
        return _table_to_lines(node)

    lines: list[str] = []
    for child in node.get("kids", []):
        lines.extend(_collect_text(child))
    return lines


def _collect_cell_text(cell: dict[str, Any]) -> str:
    parts: list[str] = []
    for child in cell.get("kids", []):
        parts.extend(_collect_text(child))
    return clean_line(" ".join(parts))


def _collect_single_cell_quote_lines(node: dict[str, Any]) -> list[str]:
    node_type = node.get("type")
    if node_type in IGNORED_NODE_TYPES:
        return []

    if node_type == "heading":
        content = clean_line(str(node.get("content") or ""))
        if not content:
            return []
        if content.startswith("<") and content.endswith(">"):
            return [f"#### {content}"]
        return [f"## {content}"]

    if node_type in {"paragraph", "caption"}:
        content = clean_line(str(node.get("content") or ""))
        return [content] if content else []

    if node_type == "list":
        lines: list[str] = []
        for item in node.get("list items", []):
            lines.extend(_collect_single_cell_quote_lines(item))
        return lines

    if node_type == "list item":
        lines: list[str] = []
        content = clean_line(str(node.get("content") or ""))
        if content:
            lines.append(content)
        for child in node.get("kids", []):
            lines.extend(_collect_single_cell_quote_lines(child))
        return lines

    lines: list[str] = []
    for child in node.get("kids", []):
        lines.extend(_collect_single_cell_quote_lines(child))
    return lines


def _table_row_to_line(row: dict[str, Any]) -> str:
    cells = [_collect_cell_text(cell) for cell in row.get("cells", [])]
    cells = [cell for cell in cells if cell]
    if not cells:
        return ""

    if len(cells) % 2 == 0 and any(cell in CONTACT_LABELS for cell in cells[::2]):
        pairs = [f"{cells[index]}: {cells[index + 1]}" for index in range(0, len(cells), 2)]
        return clean_line(" ".join(pairs))

    return clean_line(" | ".join(cells))


def _table_to_lines(table: dict[str, Any]) -> list[str]:
    rows = table.get("rows", [])
    if _is_contact_table(rows):
        return _contact_table_to_lines(rows)
    if _is_single_cell_table(rows):
        return _single_cell_table_to_lines(rows)
    if _is_simple_table(rows):
        return _simple_table_to_lines(rows)
    return _complex_table_to_lines(rows)


def _sorted_row_cells(row: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(row.get("cells", []), key=lambda cell: int(cell.get("column number", 0)))


def _is_single_cell_table(rows: list[dict[str, Any]]) -> bool:
    return len(rows) == 1 and len(_sorted_row_cells(rows[0])) == 1


def _single_cell_table_to_lines(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []

    cell = _sorted_row_cells(rows[0])[0]
    parts: list[str] = []
    for child in cell.get("kids", []):
        parts.extend(_collect_single_cell_quote_lines(child))
    lines = [clean_line(part) for part in parts if clean_line(part)]
    if not lines:
        text = _collect_cell_text(cell)
        lines = [text] if text else []
    return [f"> {line}" if line else ">" for line in lines]


def _is_simple_table(rows: list[dict[str, Any]]) -> bool:
    if not rows:
        return False

    expected_columns: int | None = None
    for row in rows:
        cells = _sorted_row_cells(row)
        if len(cells) < 2:
            return False
        for cell in cells:
            if int(cell.get("row span", 1)) != 1 or int(cell.get("column span", 1)) != 1:
                return False
        column_count = len(cells)
        if expected_columns is None:
            expected_columns = column_count
        elif expected_columns != column_count:
            return False
    return True


def _escape_markdown_table_cell(text: str) -> str:
    return clean_line(text).replace("|", "\\|")


def _split_inline_table_items(text: str) -> list[str]:
    normalized = clean_line(text)
    if not normalized:
        return []

    items: list[str] = []
    current = ""
    for token in normalized.split():
        if token and token[0] in TABLE_LIST_MARKERS:
            if current:
                items.append(current.strip())
            current = token
        else:
            current = f"{current} {token}".strip() if current else token
    if current:
        items.append(current.strip())
    return items


def _format_table_cell_text(text: str) -> str:
    items = _split_inline_table_items(text)
    if len(items) >= 2:
        return "<br>".join(item.replace("§", "•", 1) if item.startswith("§") else item for item in items)
    normalized = clean_line(text)
    if normalized.startswith("§"):
        return normalized.replace("§", "•", 1)
    return normalized


def _simple_table_to_lines(rows: list[dict[str, Any]]) -> list[str]:
    matrix: list[list[str]] = []
    for row in rows:
        matrix.append(
            [
                _escape_markdown_table_cell(_format_table_cell_text(_collect_cell_text(cell)))
                for cell in _sorted_row_cells(row)
            ]
        )

    if not matrix:
        return []

    header = matrix[0]
    separator = ["---"] * len(header)
    lines = [
        f"| {' | '.join(header)} |",
        f"| {' | '.join(separator)} |",
    ]
    for row in matrix[1:]:
        lines.append(f"| {' | '.join(row)} |")
    return lines


def _complex_table_to_lines(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []

    max_columns = max(
        (
            int(cell.get("column number", 0)) + int(cell.get("column span", 1)) - 1
            for row in rows
            for cell in row.get("cells", [])
        ),
        default=0,
    )
    if max_columns <= 0:
        return []

    active_spans: dict[int, tuple[int, str]] = {}
    matrix: list[list[str]] = []
    for row in rows:
        current_row = [""] * max_columns
        next_active_spans: dict[int, tuple[int, str]] = {}

        for column_index, (remaining_rows, value) in active_spans.items():
            current_row[column_index] = value
            if remaining_rows > 1:
                next_active_spans[column_index] = (remaining_rows - 1, value)

        for cell in _sorted_row_cells(row):
            start_column = max(int(cell.get("column number", 1)) - 1, 0)
            row_span = max(int(cell.get("row span", 1)), 1)
            column_span = max(int(cell.get("column span", 1)), 1)
            formatted = _escape_markdown_table_cell(_format_table_cell_text(_collect_cell_text(cell)))

            for offset in range(column_span):
                column_index = start_column + offset
                if column_index >= max_columns:
                    break
                value = formatted if offset == 0 else ""
                current_row[column_index] = value
                if row_span > 1:
                    next_active_spans[column_index] = (row_span - 1, value)

        matrix.append(current_row)
        active_spans = next_active_spans

    if not matrix:
        return []

    header = matrix[0]
    separator = ["---"] * len(header)
    lines = [
        f"| {' | '.join(header)} |",
        f"| {' | '.join(separator)} |",
    ]
    for row in matrix[1:]:
        lines.append(f"| {' | '.join(row)} |")
    return lines


def _is_contact_table(rows: list[dict[str, Any]]) -> bool:
    for row in rows:
        for cell in row.get("cells", []):
            cell_text = _collect_cell_text(cell)
            if cell_text in CONTACT_LABELS:
                return True
    return False


def _contact_table_to_lines(rows: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    current_department = ""
    department_label = "담당 부서"

    for row in rows:
        column_map: dict[int, str] = {}
        for cell in row.get("cells", []):
            column = int(cell.get("column number", 0))
            text = _collect_cell_text(cell)
            if text:
                column_map[column] = text

        if 1 in column_map and column_map[1] in CONTACT_LABELS:
            department_label = column_map[1]
        if 2 in column_map:
            current_department = column_map[2]

        role = column_map.get(3, "")
        person = column_map.get(4, "")
        if current_department and role and person:
            lines.append(clean_line(f"{department_label}: {current_department} {role}: {person}"))

    return lines


def extract_text_from_json(json_path: str | Path) -> str:
    data = json.loads(Path(json_path).read_text(encoding="utf-8"))
    lines: list[str] = []
    for node in data.get("kids", []):
        lines.extend(_collect_text(node))
    return "\n".join(line for line in lines if line).strip() + "\n"
