"""HWPX -> Markdown converter."""
from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .hwpx_postprocessor import HwpxParagraph, postprocess_hwpx

TableMode = Literal["text", "html"]


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _iter_local(elem: ET.Element, name: str):
    for node in elem.iter():
        if _local_name(node.tag) == name:
            yield node


def _direct_children_local(elem: ET.Element, name: str):
    for child in elem:
        if _local_name(child.tag) == name:
            yield child


def _find_local(elem: ET.Element, name: str) -> ET.Element | None:
    for node in elem:
        if _local_name(node.tag) == name:
            return node
    return None


def _get_attr(elem: ET.Element, *names: str) -> str:
    for name in names:
        if name in elem.attrib:
            return elem.attrib[name]
    lowered = {key.lower(): value for key, value in elem.attrib.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value is not None:
            return value
    return ""


def _collect_run_text(p_elem: ET.Element) -> str:
    parts: list[str] = []
    for run in (child for child in p_elem if _local_name(child.tag) == "run"):
        for text_node in _iter_local(run, "t"):
            if text_node.text:
                parts.append(text_node.text)
    return "".join(parts).strip()


@dataclass
class TableCell:
    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    paragraphs: list[str] = field(default_factory=list)
    nested_tables: list["Table"] = field(default_factory=list)


@dataclass
class Table:
    rows: int
    cols: int
    cells: list[TableCell]
    has_rowspan: bool = False
    has_colspan: bool = False
    is_drawing_table: bool = False


_COLSPAN_ATTRS = (
    "colSpan",
    "colspan",
    "numMergedCols",
    "columnSpan",
    "mergedColCount",
    "spanCols",
    "col_span",
)
_ROWSPAN_ATTRS = (
    "rowSpan",
    "rowspan",
    "numMergedRows",
    "rowCount",
    "mergedRowCount",
    "spanRows",
    "row_span",
)


def _read_span(elem: ET.Element, candidates: tuple[str, ...]) -> int:
    value = _get_attr(elem, *candidates)
    if value:
        try:
            return max(int(value), 1)
        except ValueError:
            pass
    for child in elem:
        child_value = _get_attr(child, *candidates)
        if child_value:
            try:
                return max(int(child_value), 1)
            except ValueError:
                pass
    return 1


def _is_drawing_table(cells: list[TableCell], rows: int, cols: int) -> bool:
    if rows < 3 or not cells:
        return False
    empty = sum(1 for cell in cells if not any(p.strip() for p in cell.paragraphs) and not cell.nested_tables)
    return (empty / len(cells)) >= 0.80


def _collect_cell_paragraphs(tc: ET.Element) -> list[str]:
    parts: list[str] = []
    for sub_list in _direct_children_local(tc, "subList"):
        for p in _direct_children_local(sub_list, "p"):
            text = _collect_run_text(p).strip()
            if text:
                parts.append(text)
    if not parts:
        for p in _direct_children_local(tc, "p"):
            text = _collect_run_text(p).strip()
            if text:
                parts.append(text)
    return parts


def _collect_table_data(tbl_elem: ET.Element) -> Table:
    cells: list[TableCell] = []
    occupied: set[tuple[int, int]] = set()
    max_col = 0

    for tr_idx, tr in enumerate(list(_direct_children_local(tbl_elem, "tr"))):
        col_cursor = 0
        for tc in _direct_children_local(tr, "tc"):
            while (tr_idx, col_cursor) in occupied:
                col_cursor += 1

            colspan = _read_span(tc, _COLSPAN_ATTRS)
            rowspan = _read_span(tc, _ROWSPAN_ATTRS)
            paragraphs = _collect_cell_paragraphs(tc)

            nested: list[Table] = []
            for sub_list in _direct_children_local(tc, "subList"):
                for p in _direct_children_local(sub_list, "p"):
                    for ctrl in _direct_children_local(p, "ctrl"):
                        for sub_tbl in _iter_local(ctrl, "tbl"):
                            nested.append(_collect_table_data(sub_tbl))
            for ctrl in _direct_children_local(tc, "ctrl"):
                for sub_tbl in _iter_local(ctrl, "tbl"):
                    nested.append(_collect_table_data(sub_tbl))
            for sub_tbl in _direct_children_local(tc, "tbl"):
                nested.append(_collect_table_data(sub_tbl))

            cells.append(
                TableCell(
                    row=tr_idx,
                    col=col_cursor,
                    rowspan=rowspan,
                    colspan=colspan,
                    paragraphs=paragraphs,
                    nested_tables=nested,
                )
            )

            for dr in range(rowspan):
                for dc in range(colspan):
                    if dr > 0 or dc > 0:
                        occupied.add((tr_idx + dr, col_cursor + dc))

            end_col = col_cursor + colspan
            if end_col > max_col:
                max_col = end_col
            col_cursor = end_col

    row_count = sum(1 for _ in _direct_children_local(tbl_elem, "tr"))
    has_colspan = any(cell.colspan > 1 for cell in cells)
    has_rowspan = any(cell.rowspan > 1 for cell in cells)
    return Table(
        rows=row_count,
        cols=max_col,
        cells=cells,
        has_rowspan=has_rowspan,
        has_colspan=has_colspan,
        is_drawing_table=_is_drawing_table(cells, row_count, max_col),
    )


def _escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cell_text(cell: TableCell, html: bool = False) -> str:
    if html:
        parts = [_escape_html(p) for p in cell.paragraphs]
        for nested_table in cell.nested_tables:
            parts.append(_render_table(nested_table, table_mode="html"))
        return "<br>".join(parts)

    parts = [_escape_md_cell(p) for p in cell.paragraphs]
    for nested_table in cell.nested_tables:
        parts.append(_render_table(nested_table, table_mode="text"))
    return "<br>".join(part for part in parts if part)


def _render_tier1_markdown(table: Table) -> str:
    grid: dict[tuple[int, int], str] = {}
    for cell in table.cells:
        grid[(cell.row, cell.col)] = _cell_text(cell)

    lines: list[str] = []
    for row in range(table.rows):
        row_cells = [grid.get((row, col), "") for col in range(table.cols)]
        lines.append("| " + " | ".join(row_cells) + " |")
        if row == 0:
            lines.append("| " + " | ".join("---" for _ in range(table.cols)) + " |")
    return "\n".join(lines)


def _render_tier2_markdown_rowspan(table: Table) -> str:
    active_spans: dict[int, tuple[int, str]] = {}
    grid_by_row: dict[int, dict[int, str]] = {}
    cells_by_row: dict[int, list[TableCell]] = {}

    for cell in table.cells:
        cells_by_row.setdefault(cell.row, []).append(cell)

    for row in range(table.rows):
        row_grid: dict[int, str] = {}
        next_spans: dict[int, tuple[int, str]] = {}

        for col, (remaining, text) in active_spans.items():
            row_grid[col] = text
            if remaining > 1:
                next_spans[col] = (remaining - 1, text)

        for cell in sorted(cells_by_row.get(row, []), key=lambda current: current.col):
            text = _cell_text(cell)
            for dc in range(cell.colspan):
                col = cell.col + dc
                row_grid[col] = text if dc == 0 else ""
                if cell.rowspan > 1:
                    next_spans[col] = (cell.rowspan - 1, text if dc == 0 else "")

        grid_by_row[row] = row_grid
        active_spans = next_spans

    lines: list[str] = []
    for row in range(table.rows):
        row_cells = [grid_by_row.get(row, {}).get(col, "") for col in range(table.cols)]
        lines.append("| " + " | ".join(row_cells) + " |")
        if row == 0:
            lines.append("| " + " | ".join("---" for _ in range(table.cols)) + " |")
    return "\n".join(lines)


def _render_tier3_html(table: Table) -> str:
    occupied: set[tuple[int, int]] = set()
    cells_by_row: dict[int, list[TableCell]] = {}
    for cell in table.cells:
        cells_by_row.setdefault(cell.row, []).append(cell)

    html_lines: list[str] = ["<table>"]
    for row in range(table.rows):
        html_lines.append("<tr>")
        for cell in sorted(cells_by_row.get(row, []), key=lambda current: current.col):
            if (cell.row, cell.col) in occupied:
                continue
            tag = "th" if row == 0 else "td"
            attrs = ""
            if cell.colspan > 1:
                attrs += f' colspan="{cell.colspan}"'
            if cell.rowspan > 1:
                attrs += f' rowspan="{cell.rowspan}"'
            text = _cell_text(cell, html=True)
            html_lines.append(f"<{tag}{attrs}>{text}</{tag}>")
            for dr in range(cell.rowspan):
                for dc in range(cell.colspan):
                    if dr > 0 or dc > 0:
                        occupied.add((row + dr, cell.col + dc))
        html_lines.append("</tr>")
    html_lines.append("</table>")
    return "\n".join(html_lines)


def _render_tier3_text(table: Table) -> str:
    cells_by_row: dict[int, list[TableCell]] = {}
    for cell in table.cells:
        cells_by_row.setdefault(cell.row, []).append(cell)

    lines = ["[표]"]
    header_cells = [_cell_text(cell) for cell in sorted(cells_by_row.get(0, []), key=lambda current: current.col)]
    has_header = bool(header_cells) and any(cell.strip() for cell in header_cells)
    if has_header:
        lines.append("- 열: " + " | ".join(header_cells))

    start_row = 1 if has_header else 0
    for row in range(start_row, table.rows):
        row_cells = [_cell_text(cell) for cell in sorted(cells_by_row.get(row, []), key=lambda current: current.col)]
        if not row_cells or not any(cell.strip() for cell in row_cells):
            continue
        lines.append(f"- 행 {row - start_row + 1}: " + " | ".join(row_cells))

    return "\n".join(lines)


def _render_tier4_drawing(table: Table) -> str:
    texts = []
    for cell in table.cells:
        text = " ".join(cell.paragraphs).strip()
        if text:
            texts.append(text)
    if not texts:
        return ""
    return "[표: " + " / ".join(texts[:8]) + "]"


def _render_table(table: Table, *, table_mode: TableMode) -> str:
    if not table.cells:
        return ""
    if table.is_drawing_table:
        return _render_tier4_drawing(table)

    has_nested = any(cell.nested_tables for cell in table.cells)
    if table.has_colspan or has_nested or table.cols > 8:
        if table_mode == "html":
            return "\n" + _render_tier3_html(table) + "\n"
        return _render_tier3_text(table)
    if table.has_rowspan:
        return _render_tier2_markdown_rowspan(table)
    return _render_tier1_markdown(table)


def _parse_paragraphs_from_xml(xml_bytes: bytes, *, table_mode: TableMode) -> list[HwpxParagraph]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"HWPX 섹션 XML 파싱 실패: {exc}") from exc

    paragraphs: list[HwpxParagraph] = []
    for paragraph in _direct_children_local(root, "p"):
        style_id = _get_attr(paragraph, "styleIDRef", "styleId", "styleID", "styleIdRef")

        level = 0
        ppr = _find_local(paragraph, "pPr")
        if ppr is not None:
            indent = _find_local(ppr, "indentPr")
            if indent is not None:
                try:
                    level = int(_get_attr(indent, "level") or "0")
                except ValueError:
                    level = 0

        table_paragraphs: list[HwpxParagraph] = []
        for container in paragraph:
            container_name = _local_name(container.tag)
            if container_name not in ("run", "ctrl"):
                continue
            for tbl in _direct_children_local(container, "tbl"):
                table = _collect_table_data(tbl)
                rendered = _render_table(table, table_mode=table_mode)
                if rendered or table.cells:
                    table_paragraphs.append(HwpxParagraph(style_id="표", text=rendered, level=0, table=table))

        if table_paragraphs:
            paragraphs.extend(table_paragraphs)
            continue

        paragraphs.append(HwpxParagraph(style_id=style_id, text=_collect_run_text(paragraph), level=level))

    return paragraphs


def _get_section_names_from_hpf(zf: zipfile.ZipFile) -> list[str]:
    try:
        root = ET.fromstring(zf.read("Contents/content.hpf"))
    except Exception:
        return []

    sections: list[str] = []
    for item in _iter_local(root, "item"):
        item_id = _get_attr(item, "id")
        if "BodyText" in item_id or "section" in item_id.lower():
            sections.append(f"Contents/{item_id}")
    return sections


def _extract_paragraphs(hwpx_path: str, *, table_mode: TableMode) -> list[HwpxParagraph]:
    try:
        zf = zipfile.ZipFile(hwpx_path, "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("HWPX 파일이 손상되었거나 유효하지 않습니다.") from exc

    with zf:
        def _candidate_section_paths() -> list[str]:
            section_paths = _get_section_names_from_hpf(zf)
            if section_paths:
                return section_paths
            scanned = sorted(name for name in zf.namelist() if name.startswith("Contents/section") and name.endswith(".xml"))
            return scanned or ["Contents/section0.xml"]

        def _load_sections(paths: list[str]) -> tuple[list[HwpxParagraph], bool]:
            paragraphs: list[HwpxParagraph] = []
            found_any = False
            for path in paths:
                try:
                    xml_bytes = zf.read(path)
                    found_any = True
                except KeyError:
                    continue
                paragraphs.extend(_parse_paragraphs_from_xml(xml_bytes, table_mode=table_mode))
            return paragraphs, found_any

        paragraphs, found_any = _load_sections(_candidate_section_paths())
        if not found_any:
            fallback_paths = sorted(name for name in zf.namelist() if name.startswith("Contents/section") and name.endswith(".xml")) or ["Contents/section0.xml"]
            paragraphs, found_any = _load_sections(fallback_paths)

        if not found_any:
            raise ValueError("HWPX 파일에서 본문 섹션을 찾을 수 없습니다.")

    return paragraphs


def convert_hwpx(hwpx_path: str, *, table_mode: TableMode = "text") -> str:
    if not Path(hwpx_path).exists():
        raise FileNotFoundError(f"HWPX 파일을 찾을 수 없습니다: {hwpx_path}")
    markdown = postprocess_hwpx(_extract_paragraphs(hwpx_path, table_mode=table_mode))
    return _apply_filename_title_fallback(markdown, Path(hwpx_path))


def _normalize_title(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text)


def _filename_title_candidate(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"^job_[0-9a-f]+-", "", stem)
    stem = re.sub(r"^\d{6}\s+\([^)]*\)\s*", "", stem)
    stem = re.sub(r"\([^)]*\)\s*$", "", stem).strip()
    return stem


def _apply_filename_title_fallback(markdown: str, path: Path) -> str:
    lines = markdown.splitlines()
    if not lines or not lines[0].startswith("# "):
        return markdown

    current_title = lines[0][2:].strip()
    candidate = _filename_title_candidate(path)
    if not candidate:
        return markdown

    current_norm = _normalize_title(current_title)
    candidate_norm = _normalize_title(candidate)
    if current_norm and candidate_norm.startswith(current_norm) and len(candidate_norm) - len(current_norm) >= 8:
        lines[0] = f"# {candidate}"
        return "\n".join(lines) + ("\n" if markdown.endswith("\n") else "")
    return markdown
