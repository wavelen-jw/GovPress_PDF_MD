#!/usr/bin/env python3
"""
hwpx_table_inspector.py

HWPX 파일의 표 XML 구조를 검사하여 colspan/rowspan 속성명을 확인하는 스크립트.
production 코드가 아닌 개발/디버깅 전용 도구입니다.

사용법:
    python hwpx_table_inspector.py <file.hwpx> [--xml] [--summary-only]

옵션:
    --xml           각 표의 전체 XML 출력 (내용이 길 수 있음)
    --summary-only  셀별 상세 정보 없이 요약만 출력

출력 내용:
    1. 아카이브 파일 목록
    2. 각 섹션 XML의 표마다:
       - Raw XML (첫 2000자, --xml 시 전체)
       - <tr> 요소 속성
       - <tc> 요소 속성 (colspan/rowspan 속성명 확인이 목적)
       - <tc>의 <p>/<tbl> 이외의 하위 요소
       - 중첩 표 깊이
       - 요약: 행수, 열수, 병합 맵
"""
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[1] if "}" in tag else tag


def _iter_local(elem, name):
    for node in elem.iter():
        if _local_name(node.tag) == name:
            yield node


def _direct_children_local(elem, name):
    for child in elem:
        if _local_name(child.tag) == name:
            yield child


def _get_attr(elem, *names) -> str:
    for n in names:
        if n in elem.attrib:
            return elem.attrib[n]
    low = {k.lower(): v for k, v in elem.attrib.items()}
    for n in names:
        v = low.get(n.lower())
        if v is not None:
            return v
    return ""


def _collect_run_text(p_elem) -> str:
    parts = []
    for run in (c for c in p_elem if _local_name(c.tag) == "run"):
        for t in _iter_local(run, "t"):
            if t.text:
                parts.append(t.text)
    return "".join(parts).strip()


def _max_nesting_depth(elem, target_tag, depth=0) -> int:
    best = depth
    for child in elem:
        if _local_name(child.tag) == target_tag:
            best = max(best, _max_nesting_depth(child, target_tag, depth + 1))
        else:
            best = max(best, _max_nesting_depth(child, target_tag, depth))
    return best


COLSPAN_CANDIDATES = ["colSpan", "colspan", "numMergedCols", "columnSpan", "col_span",
                      "ColSpan", "mergedColCount", "spanCols"]
ROWSPAN_CANDIDATES = ["rowSpan", "rowspan", "numMergedRows", "rowCount", "row_span",
                      "RowSpan", "mergedRowCount", "spanRows"]


def _try_read_span(elem, candidates) -> tuple[int, str | None]:
    """속성값과 실제 속성명을 반환. (값, 속성명) — 없으면 (1, None)."""
    for name in candidates:
        v = _get_attr(elem, name)
        if v and v != "1":
            try:
                return max(int(v), 1), name
            except ValueError:
                pass
    return 1, None


def _inspect_table(tbl, t_idx: int, dump_xml: bool, summary_only: bool) -> None:
    print(f"\n--- Table #{t_idx} ---")

    raw = ET.tostring(tbl, encoding="unicode")
    if dump_xml:
        print(f"  Full XML:\n  {raw}")
    else:
        print(f"  Raw XML (first 2000 chars):\n  {raw[:2000]}")

    tc_attr_counter: Counter = Counter()
    tc_child_tags: Counter = Counter()
    merge_map: list[list[tuple]] = []
    known_colspan_attr: str | None = None
    known_rowspan_attr: str | None = None
    tr_count = 0

    for tr_idx, tr in enumerate(list(_direct_children_local(tbl, "tr"))):
        tr_count += 1
        tr_attribs = dict(tr.attrib)
        if tr_attribs and not summary_only:
            print(f"  tr[{tr_idx}] attribs: {tr_attribs}")

        row_cells = []
        for tc_idx, tc in enumerate(list(_direct_children_local(tr, "tc"))):
            tc_attribs = dict(tc.attrib)
            tc_attr_counter.update(tc_attribs.keys())

            if not summary_only and tc_attribs:
                print(f"    tc[{tr_idx},{tc_idx}] attribs: {tc_attribs}")

            # tc 직접 속성에서 span 읽기
            colspan, cs_attr = _try_read_span(tc, COLSPAN_CANDIDATES)
            rowspan, rs_attr = _try_read_span(tc, ROWSPAN_CANDIDATES)

            # 하위 요소(cellPr 등)에서도 span 읽기
            for child in tc:
                cname = _local_name(child.tag)
                tc_child_tags[cname] += 1
                if cname not in ("p", "tbl"):
                    if not summary_only:
                        child_attribs = dict(child.attrib)
                        print(f"      <{cname}> attribs={child_attribs}")
                        for gc in child:
                            gcname = _local_name(gc.tag)
                            print(f"        <{gcname}> attribs={dict(gc.attrib)}")
                    if colspan == 1:
                        colspan, cs_attr = _try_read_span(child, COLSPAN_CANDIDATES)
                    if rowspan == 1:
                        rowspan, rs_attr = _try_read_span(child, ROWSPAN_CANDIDATES)

            if cs_attr and not known_colspan_attr:
                known_colspan_attr = cs_attr
            if rs_attr and not known_rowspan_attr:
                known_rowspan_attr = rs_attr

            # 중첩 표
            nested = list(_iter_local(tc, "tbl"))
            if nested and not summary_only:
                print(f"      !! {len(nested)} 중첩 표 in tc[{tr_idx},{tc_idx}]")

            # 셀 텍스트 미리보기
            cell_parts = []
            for p in _direct_children_local(tc, "p"):
                t = _collect_run_text(p)
                if t:
                    cell_parts.append(t)
            preview = " ".join(cell_parts)[:20]
            row_cells.append((colspan, rowspan, preview, len(nested)))

        merge_map.append(row_cells)

    # 요약
    print(f"\n  === 요약 ===")
    print(f"  행 수: {tr_count}")
    print(f"  tc 속성 키: {dict(tc_attr_counter)}")
    print(f"  tc 하위 요소 태그: {dict(tc_child_tags)}")
    if known_colspan_attr:
        print(f"  ** COLSPAN ATTRIBUTE NAME: '{known_colspan_attr}'")
    else:
        print(f"  ** colspan > 1 없음 (이 표에는 열 병합 없음)")
    if known_rowspan_attr:
        print(f"  ** ROWSPAN ATTRIBUTE NAME: '{known_rowspan_attr}'")
    else:
        print(f"  ** rowspan > 1 없음 (이 표에는 행 병합 없음)")
    print(f"  최대 중첩 깊이: {_max_nesting_depth(tbl, 'tbl', 1)}")

    print("  병합 맵 (colspan x rowspan | 텍스트 미리보기):")
    for r_idx, row in enumerate(merge_map):
        row_str = "  | "
        for cs, rs, text, nested_cnt in row:
            span = ""
            if cs > 1:
                span += f"c{cs}"
            if rs > 1:
                span += f"r{rs}"
            if nested_cnt:
                span += f"n{nested_cnt}"
            cell_repr = f"[{span}|{text}]" if span else f"[{text}]"
            row_str += cell_repr + " | "
        print(f"    행{r_idx}: {row_str}")


def inspect_hwpx_tables(hwpx_path: str, dump_xml: bool, summary_only: bool) -> None:
    with zipfile.ZipFile(hwpx_path, "r") as zf:
        print("=== 아카이브 파일 목록 ===")
        for name in sorted(zf.namelist()):
            print(f"  {name}")

        section_files = sorted(
            n for n in zf.namelist()
            if n.startswith("Contents/") and n.endswith(".xml")
        )

        for sf in section_files:
            try:
                xml_bytes = zf.read(sf)
            except KeyError:
                continue
            try:
                root = ET.fromstring(xml_bytes)
            except ET.ParseError as e:
                print(f"\n!! {sf} 파싱 오류: {e}")
                continue

            tables = list(_iter_local(root, "tbl"))
            if not tables:
                continue

            print(f"\n{'='*70}")
            print(f"섹션: {sf}  |  표 수: {len(tables)}")
            print(f"{'='*70}")

            for t_idx, tbl in enumerate(tables):
                _inspect_table(tbl, t_idx, dump_xml, summary_only)


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__)
        sys.exit(1)
    path = args[0]
    dump_xml = "--xml" in args
    summary_only = "--summary-only" in args
    inspect_hwpx_tables(path, dump_xml=dump_xml, summary_only=summary_only)
