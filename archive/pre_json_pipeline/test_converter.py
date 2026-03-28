from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.converter import (
    DependencyStatus,
    _parse_java_major_version,
    _resolve_opendataloader_command,
    convert_pdf_to_markdown,
)
from src.markdown_postprocessor import postprocess_markdown
from src.utils import save_markdown_file


FIXTURE_DIR = Path("/home/wavel/pdf_to_md_app/tests/fixtures/press_release")
GOLDEN_PRESS_RELEASE = FIXTURE_DIR / "260325 (14시) 대전 대덕구 공장 화재 중앙재난안전대책본부 6차 회의 개최(국토산업재난대응과).pdf"
GOLDEN_PRESS_RELEASE_MD = FIXTURE_DIR / "260325 (14시) 대전 대덕구 공장 화재 중앙재난안전대책본부 6차 회의 개최(국토산업재난대응과).md"
GOLDEN_PRESS_RELEASE_2 = FIXTURE_DIR / "260324 (국무회의 종료시) 78년 만의 수사‧기소 분리 중대범죄수사청 출범 본격 착수(중대범죄수사청설립지원단).pdf"
GOLDEN_PRESS_RELEASE_MD_2 = Path("/home/wavel/pdf_to_md_app/tests/converted_md/press_release/260324 (국무회의 종료시) 78년 만의 수사‧기소 분리 중대범죄수사청 출범 본격 착수(중대범죄수사청설립지원단).md")
GOLDEN_PRESS_RELEASE_3 = FIXTURE_DIR / "260324 (국무회의 종료시) 주민과 함께 만드는 풍요로운 마을 햇빛소득마을 전국 확산 본격 추진(햇빛소득마을추진단).pdf"
GOLDEN_PRESS_RELEASE_MD_3 = Path("/home/wavel/pdf_to_md_app/tests/converted_md/press_release/260324 (국무회의 종료시) 주민과 함께 만드는 풍요로운 마을 햇빛소득마을 전국 확산 본격 추진(햇빛소득마을추진단).md")
GOLDEN_PRESS_RELEASE_4 = FIXTURE_DIR / "260326 (조간) 부울경 복합재난 대비 역량 강화를 위한 한·일 공동세미나 개최(국립재난안전연구원 지진방재센터).pdf"
GOLDEN_PRESS_RELEASE_MD_4 = Path("/home/wavel/pdf_to_md_app/tests/converted_md/press_release/260326 (조간) 부울경 복합재난 대비 역량 강화를 위한 한·일 공동세미나 개최(국립재난안전연구원 지진방재센터).md")
GOLDEN_PRESS_RELEASE_5 = FIXTURE_DIR / "260326 (17시) 살피고 대피하라! 고층건축물 화재 대비 올해 첫 레디 코리아 훈련(재난대응훈련과).pdf"
GOLDEN_PRESS_RELEASE_MD_5 = Path("/home/wavel/pdf_to_md_app/tests/converted_md/press_release/260326 (17시) 살피고 대피하라! 고층건축물 화재 대비 올해 첫 레디 코리아 훈련(재난대응훈련과).md")
GOLDEN_PRESS_RELEASE_6 = FIXTURE_DIR / "260326 (15시) 과학수사 발전 격려하고 서민금융 현장 살펴(자치행정과).pdf"
GOLDEN_PRESS_RELEASE_MD_6 = Path("/home/wavel/pdf_to_md_app/tests/converted_md/press_release/260326 (15시) 과학수사 발전 격려하고 서민금융 현장 살펴(자치행정과).md")
GOLDEN_PRESS_RELEASE_7 = FIXTURE_DIR / "260325 (조간) 새로운 시설물 속 숨은 위험 찾는다 잠재 재난위험 분석 보고서 발간(재난대응총괄과).pdf"
GOLDEN_PRESS_RELEASE_MD_7 = Path("/home/wavel/pdf_to_md_app/tests/converted_md/press_release/260325 (조간) 새로운 시설물 속 숨은 위험 찾는다 잠재 재난위험 분석 보고서 발간(재난대응총괄과).md")


class ConverterTests(unittest.TestCase):
    @staticmethod
    def _normalize_markdown_for_assertion(text: str) -> str:
        return "\n".join(line.rstrip() for line in text.splitlines() if line.strip()).strip()

    def test_invalid_path_raises(self) -> None:
        with self.assertRaises(FileNotFoundError):
            convert_pdf_to_markdown("/tmp/does-not-exist.pdf")

    def test_non_pdf_rejected(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".txt") as handle:
            with self.assertRaises(ValueError):
                convert_pdf_to_markdown(handle.name)

    @patch("src.converter.check_runtime_dependencies")
    @patch("src.converter.subprocess.run")
    def test_conversion_reads_generated_markdown(
        self, mock_run: Mock, mock_deps: Mock
    ) -> None:
        mock_deps.return_value = DependencyStatus(True, True, "ok", "ok")
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            def fake_run(*args, **kwargs):
                output_dir = Path(args[0][3])
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "sample.md").write_text(
                    "보도자료\n보도시점 온라인 2026. 3. 25.\n제목 줄\n□ 본문\n담당 부서: 홍보팀\n",
                    encoding="utf-8",
                )
                return Mock(returncode=0, stdout="", stderr="")

            mock_run.side_effect = fake_run
            markdown = convert_pdf_to_markdown(pdf_path)
            self.assertIn("# 제목 줄", markdown)
            self.assertIn("본문", markdown)

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

    def test_java_version_parser(self) -> None:
        self.assertEqual(_parse_java_major_version('openjdk version "17.0.10" 2024-01-16'), 17)
        self.assertEqual(_parse_java_major_version('java version "1.8.0_401"'), 8)

    @patch("src.converter.shutil_lib.which")
    def test_resolve_opendataloader_command_prefers_path(self, mock_which: Mock) -> None:
        mock_which.return_value = "/tmp/opendataloader-pdf"
        self.assertEqual(_resolve_opendataloader_command(), "/tmp/opendataloader-pdf")

    def test_save_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "saved.md"
            save_markdown_file(path, "# saved\n")
            self.assertEqual(path.read_text(encoding="utf-8"), "# saved\n")

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
        self.assertNotIn("![image", markdown)
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
        self.assertIn("  - (주요 사항) 예시 설명", markdown)
        self.assertIn("- 혁신팀 책임자: 홍길동", markdown)

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
            "앞 문장은 설명형 문장으로 충분히 길어서 제목이 아니라 일반 문단으로 처리되어야 한다.\n\n  - 민‧관합동 현장지원단 구성: 광역 + 기초 지방정부\n\n- 다음 설명이다.",
            markdown,
        )

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
        expected = GOLDEN_PRESS_RELEASE_MD_2.read_text(encoding="utf-8")
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_2, timeout_seconds=300)
        self.assertEqual(
            self._normalize_markdown_for_assertion(actual),
            self._normalize_markdown_for_assertion(expected),
        )

    def test_third_golden_press_release_matches_expected_markdown(self) -> None:
        expected = GOLDEN_PRESS_RELEASE_MD_3.read_text(encoding="utf-8")
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_3, timeout_seconds=300)
        self.assertEqual(
            self._normalize_markdown_for_assertion(actual),
            self._normalize_markdown_for_assertion(expected),
        )

    def test_fourth_golden_press_release_matches_expected_markdown(self) -> None:
        expected = GOLDEN_PRESS_RELEASE_MD_4.read_text(encoding="utf-8")
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_4, timeout_seconds=300)
        self.assertEqual(
            self._normalize_markdown_for_assertion(actual),
            self._normalize_markdown_for_assertion(expected),
        )

    def test_fifth_golden_press_release_matches_expected_markdown(self) -> None:
        expected = GOLDEN_PRESS_RELEASE_MD_5.read_text(encoding="utf-8")
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_5, timeout_seconds=300)
        self.assertEqual(
            self._normalize_markdown_for_assertion(actual),
            self._normalize_markdown_for_assertion(expected),
        )

    def test_sixth_golden_press_release_matches_expected_markdown(self) -> None:
        expected = GOLDEN_PRESS_RELEASE_MD_6.read_text(encoding="utf-8")
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_6, timeout_seconds=300)
        self.assertEqual(
            self._normalize_markdown_for_assertion(actual),
            self._normalize_markdown_for_assertion(expected),
        )

    def test_seventh_golden_press_release_matches_expected_markdown(self) -> None:
        expected = GOLDEN_PRESS_RELEASE_MD_7.read_text(encoding="utf-8")
        actual = convert_pdf_to_markdown(GOLDEN_PRESS_RELEASE_7, timeout_seconds=300)
        self.assertEqual(
            self._normalize_markdown_for_assertion(actual),
            self._normalize_markdown_for_assertion(expected),
        )


if __name__ == "__main__":
    unittest.main()
