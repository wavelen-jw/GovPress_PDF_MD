from __future__ import annotations

from dataclasses import dataclass, field
from typing import Pattern
import re


@dataclass(frozen=True)
class ContactLabels:
    department: tuple[str, ...] = ("담당 부서", "담당부서")
    manager: tuple[str, ...] = ("책임자",)
    staff: tuple[str, ...] = ("담당자",)


@dataclass(frozen=True)
class PressReleaseTemplate:
    title_marker: str = "보도자료"
    briefing_marker: str = "보도시점"
    appendix_markers: tuple[str, ...] = ("붙임", "참고", "별첨")
    top_level_bullets: tuple[str, ...] = ("□",)
    second_level_bullets: tuple[str, ...] = ("○",)
    third_level_bullets: tuple[str, ...] = ("-", "*")
    page_noise_pattern: Pattern[str] = field(
        default_factory=lambda: re.compile(r"^\s*-\s*\d+\s*-\s*$")
    )
    press_label_pattern: Pattern[str] = field(
        default_factory=lambda: re.compile(r"^\s*보도자료\s*$")
    )
    briefing_line_pattern: Pattern[str] = field(
        default_factory=lambda: re.compile(r"^\s*보도시점\b")
    )
    contact_labels: ContactLabels = field(default_factory=ContactLabels)


DEFAULT_TEMPLATE = PressReleaseTemplate()
