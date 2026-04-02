"""HWPX -> Markdown converter."""
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re

from src.hwpx_postprocessor import HwpxParagraph, postprocess_hwpx


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def _iter_local(elem: ET.Element, name: str):
    for node in elem.iter():
        if _local_name(node.tag) == name:
            yield node


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


def _collect_table_text(tbl_elem: ET.Element) -> str:
    rows: list[list[str]] = []
    for tr in _iter_local(tbl_elem, "tr"):
        row: list[str] = []
        for tc in _iter_local(tr, "tc"):
            cell_parts: list[str] = []
            for paragraph in _iter_local(tc, "p"):
                text = _collect_run_text(paragraph).strip()
                if text:
                    cell_parts.append(text)
            row.append(" ".join(cell_parts))
        if row:
            rows.append(row)

    if not rows:
        return ""

    lines = ["| " + " | ".join(rows[0]) + " |"]
    lines.append("| " + " | ".join("---" for _ in rows[0]) + " |")
    for row in rows[1:]:
        padded = row + [""] * (len(rows[0]) - len(row))
        lines.append("| " + " | ".join(padded[: len(rows[0])]) + " |")
    return "\n".join(lines)


def _parse_paragraphs_from_xml(xml_bytes: bytes) -> list[HwpxParagraph]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"HWPX 섹션 XML 파싱 실패: {exc}") from exc

    paragraphs: list[HwpxParagraph] = []
    for paragraph in _iter_local(root, "p"):
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

        table_lines: list[str] = []
        for ctrl in (child for child in paragraph if _local_name(child.tag) == "ctrl"):
            for tbl in _iter_local(ctrl, "tbl"):
                table_text = _collect_table_text(tbl)
                if table_text:
                    table_lines.append(table_text)

        if table_lines:
            for table_text in table_lines:
                paragraphs.append(HwpxParagraph(style_id="표", text=table_text, level=0))
            continue

        paragraphs.append(
            HwpxParagraph(style_id=style_id, text=_collect_run_text(paragraph), level=level)
        )

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
