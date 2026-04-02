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

from .markdown_postprocessor import postprocess_markdown


@dataclass
class HwpxParagraph:
    """HWPX 단락 하나를 표현하는 중간 표현."""
    style_id: str   # 한글 스타일 이름 (실제로는 모두 "본문"이므로 사용하지 않음)
    text: str       # 정제된 텍스트
    level: int = 0  # 들여쓰기 수준 (사용하지 않음)


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

    raw_text = "\n".join(para.text for para in paragraphs)
    return postprocess_markdown(raw_text)
