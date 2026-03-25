from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Iterable

from .document_template import PressReleaseTemplate, DEFAULT_TEMPLATE


CONTACT_SPLIT_PATTERN = re.compile(
    r"(?=(?:담당\s*부서|담당부서|책임자|담당자)\s*[:：]?)"
)
BRIEFING_DETAIL_PATTERN = re.compile(
    r"^(?:\(.+\)|.+\d{4}\.\s*\d{1,2}\.\s*\d{1,2}\.?.*|.*조간.*|.*석간.*)$"
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
    text = re.sub(r"\s+", " ", line.replace("\u00a0", " ")).strip()
    return text


def is_page_noise(line: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE) -> bool:
    return bool(template.page_noise_pattern.match(line))


def is_appendix_line(line: str, template: PressReleaseTemplate = DEFAULT_TEMPLATE) -> bool:
    stripped = clean_line(line)
    return stripped.startswith(("붙임", "별첨"))


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


def normalize_contact_line(line: str) -> str:
    text = clean_line(line)
    text = text.replace("：", ":")
    return re.sub(r"\s*:\s*", ": ", text)


def split_contact_chunks(lines: Iterable[str]) -> list[str]:
    joined = " ".join(clean_line(line) for line in lines if clean_line(line))
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
    for line in lines:
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
            if is_briefing_detail_line(line):
                sections.metadata_lines.append(line)
            elif is_top_level_body_line(line, template):
                current = "body"
                sections.body_lines.append(line)
            elif line.startswith("-"):
                sections.subtitle_lines.append(line)
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
