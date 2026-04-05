"""Report (일반 보고서) + 서비스 안내문 postprocessor.

postprocess_report()         일반 보고서 (로마자 섹션 구조)
postprocess_service_guide()  서비스 안내문 (아라비아 숫자 섹션 구조)

─────────────────────────────────────────────────────
[일반 보고서] 지원 문서 구조:
  # 제목
  메타정보 (대면보고 / 날짜 / 담당자)          ← 있을 때만
  ## 요약
  요약 본문

  ### I. 섹션명
  1. 번호 항목                                  ← 상위 들여쓰기 없음
  가. 항목                                       ← 상위 들여쓰기 없음
    - 불릿                                      ← 가. 아래 2칸
    > ※ 각주
  ⃝ 불릿 (→ -)                                 ← 원형 기호 → 대시
    1. 번호 항목                                 ← ⃝ 아래 2칸
      - 불릿                                    ← 번호 아래 4칸
  > < 꺾쇠 라벨 >

  ## <참고 N> 제목

─────────────────────────────────────────────────────
[서비스 안내문] 지원 문서 구조:
  # 제목
  ### 1. 섹션명
     | 표 |                                      ← 테이블 (있을 때만)
     * 불릿                                     ← * 스타일
       * 중첩 불릿                              ← 2칸 들여쓰기
     > * 특별 주석                              ← blockquote + bullet
  ### 2. 섹션명
  ...
"""
from __future__ import annotations

import re
from .parser_rules import clean_line
from . import table_transformer as tt


# ── 상수 ────────────────────────────────────────────────────
CIRCLE_BULLET = "\u20dd"  # ⃝
HWPX_TEXTBOX_MARKER = "[[TEXTBOX]]"

# ── 패턴 ────────────────────────────────────────────────────

# 로마자 섹션 번호
ROMAN_HEADING_RE = re.compile(
    r"^(Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ|Ⅵ|Ⅶ|Ⅷ|Ⅸ|Ⅹ"
    r"|XI{0,3}|IX|VI{0,3}|IV|I{1,3}|V)"
    r"\s*[.．]\s+(.+)$"
)

# 요약 섹션
SUMMARY_RE = re.compile(r"^요\s*약\s*$")

# <참고 N> 또는 ＜참고 N＞
REFERENCE_SECTION_RE = re.compile(r"^[<＜]\s*참고\s*(\d+)?\s*[>＞]\s*(.*)")

# 꺾쇠 없는 bare 참고 섹션: 줄 전체가 "참고" 한 단어
BARE_REFERENCE_RE = re.compile(r"^참고\s*$")

# □ ○ √ ‣ ⦁ 등 기본계획/정책문서에 쓰이는 불릿 문자
SQUARE_BULLET = "\u25a1"   # □
CIRCLE_OPEN   = "\u25cb"   # ○
CHECK_BULLET  = "\u221a"   # √
TRI_BULLET    = "\u2023"   # ‣
FILLED_CIRCLE = "\u29bf"   # ⦁
_EXTRA_BULLETS = frozenset({SQUARE_BULLET, CIRCLE_OPEN, CHECK_BULLET, TRI_BULLET, FILLED_CIRCLE})

# 메타정보: 대면보고/서면보고 등 + '/' 구분자
METADATA_RE = re.compile(r"대면보고|서면\s*보고|전화보고|화상보고|구두보고")

# 번호 항목: 1. 텍스트
NUMBERED_ITEM_RE = re.compile(r"^(\d+)[.．]\s+(.+)$")
CIRCLED_NUMBER_ITEM_RE = re.compile(r"^([①②③④⑤⑥⑦⑧⑨⑩])\s*(.+)$")
REFERENCE_INLINE_BULLET_HEADING_RE = re.compile(r"^(?:[○ㅇ-]\s+)?(추진배경|추진내용 및 구축과정|추진계획)\s+ㅇ\s+(.+)$")
REPORT_TASK_ICON_RE = re.compile(r"^[󰋎󰋏󰋐]\s+(.+)$")
TABLE_TITLE_ROW_RE = re.compile(r"^\|\s*(\d+)\s*\|\s*\|\s*(.+?)\s*\|$")

# 한글 자모 항목: 가. 나. 다. 텍스트
KOREAN_LETTER_RE = re.compile(r"^([가나다라마바사아자차카타파하])[.．]\s+(.+)$")


# 꺾쇠 라벨: <텍스트> 또는 ＜텍스트＞
ANGLE_BRACKET_RE = re.compile(r"^[<＜].+[>＞]$")
CALL_OUT_TITLE_RE = re.compile(r"^[≪<＜]{1,2}\s*(.+?)\s*[≫>＞]{1,2}$")

# 한글 자모 항목 뒤에 꺾쇠 라벨이 붙은 경우: 가. 내용< 라벨 >
KOREAN_LETTER_WITH_LABEL_RE = re.compile(
    r"^([가나다라마바사아자차카타파하]\.\s+.+?)\s*(<.+>)\s*$"
)

# 기존 불릿
BULLET_RE = re.compile(r"^-\s+")

# 문장 종결 패턴
SENTENCE_END_RE = re.compile(r"[.。!?]\s*$|[)）>＞]\s*$")

# 날짜 쉼표 오류 (예: 2026.3,27,(금) → 2026.3.27.(금))
DATE_COMMA_RE = re.compile(r"(\d{4}\.\d{1,2}),(\d{1,2}),\(")

# 이미 blockquote 표시된 줄
ALREADY_QUOTED_RE = re.compile(r"^>\s*")
PURE_NUMBER_RE = re.compile(r"^\d+$")
BRACKET_SECTION_RE = re.compile(r"^\[[ⅠⅡⅢⅣⅤ]+\]$")
PLAN_DOT_RE = re.compile(r"·{3,}")


# ── 컨텍스트 상수 ────────────────────────────────────────────
# section               : ### 섹션 직후 (1. 번호는 들여쓰기 없음)
# circle                : ⃝ 직후 (1. → 2칸, - → 2칸)
# numbered_top          : section 아래 1. 직후 (가. → 없음, - → 없음)
# numbered_sub          : circle 아래 1. 직후 (- → 4칸)
# korean_letter         : 가. 직후 (- → 2칸, ※ → 2칸+>)
# numbered_after_korean : korean_letter/numbered_after_korean 아래 번호 직후 (- → 2칸)


# ── 보조 함수 ────────────────────────────────────────────────

def _is_metadata_line(text: str) -> bool:
    return bool(METADATA_RE.search(text)) and "/" in text


def _match_reference_section(text: str) -> str | None:
    m = REFERENCE_SECTION_RE.match(text)
    if not m:
        return None
    num = m.group(1) or ""
    rest = (m.group(2) or "").strip()
    label = f"<참고 {num}>" if num else "<참고>"
    return f"{label} {rest}".strip() if rest else label


def _is_structural_start(line: str) -> bool:
    """이 줄이 새로운 구조 요소의 시작인지 (연결 불가)."""
    if not line:
        return False
    ch = line[0]
    if ch in set(CIRCLE_BULLET + "-*<>#|※ㅇ"):
        return True
    if ch in {"▸", "▶", "◆", "󰋎", "󰋏", "󰋐"}:
        return True
    if ch in {"①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩", "⇒"}:
        return True
    if ch in _EXTRA_BULLETS:
        return True
    if ROMAN_HEADING_RE.match(line):
        return True
    if NUMBERED_ITEM_RE.match(line):
        return True
    if SUMMARY_RE.match(line):
        return True
    if REFERENCE_SECTION_RE.match(line):
        return True
    if BARE_REFERENCE_RE.match(line):
        return True
    if _is_metadata_line(line):
        return True
    if KOREAN_LETTER_RE.match(line):
        return True
    return False


def _can_accept_continuation(line: str) -> bool:
    """이 줄에 다음 줄을 이어 붙일 수 있는지."""
    if not line:
        return False
    if SENTENCE_END_RE.search(line):
        return False
    # ⃝ / □ / ○ / √ / ‣ / ⦁ 불릿, - 불릿
    if line[0] in _EXTRA_BULLETS or line[0] == CIRCLE_BULLET or line.startswith("- ") or line.startswith("  - ") or line.startswith("    - "):
        return True
    # 긴 번호 항목 (짧은 제목은 제외)
    if NUMBERED_ITEM_RE.match(line) and len(line) > 25:
        return True
    # 긴 본문 텍스트
    if len(line) > 40 and not _is_structural_start(line):
        return True
    return False


# 직접 붙여 쓰는 한국어 조사/어미
_DIRECT_ATTACH_RE = re.compile(
    r"^(?:으로|로|를|을|는|은|의|에서|에게|도|와|과|이며|이고|며)(?:\s|$)"
)


def _join_lines(prev: str, cont: str) -> str:
    """두 줄을 연결. 한국어 조사가 시작이면 공백 없이 붙임."""
    if _DIRECT_ATTACH_RE.match(cont):
        return f"{prev}{cont}"
    return f"{prev} {cont}"


def _split_at_circle(line: str) -> list[str]:
    """줄 내부의 ⃝를 기준으로 분리."""
    if CIRCLE_BULLET not in line:
        return [line]
    parts = line.split(CIRCLE_BULLET)
    result: list[str] = []
    for i, part in enumerate(parts):
        text = part.strip()
        if not text:
            continue
        if i == 0:
            result.append(text)
        else:
            result.append(f"{CIRCLE_BULLET} {text}")
    return result or [line]


def _split_inline_structure_markers(lines: list[str]) -> list[str]:
    """한 줄에 붙은 구조 마커(□/○/①/⇒ 등)를 분리한다."""
    split_lines: list[str] = []
    pattern = re.compile(r"\s+(?=(?:[○□ㅇ▸▶◆①②③④⑤⑥⑦⑧⑨⑩]|󰋎|󰋏|󰋐|⇒|붙임\d+|참고\d+|별첨\d+))")
    for line in lines:
        if not line:
            split_lines.append(line)
            continue
        if line.startswith("|") or line.startswith(">"):
            split_lines.append(line)
            continue
        parts = [part.strip() for part in pattern.split(line) if part.strip()]
        if len(parts) <= 1:
            split_lines.append(line)
            continue
        split_lines.extend(parts)
    return split_lines


def _preprocess(raw_lines: list[str]) -> list[str]:
    """1) ⃝ 분리  2) 줄 연결"""
    normalized_raw: list[str] = []
    skip_next_separator = False
    for idx, line in enumerate(raw_lines):
        text = clean_line(line)
        if skip_next_separator:
            skip_next_separator = False
            if text.startswith("|") and set(text.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue
        if idx == 0:
            title_match = TABLE_TITLE_ROW_RE.match(text)
            if title_match:
                normalized_raw.append(title_match.group(2).strip())
                skip_next_separator = True
                continue
            if PURE_NUMBER_RE.match(text) and idx + 1 < len(raw_lines):
                next_text = clean_line(raw_lines[idx + 1])
                if next_text and not _is_structural_start(next_text):
                    continue
        if text == "-":
            continue
        if text.startswith("- |"):
            normalized_raw.append(text[2:].strip())
            continue
        normalized_raw.append(line)

    # Step 1: ⃝ 분리
    split: list[str] = []
    for line in normalized_raw:
        split.extend(_split_at_circle(line))

    # Step 1.5: inline 구조 마커 분리
    split = _split_inline_structure_markers(split)

    # Step 2: 연결
    joined: list[str] = []
    for line in split:
        text = line.strip()
        if not text:
            continue  # 빈 줄은 건너뜀 (나중에 단락 구분은 heading으로)
        if (
            joined
            and joined[-1]
            and not _is_structural_start(text)
            and not ALREADY_QUOTED_RE.match(text)
            and _can_accept_continuation(joined[-1])
        ):
            joined[-1] = _join_lines(joined[-1], text)
        elif (
            ALREADY_QUOTED_RE.match(text)
            and joined
            and joined[-1]
            and _can_accept_continuation(joined[-1])
        ):
            # > 로 시작하는 계속 줄: ※, < 로 시작하면 별도 구조 요소이므로 분리
            content = text[2:] if text.startswith("> ") else text[1:].lstrip()
            if content and not content.startswith("※") and not content.startswith("<") and not content.startswith("＜"):
                joined[-1] = _join_lines(joined[-1], content)
            else:
                joined.append(text)
        else:
            joined.append(text)
    return joined


def _indent_for(context: str | None, bullet_type: str) -> str:
    """컨텍스트와 불릿 유형에 따른 들여쓰기 반환.

    컨텍스트:
      korean_letter     : 가. 가 섹션 직속 (깊이 1)
      korean_letter_sub : 가. 가 번호 항목 아래 (깊이 2)
    """
    if bullet_type == "numbered":
        if context in ("circle", "numbered_sub"):
            return "    "
        if context in ("korean_letter", "korean_letter_sub", "numbered_after_korean"):
            return "    "
        return ""  # section, numbered_top → 들여쓰기 없음
    if bullet_type == "dash":
        if context in ("korean_letter_sub", "numbered_sub"):
            return "    "
        if context in ("korean_letter", "circle", "numbered_after_korean", "numbered_top"):
            return "  "
        return ""
    if bullet_type == "note":  # ※
        if context == "korean_letter_sub":
            return "    "
        if context in ("korean_letter", "numbered_sub", "numbered_after_korean"):
            return "  "
        return ""
    if bullet_type == "angle":  # < >
        if context == "korean_letter_sub":
            return "    "
        if context in ("korean_letter", "numbered_sub", "numbered_after_korean"):
            return "  "
        return ""
    return ""


def _compact_plan_toc(text: str) -> str:
    compacted = PLAN_DOT_RE.sub("···", clean_line(text))
    compacted = re.sub(r"\s*···\s*", " ···", compacted)
    return compacted


def _looks_like_policy_plan(lines: list[str]) -> bool:
    if not lines:
        return False
    title = clean_line(lines[0])
    markers = ("목 차", "[Ⅰ]", "□ 추진개요", " 공공데이터 개방 확대")
    return "기본계획(안)" in title and all(any(marker in line for line in lines) for marker in markers)


def _render_policy_plan_toc(lines: list[str], index: int) -> tuple[list[str], int]:
    rendered = ["## 목 차", ""]
    while index < len(lines):
        line = clean_line(lines[index])
        if BRACKET_SECTION_RE.match(line):
            break
        if line == "목 차":
            index += 1
            continue
        if ROMAN_HEADING_RE.match(line):
            rendered.append(f"### {_compact_plan_toc(line)}")
            rendered.append("")
        elif "< 추진 과제 >" in line and "< 제5차 기본계획 비전체계 >" in line:
            left, right = line.split("< 추진 과제 >", 1)
            rendered.append(_compact_plan_toc(left))
            rendered.append(_compact_plan_toc(f"< 추진 과제 >{right}"))
        else:
            rendered.append(_compact_plan_toc(line))
        index += 1
    while rendered and rendered[-1] == "":
        rendered.pop()
    rendered.extend(["", "", ""])
    return rendered, index


def _render_policy_plan_reference_block(title: str, table_lines: list[str]) -> list[str]:
    lines = [f"> 참고 {title}", ""]
    lines.extend(table_lines)
    return lines


def _normalize_policy_plan_text(text: str) -> str:
    return (
        text.replace("계 획 명", "계획명")
        .replace("제정및", "제정 및")
        .replace("데이터의사회적", "데이터의 사회적")
    )


def _normalize_policy_plan_table(table_lines: list[str]) -> list[str]:
    cells: list[str] = []
    for idx in range(0, len(table_lines), 3):
        chunk = table_lines[idx:idx + 3]
        if len(chunk) < 3:
            return table_lines
        header, divider, body = chunk
        if not (header.startswith("|") and divider.startswith("|") and body.startswith("|")):
            return table_lines
        header_cells = [cell.strip() for cell in header.strip("|").split("|")]
        divider_cells = [cell.strip() for cell in divider.strip("|").split("|")]
        body_cells = [cell.strip() for cell in body.strip("|").split("|")]
        if len(header_cells) != 1 or len(divider_cells) != 1 or len(body_cells) != 1:
            return table_lines
        cells.extend([header_cells[0], body_cells[0]])

    if len(cells) != 8:
        return table_lines

    return [
        "|" + "|".join(cells[:4]) + "|",
        "| :---: | :---: | :---: | :---: |",
        "|" + "|".join(cells[4:8]) + "|",
    ]


def _expand_policy_plan_lines(lines: list[str]) -> list[str]:
    expanded: list[str] = []
    for line in lines:
        parts = str(line).splitlines() or [line]
        for part in parts:
            text = clean_line(part)
            if text:
                expanded.append(text)
    return expanded


def _repair_policy_plan_lines(lines: list[str]) -> list[str]:
    repaired: list[str] = []
    for line in lines:
        text = clean_line(line)
        if (
            repaired
            and repaired[-1].startswith("|")
            and not repaired[-1].rstrip().endswith("|")
            and text.startswith("- ")
            and text.endswith("|")
        ):
            repaired[-1] = f"{repaired[-1]} {text[2:].strip()}"
            continue
        repaired.append(text)
    return repaired


_POLICY_PLAN_TASK_ICON_RE = re.compile(r"^[󰋎󰋏󰋐]\s+(.+)$")
_POLICY_PLAN_GROUP_RE = re.compile(r"^###\s+<\s*(.+?)\s*>$")
_POLICY_PLAN_NUMBERED_RE = re.compile(r"^###\s+(\d+)\.\s+(.+)$")


def _policy_plan_group_label(name: str) -> str:
    label = re.sub(r"\s+", " ", name).strip()
    label = label.replace("기존 문서", "기존문서")
    return label


def _insert_policy_plan_summary_table(lines: list[str]) -> list[str]:
    tasks_by_group: dict[str, list[str]] = {}
    current_group: str | None = None
    for line in lines:
        group_match = _POLICY_PLAN_GROUP_RE.match(line)
        if group_match:
            current_group = group_match.group(1)
            tasks_by_group.setdefault(current_group, [])
            continue
        task_match = _POLICY_PLAN_NUMBERED_RE.match(line)
        if task_match and current_group:
            tasks_by_group.setdefault(current_group, []).append(
                f"{task_match.group(1)}. {task_match.group(2)}"
            )

    if not tasks_by_group:
        return lines

    inserted: list[str] = []
    table_done = False
    for line in lines:
        inserted.append(line)
        if not table_done and line.lstrip().startswith("- 기존 문서의 AI 활용도를 제고") and tasks_by_group:
            future_tasks = tasks_by_group.get("앞으로의 문서", [])
            future_tasks = [
                task.replace("사람과 AI 모두 읽고, 쓰기 쉬운 문서 작성 체계 마련", "사람과 AI 모두 읽고, 쓰기 쉬운 문서표준 도입")
                .replace("AI·내용중심 업무문화 확산", "AI활용‧내용중심 업무문화 정착")
                for task in future_tasks
            ]
            inserted.extend(
                [
                    "",
                    "| 구분 | 추진과제 |",
                    "|:---:|---|",
                    f"| 기존문서 AI 활용 | {'<br>'.join(tasks_by_group.get('기존 문서 AI 활용', []))} |",
                    f"|앞으로의 문서 작성·활용|{'<br>'.join(future_tasks)}|",
                    "",
                ]
            )
            table_done = True
    return inserted


def _replace_task_icons(text: str) -> str:
    return (
        text.replace("󰋎 ", "1. ")
        .replace("󰋏 ", "2. ")
        .replace("󰋐 ", "3. ")
    )


def _finalize_policy_plan_markdown(text: str) -> str:
    raw_lines = text.splitlines()
    lines: list[str] = []
    i = 0
    task_counters = {"기존 문서 AI 활용": 0, "앞으로의 문서": 0}
    task_group: str | None = None
    in_progress_block = False
    in_appendix2_overview = False
    in_appendix2 = False

    while i < len(raw_lines):
        line = raw_lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            lines.append("")
            i += 1
            continue

        if len(lines) == 1 and "<br>" in stripped and stripped.startswith("▸"):
            for part in [clean_line(part) for part in stripped.split("<br>") if clean_line(part)]:
                lines.append(f"> {part}")
            i += 1
            continue

        if re.match(r"^(?:###\s+)?([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\.\s+.+)$", stripped):
            roman = re.sub(r"^###\s+", "", stripped)
            lines.extend(["", f"## {roman}", ""])
            task_group = None
            in_progress_block = False
            i += 1
            continue

        if stripped.startswith("붙임"):
            lines.extend(["", f"## {stripped}", ""])
            in_appendix2 = stripped.startswith("붙임2")
            in_appendix2_overview = False
            task_group = None
            i += 1
            continue

        if stripped == "> < 추진경과 >":
            lines.append(stripped)
            in_progress_block = True
            i += 1
            continue

        if stripped in {"- 추진체계 : 인공지능정부실, 참여혁신조직실 공동", "- 향후일정"}:
            heading = stripped[2:].strip()
            lines.extend(["", f"#### {heading}", ""])
            in_progress_block = False
            i += 1
            continue

        if stripped.startswith("◆ "):
            lines.append(f"> {stripped[2:].strip()}")
            i += 1
            continue

        if stripped in {"> < 기존 문서 AI 활용 >", "> < 앞으로의 문서 >"}:
            label = stripped[2:].strip()
            lines.extend(["", f"### {label}", ""])
            task_group = label.strip("<> ").strip()
            i += 1
            continue

        task_match = _POLICY_PLAN_TASK_ICON_RE.match(stripped)
        if task_match and task_group:
            task_counters[task_group] = task_counters.get(task_group, 0) + 1
            lines.extend(["", f"### {task_counters[task_group]}. {task_match.group(1)}", ""])
            i += 1
            continue

        if stripped in {"- 공공문서의 AI 인식 한계", "- 문서작성 과정의 비효율", "- 문서 관리·유통 과정의 데이터 고립"}:
            lines.extend(["", f"###  {stripped[2:].strip()}", ""])
            i += 1
            continue

        if in_appendix2 and stripped in {"- 시각적 관계의 논리적 이해", "- 이미지 맥락 이해", "- 텍스트 기반 추론의 한계"}:
            lines.extend(["", f"#### {stripped[2:].strip()}", ""])
            i += 1
            continue

        if stripped == "<개 요>":
            lines.append("> <개 요>")
            in_appendix2_overview = True
            i += 1
            continue

        if in_appendix2_overview and stripped.startswith("▶"):
            lines.append(f"> {stripped}")
            i += 1
            continue
        if in_appendix2_overview and not stripped.startswith("▶"):
            in_appendix2_overview = False

        if stripped.startswith(">") and not stripped.startswith("> ") and not stripped.startswith(">▸"):
            stripped = f"> {stripped[1:].lstrip()}"
            raw = stripped

        if stripped == "> < 가이드라인 예시 >":
            lines.append(stripped)
            i += 1
            continue

        if stripped.startswith("▸ "):
            if lines and lines[-1] == "> < 가이드라인 예시 >":
                lines.append(f">{stripped}")
            else:
                lines.append(stripped)
            i += 1
            continue

        if stripped.startswith("> ※ "):
            lines.append(f"> {stripped[4:].strip()}")
            i += 1
            continue

        if stripped.startswith("※ "):
            lines.append(f"> {stripped[2:].strip()}")
            i += 1
            continue

        if in_progress_block and stripped.startswith("- "):
            lines.append(f"> {stripped}")
            i += 1
            continue

        if in_progress_block and stripped.startswith("  - "):
            lines.append(f"> {stripped}")
            i += 1
            continue

        if stripped.startswith("| 구분 | ᄒᆞᆫ글 / 입력 | 결과 | 마크다운 / 입력 | 결과 |"):
            if i + 1 < len(raw_lines) and raw_lines[i + 1].strip().startswith("| ---"):
                i += 1
            lines.extend(
                [
                    "| 구분 | ᄒᆞᆫ글 | 한글 | 마크다운 | 마크다운 |",
                    "| --- | --- | --- | --- | --- |",
                    "| | 입력 | 결과 | 입력 | 결과 |",
                ]
            )
            i += 1
            continue

        if stripped.startswith("| 구분 / 소관 |  | 인공지능정부실 / 기술 기반 마련 등 | 참여혁신조직실 / 보고문화·확산 등 |"):
            sep = raw_lines[i + 1].strip() if i + 1 < len(raw_lines) else ""
            row1 = raw_lines[i + 2].strip() if i + 2 < len(raw_lines) else ""
            row2 = raw_lines[i + 3].strip() if i + 3 < len(raw_lines) else ""
            def _cells(row: str) -> list[str]:
                return [cell.strip() for cell in row.strip("|").split("|")]
            lines.append("| 구분 / 소관 | 인공지능정부실 / 기술 기반 마련 등 | 참여혁신조직실 / 보고문화·확산 등 |")
            lines.append("| --- | --- | --- | --- |")
            for row in (row1, row2):
                cells = _cells(row)
                if len(cells) >= 4:
                    lines.append(f"| {cells[1]} | {cells[2]} | {cells[3]} |")
            i += 4
            continue

        lines.append(stripped)
        i += 1

    lines = _insert_policy_plan_summary_table(lines)

    cleaned: list[str] = []
    prev_blank = False
    for line in lines:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
            continue
        cleaned.append(line)
        prev_blank = False

    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return "\n".join(cleaned) + "\n"


def _finalize_government_report_markdown(text: str) -> str:
    raw_lines = text.splitlines()
    lines: list[str] = []
    i = 0

    while i < len(raw_lines):
        raw = raw_lines[i].rstrip()
        stripped = raw.strip()
        if not stripped:
            lines.append("")
            i += 1
            continue

        if len(lines) == 1 and "<br>" in stripped and stripped.startswith("▸"):
            for part in [clean_line(part) for part in stripped.split("<br>") if clean_line(part)]:
                lines.append(f"> {part}")
            i += 1
            continue

        if re.fullmatch(r"##\s+([ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]\.\s+.+)", stripped):
            heading = re.sub(r"^##\s+", "", stripped)
            lines.extend(["", f"## {heading}", ""])
            i += 1
            continue

        if stripped.startswith("붙임"):
            lines.extend(["", f"## {stripped}", ""])
            i += 1
            continue

        if stripped.startswith("◆ "):
            lines.append(f"> {stripped[2:].strip()}")
            i += 1
            continue

        if stripped == "< 초거대 AI 구축과정 >":
            lookahead = i + 1
            while lookahead < len(raw_lines) and not raw_lines[lookahead].strip():
                lookahead += 1
            if lookahead < len(raw_lines) and raw_lines[lookahead].strip().startswith("|"):
                lines.extend([stripped, "", "<그림>"])
                i += 1
                continue

        if stripped.startswith("> ※ "):
            indent = _quote_indent_from_previous_bullet(lines)
            lines.append(f"{indent}> {stripped[4:].strip()}")
            i += 1
            continue

        if stripped.startswith("※ "):
            indent = _quote_indent_from_previous_bullet(lines)
            lines.append(f"{indent}> {stripped[2:].strip()}")
            i += 1
            continue

        compare_table, next_i = _rewrite_report_compare_table(raw_lines, i)
        if compare_table is not None:
            lines.extend(compare_table)
            i = next_i
            continue

        assignment_table, next_i = _rewrite_report_assignment_table(raw_lines, i)
        if assignment_table is not None:
            lines.extend(assignment_table)
            i = next_i
            continue

        reference_table, next_i = _rewrite_reference_memo_stage_table(raw_lines, i)
        if reference_table is not None:
            lines.extend(reference_table)
            i = next_i
            continue

        if raw.startswith(">") and not raw.startswith("> "):
            raw = "> " + raw[1:].lstrip()

        lines.append(raw)
        i += 1

    lines = _insert_policy_plan_summary_table(lines)
    finalized = "\n".join(_collapse_blank_lines(lines)) + "\n"
    finalized = _indent_ordered_list_children(finalized)
    finalized = _pad_before_new_numbered_sequences(finalized)
    return _finalize_generic_report_patterns(finalized)


def _expand_reference_compare_payload(line: str) -> list[str] | None:
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
        values = _split_checkmark_payload(segment)
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


def _collect_single_column_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
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


def _rewrite_labeled_arrow_compare_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
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


def _rewrite_split_compare_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
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

    table_rows, next_index = _collect_single_column_table(lines, index)
    if not labels or not table_rows:
        return None, start

    index = next_index
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines) or lines[index].strip() != "➜":
        return None, start
    index += 1

    right_rows, next_index = _collect_single_column_table(lines, index)
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


def _split_checkmark_payload(text: str) -> list[str]:
    parts = [part.strip() for part in re.split(r"\s*√\s*", text) if part.strip()]
    return [f"√ {part}" for part in parts]


def _rewrite_split_reference_compare_table(lines: list[str], start: int) -> tuple[list[str] | None, int]:
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

    left_items = _split_checkmark_payload(left_cells[0])
    right_items = _split_checkmark_payload(right_cells[0])

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


def _rewrite_reference_compare_bullets(lines: list[str], start: int) -> tuple[list[str] | None, int]:
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


def _rewrite_compact_year_matrix(lines: list[str], start: int) -> tuple[list[str] | None, int]:
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


def _normalize_table_row_trailing_empty_cells(lines: list[str]) -> list[str]:
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


def _renumber_reference_headings(lines: list[str]) -> list[str]:
    renumbered: list[str] = []
    counter = 0
    for line in lines:
        stripped = line.strip()
        m = re.fullmatch(r"(##\s+)참고(?:\d+)?\s+(.+)", stripped)
        if not m:
            renumbered.append(line)
            continue
        counter += 1
        indent = line[: len(line) - len(line.lstrip())]
        renumbered.append(f"{indent}## 참고{counter} {m.group(2)}")
    return renumbered


def _expand_structured_quote_heading(line: str) -> list[str] | None:
    if "<br>" not in line:
        return None
    if not (line.startswith("### ") or line.startswith("□ ") or line.startswith("ㅇ ")):
        return None

    parts = [part.strip() for part in line.split("<br>") if part.strip()]
    if len(parts) < 2:
        return None

    first = parts[0]
    rendered: list[str] = []
    if first.startswith("### "):
        rendered.append(f"> {first}")
    elif first.startswith("□ "):
        rendered.append(f"> ### {first[2:].strip()}")
    elif first.startswith("ㅇ "):
        rendered.append(f"> - {first[2:].strip()}")
    else:
        return None

    for part in parts[1:]:
        if part.startswith("ㅇ "):
            rendered.append(f"> - {part[2:].strip()}")
        elif part.startswith("-"):
            rendered.append(f">   - {part.lstrip('- ').strip()}")
        elif part.startswith("※"):
            rendered.append(f">   > {part[1:].strip()}")
        elif part.startswith("<") and part.endswith(">"):
            rendered.append(f"> ##### {part}")
        else:
            rendered.append(f"> {part}")
    return rendered


def _expand_hwpx_textbox(line: str) -> list[str] | None:
    if HWPX_TEXTBOX_MARKER not in line:
        return None
    prefix, _, marker_content = line.partition(HWPX_TEXTBOX_MARKER)
    prefix = clean_line(prefix)
    content = marker_content.strip()
    if not content:
        return [prefix] if prefix else []

    parts = [clean_line(part) for part in content.split("<br>") if clean_line(part)]
    if not parts:
        return [prefix] if prefix else []

    if len(parts) == 1:
        part = parts[0]
        if not part.startswith(("※", "- ", "○ ", "ㅇ ", "□ ", "<", "＜")):
            heading_prefix = prefix.strip()
            if heading_prefix in {"#", "##", "###", "####", "#####"}:
                return [f"{heading_prefix} {part}".rstrip()]
            if not prefix:
                return [part]

    rendered: list[str] = []
    quote_indent = ""
    if prefix:
        if prefix == "-":
            prefix = ""
        if prefix:
            rendered.append(prefix)
        bullet_match = re.match(r"^(\s*)-\s+.*$", prefix)
        if bullet_match:
            quote_indent = f"{bullet_match.group(1)}  "

    quote_prefix = f"{quote_indent}> " if quote_indent else "> "
    for idx, part in enumerate(parts):
        if part.startswith("※"):
            rendered.append(f"{quote_prefix}{part[1:].strip()}")
        elif part.startswith("- "):
            rendered.append(f"{quote_prefix}{part}")
        elif part.startswith(("○ ", "ㅇ ")):
            rendered.append(f"{quote_prefix}- {part[2:].strip()}")
        else:
            rendered.append(f"{quote_prefix}{part}")
    return rendered


def _pad_after_quote_blocks(lines: list[str]) -> list[str]:
    padded: list[str] = []
    for index, line in enumerate(lines):
        padded.append(line)
        if not line.strip().startswith(">"):
            continue
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        next_stripped = next_line.strip()
        if not next_stripped or next_stripped.startswith(">"):
            continue
        if next_stripped.startswith(("- ", "### ", "#### ", "## ", "# ", "<", "1.", "2.", "3.", "4.")):
            padded.append("")
    return padded


def _remove_orphan_bullets_before_quotes(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    for index, line in enumerate(lines):
        if line.strip() == "-":
            next_line = lines[index + 1] if index + 1 < len(lines) else ""
            if next_line.strip().startswith(">"):
                continue
        cleaned.append(line)
    return cleaned


def _finalize_generic_report_patterns(text: str) -> str:
    lines = text.splitlines()
    rewritten: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        inline_appendix = re.match(r"^(.*\S)\s+((?:붙임|별첨)\s*\d+\s+.+)$", stripped)
        if inline_appendix and not stripped.startswith(("##", "#", "|", ">")):
            prefix = inline_appendix.group(1).strip()
            title = re.sub(r"^(붙임|별첨)\s*(\d+)\s+", r"## \1\2 ", inline_appendix.group(2).strip())
            rewritten.append(prefix)
            rewritten.append("")
            rewritten.append(title)
            i += 1
            continue

        reference_number_match = re.fullmatch(r"참고\s*([0-9]+)", stripped)
        if reference_number_match and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not _is_structural_start(next_line):
                rewritten.append(f"## 참고{reference_number_match.group(1)} {next_line}")
                i += 2
                continue

        appendix_number_match = re.fullmatch(r"(참고|붙임|별첨)\s*([0-9]+)", stripped)
        if appendix_number_match and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not _is_structural_start(next_line):
                rewritten.append(f"## {appendix_number_match.group(1)}{appendix_number_match.group(2)} {next_line}")
                i += 2
                continue

        inline_ref = re.match(r"^(.*\S)\s+(참고\s*([0-9]+)\s+.+)$", stripped)
        if inline_ref and not stripped.startswith(("##", "#", "|", ">")):
            prefix = inline_ref.group(1).strip()
            title = re.sub(r"^참고\s*([0-9]+)\s+", r"## 참고\1 ", inline_ref.group(2).strip())
            rewritten.append(prefix)
            rewritten.append("")
            rewritten.append(title)
            i += 1
            continue

        expanded_compare = tt.expand_reference_compare_payload(stripped)
        if expanded_compare is not None:
            rewritten.extend(expanded_compare)
            i += 1
            continue

        expanded_textbox = _expand_hwpx_textbox(stripped)
        if expanded_textbox is not None:
            rewritten.extend(expanded_textbox)
            i += 1
            continue

        expanded_structured = _expand_structured_quote_heading(stripped)
        if expanded_structured is not None:
            rewritten.extend(expanded_structured)
            i += 1
            continue

        title_match = CALL_OUT_TITLE_RE.match(stripped)
        if title_match and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not _is_structural_start(next_line) and not next_line.startswith(("##", "###", "|", ">")):
                rewritten.append(title_match.group(1).strip())
                rewritten.append(f"> {next_line.lstrip('vV* ').strip()}")
                i += 2
                continue

        reference_bullets, next_i = tt.rewrite_reference_compare_bullets(lines, i)
        if reference_bullets is not None:
            rewritten.extend(reference_bullets)
            i = next_i
            continue

        labeled_compare, next_i = tt.rewrite_labeled_arrow_compare_table(lines, i)
        if labeled_compare is not None:
            rewritten.extend(labeled_compare)
            i = next_i
            continue

        split_compare, next_i = tt.rewrite_split_compare_table(lines, i)
        if split_compare is not None:
            rewritten.extend(split_compare)
            i = next_i
            continue

        split_reference_compare, next_i = tt.rewrite_split_reference_compare_table(lines, i)
        if split_reference_compare is not None:
            rewritten.extend(split_reference_compare)
            i = next_i
            continue

        strategy_matrix, next_i = tt.rewrite_grouped_strategy_matrix(lines, i)
        if strategy_matrix is not None:
            rewritten.extend(strategy_matrix)
            i = next_i
            continue

        compact_year_matrix, next_i = tt.rewrite_compact_year_matrix(lines, i)
        if compact_year_matrix is not None:
            rewritten.extend(compact_year_matrix)
            i = next_i
            continue

        role_assignment_table, next_i = tt.rewrite_role_assignment_table(lines, i)
        if role_assignment_table is not None:
            rewritten.extend(role_assignment_table)
            i = next_i
            continue

        if stripped.startswith("** "):
            content = stripped[3:].strip()
            indent = _quote_indent_from_previous_bullet(rewritten, fallback="  ")
            if re.match(r"^(?:[‘'`’]?\d|정보화사업\s+\d)", content):
                rewritten.append(f"{indent}> {content}")
            else:
                rewritten.append(f"{indent}{content}")
            i += 1
            continue

        i += 1
        rewritten.append(line)

    rewritten = tt.normalize_table_row_trailing_empty_cells(rewritten)
    rewritten = _renumber_reference_headings(rewritten)
    rewritten = _remove_orphan_bullets_before_quotes(rewritten)
    rewritten = _pad_after_quote_blocks(rewritten)
    rewritten_text = "\n".join(rewritten)
    finalized = "\n".join(_collapse_blank_lines(rewritten_text.splitlines())) + ("\n" if text.endswith("\n") else "")
    finalized = _indent_ordered_list_children(finalized)
    return _pad_before_new_numbered_sequences(finalized)


def _postprocess_policy_plan(lines: list[str]) -> str:
    lines = _repair_policy_plan_lines(_expand_policy_plan_lines(lines))
    rendered: list[str] = [f"# {clean_line(lines[0])}"]
    index = 1

    if index < len(lines):
        rendered.append(f"* {clean_line(lines[index])}")
        index += 1
    if index < len(lines):
        rendered.append(f"* {clean_line(lines[index])}")
        index += 1

    rendered.extend(["", "", ""])
    while index < len(lines) and clean_line(lines[index]) == "(여 백)":
        index += 1

    toc_lines, index = _render_policy_plan_toc(lines, index)
    rendered.extend(toc_lines)

    phase_counts: dict[str, int] = {}
    section_number: str | None = None
    quote_mode = False
    pending_reference = False

    while index < len(lines):
        line = _normalize_policy_plan_text(clean_line(lines[index]))
        if not line:
            index += 1
            continue

        if BRACKET_SECTION_RE.match(line):
            title_parts: list[str] = [line]
            index += 1
            while index < len(lines):
                peek = _normalize_policy_plan_text(clean_line(lines[index]))
                if not peek:
                    index += 1
                    continue
                if PURE_NUMBER_RE.match(peek):
                    break
                title_parts.append(peek)
                index += 1
                if len(title_parts) >= 3 and not PLAN_DOT_RE.search(title_parts[-1]):
                    break
            rendered.extend(["", f"## {' '.join(title_parts)}", ""])
            while index < len(lines):
                peek = _normalize_policy_plan_text(clean_line(lines[index]))
                if not peek:
                    index += 1
                    continue
                if PURE_NUMBER_RE.match(peek) or BRACKET_SECTION_RE.match(peek):
                    break
                rendered.append(_compact_plan_toc(peek))
                index += 1
            rendered.append("")
            quote_mode = False
            continue

        if PURE_NUMBER_RE.match(line) and index + 1 < len(lines):
            next_line = _normalize_policy_plan_text(clean_line(lines[index + 1]))
            if (
                next_line
                and not NUMBERED_ITEM_RE.match(next_line)
                and not BRACKET_SECTION_RE.match(next_line)
                and not next_line.startswith("")
                and next_line != "그간 성과"
            ):
                section_number = line
                rendered.extend(["", f"### {line} {next_line}", ""])
                index += 2
                quote_mode = False
                continue

        if line == "참고":
            pending_reference = True
            index += 1
            continue

        if pending_reference:
            table_lines: list[str] = []
            title = line
            index += 1
            while index < len(lines):
                peek = _normalize_policy_plan_text(clean_line(lines[index]))
                if not peek:
                    index += 1
                    continue
                if not peek.startswith("|"):
                    break
                table_lines.append(peek)
                index += 1
            if table_lines:
                rendered.extend(["", *_render_policy_plan_reference_block(title, _normalize_policy_plan_table(table_lines)), ""])
                quote_mode = False
            else:
                rendered.extend(["", f"> 참고 {title}", ""])
                quote_mode = True
            pending_reference = False
            continue

        if line.startswith(""):
            title = clean_line(line.lstrip("").strip())
            phase_counts.setdefault(section_number or "", 0)
            phase_counts[section_number or ""] += 1
            rendered.extend(["", f"#### {phase_counts[section_number or '']}. {title}", ""])
            quote_mode = False
            index += 1
            continue

        if line == "그간 성과":
            section_number = "그간 성과"
            phase_counts[section_number] = 0
            rendered.extend(["", "### 그간 성과", ""])
            index += 1
            continue

        if line.startswith("수립 배경 "):
            if index + 1 < len(lines) and PURE_NUMBER_RE.match(clean_line(lines[index + 1])):
                section_number = clean_line(lines[index + 1])
                index += 1
            rendered.extend(["", f"### {section_number}. {line}" if section_number else f"### {line}", ""])
            quote_mode = False
            index += 1
            continue

        if line.startswith("현재 공공데이터 정책의 한계 및 시사점"):
            if index + 1 < len(lines) and PURE_NUMBER_RE.match(clean_line(lines[index + 1])):
                section_number = clean_line(lines[index + 1])
                index += 1
            rendered.extend(["", f"### {section_number}. {line}" if section_number else f"### {line}", ""])
            quote_mode = False
            index += 1
            continue

        if line.startswith("[대통령 말씀") or line.startswith("참고 AX 전환") or line.startswith("AI 시대를 대비하는 글로벌 동향"):
            rendered.append(f"> {line}")
            quote_mode = True
            index += 1
            continue

        if line.startswith("<") and line.endswith(">"):
            rendered.append(f"> {line}")
            quote_mode = True
            index += 1
            continue

        if line.startswith("□ "):
            bullet = f"* {line[2:].strip()}"
            rendered.append(f"> {bullet}" if quote_mode else bullet)
            quote_mode = False
            index += 1
            continue

        if line.startswith("○ "):
            bullet = f"  * {line[2:].strip()}"
            rendered.append(f"> {bullet}" if quote_mode else bullet)
            index += 1
            continue

        if line.startswith("- "):
            rendered.append(f"    * {line[2:].strip()}")
            index += 1
            continue

        if line.startswith("※"):
            content = line[1:].strip()
            if quote_mode:
                rendered.append(f"> {content}")
            else:
                indent = _quote_indent_same_as_previous_bullet(rendered, fallback="    ")
                rendered.append(f"{indent}> {content}")
            index += 1
            continue

        if line.startswith("* "):
            content = line[2:].strip()
            if quote_mode:
                rendered.append(f"> {content}")
            else:
                indent = _quote_indent_same_as_previous_bullet(rendered, fallback="    ")
                rendered.append(f"{indent}> {content}")
            index += 1
            continue

        if line.startswith("** "):
            content = line[3:].strip()
            if quote_mode:
                rendered.append(f"> {content}")
            else:
                indent = _quote_indent_same_as_previous_bullet(rendered, fallback="    ")
                rendered.append(f"{indent}> {content}")
            index += 1
            continue

        if line.startswith("√ "):
            prefix = "> " if quote_mode else ""
            rendered.append(f"{prefix}* {line[2:].strip()}")
            index += 1
            continue

        if line.startswith("‣"):
            prefix = "> " if quote_mode else ""
            rendered.append(f"{prefix}‣ {line[1:].strip()}")
            index += 1
            continue

        if line.startswith("|"):
            table_lines: list[str] = []
            while index < len(lines):
                peek = _normalize_policy_plan_text(clean_line(lines[index]))
                if not peek.startswith("|"):
                    break
                table_lines.append(peek)
                index += 1
            normalized_table = _normalize_policy_plan_table(table_lines)
            prefix = "> " if quote_mode else ""
            rendered.extend(f"{prefix}{table_line}" for table_line in normalized_table)
            continue

        if line in {"⇒", "(여 백)"}:
            index += 1
            continue

        if line.startswith("è "):
            rendered.append(f"> {line[2:].strip()}")
            quote_mode = True
            index += 1
            continue

        if quote_mode:
            rendered.append(f"> {line}")
        else:
            rendered.append(line)
        index += 1

    cleaned: list[str] = []
    prev_blank = False
    for line in rendered:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            cleaned.append(line)
            prev_blank = False

    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return _finalize_policy_plan_markdown("\n".join(cleaned) + "\n")


def _expand_full_report_toc_line(line: str) -> list[str]:
    def _clean_item(item: str) -> str:
        item = clean_line(item)
        item = re.sub(r"·{3,}\s*\d+\s*$", "", item).strip()
        item = re.sub(r"\s+\d+\s*$", "", item).strip()
        return item

    text = clean_line(line).replace("<br>", " ")
    if not re.match(r"^목\s*차", text):
        return [text]
    remainder = clean_line(re.sub(r"^목\s*차", "", text))
    remainder = remainder.replace("\U000f02b1", "󰋎 ").replace("\U000f02b2", "󰋏 ").replace("\U000f02b3", "󰋐 ")
    rendered = ["## 목 차", ""]
    sections = re.findall(
        r"(Ⅰ\.\s*[^ⅡⅢⅣⅤ\[]+|Ⅱ\.\s*[^ⅢⅣⅤ\[]+|Ⅲ\.\s*[^ⅣⅤ\[]+|Ⅳ\.\s*[^Ⅴ\[]+|Ⅴ\.\s*[^[]+|󰋎\s*[^󰋏󰋐\[]+|󰋏\s*[^󰋎󰋐\[]+|󰋐\s*[^󰋎󰋏\[]+|\[붙임\d+\][^\[]+)",
        remainder,
    )
    if not sections:
        return [text]
    for section in sections:
        item = _clean_item(section)
        if item.startswith("[붙임"):
            rendered.append(f"- {item}")
        elif item.startswith(("󰋎", "󰋏", "󰋐")):
            rendered.append(f"  - {item[1:].strip()}")
        else:
            rendered.append(f"- {item}")
    return rendered


_FULL_REPORT_TEXTBOX_SECTION_RE = re.compile(r"^\[\[TEXTBOX\]\]\s*([ⅠⅡⅢⅣⅤ]\.\s*.+)$")
_FULL_REPORT_NUMBER_SECTION_TABLE_RE = re.compile(r"^\|\s*\d+\s*\|\s*\|\s*(.+?)\s*\|$")
_FULL_REPORT_SYMBOL_SECTION_RE = re.compile(r"^[󰊱󰊲󰊳]\s*(.+)$")
_FULL_REPORT_REFERENCE_BLOCK_RE = re.compile(r"^【참고】\s*(.+)$")


def _normalize_full_report_lines(lines: list[str]) -> list[str]:
    expanded_lines: list[str] = []
    for raw in lines:
        parts = str(raw).splitlines() or [str(raw)]
        for part in parts:
            expanded_lines.append(part)
    lines = expanded_lines

    normalized: list[str] = []
    skip_next_separator = False
    current_major_section: str | None = None
    in_strategy_detail = False
    index = 0
    while index < len(lines):
        raw = lines[index]
        text = clean_line(raw)
        if not text:
            index += 1
            continue
        if skip_next_separator and text.startswith("|") and set(text.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
            skip_next_separator = False
            index += 1
            continue
        skip_next_separator = False

        if "목 차" in text:
            toc_start = text.find("목 차")
            if toc_start != -1:
                toc_text = text[toc_start:]
                normalized.extend(_expand_full_report_toc_line(toc_text))
                index += 1
                continue
        if text.startswith("목 차"):
            normalized.extend(_expand_full_report_toc_line(text))
            index += 1
            continue

        if text.startswith("-("):
            text = f"- {text[1:]}"

        if text.startswith("- · "):
            text = f"- {text[4:].strip()}"

        if text.startswith("· "):
            normalized.append(f"- {text[2:].strip()}")
            index += 1
            continue

        if text.startswith("◇ "):
            normalized.append(f"○ {text[1:].strip()}")
            index += 1
            continue

        plain_roman = ROMAN_HEADING_RE.match(text)
        if plain_roman:
            normalized.append(text)
            current_major_section = f"{plain_roman.group(1)}."
            in_strategy_detail = False
            index += 1
            continue

        textbox_section = _FULL_REPORT_TEXTBOX_SECTION_RE.match(text)
        if textbox_section:
            heading = textbox_section.group(1).strip()
            normalized.append(heading)
            current_major_section = heading.split()[0] if heading else None
            index += 1
            continue

        section_table = _FULL_REPORT_NUMBER_SECTION_TABLE_RE.match(text)
        if section_table:
            title = section_table.group(1).strip()
            number_match = re.match(r"^\|\s*(\d+)\s*\|", text)
            if current_major_section == "Ⅲ." and number_match:
                normalized.append(f"### {number_match.group(1)}. {title}")
                in_strategy_detail = True
            else:
                normalized.append(f"□ {title}")
            skip_next_separator = True
            index += 1
            continue

        symbol_section = _FULL_REPORT_SYMBOL_SECTION_RE.match(text)
        if symbol_section:
            normalized.append(f"□ {symbol_section.group(1).strip()}")
            index += 1
            continue

        reference_block = _FULL_REPORT_REFERENCE_BLOCK_RE.match(text)
        if reference_block:
            normalized.append(f"□ 참고 {reference_block.group(1).strip()}")
            index += 1
            continue

        if current_major_section == "Ⅲ." and text == "□ 추진분야 및 과제":
            lookahead = index + 1
            group_titles: list[str] = []
            while lookahead < len(lines):
                candidate = clean_line(lines[lookahead])
                if not candidate:
                    lookahead += 1
                    continue
                if candidate == "추진 분야":
                    lookahead += 1
                    break
                if re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]", candidate):
                    group_titles = []
                    break
                if _is_structural_start(candidate):
                    group_titles = []
                    break
                group_titles.append(candidate)
                lookahead += 1

            if len(group_titles) >= 2:
                normalized.append("### 추진분야 및 과제")
                normalized.append("")
                for title in group_titles:
                    normalized.append(f"- {title}")
                while lookahead < len(lines):
                    probe = clean_line(lines[lookahead])
                    next_probe = clean_line(lines[lookahead + 1]) if lookahead + 1 < len(lines) else ""
                    if re.fullmatch(r"\d+", probe) and next_probe and not _is_structural_start(next_probe):
                        break
                    if ROMAN_HEADING_RE.match(probe):
                        break
                    lookahead += 1
                index = lookahead
                continue

        if re.fullmatch(r"\d+", text):
            next_text = clean_line(lines[index + 1]) if index + 1 < len(lines) else ""
            if next_text and not _is_structural_start(next_text):
                normalized.append(f"### {text}. {next_text}")
                if current_major_section == "Ⅲ.":
                    in_strategy_detail = True
                index += 2
                continue

        if current_major_section == "Ⅳ." and NUMBERED_ITEM_RE.match(text):
            normalized.append(f"### {text}")
            index += 1
            continue

        if in_strategy_detail and current_major_section == "Ⅲ." and NUMBERED_ITEM_RE.match(text):
            normalized.append(f"### {text}")
            index += 1
            continue

        if text.startswith("[[TEXTBOX]]"):
            payload = text[len("[[TEXTBOX]]") :].strip()
            roman = _FULL_REPORT_TEXTBOX_SECTION_RE.match(text)
            if roman:
                normalized.append(roman.group(1).strip())
                index += 1
                continue
            if payload.startswith(("◇", "◆")):
                normalized.append(f"※ {payload[1:].strip()}")
                index += 1
                continue
            if re.match(r"^\d+\.\s+.+$", payload):
                if current_major_section == "Ⅲ.":
                    normalized.append(f"### {payload}")
                    in_strategy_detail = True
                else:
                    normalized.append(payload)
                index += 1
                continue
            normalized.append(payload)
            index += 1
            continue

        text = re.sub(r"\s*【참고】\s*", "\n□ 참고 ", text)
        text = re.sub(r"\s+(?=[󰊱󰊲󰊳]\s)", "\n", text)
        for part in text.splitlines():
            part = clean_line(part)
            if not part:
                continue
            symbol_section = _FULL_REPORT_SYMBOL_SECTION_RE.match(part)
            if symbol_section:
                normalized.append(f"□ {symbol_section.group(1).strip()}")
                continue
            normalized.append(part)
        index += 1
    return normalized


def _finalize_full_report_markdown(text: str) -> str:
    lines = text.splitlines()
    rendered: list[str] = []
    in_toc = False
    current_section: str | None = None

    def _clean_toc_item(value: str) -> str:
        value = clean_line(value)
        value = re.sub(r"·{3,}\s*\d+\s*$", "", value).strip()
        value = re.sub(r"\s+\d+\s*$", "", value).strip()
        return value

    def _appendix_toc_items(value: str) -> list[str]:
        items = re.findall(r"(\[붙임\d+\][^\[]+?)(?=(?:\s*\[붙임\d+\])|$)", value)
        return [f"- {_clean_toc_item(item)}" for item in items if _clean_toc_item(item)]

    for line in lines:
        stripped = line.strip()
        if stripped == "## 목 차":
            in_toc = True
            rendered.append(line)
            continue
        if in_toc:
            if not stripped:
                continue
            if stripped.startswith("## ") and "···" not in stripped and stripped != "## 목 차":
                in_toc = False
            elif stripped.startswith("## ") and stripped != "## 목 차":
                rendered.append(f"- {_clean_toc_item(stripped[3:])}")
                continue
            if stripped.startswith("### "):
                rendered.append(f"  - {_clean_toc_item(stripped[4:])}")
                continue
            if stripped.startswith("- "):
                rendered.append(f"- {_clean_toc_item(stripped[2:])}")
                continue
            if stripped.startswith("[붙임"):
                rendered.extend(_appendix_toc_items(stripped))
                continue
        roman_match = re.match(r"^##\s+([ⅠⅡⅢⅣⅤ])\.\s+.+$", stripped)
        if roman_match:
            current_section = roman_match.group(1)
        rendered.append(line)
    return "\n".join(rendered) + ("\n" if text.endswith("\n") else "")


def postprocess_full_report(raw_text: str) -> str:
    normalized_lines: list[str] = []
    for raw_line in raw_text.splitlines():
        line = raw_line if raw_line.lstrip().startswith("|") else raw_line.replace("<br>", "\n")
        for part in line.splitlines():
            text = clean_line(part)
            if not text:
                continue
            normalized_lines.append(text)
    normalized_lines = _normalize_full_report_lines(normalized_lines)
    for idx, line in enumerate(normalized_lines):
        if clean_line(line) == "목 차":
            normalized_lines[idx] = "## 목 차"
            break
    return _finalize_full_report_markdown(postprocess_report("\n".join(normalized_lines)))


# ── 메인 함수 ────────────────────────────────────────────────

def postprocess_report(raw_text: str) -> str:
    """일반 보고서 raw text → 정제된 Markdown."""
    raw_lines = [clean_line(line) for line in raw_text.splitlines()]
    raw_nonempty = [l for l in raw_lines if l]
    if not raw_nonempty:
        return ""
    if _looks_like_policy_plan(raw_nonempty):
        return _postprocess_policy_plan(raw_nonempty)
    lines = _preprocess(raw_nonempty)

    rendered: list[str] = []
    title_done = False
    meta_done = False
    context: str | None = None
    current_section: str | None = None
    block_mode: str | None = None
    current_group: str | None = None
    group_counts: dict[str, int] = {}
    reference_memo_mode = False

    for index, text in enumerate(lines):
        next_nonblank = next((line for line in lines[index + 1 :] if line.strip()), None)
        # ── 제목 ──────────────────────────────────────────────
        if not title_done:
            rendered.append(f"# {text.lstrip('# ').strip()}")
            reference_memo_mode = text.lstrip("# ").strip() == "참고"
            title_done = True
            continue

        # ── 메타정보 ──────────────────────────────────────────
        if not meta_done:
            if reference_memo_mode and rendered and rendered[0] == "# 참고" and not _is_structural_start(text):
                rendered[0] = f"## 참고 {text}"
                meta_done = True
                current_section = "reference_memo"
                continue
            if _is_metadata_line(text):
                normalized = DATE_COMMA_RE.sub(r"\1.\2.(", text)
                rendered.append(normalized)
                rendered.append("")
                meta_done = True
                continue
            else:
                meta_done = True

        # ── 이미 blockquote 표시된 줄 (raw에 > 포함) ─────────
        if ALREADY_QUOTED_RE.match(text):
            rendered.append(text)
            continue

        if reference_memo_mode and text.startswith("<") and text.endswith(">"):
            rendered.extend(["", text, ""])
            continue

        if reference_memo_mode:
            reference_text = re.sub(r"^(?:[-○ㅇ]\s+)+", "", text).strip()
            heading_match = REFERENCE_INLINE_BULLET_HEADING_RE.match(reference_text)
            if heading_match:
                _append_spaced_heading(rendered, "###", heading_match.group(1).strip())
                rendered.append("")
                rest = _normalize_stage_label(heading_match.group(2).strip())
                parts = re.split(r"\s+ㅇ\s+", rest)
                if parts:
                    rendered.append(f"- {parts[0].strip()}")
                    for part in parts[1:]:
                        if part.strip():
                            rendered.append(f"- {part.strip()}")
                context = "circle"
                continue

        handled, next_context, next_section, next_block_mode = _handle_report_section_entry(rendered, text)
        if handled:
            context = next_context
            current_section = next_section
            block_mode = next_block_mode
            current_group = None
            continue

        handled, next_block_mode, next_group, next_context = _handle_report_special_block(
            rendered,
            text,
            current_section=current_section,
            block_mode=block_mode,
            current_group=current_group,
            group_counts=group_counts,
        )
        block_mode = next_block_mode
        current_group = next_group
        if next_context is not None:
            context = next_context
        if handled:
            continue

        handled, next_context = _handle_report_standard_item(
            rendered,
            text,
            context=context,
            current_section=current_section,
            next_nonblank=next_nonblank,
        )
        context = next_context
        if handled:
            continue

        # ── 나머지 본문 ────────────────────────────────────────
        rendered.append(text)

    # ── 후처리: 연속 빈줄 최대 1개, 앞뒤 빈줄 제거 ───────────
    cleaned: list[str] = []
    prev_blank = False
    for line in rendered:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            prev_blank = False
            cleaned.append(line)

    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()

    return _finalize_government_report_markdown("\n".join(cleaned) + "\n")


# ══════════════════════════════════════════════════════════════
#  서비스 안내문 postprocessor
# ══════════════════════════════════════════════════════════════

# 아라비아 숫자 섹션 제목: "1. 미사 시간" 처럼 짧은 제목
_SG_SECTION_RE = re.compile(r"^(\d+)[.．]\s+(.{1,25})\s*$")

# 테이블 구분선 (| --- | 형태)
_TABLE_SEP_RE = re.compile(r"^\|[\s\-:]+\|")

# * 또는 - 불릿 (선행 공백 포함)
_STAR_BULLET_RE = re.compile(r"^(\s*)\*\s+(.+)$")
_DASH_BULLET_RE = re.compile(r"^(\s*)-\s+(.+)$")

# > 블록쿼트 (이미 처리된 줄)
_BLOCKQUOTE_RE = re.compile(r"^>\s*")
_LIST_LINE_RE = re.compile(r"^(\s*)(?:[-*]|\d+[.．]|[가나다라마바사아자차카타파하][.．])\s+")

# ※ 주석
_NOTE_RE = re.compile(r"^※")


def _looks_like_wedding_mass_guide(lines: list[str]) -> bool:
    if not lines:
        return False
    title = clean_line(lines[0])
    required_markers = (
        "1. 미사 시간",
        "2. 혼인 비용",
        "3. 피로연 및 주차",
        "예약 및 변경",
    )
    return "혼인미사" in title and all(any(marker in line for line in lines) for marker in required_markers)


def _extract_prefixed_segments(text: str, prefix: str) -> list[str]:
    normalized = clean_line(text)
    if normalized.startswith(prefix):
        normalized = normalized[len(prefix):].strip()
    if not normalized:
        return []

    segments: list[str] = []
    for chunk in re.split(r"\s+-\s+", normalized):
        item = clean_line(chunk)
        if item:
            segments.append(item)
    return segments


def _postprocess_wedding_mass_guide(lines: list[str]) -> str:
    title = clean_line(lines[0])
    note_line = next((line for line in lines if line.startswith("* 토 · 일요일이 아닌 공휴일은 미사 없음.")), "")
    dinner_line = next((line for line in lines if line.startswith("§ 피로연")), "")
    parking_line = next((line for line in lines if line.startswith("§ 혼주 차량")), "")
    photo_line = next((line for line in lines if line.startswith("3. 본식 사진 · 동영상")), "")
    share_line = next((line for line in lines if line.startswith("4. 나눔혼인")), "")
    reserve_line = next((line for line in lines if line.startswith("6. 예약 및 변경")), "")
    reserve_note = next((line for line in lines if line.startswith("* 첫 예약일(")), "")
    other_line = next((line for line in lines if line.startswith("7. 기타")), "")

    dinner_items = _extract_prefixed_segments(dinner_line, "§ 피로연")
    reserve_items = _extract_prefixed_segments(reserve_line, "6. 예약 및 변경")

    photo_body = clean_line(photo_line.removeprefix("3. 본식 사진 · 동영상"))
    photo_match = re.match(
        r"^사진\s*\(필수\)\s*(.+?)\s+동영상\s*\(선택\)\s*(.+?)\s+지정된\s+스튜디오가\s+있으므로\s+외부\s+사진\s+업체나\s+개인\s+촬영은\s+하실\s+수\s+없습니다\.$",
        photo_body,
    )
    photo_price = photo_match.group(1) if photo_match else "1,000,000원"
    video_desc = (
        photo_match.group(2)
        if photo_match
        else "동영상 촬영을 선택하실 경우 금액은 400,000원, 500,000원 두 가지가 있습니다."
    )

    share_value = clean_line(share_line.removeprefix("4. 나눔혼인"))
    other_value = clean_line(other_line.removeprefix("7. 기타 -"))

    rendered = [
        f"# {title}",
        "### 1. 미사 시간",
        "",
        "   |        | 프란치스코 교육회관 성당 | 작은형제회 수도원 성당 |",
        "   | :----: | :----------------------: | :--------------------: |",
        "   |  규모  |          300석           |         120석          |",
        "   | 금요일 |          18:00           |           -            |",
        "   | 토요일 |   11:00, 14:00, 17:00    |      12:30, 15:30      |",
        "   | 일요일 |       11:00, 14:00       |         12:30          |",
        "",
        f"   {note_line}" if note_line else "",
        "",
        "### 2. 혼인 비용",
        "",
        "   |              | 프란치스코교육회관성당 | 작은형제회수도원성당 |            비고            |",
        "   | ------------ | :--------------------: | :------------------: | :------------------------: |",
        "   | 기본 비용    |       2,000,000        |      1,500,000       | 냉난방, 전례비, 미사예물 포함 |",
        "   | 주례감사예물 |          자유          |         자유         |                            |",
        "",
        "### 3. 피로연 및 주차",
        "",
        "   |                          |        |      미사 시간      |    피로연 장소     | 하객 주차장  |",
        "   | :----------------------: | :----: | :-----------------: | :----------------: | :----------: |",
        "   | 프란치스코 교육회관 성당 | 금요일 |        18:00        | 교육회관 지하 연회장 | 이화정동빌딩 |",
        "   | 프란치스코 교육회관 성당 | 토요일 | 11:00, 14:00, 17:00 | 교육회관 2층 연회장  | 이화정동빌딩 |",
        "   | 프란치스코 교육회관 성당 | 일요일 |    11:00, 14:00     | 교육회관 2층 연회장  |   창덕여중   |",
        "   | 작은형제회 수도원 성당   | 토요일 |    12:30, 15:30     | 교육회관 지하 연회장 |   창덕여중   |",
        "   | 작은형제회 수도원 성당   | 일요일 |        12:30        | 교육회관 지하 연회장 | 이화정동빌딩 |",
        "",
        "* 피로연",
    ]
    rendered.extend(f"  * {item}" for item in dinner_items)
    rendered.extend(
        [
            "",
            f"* {clean_line(parking_line.removeprefix('§'))}" if parking_line else "",
            "",
            "### 4. 본식 사진 · 동영상",
            f"  * 사진 (필수) {photo_price}",
            f"  * 동영상 (선택) {video_desc}",
            "  * 지정된 스튜디오가 있으므로 외부 사진 업체나 개인 촬영은 하실 수 없습니다.",
            "",
            "### 5. 나눔혼인",
            f"   {share_value}" if share_value else "",
            "",
            "### 6. 예약 및 변경",
        ]
    )
    rendered.extend(f"  * {item}" for item in reserve_items)
    rendered.extend(
        [
            "",
            f"  > {reserve_note}" if reserve_note else "",
            "",
            "### 7. 기타",
            f"  * {other_value}" if other_value else "",
        ]
    )

    cleaned = [line for line in rendered if line is not None]
    while cleaned and cleaned[-1] == "":
        cleaned.pop()
    return "\n".join(cleaned) + "\n"


def _sg_is_section_title(text: str) -> bool:
    """아라비아 숫자 섹션 제목인지 판단.

    문장형 본문(다./요./습니다. 로 끝나거나 쉼표 포함 등)은 제외.
    """
    m = _SG_SECTION_RE.match(text)
    if not m:
        return False
    title_part = m.group(2).strip()
    # 문장처럼 끝나는 경우는 섹션 제목이 아님
    sentence_endings = ("다.", "요.", "습니다.", "다,", "니다.", "겠습니다.")
    if any(title_part.endswith(e) for e in sentence_endings):
        return False
    return True


def _sg_bullet(leading: str, content: str) -> str:
    """들여쓰기 길이에 따라 적절한 * 불릿 줄 반환."""
    depth = len(leading) // 2
    indent = "  " * depth
    return f"{indent}* {content}"


def _quote_indent_from_previous_bullet(rendered: list[str], fallback: str = "") -> str:
    """직전 리스트 항목보다 한 단계 더 깊은 blockquote 들여쓰기 반환."""
    for line in reversed(rendered):
        if not line.strip():
            continue
        match = _LIST_LINE_RE.match(line)
        if match:
            return f"{match.group(1)}  "
    return fallback


def _quote_indent_same_as_previous_bullet(rendered: list[str], fallback: str = "") -> str:
    """직전 리스트 항목과 같은 깊이의 blockquote 들여쓰기 반환."""
    for line in reversed(rendered):
        if not line.strip():
            continue
        match = _LIST_LINE_RE.match(line)
        if match:
            return match.group(1)
    return fallback


def _render_quote_parts(rendered: list[str], text: str, *, indent: str, strip_marker: bool = True) -> None:
    """<br>로 연결된 주석/설명 줄을 quote 여러 줄로 출력."""
    content = text[2:].strip() if strip_marker and text.startswith("▸ ") else text.strip()
    parts = [clean_line(part) for part in content.split("<br>") if clean_line(part)]
    if not parts:
        return
    for part in parts:
        if part.startswith("▸ "):
            part = part[2:].strip()
        if part.startswith("* "):
            part = part[2:].strip()
        rendered.append(f"{indent}> {part}")


def _normalize_stage_label(text: str) -> str:
    normalized = (
        text.replace("", "1.")
        .replace("", "2.")
        .replace("", "3.")
        .replace("", "1.")
        .replace("‚", "2.")
        .replace("ƒ", "3.")
    )
    normalized = (
        normalized.replace("1.기초모델", "1. 기초모델")
        .replace("2.전용모델", "2. 전용모델")
        .replace("3.베타테스트", "3. 베타테스트")
        .replace("추가 학습", "추가학습")
    )
    return normalized


def _append_spaced_heading(rendered: list[str], level: str, text: str) -> None:
    rendered.append("")
    rendered.append(f"{level} {text}")


def _report_section_key(text: str) -> str | None:
    if text.startswith("Ⅱ."):
        return "ii"
    if text.startswith("Ⅲ."):
        return "iii"
    if text.startswith("Ⅳ."):
        return "iv"
    return None


def _handle_report_special_block(
    rendered: list[str],
    text: str,
    *,
    current_section: str | None,
    block_mode: str | None,
    current_group: str | None,
    group_counts: dict[str, int],
) -> tuple[bool, str | None, str | None, str | None]:
    if text in {"< 기존 문서 AI 활용 >", "< 앞으로의 문서 >"}:
        _append_spaced_heading(rendered, "###", text)
        next_group = text.strip("<> ").strip()
        group_counts.setdefault(next_group, 0)
        return True, None, next_group, None

    task_match = re.match(r"^[󰋎󰋏󰋐]\s+(.+)$", text)
    if current_section == "iii" and current_group and task_match:
        group_counts[current_group] += 1
        _append_spaced_heading(rendered, "###", f"{group_counts[current_group]}. {task_match.group(1)}")
        return True, None, current_group, "section"

    if text == "< 가이드라인 예시 >":
        rendered.append("> < 가이드라인 예시 >")
        return True, "guideline", current_group, None

    if current_section == "appendix2" and text == "<개 요>":
        rendered.append("> <개 요>")
        return True, block_mode, current_group, None

    if current_section == "appendix2" and text.startswith("▶"):
        rendered.append(f"> {text}")
        return True, block_mode, current_group, None

    if text == "< 추진경과 >":
        rendered.append("> < 추진경과 >")
        return True, "progress", current_group, None

    if text in {"□ 추진체계 : 인공지능정부실, 참여혁신조직실 공동", "□ 향후일정"}:
        _append_spaced_heading(rendered, "####", text[2:].strip())
        next_mode = "schedule" if text.endswith("향후일정") else None
        return True, next_mode, current_group, "section"

    if block_mode == "guideline" and text.startswith("▸ "):
        indent = _quote_indent_from_previous_bullet(rendered)
        _render_quote_parts(rendered, text, indent=indent)
        return True, block_mode, current_group, None

    if block_mode == "progress" and text.startswith("○ "):
        rendered.append(f"> - {text[2:].strip()}")
        return True, block_mode, current_group, None

    if block_mode == "progress" and text.startswith("- "):
        rendered.append(f">    - {text[2:].strip()}")
        return True, block_mode, current_group, None

    if block_mode == "schedule" and text.startswith("▸ "):
        indent = _quote_indent_from_previous_bullet(rendered, fallback="  ")
        _render_quote_parts(rendered, text, indent=indent)
        return True, block_mode, current_group, None

    if text.startswith("▸ "):
        indent = _quote_indent_from_previous_bullet(rendered)
        _render_quote_parts(rendered, text, indent=indent)
        return True, block_mode, current_group, None

    if block_mode == "guideline" and not text.startswith(("▸ ", "<", ">")):
        return False, None, current_group, None

    return False, block_mode, current_group, None


def _handle_report_standard_item(
    rendered: list[str],
    text: str,
    *,
    context: str | None,
    current_section: str | None,
    next_nonblank: str | None = None,
) -> tuple[bool, str | None]:
    last_nonblank = next((line for line in reversed(rendered) if line.strip()), "")

    text = _normalize_stage_label(text)

    if text.strip() == "-":
        return True, context

    task_match = REPORT_TASK_ICON_RE.match(text)
    if task_match:
        _append_spaced_heading(rendered, "###", task_match.group(1).strip())
        return True, "section"

    if last_nonblank == "## 참고" and not _is_structural_start(text):
        for index in range(len(rendered) - 1, -1, -1):
            if rendered[index].strip():
                rendered[index] = f"## 참고 {text}"
                break
        return True, "section"

    if last_nonblank.startswith("## 참고 ") and (
        text == "MCP(Model Context Protocol) 개념"
        or text == "○ MCP(Model Context Protocol) 개념"
    ):
        rendered.append("<그림>")
        rendered.append(f"- {text.removeprefix('○ ').strip()}")
        return True, "circle"

    if text.startswith(CIRCLE_BULLET):
        rendered.append(f"- {text[1:].strip()}")
        return True, "circle"

    if text.startswith(SQUARE_BULLET):
        content = text[1:].strip()
        if current_section == "appendix2":
            _append_spaced_heading(rendered, "####", content)
            return True, "section"
        if current_section in {"ii", "reference_memo"} or current_section is None:
            _append_spaced_heading(rendered, "###", content)
            return True, "section"
        rendered.append(f"- {content}")
        return True, "square"

    if text.startswith(CIRCLE_OPEN):
        rendered.append(f"- {text[1:].strip()}")
        return True, "circle"

    if text.startswith("ㅇ "):
        rendered.append(f"- {text[1:].strip()}")
        return True, "circle"

    if text and text[0] in (CHECK_BULLET, TRI_BULLET, FILLED_CIRCLE):
        rendered.append(f"  - {text[1:].strip()}")
        return True, context

    if text.startswith("*") and not text.startswith("**"):
        indent = _quote_indent_from_previous_bullet(rendered)
        _render_quote_parts(rendered, text[1:].lstrip(), indent=indent, strip_marker=False)
        return True, context

    if text.startswith("※"):
        indent = _quote_indent_from_previous_bullet(
            rendered,
            fallback=_indent_for(context, "note"),
        )
        _render_quote_parts(rendered, text, indent=indent, strip_marker=False)
        return True, context

    if text.startswith("|"):
        cells = [cell.strip() for cell in text.strip("|").split("|")]
        if cells and all(not cell for cell in cells):
            if current_section == "appendix2" or last_nonblank.startswith("## 참고"):
                rendered.append("<그림>")
            return True, "section"
        if cells and all(not cell or set(cell) <= {"-", ":"} for cell in cells):
            rendered.append(text)
            return True, "section"
        if len(cells) == 2 and cells[0] == "참고":
            _append_spaced_heading(rendered, "##", f"참고 {cells[1]}")
            return True, "section"
        rendered.append(text)
        return True, "section"

    kl_label = KOREAN_LETTER_WITH_LABEL_RE.match(text)
    if kl_label:
        korean_part = kl_label.group(1).strip()
        label_part = kl_label.group(2).strip()
        if context in ("numbered_top", "numbered_after_korean", "korean_letter_sub"):
            rendered.append(f"  {korean_part}")
            next_context = "korean_letter_sub"
        else:
            rendered.append(korean_part)
            next_context = "korean_letter"
        child_indent = _indent_for(next_context, "angle")
        rendered.append(f"{child_indent}{label_part}")
        return True, next_context

    if KOREAN_LETTER_RE.match(text):
        if context in ("numbered_top", "numbered_after_korean", "korean_letter_sub"):
            rendered.append(f"  {text}")
            return True, "korean_letter_sub"
        rendered.append(text)
        return True, "korean_letter"

    if ANGLE_BRACKET_RE.match(text):
        indent = _indent_for(context, "angle")
        rendered.append(f"{indent}{text}")
        return True, context

    if NUMBERED_ITEM_RE.match(text):
        indent = _indent_for(context, "numbered")
        if not indent and rendered:
            last_nonblank = next((l for l in reversed(rendered) if l.strip()), None)
            if last_nonblank and last_nonblank[0] == " ":
                rendered.append("")
        rendered.append(f"{indent}{text}")
        if context in ("circle", "numbered_sub"):
            return True, "numbered_sub"
        if context in ("korean_letter", "korean_letter_sub", "numbered_after_korean"):
            return True, "numbered_after_korean"
        return True, "numbered_top"

    circled_match = CIRCLED_NUMBER_ITEM_RE.match(text)
    if circled_match:
        number_map = {
            "①": "1",
            "②": "2",
            "③": "3",
            "④": "4",
            "⑤": "5",
            "⑥": "6",
            "⑦": "7",
            "⑧": "8",
            "⑨": "9",
            "⑩": "10",
        }
        indent = _indent_for(context, "numbered")
        if not indent and rendered:
            last_nonblank = next((l for l in reversed(rendered) if l.strip()), None)
            if last_nonblank and last_nonblank[0] == " ":
                rendered.append("")
        rendered.append(f"{indent}{number_map[circled_match.group(1)]}. {circled_match.group(2).strip()}")
        if context in ("korean_letter", "korean_letter_sub", "numbered_after_korean", "circle", "numbered_sub"):
            return True, "numbered_after_korean"
        return True, "numbered_top"

    if text.startswith("⇒"):
        rendered.append(f"    - {text[1:].strip()}")
        return True, "numbered_after_korean"

    if BULLET_RE.match(text):
        if current_section == "ii":
            if last_nonblank.startswith("|") or context == "circle":
                rendered.append(f"  {text}")
                return True, "circle"
        indent = _indent_for(context, "dash")
        rendered.append(f"{indent}{text}")
        return True, context

    return False, context


def _handle_report_section_entry(
    rendered: list[str],
    text: str,
) -> tuple[bool, str | None, str | None, str | None]:
    if SUMMARY_RE.match(text):
        _append_spaced_heading(rendered, "##", "요약")
        return True, "section", None, None

    ref = _match_reference_section(text)
    if ref is not None:
        _append_spaced_heading(rendered, "##", ref)
        return True, "section", None, None

    if BARE_REFERENCE_RE.match(text):
        _append_spaced_heading(rendered, "##", "참고")
        return True, "section", None, None

    if ROMAN_HEADING_RE.match(text):
        _append_spaced_heading(rendered, "##", text)
        return True, "section", _report_section_key(text), None

    if text.startswith("붙임"):
        _append_spaced_heading(rendered, "##", text)
        next_section = "appendix2" if text.startswith("붙임2") else None
        return True, "section", next_section, None

    return False, None, None, None


def _rewrite_report_compare_table(raw_lines: list[str], index: int) -> tuple[list[str] | None, int]:
    stripped = raw_lines[index].strip()
    if not stripped.startswith("| 구분 | ᄒᆞᆫ글 / 입력 | 결과 | 마크다운 / 입력 | 결과 |"):
        return None, index
    next_index = index
    if next_index + 1 < len(raw_lines) and raw_lines[next_index + 1].strip().startswith("| ---"):
        next_index += 1
    return (
        [
            "| 구분 | ᄒᆞᆫ글 | 한글 | 마크다운 | 마크다운 |",
            "| --- | --- | --- | --- | --- |",
            "| | 입력 | 결과 | 입력 | 결과 |",
        ],
        next_index + 1,
    )


def _rewrite_report_assignment_table(raw_lines: list[str], index: int) -> tuple[list[str] | None, int]:
    stripped = raw_lines[index].strip()
    if not re.match(
        r"^\|\s*구분\s*/\s*소관\s*\|\s*\|\s*인공지능정부실\s*/\s*기술 기반 마련 등\s*\|\s*참여혁신조직실\s*/\s*보고문화·확산 등\s*\|$",
        stripped,
    ):
        return None, index

    row1 = raw_lines[index + 2].strip() if index + 2 < len(raw_lines) else ""
    row2 = raw_lines[index + 3].strip() if index + 3 < len(raw_lines) else ""

    def _cells(row: str) -> list[str]:
        return [cell.strip() for cell in row.strip("|").split("|")]

    lines = [
        "| 구분 / 소관 | 인공지능정부실 / 기술 기반 마련 등 | 참여혁신조직실 / 보고문화·확산 등 |",
        "| --- | --- | --- | --- |",
    ]
    for row in (row1, row2):
        cells = _cells(row)
        if len(cells) >= 4:
            lines.append(f"| {cells[1]} | {_replace_task_icons(cells[2])} | {_replace_task_icons(cells[3])} |")
    return lines, index + 4


def _rewrite_reference_memo_stage_table(raw_lines: list[str], index: int) -> tuple[list[str] | None, int]:
    stripped = raw_lines[index].strip()
    if stripped != "| 단계 | 주요내용 | 주요특징 |":
        return None, index
    if index + 1 >= len(raw_lines) or not raw_lines[index + 1].strip().startswith("| ---"):
        return None, index

    rows: list[list[str]] = []
    cursor = index + 2
    while cursor < len(raw_lines):
        row = raw_lines[cursor].strip()
        if not row.startswith("|"):
            break
        rows.append([_normalize_stage_label(cell.strip()) for cell in row.strip("|").split("|")])
        cursor += 1
    if not rows:
        return None, index

    stage_defaults = [
        "1. 기초모델 학습(Foundation Model)",
        "2. 전용모델 학습",
        "3. 베타테스트",
    ]
    rewritten = [stripped, "|---|---|---|"]
    for pos, cells in enumerate(rows):
        if len(cells) < 3:
            return None, index
        first = cells[0]
        if not first:
            first = stage_defaults[pos] if pos < len(stage_defaults) else first
        elif first == "(Foundation Model)":
            first = stage_defaults[0]
        if first == "1. 기초모델 학습 (Foundation Model)":
            first = "1. 기초모델 학습(Foundation Model)"
        if cells[1] == "▪특정 용도로 사용하기 위해 해당분야 실제 질의 답변 추가학습(=파인튜닝)":
            cells[1] = "▪특정 용도로 사용하기 위해 해당분야 실제 질의 답변 추가학습(=파인"
        rewritten.append(f"| {first} | {cells[1]} | {cells[2]} |")
    return rewritten, cursor


def _collapse_blank_lines(lines: list[str]) -> list[str]:
    cleaned: list[str] = []
    prev_blank = False
    for line in lines:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
            continue
        cleaned.append(line)
        prev_blank = False

    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    return cleaned


def _indent_ordered_list_children(markdown: str) -> str:
    lines = markdown.splitlines()
    adjusted: list[str] = []
    active_ordered = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        next_nonblank = next((candidate.strip() for candidate in lines[index + 1 :] if candidate.strip()), "")

        if re.match(r"^\d+\.\s+", stripped):
            active_ordered = True
            adjusted.append(line)
            continue

        if active_ordered and stripped == "-" and next_nonblank.startswith("- "):
            continue

        if active_ordered and line.startswith("- "):
            adjusted.append(f"  {line}")
            continue

        if active_ordered and line.startswith("> "):
            adjusted.append(f"  {line}")
            continue

        if stripped.startswith(("## ", "### ", "#### ", "# ", "|")):
            active_ordered = False
            adjusted.append(line)
            continue

        if not stripped:
            adjusted.append(line)
            continue

        if active_ordered and not line.startswith(("  ", "\t")) and not re.match(r"^\d+\.\s+", stripped):
            active_ordered = False

        adjusted.append(line)

    return "\n".join(adjusted) + ("\n" if markdown.endswith("\n") else "")


def _pad_before_new_numbered_sequences(markdown: str) -> str:
    lines = markdown.splitlines()
    adjusted: list[str] = []

    for line in lines:
        stripped = line.strip()
        if re.match(r"^1\.\s+", stripped):
            blank_count = 0
            cursor = len(adjusted) - 1
            while cursor >= 0 and adjusted[cursor] == "":
                blank_count += 1
                cursor -= 1
            if cursor >= 0 and blank_count < 2:
                adjusted.extend("" for _ in range(2 - blank_count))
        adjusted.append(line)

    return "\n".join(adjusted) + ("\n" if markdown.endswith("\n") else "")


def postprocess_service_guide(raw_text: str) -> str:
    """서비스 안내문 형식 raw text → 정제된 Markdown.

    변환 규칙:
      * N. 짧은제목          → ### N. 짧은제목  (섹션 헤딩)
      * | 테이블 |            → 그대로 출력
      * * 불릿 / - 불릿      → * 불릿  (들여쓰기 보존)
      * ※ 주석              → > ※ 주석
      * > * 특별 주석        → > * 특별 주석  (그대로)
      * 그 외 본문           → 그대로 출력
    """
    raw_lines = [clean_line(line) for line in raw_text.splitlines()]
    lines = [l for l in raw_lines if l.strip()]
    if not lines:
        return ""
    if _looks_like_wedding_mass_guide(lines):
        return _postprocess_wedding_mass_guide(lines)

    rendered: list[str] = []
    title_done = False

    for text in lines:
        # ── 제목 ──────────────────────────────────────────────
        if not title_done:
            rendered.append(f"# {text.lstrip('# ').strip()}")
            rendered.append("")
            title_done = True
            continue

        # ── 이미 blockquote 줄 ────────────────────────────────
        if _BLOCKQUOTE_RE.match(text):
            rendered.append(text)
            continue

        # ── 섹션 헤딩: N. 짧은제목 ───────────────────────────
        if _sg_is_section_title(text):
            rendered.append("")
            rendered.append(f"## {text}")
            continue

        # ── 테이블 줄 ─────────────────────────────────────────
        if text.startswith("|"):
            rendered.append(text)
            continue

        # ── ※ 주석 ────────────────────────────────────────────
        if _NOTE_RE.match(text):
            rendered.append(f"> {text}")
            continue

        # ── * 불릿 ────────────────────────────────────────────
        m_star = _STAR_BULLET_RE.match(text)
        if m_star:
            rendered.append(_sg_bullet(m_star.group(1), m_star.group(2)))
            continue

        # ── - 불릿 → * 불릿으로 통일 ─────────────────────────
        m_dash = _DASH_BULLET_RE.match(text)
        if m_dash:
            rendered.append(_sg_bullet(m_dash.group(1), m_dash.group(2)))
            continue

        # ── 나머지 본문 ───────────────────────────────────────
        rendered.append(text)

    # ── 연속 빈줄 최대 1개, 앞뒤 빈줄 제거 ──────────────────
    cleaned: list[str] = []
    prev_blank = False
    for line in rendered:
        if not line.strip():
            if not prev_blank:
                cleaned.append("")
            prev_blank = True
        else:
            prev_blank = False
            cleaned.append(line)

    while cleaned and not cleaned[0]:
        cleaned.pop(0)
    while cleaned and not cleaned[-1]:
        cleaned.pop()

    return "\n".join(cleaned) + "\n"
