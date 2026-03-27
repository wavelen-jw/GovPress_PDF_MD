from pathlib import Path
import base64
import tempfile
import unittest

from src.converter import (
    _stage_input_pdf_for_conversion,
    convert_pdf_to_document,
    convert_pdf_to_markdown,
)
from src.json_extractor import extract_text_from_json
from src.markdown_postprocessor import postprocess_markdown
from src.pymupdf_extractor import extract_text_from_pdf_with_pymupdf
from src.utils import save_markdown_file


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
FIXTURE_DIR = TESTS_DIR / "fixtures" / "press_release"
GOLDEN_DIR = TESTS_DIR / "converted_md" / "press_release"
GOLDEN_PRESS_RELEASE = FIXTURE_DIR / "260325 (14시) 대전 대덕구 공장 화재 중앙재난안전대책본부 6차 회의 개최(국토산업재난대응과).pdf"
GOLDEN_PRESS_RELEASE_MD = FIXTURE_DIR / "260325 (14시) 대전 대덕구 공장 화재 중앙재난안전대책본부 6차 회의 개최(국토산업재난대응과).md"
GOLDEN_PRESS_RELEASE_2 = FIXTURE_DIR / "260324 (국무회의 종료시) 78년 만의 수사‧기소 분리 중대범죄수사청 출범 본격 착수(중대범죄수사청설립지원단).pdf"
GOLDEN_PRESS_RELEASE_MD_2 = GOLDEN_DIR / "260324 (국무회의 종료시) 78년 만의 수사‧기소 분리 중대범죄수사청 출범 본격 착수(중대범죄수사청설립지원단).md"
GOLDEN_PRESS_RELEASE_3 = FIXTURE_DIR / "260324 (국무회의 종료시) 주민과 함께 만드는 풍요로운 마을 햇빛소득마을 전국 확산 본격 추진(햇빛소득마을추진단).pdf"
GOLDEN_PRESS_RELEASE_MD_3 = GOLDEN_DIR / "260324 (국무회의 종료시) 주민과 함께 만드는 풍요로운 마을 햇빛소득마을 전국 확산 본격 추진(햇빛소득마을추진단).md"
GOLDEN_PRESS_RELEASE_4 = FIXTURE_DIR / "260326 (조간) 부울경 복합재난 대비 역량 강화를 위한 한·일 공동세미나 개최(국립재난안전연구원 지진방재센터).pdf"
GOLDEN_PRESS_RELEASE_MD_4 = GOLDEN_DIR / "260326 (조간) 부울경 복합재난 대비 역량 강화를 위한 한·일 공동세미나 개최(국립재난안전연구원 지진방재센터).md"
GOLDEN_PRESS_RELEASE_5 = FIXTURE_DIR / "260326 (17시) 살피고 대피하라! 고층건축물 화재 대비 올해 첫 레디 코리아 훈련(재난대응훈련과).pdf"
GOLDEN_PRESS_RELEASE_MD_5 = GOLDEN_DIR / "260326 (17시) 살피고 대피하라! 고층건축물 화재 대비 올해 첫 레디 코리아 훈련(재난대응훈련과).md"
GOLDEN_PRESS_RELEASE_6 = FIXTURE_DIR / "260326 (15시) 과학수사 발전 격려하고 서민금융 현장 살펴(자치행정과).pdf"
GOLDEN_PRESS_RELEASE_MD_6 = GOLDEN_DIR / "260326 (15시) 과학수사 발전 격려하고 서민금융 현장 살펴(자치행정과).md"
GOLDEN_PRESS_RELEASE_7 = FIXTURE_DIR / "260325 (조간) 새로운 시설물 속 숨은 위험 찾는다 잠재 재난위험 분석 보고서 발간(재난대응총괄과).pdf"
GOLDEN_PRESS_RELEASE_MD_7 = GOLDEN_DIR / "260325 (조간) 새로운 시설물 속 숨은 위험 찾는다 잠재 재난위험 분석 보고서 발간(재난대응총괄과).md"
COMBINED_BRIEFING_PRESS_RELEASE = FIXTURE_DIR / "260326 (18시) 전남·광주 통합 지역소멸 극복과 대한민국 대도약의 마중물 만들 것(자치행정과).pdf"
MULTILINE_TITLE_PRESS_RELEASE = FIXTURE_DIR / "260325 (조간) 공공부문에서 인공지능(AI) 어떻게 써야해 「AI 정부 서비스 사례집」에 우수사례 총집합(공공인공지능혁신과).pdf"
SAMPLE_PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aP1cAAAAASUVORK5CYII="
)


class ConverterTests(unittest.TestCase):
    @staticmethod
    def _normalize_markdown_for_assertion(text: str) -> str:
        return "\n".join(line.rstrip() for line in text.splitlines() if line.strip()).strip()

    def _assert_matches_golden(self, actual: str, golden_path: Path) -> None:
        if not golden_path.exists():
            self.skipTest(f"golden fixture missing: {golden_path}")

        expected = golden_path.read_text(encoding="utf-8")
        self.assertEqual(
            self._normalize_markdown_for_assertion(actual),
            self._normalize_markdown_for_assertion(expected),
        )

    def test_invalid_path_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            convert_pdf_to_markdown("/tmp/does-not-exist.pdf")

    def test_non_pdf_rejected(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".txt") as handle:
            with self.assertRaises(ValueError):
                convert_pdf_to_markdown(handle.name)

    def test_invalid_backend_rejected(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".pdf") as handle:
            with self.assertRaises(ValueError):
                convert_pdf_to_markdown(handle.name, backend="unknown")

    def test_pymupdf_extractor_reads_press_release_structure(self) -> None:
        raw = extract_text_from_pdf_with_pymupdf(GOLDEN_PRESS_RELEASE)
        self.assertIn("보도자료", raw)
        self.assertIn("보도시점", raw)
        self.assertIn("중앙재난안전대책본부 6차 회의 개최", raw)
        self.assertIn("담당 부서:", raw)

    def test_pymupdf_backend_keeps_core_sections_on_golden_fixture(self) -> None:
        markdown = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE, backend="pymupdf")
        for snippet in (
            "# 대전 대덕구 공장 화재 중앙재난안전대책본부 6차 회의 개최",
            "> 보도시점: (인터넷, 지면) 2026. 3. 25.(수) 14:00",
            "---",
            "정부는 중앙재난안전대책본부 차장",
            "## 담당부서",
        ):
            self.assertIn(snippet, markdown)

    def test_pymupdf_backend_normalizes_split_briefing_metadata(self) -> None:
        markdown = convert_pdf_to_markdown(COMBINED_BRIEFING_PRESS_RELEASE, backend="pymupdf")
        self.assertIn(
            "# 전남·광주 통합, 지역소멸 극복과 대한민국 대도약의 마중물 만들 것",
            markdown,
        )
        self.assertIn(
            "> 보도시점: (온라인) 2026. 3. 25.(수) 18:00 / (지 면) 2026. 3. 26.(목) 조간",
            markdown,
        )
        self.assertIn("## 담당부서", markdown)

    def test_pymupdf_backend_preserves_multiline_title_after_metadata(self) -> None:
        markdown = convert_pdf_to_markdown(MULTILINE_TITLE_PRESS_RELEASE, backend="pymupdf")
        self.assertIn(
            "# 공공부문에서 인공지능(AI) 어떻게 써야해? 「AI 정부 서비스 사례집」에 우수사례 총집합",
            markdown,
        )
        self.assertIn(
            "> 보도시점: (온라인) 2026. 3. 24.(화) 12:00 / (지 면) 2026. 3. 25.(수) 조간",
            markdown,
        )
        self.assertIn("## 담당부서", markdown)

    def test_stage_input_pdf_for_conversion_copies_to_temp_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "sample.pdf"
            source_path.write_bytes(b"%PDF-1.4")
            temp_root = Path(temp_dir) / "work"
            temp_root.mkdir()

            staged_path = _stage_input_pdf_for_conversion(source_path, temp_root)

            self.assertEqual(staged_path, temp_root / "input.pdf")
            self.assertTrue(staged_path.exists())
            self.assertEqual(staged_path.read_bytes(), b"%PDF-1.4")

    def test_pymupdf_document_extracts_images_and_save_copies_them(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            import fitz

            temp_root = Path(temp_dir)
            pdf_path = temp_root / "sample.pdf"
            document = fitz.open()
            page = document.new_page()
            page.insert_text((72, 72), "보도자료\n보도시점 (온라인) 2026. 3. 24.\n제목\n□ 본문")
            page.insert_image(fitz.Rect(72, 120, 144, 192), stream=SAMPLE_PNG_BYTES)
            document.save(pdf_path)
            document.close()

            converted = convert_pdf_to_document(pdf_path, backend="pymupdf")

            self.assertIsNotNone(converted.image_dir)
            image_files = list(converted.image_dir.glob("*")) if converted.image_dir else []
            self.assertTrue(image_files)

            save_path = temp_root / "saved.md"
            save_markdown_file(save_path, "![image 1](sample_images/test.png)\n", converted.image_dir)

            copied_dir = temp_root / converted.image_dir.name
            self.assertTrue(copied_dir.exists())
            self.assertTrue(any(path.is_file() for path in copied_dir.iterdir()))
            self.assertIn("sample_images/test.png", save_path.read_text(encoding="utf-8"))

    def test_pymupdf_document_keeps_image_links_in_real_fixture(self) -> None:
        pdf = Path(
            "/home/wavel/GovPress_PDF_MD/re_test/press/260325 (조간) 보고서 꾸미는 시간에 민생 현장으로 행정안전부 AI친화 행정문서 혁신 시범 실시(혁신행정담당관).pdf"
        )
        converted = convert_pdf_to_document(pdf, backend="pymupdf")
        self.assertIn("![image 1](", converted.markdown)
        self.assertIsNotNone(converted.image_dir)

    def test_postprocessor_formats_contacts(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 온라인 2026. 3. 25.\n"
            "전남·광주 통합,\n"
            "대한민국 대도약의 마중물\n"
            "- 부제 예시\n"
            "□ 첫 문단\n"
            "○ 설명\n"
            "담당 부서: 혁신팀 책임자: 홍길동 담당자: 김철수\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("# 전남·광주 통합, 대한민국 대도약의 마중물", markdown)
        self.assertIn("## 담당부서", markdown)
        self.assertIn("- 혁신팀 책임자: 홍길동", markdown)
        self.assertIn("- 혁신팀 담당자: 김철수", markdown)

    def test_reference_line_stays_in_body(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 온라인 2026. 3. 25.\n"
            "제목\n"
            "□ 첫 문단\n"
            "<참고 : 부연 설명>\n"
            "○ 세부 설명\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("> <참고 : 부연 설명>", markdown)
        self.assertIn("- 세부 설명", markdown)

    def test_reference_block_keeps_star_lines_as_blockquote(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 온라인 2026. 3. 25.\n"
            "제목\n"
            "□ 첫 문단\n"
            "< 참고 : 주요 연혁>\n"
            "- 첫 번째 연혁\n"
            "- 두 번째 연혁\n"
            "- 먼저, 다음 본문\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("> < 참고 : 주요 연혁>", markdown)
        self.assertIn("> - 첫 번째 연혁", markdown)
        self.assertIn("> - 두 번째 연혁", markdown)
        self.assertIn("\n\n  - 먼저, 다음 본문", markdown)

    def test_press_release_location_labels_and_star_notes_keep_expected_style(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 온라인 2026. 3. 25.\n"
            "제목\n"
            "□ 첫 문단 설명이다.\n"
            "<광주 : 사회적경제지원센터>\n"
            "먼저, 현장을 방문했다.\n"
            "* 광주 권역 사회연대경제 중간지원조직 설명\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("#### <광주 : 사회적경제지원센터>", markdown)
        self.assertIn("> 광주 권역 사회연대경제 중간지원조직 설명", markdown)

    def test_press_release_inline_triangle_bullets_stay_in_normal_bullet(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 온라인 2026. 3. 25.\n"
            "제목\n"
            "□ 설명 문장이다.\n"
            "○ 화재 장소와 불길 확산 여부에 따른 ▴대피, ▴구조요청, ▴대기, ▴대피 또는 구조요청을 숙지해야 한다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn(
            "- 화재 장소와 불길 확산 여부에 따른 ▴대피, ▴구조요청, ▴대기, ▴대피 또는 구조요청을 숙지해야 한다.",
            markdown,
        )

    def test_press_release_sentence_and_trailing_angle_label_are_split(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 온라인 2026. 3. 25.\n"
            "제목\n"
            "□ 본문 시작\n"
            "□ 이번 보고서에는 이러한 시설의 위험 요소 분석과 그 개선 방안을 담았다. <지하 복합형 자원순환시설에서의 화재·침수>\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("이번 보고서에는 이러한 시설의 위험 요소 분석과 그 개선 방안을 담았다.", markdown)
        self.assertIn("#### <지하 복합형 자원순환시설에서의 화재·침수>", markdown)
        self.assertIn(
            "이번 보고서에는 이러한 시설의 위험 요소 분석과 그 개선 방안을 담았다.\n\n#### <지하 복합형 자원순환시설에서의 화재·침수>",
            markdown,
        )

    def test_press_release_table_header_is_split_correctly(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점\n"
            "(온라인) 2026. 3. 25. 12:00\n"
            "|제목 줄|\n"
            "|---|\n"
            "- 부제 1\n"
            "- 부제 2\n"
            "- □ 본문 시작\n"
            "○ 세부 설명\n"
            "담당 부서: 혁신팀 책임자: 홍길동\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("# 제목 줄", markdown)
        self.assertIn("> 보도시점: (온라인) 2026. 3. 25. 12:00", markdown)
        self.assertIn("- 부제 1", markdown)
        self.assertIn("본문 시작", markdown)
        self.assertLess(markdown.index("> 행정안전부 보도자료"), markdown.index("- 부제 1"))
        self.assertLess(markdown.index("> 행정안전부 보도자료"), markdown.index("> 보도시점: (온라인) 2026. 3. 25. 12:00"))

    def test_press_release_without_square_bullets_starts_body_after_subtitle(self) -> None:
        raw = (
            "보도자료\n"
            "(온라인) 2026. 3. 23.(월) 12:00 (지 면) 2026. 3. 24.(화) 조간\n"
            "보도시점\n"
            "지역 거주 인재 공직 진출 확대 등 채용제도 개선\n"
            "- 지역 장기거주 가산 및 거주지 응시요건 강화, 신규 공무원 마약류 검사 도입 등 -\n"
            "행정안전부(장관 윤호중)는 인사혁신처와 함께 지역 출신 인재 등의 채용 기회 확대를 위한 제도 개선을 추진한다고 23일 밝혔다.\n"
            "◆ 지역 출신 인재 우대 강화\n"
            "담당 부서: 지방인사제도과 책임자: 과 장 이정석\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("# 지역 거주 인재 공직 진출 확대 등 채용제도 개선", markdown)
        self.assertIn(
            "행정안전부(장관 윤호중)는 인사혁신처와 함께 지역 출신 인재 등의 채용 기회 확대를 위한 제도 개선을 추진한다고 23일 밝혔다.",
            markdown,
        )
        self.assertNotIn(
            "# 지역 거주 인재 공직 진출 확대 등 채용제도 개선 행정안전부",
            markdown,
        )

    def test_press_release_education_plan_box_stays_blockquote(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점\n"
            "(온라인) 2026. 3. 23.(월) 12:00\n"
            "제목\n"
            "□ 본문\n"
            "< 2026년 자치인재원 지방의회 교육계획 > △ 지방의회 의원교육 : 지방의회 당선인 과정(6월), 찾아가는 초선의원 직무연수(6~8월),\n"
            "지방의회 아카데미(8월), 지방의회 맞춤형 직무연수(연중) 등\n"
            "△ 지방의회 직원교육 : 지방의회 직무공통과정(1ㆍ5ㆍ9월), 핵심직무 심화과정(1ㆍ3ㆍ6월)\n"
            "안준호 지방자치인재개발원장은 말했다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("> < 2026년 자치인재원 지방의회 교육계획 >", markdown)
        self.assertIn("> △ 지방의회 의원교육 : 지방의회 당선인 과정(6월), 찾아가는 초선의원 직무연수(6~8월), 지방의회 아카데미(8월), 지방의회 맞춤형 직무연수(연중) 등", markdown)
        self.assertIn("> △ 지방의회 직원교육 : 지방의회 직무공통과정(1ㆍ5ㆍ9월), 핵심직무 심화과정(1ㆍ3ㆍ6월)", markdown)

    def test_save_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "saved.md"
            save_markdown_file(path, "# saved\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "# saved\n")

    def test_json_extractor_keeps_caption_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {"type": "heading", "content": "제목"},
                    {"type": "caption", "content": "○ 마지막 인용문"},
                    {"type": "paragraph", "content": "담당 부서: 혁신팀"}
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("제목", extracted)
            self.assertIn("○ 마지막 인용문", extracted)
            self.assertIn("담당 부서: 혁신팀", extracted)

    def test_json_extractor_keeps_contact_table_rowspan_structure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {"column number": 1, "kids": [{"type": "paragraph", "content": "담당 부서"}]},
                            {"column number": 2, "kids": [{"type": "paragraph", "content": "행정안전부 혁신과"}]},
                            {"column number": 3, "kids": [{"type": "paragraph", "content": "책임자"}]},
                            {"column number": 4, "kids": [{"type": "paragraph", "content": "과 장 홍길동"}]}
                          ]
                        },
                        {
                          "cells": [
                            {"column number": 3, "kids": [{"type": "paragraph", "content": "담당자"}]},
                            {"column number": 4, "kids": [{"type": "paragraph", "content": "사무관 김철수"}]}
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("담당 부서: 행정안전부 혁신과 책임자: 과 장 홍길동", extracted)
            self.assertIn("담당 부서: 행정안전부 혁신과 담당자: 사무관 김철수", extracted)

    def test_json_extractor_renders_simple_table_as_markdown_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {"column number": 1, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "구분"}]},
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "현행"}]},
                            {"column number": 3, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "개선"}]}
                          ]
                        },
                        {
                          "cells": [
                            {"column number": 1, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "AI 가독성"}]},
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "개조식 문장"}]},
                            {"column number": 3, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "정확한 학습"}]}
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("| 구분 | 현행 | 개선 |", extracted)
            self.assertIn("| --- | --- | --- |", extracted)

    def test_json_extractor_renders_single_cell_table_as_blockquote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {
                              "column number": 1,
                              "row span": 1,
                              "column span": 1,
                              "kids": [
                                {"type": "paragraph", "content": "< 2026년 자치인재원 지방의회 교육계획 >"},
                                {"type": "paragraph", "content": "△ 지방의회 의원교육"}
                              ]
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("> < 2026년 자치인재원 지방의회 교육계획 >", extracted)
            self.assertIn("> △ 지방의회 의원교육", extracted)

    def test_json_extractor_preserves_heading_nodes_inside_single_cell_quote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {
                              "column number": 1,
                              "row span": 1,
                              "column span": 1,
                              "kids": [
                                {"type": "heading", "content": "높은 수익률의 투자 정보, 확인하고 투자하는 ㄱ씨"},
                                {"type": "paragraph", "content": "직장인 ㄱ씨는 최근 광고를 접했다."}
                              ]
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("> ## 높은 수익률의 투자 정보, 확인하고 투자하는 ㄱ씨", extracted)
            self.assertIn("> 직장인 ㄱ씨는 최근 광고를 접했다.", extracted)

    def test_json_extractor_preserves_angle_heading_nodes_inside_single_cell_quote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {
                              "column number": 1,
                              "row span": 1,
                              "column span": 1,
                              "kids": [
                                {"type": "heading", "content": "< 2025년도 데이터기반행정 추진 사례 >"},
                                {"type": "paragraph", "content": "(해양수산부) 어업용 면세유 부정 유통 감독을 위한 데이터 분석"}
                              ]
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("> #### < 2025년도 데이터기반행정 추진 사례 >", extracted)
            self.assertIn("> (해양수산부) 어업용 면세유 부정 유통 감독을 위한 데이터 분석", extracted)

    def test_json_extractor_preserves_nested_lists_inside_single_cell_quote(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {
                              "column number": 1,
                              "kids": [
                                {"type": "paragraph", "content": "(서울특별시) 전세사기 위험 분석 보고서 서비스"},
                                {
                                  "type": "list",
                                  "list items": [
                                    {
                                      "type": "list item",
                                      "content": "임대차계약 전에 주택 위험 요인을 확인 할수 있도록 서비스 제공",
                                      "kids": []
                                    },
                                    {
                                      "type": "list item",
                                      "content": "전세사기 가담 임대인 약 1,500명의 데이터 분석 후 정보 제공",
                                      "kids": [
                                        {
                                          "type": "list",
                                          "list items": [
                                            {
                                              "type": "list item",
                                              "content": "내집스캔을 통해 서비스 제공 중",
                                              "kids": [
                                                {
                                                  "type": "list",
                                                  "list items": [
                                                    {
                                                      "type": "list item",
                                                      "content": "임차인이 숨겨진 위험 징후를 인지하도록 지원",
                                                      "kids": []
                                                    }
                                                  ]
                                                }
                                              ]
                                            }
                                          ]
                                        }
                                      ]
                                    }
                                  ]
                                }
                              ]
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("> (서울특별시) 전세사기 위험 분석 보고서 서비스", extracted)
            self.assertIn("> - 임대차계약 전에 주택 위험 요인을 확인 할수 있도록 서비스 제공", extracted)
            self.assertIn("> - 전세사기 가담 임대인 약 1,500명의 데이터 분석 후 정보 제공", extracted)
            self.assertIn(">   - 내집스캔을 통해 서비스 제공 중", extracted)
            self.assertIn(">     - 임차인이 숨겨진 위험 징후를 인지하도록 지원", extracted)

    def test_json_extractor_rebuilds_single_column_service_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {"column number": 1, "kids": [{"type": "paragraph", "content": "서비스 주요 내용 신청 방법"}]}
                          ]
                        },
                        {
                          "cells": [
                            {
                              "column number": 1,
                              "kids": [
                                {"type": "paragraph", "content": "금융소비자 포털 (금융감독원)"},
                                {"type": "paragraph", "content": "금융상품 한눈에, 제도권 금융회사 조회"},
                                {"type": "paragraph", "content": "금융소비자 포털 파인 접속 후 이용"},
                                {"type": "paragraph", "content": "* 문의: 콜센터 1332"}
                              ]
                            }
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("|서비스|주요내용|신청방법|", extracted)
            self.assertIn("|:---:|:---:|:---:|", extracted)
            self.assertIn("|금융소비자 포털 (금융감독원)|금융상품 한눈에, 제도권 금융회사 조회|금융소비자 포털 파인 접속 후 이용 * 문의: 콜센터 1332|", extracted)

    def test_json_extractor_splits_inline_items_inside_table_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {"column number": 1, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "구분"}]},
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "현행"}]}
                          ]
                        },
                        {
                          "cells": [
                            {"column number": 1, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "자료 분석"}]},
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "§ 단편적 통계자료 활용 § 부처간 정보 활용 제한"}]}
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("• 단편적 통계자료 활용<br>• 부처간 정보 활용 제한", extracted)

    def test_json_extractor_renders_complex_table_as_markdown_table(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {"column number": 1, "row span": 2, "column span": 1, "kids": [{"type": "paragraph", "content": "구분"}]},
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "현행"}]}
                          ]
                        },
                        {
                          "cells": [
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "개선"}]}
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("| 구분 | 현행 |", extracted)
            self.assertIn("| --- | --- |", extracted)
            self.assertIn("| 구분 | 개선 |", extracted)

    def test_json_extractor_splits_inline_items_inside_markdown_table_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            json_path = Path(temp_dir) / "sample.json"
            json_path.write_text(
                """
                {
                  "kids": [
                    {
                      "type": "table",
                      "rows": [
                        {
                          "cells": [
                            {"column number": 1, "row span": 2, "column span": 1, "kids": [{"type": "paragraph", "content": "구분"}]},
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "§ 항목1 § 항목2"}]}
                          ]
                        },
                        {
                          "cells": [
                            {"column number": 2, "row span": 1, "column span": 1, "kids": [{"type": "paragraph", "content": "개선"}]}
                          ]
                        }
                      ]
                    }
                  ]
                }
                """,
                encoding="utf-8",
            )
            extracted = extract_text_from_json(json_path)
            self.assertIn("• 항목1<br>• 항목2", extracted)
            self.assertIn("| 구분 | • 항목1<br>• 항목2 |", extracted)
            self.assertNotIn("<table>", extracted)

    def test_generic_document_cleanup_removes_toc_and_images(self) -> None:
        raw = (
            "2025년 주요업무 추진계획\n\n"
            "2025. 1.\n\n"
            "![image 1](file.png)\n\n"
            "# 순 서\n"
            "- Ⅰ. 항목 ········ 1\n"
            "- Ⅱ. 항목 ········ 2\n"
            "### 기본 방향\n"
            "#### □ 국민안전 확보\n"
            "#### ㅇ 정책 설명\n"
            "￭ 세부 항목\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("# 2025년 주요업무 추진계획", markdown)
        self.assertIn("![image 1](file.png)", markdown)
        self.assertNotIn("순 서", markdown)
        self.assertIn("## 국민안전 확보", markdown)
        self.assertIn("- 정책 설명", markdown)

    def test_press_release_appendix_after_contacts_is_separated(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점\n"
            "(온라인) 2026. 3. 25. 12:00\n"
            "제목\n"
            "□ 본문\n"
            "담당 부서: 혁신팀 책임자: 홍길동\n"
            "붙임 세미나 계획\n"
            "○ 일시: 2026. 3. 26.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("## 담당부서", markdown)
        self.assertNotIn("## 붙임", markdown)
        self.assertNotIn("붙임 세미나 계획", markdown)

    def test_press_release_metadata_and_note_style(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인,지면) 2026. 3. 24. 국무회의 종료 시\n"
            "제목\n"
            "- 부제\n"
            "□ 본문 문장이다.\n"
            "※ (주요 사항) 예시 설명\n"
            "담당 부서: 혁신팀 책임자: 홍길동\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("> 행정안전부 보도자료", markdown)
        self.assertIn("> 보도시점: (온라인,지면) 2026. 3. 24. 국무회의 종료 시", markdown)
        self.assertIn("> (주요 사항) 예시 설명", markdown)
        self.assertIn("- 혁신팀 책임자: 홍길동", markdown)
        self.assertLess(markdown.index("# 제목"), markdown.index("- 부제"))
        self.assertLess(markdown.index("> 행정안전부 보도자료"), markdown.index("- 부제"))
        self.assertIn(
            "> 보도시점: (온라인,지면) 2026. 3. 24. 국무회의 종료 시\n\n- 부제\n\n---\n\n본문 문장이다.",
            markdown,
        )

    def test_press_release_without_subtitle_keeps_rule_before_body(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 본문 문장이다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn(
            "> 보도시점: (온라인) 2026. 3. 24.\n\n---\n\n본문 문장이다.",
            markdown,
        )

    def test_press_release_note_continuations_follow_parent_list_depth(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 본문\n"
            "○ 상위 항목\n"
            "※ 유의사항 첫 줄\n"
            "추가 설명\n"
            "○ 다음 항목\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("- 상위 항목", markdown)
        self.assertIn("  > 유의사항 첫 줄\n  > 추가 설명", markdown)
        self.assertIn("- 다음 항목", markdown)

    def test_press_release_intro_story_headings_are_rendered_as_quote_block(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "- 부제\n"
            "# 높은 수익률의 투자 정보, 확인하고 투자하는 ㄱ씨\n"
            "직장인 ㄱ씨는 최근 광고를 접했다.\n"
            "# 흩어진 금융자산 파악하고 투자 계획 세우는 ㄴ씨\n"
            "자영업자 ㄴ씨는 여러 금융기관 정보를 확인했다.\n"
            "□ 행정안전부는 서비스를 선정했다고 밝혔다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("> ## 높은 수익률의 투자 정보, 확인하고 투자하는 ㄱ씨", markdown)
        self.assertIn("> 직장인 ㄱ씨는 최근 광고를 접했다.", markdown)
        self.assertIn("> ## 흩어진 금융자산 파악하고 투자 계획 세우는 ㄴ씨", markdown)
        self.assertIn("> 자영업자 ㄴ씨는 여러 금융기관 정보를 확인했다.", markdown)
        self.assertIn("행정안전부는 서비스를 선정했다고 밝혔다.", markdown)

    def test_press_release_data_report_lead_lines_become_quote_instead_of_bullets(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "- 실태점검 결과 발표\n"
            "- 우수 사례 확산 및 미흡 기관 지원\n"
            "#### < 2025년도 데이터기반행정 추진 사례 >\n"
            "(해양수산부) 어업용 면세유 부정 유통 감독을 위한 데이터 분석\n"
            "§ 면세유 거래 데이터 등을 활용하여 이상 패턴 분석\n"
            "§ 이상 탐지 모델 구축\n"
            "□ 행정안전부는 결과를 발표했다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("보도시점: (온라인) 2026. 3. 24.", markdown)
        self.assertIn("> 실태점검 결과 발표", markdown)
        self.assertIn("> 우수 사례 확산 및 미흡 기관 지원", markdown)
        self.assertNotIn("- 실태점검 결과 발표", markdown)
        self.assertIn("#### < 2025년도 데이터기반행정 추진 사례 >", markdown)
        self.assertIn("> (해양수산부) 어업용 면세유 부정 유통 감독을 위한 데이터 분석", markdown)
        self.assertIn("> - 면세유 거래 데이터 등을 활용하여 이상 패턴 분석", markdown)
        self.assertIn("> - 이상 탐지 모델 구축", markdown)

    def test_press_release_case_study_mode_splits_nested_note_and_continuation(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24. 실태점검\n"
            "제목\n"
            "- 실태점검 결과 발표\n"
            "#### < 2025년도 데이터기반행정 추진 사례 >\n"
            "(서울특별시) 전세사기 위험 분석 보고서 서비스\n"
            "§ 임대차계약 전에 주택 위험 요인을 확인할 수 있도록 서비스 제공\n"
            "※ 내집스캔을 통해 서비스 제공 중 § 임차인이 사전에 위험 징후를 인지하도록 지원\n"
            "(한국도로공사) 눈으로 보이지 않던 교통사고의 원인을 밝히는 디지털 도로안전진단\n"
            "§ 차량형 라이다 장비로 사고 원인 진단\n"
            "빗길 교통사고 취약 구간 분석\n"
            "△ 전국 도로로 확산 적용하기 위해 시범사업 추진 예정\n"
            "□ 본문 시작\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("행정안전부 보도자료", markdown)
        self.assertNotIn("> 행정안전부 보도자료", markdown)
        self.assertIn("> 실태점검 결과 발표", markdown)
        self.assertIn("> (서울특별시) 전세사기 위험 분석 보고서 서비스", markdown)
        self.assertIn("> - 임대차계약 전에 주택 위험 요인을 확인할 수 있도록 서비스 제공", markdown)
        self.assertIn(">   - 내집스캔을 통해 서비스 제공 중 § 임차인이 사전에 위험 징후를 인지하도록 지원", markdown)
        self.assertIn("> - 차량형 라이다 장비로 사고 원인 진단", markdown)
        self.assertIn("> - 빗길 교통사고 취약 구간 분석", markdown)
        self.assertIn(">    - 전국 도로로 확산 적용하기 위해 시범사업 추진 예정", markdown)

    def test_press_release_top_level_body_paragraphs_are_separated(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 첫 번째 상위 문단은 보도자료의 설명형 문장으로 충분히 길어서 제목이 아니라 일반 문단으로 처리되어야 한다.\n"
            "□ 두 번째 상위 문단도 설명형 문장으로 길게 이어져서 단락은 분리되지만 제목으로 승격되면 안 된다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn(
            "첫 번째 상위 문단은 보도자료의 설명형 문장으로 충분히 길어서 제목이 아니라 일반 문단으로 처리되어야 한다.\n\n두 번째 상위 문단도 설명형 문장으로 길게 이어져서 단락은 분리되지만 제목으로 승격되면 안 된다.",
            markdown,
        )

    def test_appendix_fields_are_readable(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점\n"
            "(온라인) 2026. 3. 25. 12:00\n"
            "제목\n"
            "□ 본문\n"
            "붙임 세미나 계획\n"
            "□ 개요\n"
            "○ 일 시: 2026. 3. 26.(목) 14:00\n"
            "○ 장 소: 부산항국제전시컨벤션센터\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertNotIn("개요", markdown)
        self.assertNotIn("부산항국제전시컨벤션센터", markdown)

    def test_press_release_support_team_line_is_visually_separated(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 앞 문장은 설명형 문장으로 충분히 길어서 제목이 아니라 일반 문단으로 처리되어야 한다.\n"
            "* 민‧관합동 현장지원단 구성: 광역 + 기초 지방정부\n"
            "○ 다음 설명이다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn(
            "앞 문장은 설명형 문장으로 충분히 길어서 제목이 아니라 일반 문단으로 처리되어야 한다.\n\n  >민‧관합동 현장지원단 구성: 광역 + 기초 지방정부\n\n- 다음 설명이다.",
            markdown,
        )

    def test_bullet_continuation_parenthetical_line_is_joined(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 본문\n"
            "○ 공문서 작성 표준 번호체계(Ⅰ., 1., 가., 1), 가), (1),\n"
            "(가), ①, ㉮)를 준수해 체계성을 잡는다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn(
            "- 공문서 작성 표준 번호체계(Ⅰ., 1., 가., 1), 가), (1), (가), ①, ㉮)를 준수해 체계성을 잡는다.",
            markdown,
        )

    def test_contact_chunks_drop_trailing_reference_noise(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 본문\n"
            "담당 부서: 혁신행정담당관 책임자: 과장 홍길동 담당자: 사무관 김철수 "
            "<참고> AI 가이드라인 적용 전/후 예시 □ 적용 전\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("- 혁신행정담당관 책임자: 과장 홍길동", markdown)
        self.assertIn("- 혁신행정담당관 담당자: 사무관 김철수", markdown)
        self.assertNotIn("<참고>", markdown)
        self.assertNotIn("적용 전", markdown)

    def test_postprocessor_preserves_markdown_table_lines(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 본문\n"
            "| 구분 | 현행 | 개선 |\n"
            "| --- | --- | --- |\n"
            "| AI 가독성 | 개조식 문장 | 정확한 학습 |\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("| 구분 | 현행 | 개선 |", markdown)
        self.assertIn("| --- | --- | --- |", markdown)
        self.assertIn("| AI 가독성 | 개조식 문장 | 정확한 학습 |", markdown)

    def test_pymupdf_table_cells_replace_section_marker_with_plain_bullet(self) -> None:
        pdf = Path(
            "/home/wavel/GovPress_PDF_MD/re_test/press/260325 (조간) 보고서 꾸미는 시간에 민생 현장으로 행정안전부 AI친화 행정문서 혁신 시범 실시(혁신행정담당관).pdf"
        )
        markdown = convert_pdf_to_markdown(pdf, backend="pymupdf")
        self.assertIn("AI 가독성 | • 주어·서술어가 생략된 개조식 문장 이나 복잡한 표 등으로 학습에 제한 | • 정부 공문서를 정확하게 학습", markdown)
        self.assertNotIn("§ 정부 공문서를 정확하게 학습", markdown)

    def test_postprocessor_drops_dotted_table_separator_lines_like_solid_ones(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 본문\n"
            "| 구분 | 현행 | 개선 |\n"
            "| ··· | ··· | ··· |\n"
            "| AI 가독성 | 개조식 문장 | 정확한 학습 |\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("| 구분 | 현행 | 개선 |", markdown)
        self.assertNotIn("| ··· | ··· | ··· |", markdown)
        self.assertIn("| AI 가독성 | 개조식 문장 | 정확한 학습 |", markdown)

    def test_triangle_bullets_after_dash_line_are_indented(self) -> None:
        raw = (
            "보도자료\n"
            "보도시점 (온라인) 2026. 3. 24.\n"
            "제목\n"
            "□ 본문\n"
            "○ 본선에 오른 2개 과제는\n"
            "△첫 번째 과제,\n"
            "△두 번째 과제이다.\n"
        )
        markdown = postprocess_markdown(raw)
        self.assertIn("- 본선에 오른 2개 과제는", markdown)
        self.assertIn("  △첫 번째 과제,", markdown)
        self.assertIn("  △두 번째 과제이다.", markdown)

    def test_fixture_press_releases_keep_core_sections(self) -> None:
        fixture_expectations = {
            "260326 (18시) 전남·광주 통합 지역소멸 극복과 대한민국 대도약의 마중물 만들 것(자치행정과).pdf": [
                "# 전남·광주 통합, 지역소멸 극복과 대한민국 대도약의 마중물 만들 것",
                "> 보도시점",
                "## 담당부서",
            ],
            "260326 (조간) 부울경 복합재난 대비 역량 강화를 위한 한·일 공동세미나 개최(국립재난안전연구원 지진방재센터).pdf": [
                "# 부울경 복합재난 대비 역량 강화를 위한 한·일 공동세미나 개최",
                "## 담당부서",
            ],
            "260325 (조간) 공공부문에서 인공지능(AI) 어떻게 써야해 「AI 정부 서비스 사례집」에 우수사례 총집합(공공인공지능혁신과).pdf": [
                "# 공공부문에서 인공지능(AI) 어떻게 써야해? 「AI 정부 서비스 사례집」에 우수사례 총집합",
                "> 보도시점",
                "## 담당부서",
            ],
        }
        for file_name, required_snippets in fixture_expectations.items():
            with self.subTest(file_name=file_name):
                markdown = convert_pdf_to_markdown(FIXTURE_DIR / file_name, timeout_seconds=300)
                for snippet in required_snippets:
                    self.assertIn(snippet, markdown)

    def test_golden_press_release_matches_expected_structure(self) -> None:
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE, timeout_seconds=300)
        for snippet in (
            "# 대전 대덕구 공장 화재 중앙재난안전대책본부 6차 회의 개최",
            "- 피해 유가족과 부상자·근로자에 대한 심리·치료·생활안정 지원 지속",
            "정부는 유가족, 피해자 및 피해자 보호자 분들에 대한 지원에 소홀함이 없도록 최선을 다하고 있다.",
            "김광용 재난안전관리본부장은",
            "## 담당부서",
        ):
            self.assertIn(snippet, actual)

    def test_second_golden_press_release_matches_expected_markdown(self) -> None:
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_2, timeout_seconds=300)
        self._assert_matches_golden(actual, GOLDEN_PRESS_RELEASE_MD_2)

    def test_third_golden_press_release_matches_expected_markdown(self) -> None:
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_3, timeout_seconds=300)
        self._assert_matches_golden(actual, GOLDEN_PRESS_RELEASE_MD_3)

    def test_fourth_golden_press_release_matches_expected_markdown(self) -> None:
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_4, timeout_seconds=300)
        self._assert_matches_golden(actual, GOLDEN_PRESS_RELEASE_MD_4)

    def test_fifth_golden_press_release_matches_expected_markdown(self) -> None:
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_5, timeout_seconds=300)
        self._assert_matches_golden(actual, GOLDEN_PRESS_RELEASE_MD_5)

    def test_sixth_golden_press_release_matches_expected_markdown(self) -> None:
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_6, timeout_seconds=300)
        self._assert_matches_golden(actual, GOLDEN_PRESS_RELEASE_MD_6)

    def test_seventh_golden_press_release_matches_expected_markdown(self) -> None:
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_7, timeout_seconds=300)
        self._assert_matches_golden(actual, GOLDEN_PRESS_RELEASE_MD_7)


if __name__ == "__main__":
    unittest.main()
