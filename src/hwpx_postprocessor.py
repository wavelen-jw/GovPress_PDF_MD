"""HWPX postprocessor aligned to the PDF markdown baseline."""
from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING

from .markdown_postprocessor import postprocess_markdown

if TYPE_CHECKING:
    from .hwpx_converter import Table


@dataclass
class HwpxParagraph:
    style_id: str
    text: str
    level: int = 0
    table: "Table | None" = field(default=None, repr=False, compare=False)


def _normalize_compare_text(text: str) -> str:
    return re.sub(r"\s+", "", text).strip()


def _normalize_loose_text(text: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", text)


def _canonical_line(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith(">"):
        stripped = stripped.lstrip("> ").strip()
    if _is_bullet_line(stripped):
        stripped = _strip_bullet(stripped)
    if stripped.startswith("※"):
        stripped = stripped[1:].strip()
    return stripped


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


def _is_merged_duplicate_line(text: str, upcoming: list[str]) -> bool:
    current = _normalize_loose_text(_canonical_line(text))
    if len(current) < 24:
        return False

    matched = 0
    covered = 0
    saw_structural = False

    for candidate in upcoming[:10]:
        candidate_norm = _normalize_loose_text(_canonical_line(candidate))
        if not candidate_norm:
            continue
        if len(candidate_norm) < 6 and not candidate.lstrip().startswith(("<", "(", "※", "□", "○", "▪", "", "▴")):
            continue
        if candidate_norm in current:
            matched += 1
            covered += len(candidate_norm)
            if candidate.lstrip().startswith(("<", "(", "※", "□", "○", "▪", "", "▴")):
                saw_structural = True
            continue
        if matched >= 3:
            break

    if matched >= 4 and covered >= max(28, int(len(current) * 0.45)):
        return True
    if saw_structural and matched >= 3 and covered >= max(24, int(len(current) * 0.35)):
        return True
    return False


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
        if cleaned and current_norm == _normalize_compare_text(cleaned[-1].text):
            index += 1
            continue

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

        upcoming: list[str] = []
        for offset in range(1, 13):
            if index + offset >= len(paragraphs):
                break
            next_text = paragraphs[index + offset].text.strip()
            if not next_text:
                continue
            upcoming.append(next_text)
            joined_norm = _normalize_compare_text("".join(upcoming))
            joined_loose = _normalize_loose_text("".join(upcoming))
            current_loose = _normalize_loose_text(text)
            if joined_norm == current_norm:
                text = ""
                break
            if joined_loose and len(joined_loose) >= 8 and joined_loose in current_loose:
                text = ""
                break
            if (
                next_nonblank
                and len(_normalize_loose_text(next_nonblank)) >= 8
                and current_loose.startswith(_normalize_loose_text(next_nonblank))
                and any(_normalize_loose_text(part) in current_loose for part in upcoming[1:] if part.strip())
            ):
                text = ""
                break
        if text and _is_merged_duplicate_line(text, upcoming):
            text = ""

        if text:
            cleaned.append(HwpxParagraph(style_id=para.style_id, text=text, level=para.level))
        index += 1

    return cleaned


def _normalize_preamble_lines(lines: list[str]) -> list[str]:
    normalized: list[str] = []
    index = 0
    while index < len(lines):
        text = lines[index].strip()
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


def _dedupe_structural_lines(lines: list[str]) -> list[str]:
    deduped: list[str] = []

    for text in lines:
        stripped = text.strip()
        if not stripped:
            deduped.append("")
            continue

        if deduped:
            previous = deduped[-1].strip()
            if previous and _normalize_compare_text(previous) == _normalize_compare_text(stripped):
                continue
            if (
                previous.startswith("〈 평가 영역별 결과")
                and stripped.startswith(("관리체계", "품질", "개방·활용"))
                and _normalize_loose_text(stripped) in _normalize_loose_text(previous)
            ):
                continue
            if (
                stripped.startswith("〈 평가 영역별 결과")
                and previous.startswith("〈 평가 영역별 결과")
                and _normalize_loose_text(previous) in _normalize_loose_text(stripped)
            ):
                deduped[-1] = stripped
                continue

        deduped.append(stripped)

    return deduped


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
            if (
                candidate.startswith("<참고")
                or candidate.startswith("참고")
                or candidate.startswith("붙임")
                or candidate.startswith("별첨")
            ):
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
    if not paragraphs:
        return ""

    lines = [para.text for para in _clean_paragraphs(paragraphs)]
    lines = _normalize_preamble_lines(lines)
    lines = _merge_contact_lines(lines)
    lines = _dedupe_structural_lines(lines)
    lines = _render_comparison_tables(lines)
    return postprocess_markdown("\n".join(line for line in lines if line is not None))
