"""HWPX 후처리기.

HWPX에서는 단락 스타일이 모두 '본문'으로 설정되어 있어 스타일 정보를 활용할 수 없다.
따라서 텍스트 내용만으로 문서 구조를 판단하며, PDF와 동일한 변환규칙을 적용한다.

처리 흐름
----------
postprocess_hwpx(paragraphs)
  → 단락 텍스트를 줄 단위로 이어붙임
  → postprocess_markdown()에 위임
     ├─ 보도자료 감지  → _postprocess_press_release()
     ├─ 보고서 감지    → postprocess_report()
     ├─ 안내문 감지    → postprocess_service_guide()
     └─ 기타           → _postprocess_generic_markdown()

HWPX 텍스트는 PDF 아티팩트(페이지 번호, TOC 점선, 이미지 참조)가 없으므로
preclean 단계가 실질적으로 무해하게 통과된다.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

from .markdown_postprocessor import postprocess_markdown


@dataclass
class HwpxParagraph:
    """HWPX 단락 하나를 표현하는 중간 표현."""
    style_id: str   # 한글 스타일 이름 (실제로는 모두 "본문"이므로 사용하지 않음)
    text: str       # 정제된 텍스트
    level: int = 0  # 들여쓰기 수준 (사용하지 않음)


def _normalize_compare_text(text: str) -> str:
    return re.sub(r"\s+", "", text).strip()


def _normalize_loose_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text)


def _is_short_artifact(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and len(stripped) <= 2 and not re.search(r"\d", stripped)


def _is_bullet_line(text: str) -> bool:
    return text.lstrip().startswith(("-", "•", "○", "ㅇ", "", "\uf0a7", "‧"))


def _strip_bullet(text: str) -> str:
    return text.lstrip("-•○ㅇ‧\uf0a7 ").strip()


def _looks_like_metadata_detail(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if stripped.startswith("("):
        return True
    if "보도자료" in stripped or "보도시점" in stripped:
        return True
    if re.search(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.", stripped):
        return True
    if any(token in stripped for token in ("조간", "석간", "국무회의 종료 시", "인터넷", "지면", "온라인")):
        return True
    return False


def _split_compound_title_line(text: str) -> tuple[str, list[str]] | None:
    stripped = text.strip()
    if " - " not in stripped or stripped.startswith("-"):
        return None

    parts = [part.strip(" -") for part in stripped.split(" - ") if part.strip(" -")]
    if len(parts) < 2:
        return None

    title = parts[0]
    subtitles = parts[1:]
    if len(_normalize_loose_text(title)) < 8:
        return None
    if any(len(_normalize_loose_text(item)) < 8 for item in subtitles):
        return None
    if any(_looks_like_metadata_detail(item) for item in parts):
        return None
    return title, [f"- {item}" for item in subtitles]


def _clean_paragraphs(paragraphs: list[HwpxParagraph]) -> list[HwpxParagraph]:
    cleaned: list[HwpxParagraph] = []
    index = 0

    while index < len(paragraphs):
        para = paragraphs[index]
        text = para.text.strip()
        if not text:
            cleaned.append(HwpxParagraph(style_id=para.style_id, text="", level=para.level))
            index += 1
            continue

        current_norm = _normalize_compare_text(text)

        if cleaned:
            previous_norm = _normalize_compare_text(cleaned[-1].text)
            if current_norm and current_norm == previous_norm:
                index += 1
                continue

        # 같은 문구가 짧은 간격으로 반복되면 뒤쪽 중복을 버린다.
        next_nonblank = None
        for offset in range(1, 4):
            if index + offset >= len(paragraphs):
                break
            candidate = paragraphs[index + offset].text.strip()
            if candidate:
                next_nonblank = candidate
                break
        if next_nonblank and current_norm == _normalize_compare_text(next_nonblank):
            index += 1
            continue

        if (
            index < 12
            and _is_short_artifact(text)
            and index + 1 < len(paragraphs)
            and paragraphs[index + 1].text.strip().startswith(("보도자료", "보도시점"))
        ):
            index += 1
            continue

        # 일부 HWPX는 "합쳐진 한 줄"과 "분해된 여러 줄"을 연속으로 함께 내보낸다.
        # 뒤따르는 2~4개 문단을 붙인 결과가 현재 문단과 같으면 현재 문단을 버린다.
        lookahead_parts: list[str] = []
        for offset in range(1, 5):
            if index + offset >= len(paragraphs):
                break
            next_text = paragraphs[index + offset].text.strip()
            if not next_text:
                continue
            lookahead_parts.append(next_text)
            joined_norm = _normalize_compare_text("".join(lookahead_parts))
            joined_loose = _normalize_loose_text("".join(lookahead_parts))
            current_loose = _normalize_loose_text(text)
            if joined_norm and joined_norm == current_norm:
                text = ""
                break
            if joined_loose and len(joined_loose) >= 8 and joined_loose in current_loose:
                text = ""
                break
            if (
                next_nonblank
                and len(_normalize_loose_text(next_nonblank)) >= 8
                and current_loose.startswith(_normalize_loose_text(next_nonblank))
                and any(part.strip() and _normalize_loose_text(part) in current_loose for part in lookahead_parts[1:])
            ):
                text = ""
                break

        if text:
            cleaned.append(HwpxParagraph(style_id=para.style_id, text=text, level=para.level))
        index += 1

    return cleaned


def _normalize_preamble_lines(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        text = line.strip()
        if not text:
            normalized.append("")
            index += 1
            continue

        if text.startswith("보도자료보도시점") and any(item == "보도시점" for item in lines[index + 1 : index + 4]):
            index += 1
            continue
        if _is_short_artifact(text) and index < 10:
            next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if next_line.startswith(("보도자료", "보도시점")):
                index += 1
                continue

        if text == "보도시점":
            details: list[str] = []
            cursor = index + 1
            while cursor < len(lines):
                candidate = lines[cursor].strip()
                if not candidate:
                    cursor += 1
                    continue
                if candidate.startswith(("보도자료", "#", "<")) or candidate.endswith("보도자료"):
                    break
                if candidate.startswith(("-", ">", "□", "○", "◆")) or candidate.endswith((".", "다.")):
                    break
                if not _looks_like_metadata_detail(candidate):
                    break
                details.append(candidate)
                cursor += 1
                if len(details) >= 2:
                    break
            if details:
                normalized.append(f"보도시점: {' / '.join(details)}")
                index = cursor
                continue

        compound_title = _split_compound_title_line(text)
        if compound_title and index < 16:
            title, subtitles = compound_title
            normalized.append(title)
            normalized.extend(subtitles)

            duplicate_norms = {_normalize_loose_text(title)}
            duplicate_norms.update(_normalize_loose_text(item) for item in subtitles)

            cursor = index + 1
            while cursor < len(lines):
                candidate = lines[cursor].strip()
                if not candidate:
                    cursor += 1
                    continue
                candidate_norm = _normalize_loose_text(candidate.lstrip("- ").strip())
                if candidate_norm and candidate_norm in duplicate_norms:
                    cursor += 1
                    continue
                break
            index = cursor
            continue

        if (
            index >= 1
            and not _is_bullet_line(text)
            and not text.startswith(("보도자료", "보도시점", "담당", "<", "◆", "□", "○"))
            and not text.endswith((".", "다", "다.", "했다.", "있다.", "밝혔다."))
            and lines[index - 1].strip()
            and not _is_bullet_line(lines[index - 1].strip())
            and not lines[index - 1].strip().startswith(("보도자료", "보도시점"))
        ):
            previous_normalized = next((item.strip() for item in reversed(normalized) if item.strip()), "")
            next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
            if next_line.startswith("-") and not previous_normalized.startswith(("보도자료", "보도시점")):
                normalized.append(f"- {text}")
                index += 1
                continue

        normalized.append(text)
        index += 1

    return normalized


def _merge_contact_lines(lines: list[str]) -> list[str]:
    merged: list[str] = []
    index = 0

    while index < len(lines):
        text = lines[index].strip()
        if text != "담당 부서":
            merged.append(text)
            index += 1
            continue

        block: list[str] = []
        index += 1
        while index < len(lines):
            candidate = lines[index].strip()
            if not candidate:
                index += 1
                continue
            if candidate.startswith("<참고") or candidate.startswith("붙임") or candidate.startswith("별첨"):
                break
            block.append(candidate)
            index += 1

        if not block:
            merged.append("담당 부서")
            continue

        role_labels = {"책임자", "담당자"}
        entries: list[tuple[str, str, str]] = []
        current_top = ""
        current_department = ""
        last_role = ""
        pointer = 0

        while pointer < len(block):
            token = block[pointer]
            if token in role_labels:
                role = token
                title = block[pointer + 1] if pointer + 1 < len(block) else ""
                name = block[pointer + 2] if pointer + 2 < len(block) else ""
                phone = block[pointer + 3] if pointer + 3 < len(block) else ""
                pointer += 4

                if not current_department:
                    current_department = current_top
                detail = " ".join(part for part in (title, name, phone) if part).strip()
                entries.append((current_department.strip(), role, detail))
                last_role = role
                continue

            next_token = block[pointer + 1] if pointer + 1 < len(block) else ""
            if next_token in role_labels:
                if last_role == "담당자" or not current_top:
                    current_top = token
                    current_department = token
                else:
                    current_department = " ".join(part for part in (current_top, token) if part).strip()
                    if entries:
                        dept, role, detail = entries[-1]
                        entries[-1] = (current_department, role, detail)
                pointer += 1
                continue

            pointer += 1

        if not entries:
            merged.append("담당 부서")
            merged.extend(block)
            continue

        last_department = None
        for department, role, detail in entries:
            if department != last_department:
                merged.append(f"담당 부서: {department}")
                last_department = department
            merged.append(f"{role}: {detail}")

    return merged


def _render_comparison_tables(lines: list[str]) -> list[str]:
    rendered: list[str] = []
    index = 0

    while index < len(lines):
        if index + 3 < len(lines) and lines[index].strip() == "현행" and lines[index + 1].strip() == "개선":
            rows: list[tuple[str, list[str], list[str]]] = []
            cursor = index + 2
            while cursor < len(lines):
                label = lines[cursor].strip()
                if not label:
                    break
                if label.startswith(("####", "##", "#", "<", ">", "담당 부서", "책임자:", "담당자:")):
                    break
                if _is_bullet_line(label):
                    break
                cursor += 1

                bullets: list[str] = []
                while cursor < len(lines) and _is_bullet_line(lines[cursor].strip()):
                    bullets.append(_strip_bullet(lines[cursor]))
                    cursor += 1

                if len(bullets) < 2:
                    break
                split_at = 1 if len(bullets) <= 3 else len(bullets) // 2
                rows.append((label, bullets[:split_at], bullets[split_at:]))

            if rows:
                rendered.append("| | 현행 | 개선 |")
                rendered.append("| --- | --- | --- |")
                for label, left_items, right_items in rows:
                    left = "<br>".join(item for item in left_items if item)
                    right = "<br>".join(item for item in right_items if item)
                    rendered.append(f"| {label} | {left} | {right} |")
                index = cursor
                continue

        rendered.append(lines[index])
        index += 1

    return rendered


def postprocess_hwpx(paragraphs: list[HwpxParagraph]) -> str:
    """HWPX 단락 목록을 최종 Markdown 문자열로 변환한다.

    스타일 정보를 무시하고 텍스트 내용만으로 문서 타입을 감지해
    기존 PDF 변환규칙(postprocess_markdown)을 그대로 적용한다.

    Args:
        paragraphs: hwpx_converter가 추출한 단락 목록.

    Returns:
        정규화된 Markdown 문자열.
    """
    if not paragraphs:
        return ""

    cleaned = _clean_paragraphs(paragraphs)
    lines = [para.text for para in cleaned]
    lines = _normalize_preamble_lines(lines)
    lines = _merge_contact_lines(lines)
    lines = _render_comparison_tables(lines)
    raw_text = "\n".join(line for line in lines if line is not None)
    return postprocess_markdown(raw_text)
