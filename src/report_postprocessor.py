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


# ── 상수 ────────────────────────────────────────────────────
CIRCLE_BULLET = "\u20dd"  # ⃝

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

# 한글 자모 항목: 가. 나. 다. 텍스트
KOREAN_LETTER_RE = re.compile(r"^([가나다라마바사아자차카타파하])[.．]\s+(.+)$")


# 꺾쇠 라벨: <텍스트> 또는 ＜텍스트＞
ANGLE_BRACKET_RE = re.compile(r"^[<＜].+[>＞]$")

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
    if ch in set(CIRCLE_BULLET + "-*<>#|※"):
        return True
    if ch in {"▸", "▶", "◆", "󰋎", "󰋏", "󰋐"}:
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


def _preprocess(raw_lines: list[str]) -> list[str]:
    """1) ⃝ 분리  2) 줄 연결"""
    # Step 1: ⃝ 분리
    split: list[str] = []
    for line in raw_lines:
        split.extend(_split_at_circle(line))

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
            return "  "
        return ""  # section, numbered_top → 들여쓰기 없음
    if bullet_type == "dash":
        if context in ("korean_letter_sub", "numbered_sub"):
            return "    "
        if context in ("korean_letter", "circle", "numbered_after_korean"):
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

        if re.match(r"^\|\s*구분\s*/\s*소관\s*\|\s*\|\s*인공지능정부실\s*/\s*기술 기반 마련 등\s*\|\s*참여혁신조직실\s*/\s*보고문화·확산 등\s*\|$", stripped):
            row1 = raw_lines[i + 2].strip() if i + 2 < len(raw_lines) else ""
            row2 = raw_lines[i + 3].strip() if i + 3 < len(raw_lines) else ""

            def _cells(row: str) -> list[str]:
                return [cell.strip() for cell in row.strip("|").split("|")]

            lines.append("| 구분 / 소관 | 인공지능정부실 / 기술 기반 마련 등 | 참여혁신조직실 / 보고문화·확산 등 |")
            lines.append("| --- | --- | --- | --- |")
            for row in (row1, row2):
                cells = _cells(row)
                if len(cells) >= 4:
                    lines.append(f"| {cells[1]} | {_replace_task_icons(cells[2])} | {_replace_task_icons(cells[3])} |")
            i += 4
            continue

        if raw.startswith(">") and not raw.startswith("> "):
            raw = "> " + raw[1:].lstrip()

        lines.append(raw)
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
    in_section_ii = False
    in_section_iii = False
    in_guideline_callout = False
    in_progress = False
    in_schedule_meta = False
    in_appendix2 = False
    current_group: str | None = None
    group_counts: dict[str, int] = {}

    for text in lines:
        # ── 제목 ──────────────────────────────────────────────
        if not title_done:
            rendered.append(f"# {text.lstrip('# ').strip()}")
            title_done = True
            continue

        # ── 메타정보 ──────────────────────────────────────────
        if not meta_done:
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

        # ── 요약 ──────────────────────────────────────────────
        if SUMMARY_RE.match(text):
            rendered.append("")
            rendered.append("## 요약")
            context = "section"
            continue

        # ── <참고 N> 섹션 ─────────────────────────────────────
        ref = _match_reference_section(text)
        if ref is not None:
            rendered.append("")
            rendered.append(f"## {ref}")
            context = "section"
            continue

        # ── bare 참고 섹션 (꺾쇠 없이 "참고" 단독) ───────────
        if BARE_REFERENCE_RE.match(text):
            rendered.append("")
            rendered.append("## 참고")
            context = "section"
            continue

        # ── 로마자 섹션 제목 ───────────────────────────────────
        if ROMAN_HEADING_RE.match(text):
            rendered.append("")
            rendered.append(f"## {text}")
            context = "section"
            in_section_ii = text.startswith("Ⅱ.")
            in_section_iii = text.startswith("Ⅲ.")
            in_guideline_callout = False
            in_progress = False
            in_schedule_meta = False
            in_appendix2 = False
            current_group = None
            continue

        if text.startswith("붙임"):
            rendered.append("")
            rendered.append(f"## {text}")
            context = "section"
            in_section_ii = False
            in_section_iii = False
            in_guideline_callout = False
            in_progress = False
            in_schedule_meta = False
            in_appendix2 = text.startswith("붙임2")
            current_group = None
            continue

        if text in {"< 기존 문서 AI 활용 >", "< 앞으로의 문서 >"}:
            rendered.append("")
            rendered.append(f"### {text}")
            current_group = text.strip("<> ").strip()
            group_counts.setdefault(current_group, 0)
            in_guideline_callout = False
            in_progress = False
            in_schedule_meta = False
            continue

        task_match = re.match(r"^[󰋎󰋏󰋐]\s+(.+)$", text)
        if in_section_iii and current_group and task_match:
            group_counts[current_group] += 1
            rendered.append("")
            rendered.append(f"### {group_counts[current_group]}. {task_match.group(1)}")
            context = "section"
            in_guideline_callout = False
            continue

        if text == "< 가이드라인 예시 >":
            rendered.append("> < 가이드라인 예시 >")
            in_guideline_callout = True
            continue

        if in_appendix2 and text == "<개 요>":
            rendered.append("> <개 요>")
            continue

        if in_appendix2 and text.startswith("▶"):
            rendered.append(f"> {text}")
            continue

        if text == "< 추진경과 >":
            rendered.append("> < 추진경과 >")
            in_progress = True
            in_schedule_meta = False
            continue

        if text in {"□ 추진체계 : 인공지능정부실, 참여혁신조직실 공동", "□ 향후일정"}:
            rendered.append("")
            rendered.append(f"#### {text[2:].strip()}")
            in_progress = False
            in_schedule_meta = text.endswith("향후일정")
            context = "section"
            continue

        if in_guideline_callout and text.startswith("▸ "):
            indent = _quote_indent_from_previous_bullet(rendered)
            rendered.append(f"{indent}> {text}")
            continue

        if in_guideline_callout and not text.startswith(("▸ ", "<", ">")):
            in_guideline_callout = False

        if in_progress and text.startswith("○ "):
            rendered.append(f"> - {text[2:].strip()}")
            continue

        if in_progress and text.startswith("- "):
            rendered.append(f">    - {text[2:].strip()}")
            continue

        if in_schedule_meta and text.startswith("▸ "):
            for part in [clean_line(part) for part in text.split("<br>") if clean_line(part)]:
                indent = _quote_indent_from_previous_bullet(rendered, fallback="  ")
                rendered.append(f"{indent}> {part}")
            continue

        # ── ⃝ 불릿 ─────────────────────────────────────────────
        if text.startswith(CIRCLE_BULLET):
            content = text[1:].strip()
            rendered.append(f"- {content}")
            context = "circle"
            continue

        # ── □ 불릿 (최상위, 정책문서 스타일) ─────────────────
        if text.startswith(SQUARE_BULLET):
            content = text[1:].strip()
            if in_section_ii:
                rendered.append("")
                rendered.append(f"### {content}")
                context = "section"
                continue
            if in_appendix2:
                rendered.append("")
                rendered.append(f"#### {content}")
                context = "section"
                continue
            rendered.append(f"- {content}")
            context = "square"
            continue

        # ── ○ 불릿 (□ 하위 항목) ──────────────────────────────
        if text.startswith(CIRCLE_OPEN):
            content = text[1:].strip()
            rendered.append(f"- {content}")
            context = "circle"
            continue

        # ── √ / ‣ / ⦁ 불릿 ────────────────────────────────────
        if text and text[0] in (CHECK_BULLET, TRI_BULLET, FILLED_CIRCLE):
            content = text[1:].strip()
            rendered.append(f"  - {content}")
            continue

        # ── 각주 (* 로 시작) ───────────────────────────────────
        if text.startswith("*") and not text.startswith("**"):
            indent = _quote_indent_same_as_previous_bullet(rendered)
            rendered.append(f"{indent}> {text[1:].lstrip()}")
            continue

        # ── ※ 주석 ─────────────────────────────────────────────
        if text.startswith("※"):
            indent = _quote_indent_from_previous_bullet(
                rendered,
                fallback=_indent_for(context, "note"),
            )
            rendered.append(f"{indent}> {text}")
            continue

        # ── 한글 자모 + 꺾쇠 라벨 분리 ───────────────────────────
        kl_label = KOREAN_LETTER_WITH_LABEL_RE.match(text)
        if kl_label:
            korean_part = kl_label.group(1).strip()
            label_part = kl_label.group(2).strip()
            if context in ("numbered_top", "numbered_after_korean", "korean_letter_sub"):
                rendered.append(f"  {korean_part}")
                context = "korean_letter_sub"
            else:
                rendered.append(korean_part)
                context = "korean_letter"
            child_indent = _indent_for(context, "angle")
            rendered.append(f"{child_indent}> {label_part}")
            continue

        # ── 한글 자모 항목 (가. 나. 다.) ──────────────────────────
        if KOREAN_LETTER_RE.match(text):
            if context in ("numbered_top", "numbered_after_korean", "korean_letter_sub"):
                rendered.append(f"  {text}")
                context = "korean_letter_sub"
            else:
                rendered.append(text)
                context = "korean_letter"
            continue

        # ── 꺾쇠 라벨 ──────────────────────────────────────────
        if ANGLE_BRACKET_RE.match(text):
            indent = _indent_for(context, "angle")
            rendered.append(f"{indent}> {text}")
            continue

        # ── 번호 항목 (1. 2. 3.) ────────────────────────────────
        if NUMBERED_ITEM_RE.match(text):
            indent = _indent_for(context, "numbered")
            # 최상위 번호 항목이 들여쓰기된 줄 직후에 올 때 앞에 빈 줄 삽입
            if not indent and rendered:
                last_nonblank = next((l for l in reversed(rendered) if l.strip()), None)
                if last_nonblank and last_nonblank[0] == " ":
                    rendered.append("")
            rendered.append(f"{indent}{text}")
            if context in ("circle", "numbered_sub"):
                context = "numbered_sub"
            elif context in ("korean_letter", "korean_letter_sub", "numbered_after_korean"):
                context = "numbered_after_korean"
            else:
                context = "numbered_top"
            continue

        # ── - 불릿 ─────────────────────────────────────────────
        if BULLET_RE.match(text):
            indent = _indent_for(context, "dash")
            rendered.append(f"{indent}{text}")
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
