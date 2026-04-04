# Troubleshooting

## `java`를 찾지 못하는 경우

- Java 11 이상 설치 여부를 확인합니다.
- 환경 변수 `PATH`에 Java 실행 파일 경로가 포함되어 있는지 확인합니다.

## `opendataloader-pdf`를 찾지 못하는 경우

- `pip install -U opendataloader-pdf`를 다시 실행합니다.
- 가상환경을 사용 중이면 동일한 가상환경에서 앱을 실행합니다.

## 빌드가 실패하는 경우

- `packaging\build_windows.bat`를 실행한 쉘에서 Python 버전이 3.10 이상인지 확인합니다.
- Inno Setup을 쓰는 경우 `ISCC`가 PATH에 있는지 확인합니다.

## 변환 결과가 비어 있는 경우

- PDF가 스캔본이거나 암호화되어 있는지 확인합니다.
- `opendataloader-pdf` 출력 디렉터리에 `.json` 또는 `.md`가 생성되는지 확인합니다.

## HWPX 결과가 깨지는 경우

- 같은 문서의 `.pdf`, `.hwpx`, 현재 결과를 함께 비교합니다.
- HWPX는 같은 내용을 `병합 문단`과 `분리 문단`으로 동시에 가지는 경우가 있어, 앞쪽 병합본이 남는지 확인합니다.
- `참고` 부록, 표, 담당부서 뒤 문단이 누락되면 `src/hwpx_postprocessor.py`, `src/markdown_postprocessor.py`, `src/parser_rules.py`를 함께 확인합니다.
- 재현 가능한 사례는 `tests/problem/`에 원본과 정답 `.md`를 추가해 규칙 개선 기준으로 사용합니다.

## 문제 파일 기반으로 개선할 때

- `pdf -> md`를 자동 정답으로 두지 않습니다.
- PDF/HWPX 원문을 함께 보고 사람이 더 원문에 가까운 Markdown을 정답으로 정합니다.
- 정답은 `tests/problem/<원본파일명>.md`로 저장합니다.
