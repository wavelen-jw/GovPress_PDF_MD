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


# ── 메인 함수 ────────────────────────────────────────────────

def postprocess_report(raw_text: str) -> str:
    """일반 보고서 raw text → 정제된 Markdown."""
    raw_lines = [clean_line(line) for line in raw_text.splitlines()]
    lines = _preprocess([l for l in raw_lines if l])
    if not lines:
        return ""

    rendered: list[str] = []
    title_done = False
    meta_done = False
    context: str | None = None

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
            rendered.append(f"### {text}")
            context = "section"
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
            rendered.append(f"- {content}")
            context = "square"
            continue

        # ── ○ 불릿 (□ 하위 항목) ──────────────────────────────
        if text.startswith(CIRCLE_OPEN):
            content = text[1:].strip()
            rendered.append(f"  - {content}")
            continue

        # ── √ / ‣ / ⦁ 불릿 ────────────────────────────────────
        if text and text[0] in (CHECK_BULLET, TRI_BULLET, FILLED_CIRCLE):
            content = text[1:].strip()
            rendered.append(f"  - {content}")
            continue

        # ── 각주 (* 로 시작) ───────────────────────────────────
        if text.startswith("*") and not text.startswith("**"):
            rendered.append(f">{text[1:].lstrip()}")
            continue

        # ── ※ 주석 ─────────────────────────────────────────────
        if text.startswith("※"):
            indent = _indent_for(context, "note")
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

    return "\n".join(cleaned) + "\n"


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

# ※ 주석
_NOTE_RE = re.compile(r"^※")


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
            rendered.append(f"### {text}")
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
