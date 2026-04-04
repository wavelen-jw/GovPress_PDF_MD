from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from .document_template import PressReleaseTemplate, DEFAULT_TEMPLATE


CONTACT_SPLIT_PATTERN = re.compile(
    r"(?=(?:담당\s*부서|담당부서|책임자|담당자)\s*[:：]?)"
)
CONTACT_TRAILING_NOISE_PATTERN = re.compile(
    r"(?=<\s*참고|참\s*고|붙\s*임|별첨|□\s*적용\s*전)"
)
BRIEFING_DETAIL_PATTERN = re.compile(
    r"^(?:\(.+\)|.+\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?.*|.*조간.*|.*석간.*)$"
)
BODY_SENTENCE_PATTERN = re.compile(
    r".*(?:다\.|다$|했다\.|한다고\b|밝혔다\.|말했다\.|설명했다\.|예정이다\.|기대된다\.)$"
)

SPACING_ARTIFACT_REPLACEMENTS = (
    ("과 장", "과장"),
    ("국립 과학수사연구원", "국립과학수사연구원"),
    ("장관 표창", "장관표창"),
    ("추진 방안", "추진방안"),
    ("이행 계획", "이행계획"),
    ("추진 체계", "추진체계"),
    ("지역 사회", "지역사회"),
    ("공동체 금융 기관", "공동체 금융기관"),
    ("사회 연대금융", "사회연대금융"),
)


@dataclass
class ParsedSections:
    metadata_lines: list[str] = field(default_factory=list)
    title_lines: list[str] = field(default_factory=list)
    subtitle_lines: list[str] = field(default_factory=list)
    body_lines: list[str] = field(default_factory=list)
    appendix_lines: list[str] = field(default_factory=list)
    contact_lines: list[str] = field(default_factory=list)


def clean_line(line: str) -> str:
    text = re.sub(r"\s+", " ", line.replace("\u00a0", " ").replace("\x00", "")).strip()
    for source, target in SPACING_ARTIFACT_REPLACEMENTS:
        text = text.replace(source, target)
    return text


def is_page_noise(line: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE) -> bool:
    return bool(template.page_noise_pattern.match(line))


def is_appendix_line(line: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE) -> bool:
    stripped = clean_line(line)
    return stripped.startswith(("붙임", "붙 임", "별첨", "참고 ", "참고:", "참고  ", "참고\t")) or stripped == "참고"


def is_reference_line(line: str) -> bool:
    stripped = clean_line(line)
    return (
        stripped.startswith("<참고")
        or stripped.startswith("< 참고")
        or stripped.startswith("참고 :")
        or stripped.startswith("참고:")
    )


def is_contact_line(line: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE) -> bool:
    stripped = clean_line(line)
    labels = (
        *template.contact_labels.department,
        *template.contact_labels.manager,
        *template.contact_labels.staff,
    )
    return any(stripped.startswith(label) for label in labels)


def is_top_level_body_line(
    line: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE
) -> bool:
    stripped = clean_line(line)
    return any(stripped.startswith(marker) for marker in template.top_level_bullets)


def is_briefing_detail_line(line: str) -> bool:
    stripped = clean_line(line)
    return bool(BRIEFING_DETAIL_PATTERN.match(stripped))


def looks_like_body_paragraph(line: str) -> bool:
    stripped = clean_line(line)
    if not stripped:
        return False
    if stripped.startswith(("◆", "◇", "▶", "▣")):
        return True
    if BODY_SENTENCE_PATTERN.match(stripped):
        return True
    return len(stripped) >= 55 and " " in stripped


def normalize_contact_line(line: str) -> str:
    text = clean_line(line)
    text = text.replace("：", ":")
    text = re.sub(r"\b과\s+장\b", "과장", text)
    return re.sub(r"\s*:\s*", ": ", text)


def looks_like_title_fragment(line: str) -> bool:
    stripped = clean_line(line)
    if not stripped:
        return False
    if stripped.startswith(("-", ">", "□", "○", "◆", "◇", "▶", "▣", "<")):
        return False
    if is_briefing_detail_line(stripped):
        return False
    if looks_like_body_paragraph(stripped):
        return False
    return len(stripped) <= 80


def should_join_title_lines(previous: str, current: str) -> bool:
    prev = clean_line(previous)
    curr = clean_line(current)
    if not prev or not curr:
        return False
    if prev.endswith((",", "…", ":", "·", "‧")):
        return True
    if prev.endswith(("“", "‘", "(", "〈", "<")):
        return True
    if curr.startswith(("“", "‘", "「", "『", "(", "<")):
        return True
    return False


def split_contact_chunks(lines: Iterable[str]) -> list[str]:
    joined = " ".join(clean_line(line) for line in lines if clean_line(line))
    if not joined:
        return []
    joined = CONTACT_TRAILING_NOISE_PATTERN.split(joined, maxsplit=1)[0].strip()
    if not joined:
        return []

    parts = CONTACT_SPLIT_PATTERN.split(joined)
    chunks = [normalize_contact_line(part) for part in parts if clean_line(part)]
    return chunks


def extract_sections(
    raw_text: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE
) -> ParsedSections:
    sections = ParsedSections()
    lines = [clean_line(line) for line in raw_text.splitlines()]
    lines = [line for line in lines if line and not is_page_noise(line, template)]

    current = "preamble"
    for index, line in enumerate(lines):
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if template.press_label_pattern.match(line):
            continue

        if current != "contact" and is_contact_line(line, template):
            current = "contact"
            sections.contact_lines.append(line)
            continue

        if current not in {"appendix", "contact"} and is_appendix_line(line, template):
            current = "appendix"
            sections.appendix_lines.append(line)
            continue

        if current == "preamble" and template.briefing_line_pattern.match(line):
            sections.metadata_lines.append(line)
            continue

        if current == "preamble" and sections.metadata_lines:
            if (
                sections.title_lines
                and sections.subtitle_lines
                and (
                    line.startswith(("<", "(", "※", "*"))
                    or is_top_level_body_line(line, template)
                )
            ):
                current = "body"
                sections.body_lines.append(line)
                continue

            if is_briefing_detail_line(line):
                sections.metadata_lines.append(line)
            elif line.startswith("-"):
                sections.subtitle_lines.append(line)
            elif sections.title_lines and should_join_title_lines(sections.title_lines[-1], line):
                sections.title_lines.append(line)
            elif sections.title_lines and not sections.subtitle_lines and looks_like_title_fragment(line):
                if next_line.startswith("-") or should_join_title_lines(sections.title_lines[-1], line):
                    sections.subtitle_lines.append(f"- {line}")
                else:
                    sections.title_lines.append(line)
            elif sections.title_lines and (
                sections.subtitle_lines or looks_like_body_paragraph(line)
            ):
                current = "body"
                sections.body_lines.append(line)
            elif is_top_level_body_line(line, template):
                current = "body"
                sections.body_lines.append(line)
            else:
                sections.title_lines.append(line)
            continue

        if current == "preamble":
            sections.metadata_lines.append(line)
            continue

        if current == "body":
            if is_contact_line(line, template):
                current = "contact"
                sections.contact_lines.append(line)
            elif is_appendix_line(line, template):
                current = "appendix"
                sections.appendix_lines.append(line)
            else:
                sections.body_lines.append(line)
            continue

        if current == "appendix":
            if is_contact_line(line, template):
                current = "contact"
                sections.contact_lines.append(line)
            else:
                sections.appendix_lines.append(line)
            continue

        if current == "contact":
            if is_appendix_line(line, template):
                current = "appendix"
                sections.appendix_lines.append(line)
            else:
                sections.contact_lines.append(line)

    if not sections.title_lines and sections.metadata_lines:
        fallback_title = []
        trailing_meta = []
        for line in sections.metadata_lines:
            if template.briefing_line_pattern.match(line):
                trailing_meta.append(line)
            else:
                fallback_title.append(line)
        if fallback_title:
            sections.title_lines = fallback_title
            sections.metadata_lines = trailing_meta

    return sections
