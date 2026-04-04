"""HWPX -> Markdown converter."""
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
import re

from .hwpx_postprocessor import HwpxParagraph, postprocess_hwpx


# ── XML helpers ───────────────────────────────────────────────────────────────

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


# ── Table data model ──────────────────────────────────────────────────────────

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


# colspan/rowspan 후보 속성명 (HWPX 버전에 따라 다를 수 있음)
_COLSPAN_ATTRS = ("colSpan", "colspan", "numMergedCols", "columnSpan",
                  "mergedColCount", "spanCols", "col_span")
_ROWSPAN_ATTRS = ("rowSpan", "rowspan", "numMergedRows", "rowCount",
                  "mergedRowCount", "spanRows", "row_span")


def _read_span(elem: ET.Element, candidates: tuple[str, ...]) -> int:
    """요소 및 하위 cellPr에서 span 값을 읽어 반환. 없으면 1."""
    v = _get_attr(elem, *candidates)
    if v:
        try:
            return max(int(v), 1)
        except ValueError:
            pass
    # cellPr 등 자식 요소에서 시도
    for child in elem:
        cv = _get_attr(child, *candidates)
        if cv:
            try:
                return max(int(cv), 1)
            except ValueError:
                pass
    return 1


def _is_drawing_table(cells: list[TableCell], rows: int, cols: int) -> bool:
    """80% 이상 빈 셀 + 3행 이상이면 레이아웃용 표로 간주."""
    if rows < 3 or not cells:
        return False
    empty = sum(
        1 for c in cells
        if not any(p.strip() for p in c.paragraphs) and not c.nested_tables
    )
    return (empty / len(cells)) >= 0.80


def _collect_cell_paragraphs(tc: ET.Element) -> list[str]:
    """tc > subList > p 경로에서 텍스트 수집.

    HWPX XML 구조: <tc> → <subList> → <p>
    <p>는 tc의 직접 자식이 아니므로 subList를 통해야 한다.
    """
    parts: list[str] = []
    for sub_list in _direct_children_local(tc, "subList"):
        for p in _direct_children_local(sub_list, "p"):
            text = _collect_run_text(p).strip()
            if text:
                parts.append(text)
    # fallback: 일부 HWPX 변형에서 p가 tc 직접 자식인 경우
    if not parts:
        for p in _direct_children_local(tc, "p"):
            text = _collect_run_text(p).strip()
            if text:
                parts.append(text)
    return parts


def _collect_table_data(tbl_elem: ET.Element) -> Table:
    """tbl 요소에서 구조화된 Table 객체를 추출."""
    cells: list[TableCell] = []
    # 점유 슬롯 추적 (rowspan으로 미리 점유된 위치)
    occupied: set[tuple[int, int]] = set()
    max_col = 0

    for tr_idx, tr in enumerate(list(_direct_children_local(tbl_elem, "tr"))):
        col_cursor = 0
        for tc in _direct_children_local(tr, "tc"):
            # 점유된 슬롯 건너뜀
            while (tr_idx, col_cursor) in occupied:
                col_cursor += 1

            colspan = _read_span(tc, _COLSPAN_ATTRS)
            rowspan = _read_span(tc, _ROWSPAN_ATTRS)

            paragraphs = _collect_cell_paragraphs(tc)

            # 중첩 표 재귀 처리: tc > subList > p > ctrl > tbl
            nested: list[Table] = []
            for sub_list in _direct_children_local(tc, "subList"):
                for p in _direct_children_local(sub_list, "p"):
                    for ctrl in _direct_children_local(p, "ctrl"):
                        for sub_tbl in _iter_local(ctrl, "tbl"):
                            nested.append(_collect_table_data(sub_tbl))
            # fallback: ctrl 혹은 tbl이 tc 직접 자식인 경우
            for ctrl in _direct_children_local(tc, "ctrl"):
                for sub_tbl in _iter_local(ctrl, "tbl"):
                    nested.append(_collect_table_data(sub_tbl))
            for sub_tbl in _direct_children_local(tc, "tbl"):
                nested.append(_collect_table_data(sub_tbl))

            cells.append(TableCell(
                row=tr_idx, col=col_cursor,
                rowspan=rowspan, colspan=colspan,
                paragraphs=paragraphs,
                nested_tables=nested,
            ))

            # rowspan으로 아래 행의 슬롯 점유 표시
            for dr in range(rowspan):
                for dc in range(colspan):
                    if dr > 0 or dc > 0:
                        occupied.add((tr_idx + dr, col_cursor + dc))

            end_col = col_cursor + colspan
            if end_col > max_col:
                max_col = end_col
            col_cursor = end_col

    # 행 수: tr 태그 실제 수
    row_count = sum(1 for _ in _direct_children_local(tbl_elem, "tr"))
    has_colspan = any(c.colspan > 1 for c in cells)
    has_rowspan = any(c.rowspan > 1 for c in cells)
    is_drawing = _is_drawing_table(cells, row_count, max_col)

    return Table(
        rows=row_count,
        cols=max_col,
        cells=cells,
        has_rowspan=has_rowspan,
        has_colspan=has_colspan,
        is_drawing_table=is_drawing,
    )


# ── Tiered renderer ───────────────────────────────────────────────────────────

def _escape_md_cell(text: str) -> str:
    return text.replace("|", "\\|")


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _cell_text(cell: TableCell, html: bool = False) -> str:
    """셀 단락들을 <br> 구분으로 합쳐 단일 문자열로 반환."""
    if html:
        # 개별 단락을 먼저 이스케이프한 뒤 <br>로 연결 (이스케이프 후 <br> 삽입)
        parts = [_escape_html(p) for p in cell.paragraphs]
        for nt in cell.nested_tables:
            parts.append(_render_table(nt))
        return "<br>".join(parts)
    else:
        parts = [_escape_md_cell(p) for p in cell.paragraphs]
        for nt in cell.nested_tables:
            parts.append("[중첩표]")
        return "<br>".join(parts)


def _render_tier1_markdown(table: Table) -> str:
    """등급 1: 단순 Markdown 표."""
    grid: dict[tuple[int, int], str] = {}
    for cell in table.cells:
        grid[(cell.row, cell.col)] = _cell_text(cell)

    lines: list[str] = []
    for r in range(table.rows):
        row_cells = [grid.get((r, c), "") for c in range(table.cols)]
        lines.append("| " + " | ".join(row_cells) + " |")
        if r == 0:
            lines.append("| " + " | ".join("---" for _ in range(table.cols)) + " |")
    return "\n".join(lines)


def _render_tier2_markdown_rowspan(table: Table) -> str:
    """등급 2: rowspan 있는 Markdown 표 (병합 셀 내용 반복)."""
    # active_spans: col → (remaining_rows, text)
    active_spans: dict[int, tuple[int, str]] = {}
    grid_by_row: dict[int, dict[int, str]] = {}

    # cells를 row 순으로 처리
    cells_by_row: dict[int, list[TableCell]] = {}
    for cell in table.cells:
        cells_by_row.setdefault(cell.row, []).append(cell)

    for r in range(table.rows):
        row_grid: dict[int, str] = {}
        next_spans: dict[int, tuple[int, str]] = {}

        # 이전 rowspan 적용
        for col, (remaining, text) in active_spans.items():
            row_grid[col] = text
            if remaining > 1:
                next_spans[col] = (remaining - 1, text)

        for cell in sorted(cells_by_row.get(r, []), key=lambda c: c.col):
            text = _cell_text(cell)
            for dc in range(cell.colspan):
                c = cell.col + dc
                row_grid[c] = text if dc == 0 else ""
                if cell.rowspan > 1:
                    next_spans[c] = (cell.rowspan - 1, text if dc == 0 else "")

        grid_by_row[r] = row_grid
        active_spans = next_spans

    lines: list[str] = []
    for r in range(table.rows):
        row_cells = [grid_by_row.get(r, {}).get(c, "") for c in range(table.cols)]
        lines.append("| " + " | ".join(row_cells) + " |")
        if r == 0:
            lines.append("| " + " | ".join("---" for _ in range(table.cols)) + " |")
    return "\n".join(lines)


def _render_tier3_html(table: Table) -> str:
    """등급 3: HTML <table> (colspan/rowspan 완전 지원)."""
    # 점유 맵: 이미 상위 셀이 span으로 처리한 위치
    occupied: set[tuple[int, int]] = set()
    cells_by_row: dict[int, list[TableCell]] = {}
    for cell in table.cells:
        cells_by_row.setdefault(cell.row, []).append(cell)

    html_lines: list[str] = ["<table>"]
    for r in range(table.rows):
        html_lines.append("<tr>")
        for cell in sorted(cells_by_row.get(r, []), key=lambda c: c.col):
            if (cell.row, cell.col) in occupied:
                continue
            tag = "th" if r == 0 else "td"
            attrs = ""
            if cell.colspan > 1:
                attrs += f' colspan="{cell.colspan}"'
            if cell.rowspan > 1:
                attrs += f' rowspan="{cell.rowspan}"'
            text = _cell_text(cell, html=True)
            html_lines.append(f"<{tag}{attrs}>{text}</{tag}>")
            # span 점유 표시
            for dr in range(cell.rowspan):
                for dc in range(cell.colspan):
                    if dr > 0 or dc > 0:
                        occupied.add((r + dr, cell.col + dc))
        html_lines.append("</tr>")
    html_lines.append("</table>")
    return "\n".join(html_lines)


def _render_tier4_drawing(table: Table) -> str:
    """등급 4: 레이아웃 표 — 텍스트가 있으면 한 줄로 요약, 없으면 생략."""
    texts = []
    for cell in table.cells:
        t = " ".join(cell.paragraphs).strip()
        if t:
            texts.append(t)
    if not texts:
        return ""
    return "[표: " + " / ".join(texts[:8]) + "]"


def _render_table(table: Table) -> str:
    """복잡도에 따라 적절한 등급으로 렌더링."""
    if not table.cells:
        return ""

    if table.is_drawing_table:
        return _render_tier4_drawing(table)

    has_nested = any(c.nested_tables for c in table.cells)

    if table.has_colspan or has_nested or table.cols > 8:
        return "\n" + _render_tier3_html(table) + "\n"

    if table.has_rowspan:
        return _render_tier2_markdown_rowspan(table)

    return _render_tier1_markdown(table)


def _collect_table_text(tbl_elem: ET.Element) -> str:
    """하위 호환 래퍼 — 단순 Markdown 표 문자열 반환."""
    table = _collect_table_data(tbl_elem)
    return _render_table(table)


# ── XML paragraph parser ──────────────────────────────────────────────────────

def _parse_paragraphs_from_xml(xml_bytes: bytes) -> list[HwpxParagraph]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"HWPX 섹션 XML 파싱 실패: {exc}") from exc

    paragraphs: list[HwpxParagraph] = []
    # 최상위 <p>만 순회 — _iter_local은 표 셀 내부 <p>까지 포함되어 중복 발생
    # HWPX 구조: <sec> → <p> (직접 자식), <p> 내 ctrl → <tbl> → <tr>→<tc>→<subList>→<p>
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
        # HWPX 실제 구조: <p> → <run> → <tbl>  (ctrl이 아닌 run 안에 내장)
        # fallback: <p> → <ctrl> → <tbl> (일부 버전)
        for container in paragraph:
            container_ln = _local_name(container.tag)
            if container_ln not in ("run", "ctrl"):
                continue
            for tbl in _direct_children_local(container, "tbl"):
                table = _collect_table_data(tbl)
                rendered = _render_table(table)
                if rendered or table.cells:
                    table_paragraphs.append(
                        HwpxParagraph(style_id="표", text=rendered, level=0, table=table)
                    )

        if table_paragraphs:
            paragraphs.extend(table_paragraphs)
            continue

        paragraphs.append(
            HwpxParagraph(style_id=style_id, text=_collect_run_text(paragraph), level=level)
        )

    return paragraphs


# ── Section loading ───────────────────────────────────────────────────────────

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


def _extract_paragraphs(hwpx_path: str) -> list[HwpxParagraph]:
    try:
        zf = zipfile.ZipFile(hwpx_path, "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("HWPX 파일이 손상되었거나 유효하지 않습니다.") from exc

    with zf:
        def _candidate_section_paths() -> list[str]:
            section_paths = _get_section_names_from_hpf(zf)
            if section_paths:
                return section_paths
            scanned = sorted(
                name
                for name in zf.namelist()
                if name.startswith("Contents/section") and name.endswith(".xml")
            )
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
                paragraphs.extend(_parse_paragraphs_from_xml(xml_bytes))
            return paragraphs, found_any

        paragraphs, found_any = _load_sections(_candidate_section_paths())
        if not found_any:
            fallback_paths = sorted(
                name
                for name in zf.namelist()
                if name.startswith("Contents/section") and name.endswith(".xml")
            ) or ["Contents/section0.xml"]
            paragraphs, found_any = _load_sections(fallback_paths)

        if not found_any:
            raise ValueError("HWPX 파일에서 본문 섹션을 찾을 수 없습니다.")

    return paragraphs


# ── Public API ────────────────────────────────────────────────────────────────

def convert_hwpx(hwpx_path: str) -> str:
    if not Path(hwpx_path).exists():
        raise FileNotFoundError(f"HWPX 파일을 찾을 수 없습니다: {hwpx_path}")
    markdown = postprocess_hwpx(_extract_paragraphs(hwpx_path))
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
