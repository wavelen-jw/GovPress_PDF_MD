"""HWPX → Markdown 변환 어댑터.

HWPX 파일 구조
--------------
HWPX는 ZIP 아카이브다. 주요 경로:
  Contents/section0.xml   본문 섹션 (추가 섹션은 section1.xml, section2.xml …)
  Contents/content.hpf    패키지 메타 (섹션 목록 포함)
  BinData/                이미지 등 바이너리 리소스

HWP XML 네임스페이스
---------------------
한글 2014 이후의 HWPX는 여러 네임스페이스를 사용한다.
본문과 관련된 주요 네임스페이스:
  hc  = http://www.hancom.co.kr/hwpml/2012/HWP-Core
  hp  = http://www.hancom.co.kr/hwpml/2012/HWP-Package
  hs  = http://www.hancom.co.kr/hwpml/2012/HWP-Style

본문 XML 계층 구조:
  <hc:sec>           섹션 루트
    <hc:p>           단락 (Paragraph)
      @hc:styleId    단락 스타일 이름 (예: "본문", "제목 1")
      <hc:pPr>       단락 속성
        <hc:indentPr @hc:level="0"> 들여쓰기 수준
      <hc:run>       런 (텍스트 청크)
        <hc:t>       텍스트 노드
      <hc:ctrl>      제어 문자 (표, 그림 등)
        <hc:tbl>     표 (table)

변환 전략
---------
1. ZIP에서 content.hpf를 읽어 섹션 XML 파일 목록 파악.
   content.hpf가 없거나 파싱 실패 시 section0.xml부터 순서대로 시도.
2. 각 섹션 XML의 <hc:p> 단락을 순서대로 순회.
3. 단락의 styleId와 level을 읽어 HwpxParagraph로 변환.
4. 표(<hc:tbl>)는 셀 텍스트를 파이프(|) 구분 행으로 직렬화.
5. 완성된 HwpxParagraph 목록을 hwpx_postprocessor.postprocess_hwpx()에 전달.
"""
from __future__ import annotations

import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import re

from src.hwpx_postprocessor import HwpxParagraph, postprocess_hwpx


# ── XML helpers ───────────────────────────────────────────────────────────────────

_NS_HP_2011 = "http://www.hancom.co.kr/hwpml/2011/paragraph"
_NS_HS_2011 = "http://www.hancom.co.kr/hwpml/2011/section"
_NS_HC_2011 = "http://www.hancom.co.kr/hwpml/2011/core"
_NS_HP_2012 = "http://www.hancom.co.kr/hwpml/2012/HWP-Package"
_NS_HC_2012 = "http://www.hancom.co.kr/hwpml/2012/HWP-Core"


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


# ── 내부 유틸 ─────────────────────────────────────────────────────────────────────

def _collect_run_text(p_elem: ET.Element) -> str:
    """문단 아래의 모든 텍스트 런을 이어 붙인다."""
    parts: list[str] = []
    for run in (child for child in p_elem if _local_name(child.tag) == "run"):
        for t in _iter_local(run, "t"):
            if t.text:
                parts.append(t.text)
    return "".join(parts).strip()


def _collect_table_text(tbl_elem: ET.Element) -> str:
    """표를 단순 파이프 테이블 텍스트로 직렬화한다.

    표 내부의 <hc:p>를 모아 행/열을 재구성한다.
    표가 복잡하면 셀 텍스트를 줄 단위로 나열하는 간략 형식을 사용한다.
    """
    rows: list[list[str]] = []
    for tr in _iter_local(tbl_elem, "tr"):
        row: list[str] = []
        for tc in _iter_local(tr, "tc"):
            cell_parts: list[str] = []
            for p in _iter_local(tc, "p"):
                text = _collect_run_text(p).strip()
                if text:
                    cell_parts.append(text)
            row.append(" ".join(cell_parts))
        if row:
            rows.append(row)

    if not rows:
        return ""

    # Markdown 테이블 형식
    lines: list[str] = []
    header = rows[0]
    lines.append("| " + " | ".join(header) + " |")
    lines.append("| " + " | ".join("---" for _ in header) + " |")
    for row in rows[1:]:
        # 열 수가 헤더와 다를 수 있으므로 패딩/트림
        padded = row + [""] * (len(header) - len(row))
        padded = padded[: len(header)]
        lines.append("| " + " | ".join(padded) + " |")
    return "\n".join(lines)


def _parse_paragraphs_from_xml(xml_bytes: bytes) -> list[HwpxParagraph]:
    """섹션 XML 바이트에서 HwpxParagraph 목록을 추출한다."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise ValueError(f"HWPX 섹션 XML 파싱 실패: {exc}") from exc

    paragraphs: list[HwpxParagraph] = []

    for p in _iter_local(root, "p"):
        style_id = _get_attr(p, "styleIDRef", "styleId", "styleID", "styleIdRef")

        # 들여쓰기 수준 파악
        level = 0
        ppr = _find_local(p, "pPr")
        if ppr is not None:
            indent = _find_local(ppr, "indentPr")
            if indent is not None:
                try:
                    level = int(_get_attr(indent, "level") or "0")
                except ValueError:
                    level = 0

        # 직접 자식 ctrl 요소 중 표가 있는지 확인 (표는 별도 처리)
        table_lines: list[str] = []
        for ctrl in (child for child in p if _local_name(child.tag) == "ctrl"):
            for tbl in _iter_local(ctrl, "tbl"):
                table_text = _collect_table_text(tbl)
                if table_text:
                    table_lines.append(table_text)

        if table_lines:
            # 표를 단락으로 삽입
            for tbl_text in table_lines:
                paragraphs.append(HwpxParagraph(style_id="표", text=tbl_text, level=0))
            continue

        text = _collect_run_text(p)
        # 텍스트가 비어 있어도 빈 단락 정보를 유지 (단락 간 구분용)
        paragraphs.append(HwpxParagraph(style_id=style_id, text=text, level=level))

    return paragraphs


def _get_section_names_from_hpf(zf: zipfile.ZipFile) -> list[str]:
    """content.hpf에서 섹션 XML 파일 이름 목록을 파싱해 반환한다.

    파싱 실패 시 빈 리스트를 반환하고, 호출자가 기본값을 사용하게 한다.
    """
    try:
        hpf_data = zf.read("Contents/content.hpf")
        root = ET.fromstring(hpf_data)
    except Exception:
        return []

    sections: list[str] = []
    # <hp:item> 요소에서 BodyText 타입의 섹션 파일 목록을 수집
    for item in _iter_local(root, "item"):
        id_val = _get_attr(item, "id")
        if "BodyText" in id_val or "section" in id_val.lower():
            sections.append(f"Contents/{id_val}")
    return sections


def _extract_paragraphs(hwpx_path: str) -> list[HwpxParagraph]:
    """HWPX ZIP 아카이브에서 모든 섹션의 단락을 추출한다."""
    try:
        zf = zipfile.ZipFile(hwpx_path, "r")
    except zipfile.BadZipFile as exc:
        raise ValueError("HWPX 파일이 손상되었거나 유효하지 않습니다.") from exc

    with zf:
        def _candidate_section_paths() -> list[str]:
            section_paths = _get_section_names_from_hpf(zf)
            if section_paths:
                return section_paths

            all_names = zf.namelist()
            scanned = sorted(
                [n for n in all_names if n.startswith("Contents/section") and n.endswith(".xml")]
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

        section_paths = _candidate_section_paths()
        all_paragraphs, found_any = _load_sections(section_paths)

        # content.hpf 메타가 오래됐거나 형식이 다르면 직접 section*.xml 스캔으로 재시도
        if not found_any:
            all_names = zf.namelist()
            fallback_paths = sorted(
                [n for n in all_names if n.startswith("Contents/section") and n.endswith(".xml")]
            ) or ["Contents/section0.xml"]
            all_paragraphs, found_any = _load_sections(fallback_paths)

        if not found_any:
            raise ValueError("HWPX 파일에서 본문 섹션을 찾을 수 없습니다.")

    return all_paragraphs


# ── 공개 API ──────────────────────────────────────────────────────────────────────

def convert_hwpx(hwpx_path: str) -> str:
    """HWPX 파일을 Markdown 문자열로 변환한다.

    Args:
        hwpx_path: 변환할 .hwpx 파일의 절대 경로.

    Returns:
        정규화된 Markdown 문자열.

    Raises:
        ValueError: 파일이 유효한 HWPX 형식이 아니거나 본문을 찾을 수 없을 때.
        FileNotFoundError: 파일이 존재하지 않을 때.
    """
    if not Path(hwpx_path).exists():
        raise FileNotFoundError(f"HWPX 파일을 찾을 수 없습니다: {hwpx_path}")

    paragraphs = _extract_paragraphs(hwpx_path)
    markdown = postprocess_hwpx(paragraphs)
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
