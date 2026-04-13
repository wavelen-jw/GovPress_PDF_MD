#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup, Tag


CATALOG_DIR = Path("deploy/wsl/data/storage/policy_briefing_catalog")
SITE_ROOT = "https://www.korea.kr"


def load_item(news_id: str) -> dict:
    for path in sorted(CATALOG_DIR.glob("*.json"), reverse=True):
        items = json.loads(path.read_text()).get("items", {})
        item = items.get(news_id)
        if item:
            return item
    raise SystemExit(f"news_id not found in cached catalog: {news_id}")


def parse_iframe_src(article_html: str) -> str:
    match = re.search(r'<iframe[^>]+src="([^"]+doc\.html\?[^"]+)"', article_html)
    if not match:
        raise SystemExit("docViewer iframe src not found")
    return html.unescape(match.group(1))


def iter_result_pages(result_base: str) -> Iterable[str]:
    file_name = result_base.rstrip("/").split("/")[-1]
    page = 1
    while True:
        url = f"{result_base}/{file_name}.files/{page}.html"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            break
        yield resp.text
        page += 1


def parse_style_number(style: str, key: str) -> float:
    match = re.search(rf"{re.escape(key)}\s*:\s*([-0-9.]+)pt", style)
    return float(match.group(1)) if match else 0.0


def paragraph_indent(style: str) -> int:
    margin_left = parse_style_number(style, "margin-left")
    text_indent = parse_style_number(style, "text-indent")
    effective = max(margin_left + min(text_indent, 0.0), margin_left)
    if effective >= 50:
        return 2
    if effective >= 24:
        return 1
    return 0


def normalize_text(text: str) -> str:
    text = html.unescape(text).replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.)])", r"\1", text)
    text = re.sub(r"([(])\s+", r"\1", text)
    text = re.sub(r"\s+([·:])", r"\1", text)
    text = re.sub(r"([□ㅇ➊➋➌➍➎*])\s+", r"\1 ", text)
    text = text.replace("도함께", "도 함께")
    return text.strip()


def table_to_markdown(table: Tag) -> list[str]:
    rows = []
    for tr in table.find_all("tr", recursive=False):
        cells = tr.find_all(["td", "th"], recursive=False)
        row = [normalize_text(" ".join(cell.stripped_strings)) for cell in cells]
        if any(row):
            rows.append(row)
    if not rows:
        return []
    nonempty = [cell for row in rows for cell in row if cell]
    if nonempty == ["보도자료"]:
        return []
    condensed = []
    for row in rows:
        parts = [cell for cell in row if cell]
        if parts:
            condensed.append(parts)
    if condensed and condensed[0][0].startswith("붙임"):
        heading = " ".join(condensed[0]).strip()
        lines = [f"## {heading}"]
        for parts in condensed[1:]:
            text = " ".join(parts).strip()
            if text:
                lines.append(text)
        return lines
    if condensed and all(len(parts) == 1 for parts in condensed):
        compact = [parts[0] for parts in condensed]
        first = compact[0]
        rest = compact[1:]
        if first == "보도자료":
            return []
        if all(item.startswith("-") for item in rest):
            lines = [f"## {first}"]
            for item in rest:
                lines.append(f"- {item.lstrip('-').strip()}")
            return lines
        if len(compact) == 1:
            return [first]
    if rows[0][0].startswith("담당 부서") or rows[0][0].startswith("담당부서"):
        lines = ["## 담당 부서", ""]
        for row in rows:
            cells = [cell for cell in row if cell]
            if not cells:
                continue
            if len(cells) >= 6:
                lines.append(
                    f"- {cells[0]}: {cells[1]} / {cells[2]} {cells[3]} {cells[4]} / {cells[5]}"
                )
            elif len(cells) >= 4:
                lines.append(f"- {cells[0]}: {cells[1]} / {cells[2]} {cells[3]}")
            else:
                lines.append(f"- {' / '.join(cells)}")
        return lines
    if rows[0][0] == "안건":
        lines = ["## 안건", ""]
        for row in rows[1:]:
            cells = [cell for cell in row if cell]
            if len(cells) >= 4:
                lines.append(f"- {cells[0]}")
                lines.append(f"  - 담당: {cells[1]}")
                lines.append(f"  - 연락: {cells[2]} / {cells[3]}")
            elif cells:
                lines.append(f"- {' / '.join(cells)}")
        return lines
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]
    if width == 1:
        first = rows[0][0]
        rest = [row[0] for row in rows[1:] if row[0]]
        if first and all(item.startswith("-") for item in rest):
            lines = [f"## {first}"]
            for item in rest:
                lines.append(f"- {item.lstrip('-').strip()}")
            return lines
        if first and not rest:
            return [first]
    lines = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * width) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return lines


def block_to_lines(node: Tag) -> list[str]:
    if node.name == "table":
        return table_to_markdown(node)
    if node.name != "p":
        return []
    style = node.get("style", "")
    text = normalize_text(" ".join(node.stripped_strings))
    if not text:
        return []
    if "정책브리핑" in text and len(text) < 80:
        return []
    if text == "보도자료":
        return ["# 보도자료"]
    if text.startswith("보도시점"):
        return [f"**{text}**"]
    if text.startswith("[ ") and text.endswith(" ]"):
        return [f"## {text}"]
    if text.startswith("[") and text.endswith("]"):
        return [f"## {text}"]
    if text.startswith("붙임"):
        return [f"## {text}"]
    if text.startswith("< ") and text.endswith(" >"):
        return [f"## {text[2:-2].strip()}"]
    if text.startswith("<") and text.endswith(">"):
        return [f"## {text[1:-1].strip()}"]
    if text.startswith("담당 부서"):
        return ["## 담당 부서"]
    if text.startswith("- "):
        level = paragraph_indent(style)
        return [f"{'  ' * level}- {text[2:].strip()}"]
    if re.match(r"^[□ㅇ➊➋➌➍➎*]\s", text):
        level = paragraph_indent(style)
        return [f"{'  ' * level}{text}"]
    if "text-align:center" in style and parse_style_number(style, "font-size") >= 20:
        return [f"## {text}"]
    if "text-align:center" in style and text:
        return [text]
    level = paragraph_indent(style)
    return [f"{'  ' * level}{text}"]


def render_body(page_html: str) -> list[str]:
    soup = BeautifulSoup(page_html, "lxml")
    root = soup.find(id="div_page") or soup
    lines: list[str] = []
    for child in root.children:
        if not isinstance(child, Tag):
            continue
        if child.name == "p" and child.find("table", recursive=False):
            for table in child.find_all("table", recursive=False):
                table_lines = table_to_markdown(table)
                if table_lines:
                    lines.extend(table_lines)
                    lines.append("")
            continue
        lines.extend(block_to_lines(child))
        if lines and lines[-1] != "":
            lines.append("")
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def cleanup_line_spacing(line: str) -> str:
    line = re.sub(r"(\d)\s+([조월일시분초])\b", r"\1\2", line)
    line = re.sub(r"([가-힣A-Za-z0-9])\s+\(([^)]+)\)", r"\1(\2)", line)
    line = re.sub(r"\(\s+", "(", line)
    line = re.sub(r"\s+\)", ")", line)
    line = re.sub(r"([가-힣])\s+(은|는|이|가|을|를|의|에|와|과|도|만|로|으로|에서|에게|께서)\b", r"\1\2", line)
    line = re.sub(r"([가-힣])\s+(하다|했다|하였다|한다|할|될|되다|되었다|이다|이며|이고|인|임)\b", r"\1\2", line)
    line = re.sub(r"\b(과|국|부|장|관|청|과장|국장|사무관|서기관)\s+(장|관)\b", r"\1\2", line)
    line = line.replace("과 장", "과장").replace("국 장", "국장").replace("차 관", "차관")
    line = line.replace("사 무관", "사무관").replace("서 기관", "서기관").replace("부 총리", "부총리")
    line = line.replace("책임자과장", "책임자 과장")
    line = line.replace("경제 부총리", "경제부총리").replace("대외여건의", "대외 여건의")
    line = line.replace("대외경제장관회의 를", "대외경제장관회의를")
    line = line.replace("조사개시 를", "조사개시를").replace("대응계획 을", "대응계획을")
    line = line.replace("의견 을", "의견을").replace("입장 을", "입장을")
    line = line.replace("수요 에", "수요에").replace("상황 이다", "상황이다")
    line = line.replace("계획 이다", "계획이다").replace("전략적 으로", "전략적으로")
    line = line.replace("적극적 으로", "적극적으로").replace("지속적 으로", "지속적으로")
    line = line.replace("안정적 으로", "안정적으로").replace("신속히 추진 중", "신속히 추진 중")
    line = line.replace("수급 안정화", "수급 안정화")
    line = line.replace("수렴 하고", "수렴하고").replace("활용 하여", "활용하여")
    line = line.replace("활용 해", "활용해").replace("전달 해", "전달해")
    line = line.replace("점검 하며", "점검하며").replace("관리 하는", "관리하는")
    line = line.replace("확대 되는", "확대되는").replace("출범 하여", "출범하여")
    line = line.replace("수립 하고", "수립하고").replace("도입 하고", "도입하고")
    line = line.replace("지원 하기", "지원하기").replace("확장 하고", "확장하고")
    line = line.replace("확대 하고", "확대하고").replace("시행 하고", "시행하고")
    line = line.replace("구축 하고", "구축하고").replace("추진 하여", "추진하여")
    line = line.replace("대응 하여", "대응하여").replace("변화 하는", "변화하는")
    line = line.replace("사용 되며", "사용되며").replace("될 수", "될 수")
    line = line.replace("도움 이 될", "도움이 될").replace("대상 으로", "대상으로")
    line = line.replace("원칙 으로", "원칙으로").replace("지급 받을", "지급받을")
    line = line.replace("지급 받", "지급받").replace("신 청", "신청").replace("여건 에", "여건에")
    line = line.replace("국민의 70% 를", "국민의 70%를").replace("1 인당", "1인당")
    line = line.replace("10 만원", "10만원").replace("20 만원", "20만원")
    line = line.replace("25 만원", "25만원").replace("45 만원", "45만원").replace("55 만원", "55만원")
    line = line.replace("30 억원", "30억원").replace("2 주", "2주")
    line = line.replace("나가기로하였다", "나가기로 하였다")
    line = line.replace("4 월", "4월").replace("5 월", "5월").replace("8 월", "8월")
    line = line.replace("4. 27.", "4.27.").replace("5. 18.", "5.18.").replace("7. 3.", "7.3.")
    line = line.replace("개최 하고", "개최하고").replace("부터 피해지원금", "부터 피해지원금")
    line = line.replace("부터는 그 외", "부터는 그 외").replace("원칙으로한다", "원칙으로 한다")
    line = line.replace("사용하여야한다", "사용하여야 한다").replace("도움이될", "도움이 될")
    line = line.replace("되어야한다", "되어야 한다").replace("버팀목이될", "버팀목이 될")
    line = line.replace("지원금이될", "지원금이 될").replace("신청을할", "신청을 할")
    line = line.replace("개최 하고,", "개최하고,").replace("개최 하고", "개최하고")
    line = line.replace("부터 피해지원금", "부터 피해지원금").replace("부 터", "부터")
    line = line.replace("70% 의", "70%의").replace("5 만원", "5만원").replace("15 만원", "15만원")
    line = line.replace("60 만원", "60만원").replace("24 시간", "24시간").replace("9 시", "9시")
    line = line.replace("18 시", "18시").replace("한부모가족 대상자에 대하여는", "한부모가족 대상자에 대해서는")
    line = line.replace("피해 지원금", "피해지원금").replace("지원 규모", "지원규모")
    line = line.replace("도움이 될 수", "도움이 될 수").replace("도움이 될", "도움이 될")
    line = line.replace("개별적으로", "개별적으로").replace("이 의신청", "이의신청")
    line = line.replace("국민 께는", "국민께는").replace("사 전", "사전")
    line = line.replace("하 위지역", "하위지역").replace("사 이에", "사이에")
    line = line.replace("국외에 체류 중 이던", "국외에 체류 중이던")
    line = line.replace("받으실 수", "받으실 수").replace("받을 수", "받을 수")
    line = line.replace("인터넷 주소 클릭", "인터넷 주소 클릭")
    line = re.sub(r"([가-힣])\s+(하고|하며|하여|해서|되고|되며|되는|받은|받을|받고|준다|될|될 수)\b", r"\1\2", line)
    line = re.sub(r"\s+([,.;!?])", r"\1", line)
    line = re.sub(r"\s{2,}", " ", line)
    return line.strip()


def cleanup_body_lines(lines: list[str]) -> list[str]:
    out = []
    blank = False
    for line in lines:
        prefix = "  " if line.startswith("  - ") else ""
        body = line[2:] if prefix else line
        cleaned = (prefix + cleanup_line_spacing(body)) if line.strip() else ""
        if not cleaned:
            if not blank:
                out.append("")
            blank = True
            continue
        out.append(cleaned)
        blank = False
    while out and not out[-1]:
        out.pop()
    return out


def filter_image_appendix_sections(lines: list[str]) -> list[str]:
    out: list[str] = []
    skip = False
    for line in lines:
        stripped = line.strip()
        if "| 붙임" in stripped and "카드뉴스" in stripped:
            out.append(f"## {stripped.replace('|', ' ').strip()}")
            out.append("")
            out.append("_이미지형 부록이라 본문 ground-truth에서 제외_")
            out.append("")
            skip = True
            continue
        if skip and stripped.startswith("|") and "---" in stripped:
            continue
        if stripped.startswith("## ") and "카드뉴스" in stripped:
            out.append(line)
            out.append("")
            out.append("_이미지형 부록이라 본문 ground-truth에서 제외_")
            out.append("")
            skip = True
            continue
        if skip and stripped.startswith("## 붙임") and "카드뉴스" not in stripped:
            skip = False
        if skip:
            continue
        out.append(line)
    while out and not out[-1]:
        out.pop()
    return out


def build_document(news_id: str) -> str:
    item = load_item(news_id)
    article_html = requests.get(item["original_url"], timeout=30).text
    iframe_src = parse_iframe_src(article_html)
    result_base = urljoin(SITE_ROOT, re.search(r"rs=([^&]+)", iframe_src).group(1))
    body_lines: list[str] = []
    for page_html in iter_result_pages(result_base):
        body_lines.extend(render_body(page_html))
        if body_lines and body_lines[-1] != "":
            body_lines.append("")
    body_lines = cleanup_body_lines(body_lines)
    body_lines = filter_image_appendix_sections(body_lines)

    attachments = [att["file_name"] for att in item.get("attachments", [])]
    lines = [
        f"# {item['title']}",
        "",
        "- 출처: 대한민국 정책브리핑 보도자료",
        f"- 부처: {item['department']}",
        f"- 게시 시각: {item['approve_date']}",
        f"- 기사 URL: {item['original_url']}",
    ]
    for att in attachments:
        if att.lower().endswith(".hwpx"):
            lines.append(f"- HWPX 첨부: {att}")
        if att.lower().endswith(".pdf"):
            lines.append(f"- PDF 첨부: {att}")
    lines.extend(["", "## 본문", ""])
    lines.extend(body_lines)
    if attachments:
        lines.extend(["", "## 첨부파일", ""])
        lines.extend([f"- {att}" for att in attachments])
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("news_id")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    content = build_document(args.news_id)
    Path(args.output).write_text(content)


if __name__ == "__main__":
    main()
