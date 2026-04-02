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

from src.hwpx_postprocessor import HwpxParagraph, postprocess_hwpx


# ── XML 네임스페이스 ──────────────────────────────────────────────────────────────

_NS_HC = "http://www.hancom.co.kr/hwpml/2012/HWP-Core"
_NS_HP = "http://www.hancom.co.kr/hwpml/2012/HWP-Package"

_Q = {
    "sec":      f"{{{_NS_HC}}}sec",
    "p":        f"{{{_NS_HC}}}p",
    "pPr":      f"{{{_NS_HC}}}pPr",
    "indentPr": f"{{{_NS_HC}}}indentPr",
    "run":      f"{{{_NS_HC}}}run",
    "t":        f"{{{_NS_HC}}}t",
    "ctrl":     f"{{{_NS_HC}}}ctrl",
    "tbl":      f"{{{_NS_HC}}}tbl",
    "tr":       f"{{{_NS_HC}}}tr",
    "tc":       f"{{{_NS_HC}}}tc",
}

_ATTR_STYLE_ID = f"{{{_NS_HC}}}styleId"
_ATTR_LEVEL    = f"{{{_NS_HC}}}level"
_ATTR_OBJ_TYPE = f"{{{_NS_HC}}}objType"


# ── 내부 유틸 ─────────────────────────────────────────────────────────────────────

def _collect_run_text(p_elem: ET.Element) -> str:
    """<hc:p> 아래의 모든 <hc:t> 텍스트를 이어 붙인다."""
    parts: list[str] = []
    for run in p_elem.iter(_Q["run"]):
        for t in run.iter(_Q["t"]):
            if t.text:
                parts.append(t.text)
    return "".join(parts).strip()


def _collect_table_text(tbl_elem: ET.Element) -> str:
    """<hc:tbl>을 단순 파이프 테이블 텍스트로 직렬화한다.

    표 내부의 <hc:p>를 모아 행/열을 재구성한다.
    표가 복잡하면 셀 텍스트를 줄 단위로 나열하는 간략 형식을 사용한다.
    """
    rows: list[list[str]] = []
    for tr in tbl_elem.iter(_Q["tr"]):
        row: list[str] = []
        for tc in tr.iter(_Q["tc"]):
            cell_parts: list[str] = []
            for p in tc.iter(_Q["p"]):
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

    for p in root.iter(_Q["p"]):
        style_id: str = p.get(_ATTR_STYLE_ID, "") or ""

        # 들여쓰기 수준 파악
        level = 0
        ppr = p.find(_Q["pPr"])
        if ppr is not None:
            indent = ppr.find(_Q["indentPr"])
            if indent is not None:
                try:
                    level = int(indent.get(_ATTR_LEVEL, "0") or "0")
                except ValueError:
                    level = 0

        # 직접 자식 ctrl 요소 중 표가 있는지 확인 (표는 별도 처리)
        table_lines: list[str] = []
        for ctrl in p.findall(_Q["ctrl"]):
            for tbl in ctrl.iter(_Q["tbl"]):
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
    for item in root.iter(f"{{{_NS_HP}}}item"):
        id_val = item.get(f"{{{_NS_HP}}}id", "")
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
        # 1. content.hpf에서 섹션 목록 파악 시도
        section_paths = _get_section_names_from_hpf(zf)

        # 2. content.hpf 파싱 실패 시 ZIP 내의 section*.xml 파일을 직접 탐색
        if not section_paths:
            all_names = zf.namelist()
            section_paths = sorted(
                [n for n in all_names if n.startswith("Contents/section") and n.endswith(".xml")]
            )

        # 3. 그래도 없으면 section0.xml 단독 시도
        if not section_paths:
            section_paths = ["Contents/section0.xml"]

        all_paragraphs: list[HwpxParagraph] = []
        found_any = False
        for path in section_paths:
            try:
                xml_bytes = zf.read(path)
                found_any = True
            except KeyError:
                continue
            paras = _parse_paragraphs_from_xml(xml_bytes)
            all_paragraphs.extend(paras)

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
    return postprocess_hwpx(paragraphs)
