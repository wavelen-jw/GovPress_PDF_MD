# GovPress_PDF_MD

정부 보도자료 PDF 파일을 Markdown으로 변환하고 편집하는 Windows용 데스크톱 프로젝트입니다.

Windows 환경에서 PDF를 드래그 앤 드롭으로 받아 `opendataloader-pdf`로 로컬 변환하고, 결과를 바로 편집하고 저장할 수 있게 구성했습니다. 일반 PDF 변환기보다는 행정기관 보도자료 템플릿에 맞춘 후처리 품질을 우선합니다.

## 주요 기능

- PDF 드래그 앤 드롭 입력
- `opendataloader-pdf` CLI 기반 로컬 변환
- JSON 우선 기반 보도자료 템플릿 후처리
- Markdown 소스 편집
- HTML 렌더링 미리보기
- 분할 보기, 소스 모드, 미리보기 모드
- `.md` 다른 이름으로 저장
- Java 및 `opendataloader-pdf` 미설치 안내

## 실행 환경

- Windows 10/11 권장
- Python 3.10+
- Java 11+
- 제한된 인터넷 환경에서도 실행 가능

## 사전 요구사항

### Python

```bash
python --version
```

### Java 11+

```bash
java -version
```

Java가 없다면 사내 표준 배포 경로 또는 공식 배포본으로 Java 11 이상을 먼저 설치합니다.

### opendataloader-pdf

```bash
pip install -U opendataloader-pdf
```

설치 후 아래 명령으로 확인합니다.

```bash
opendataloader-pdf --help
```

## 설치 방법

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -U opendataloader-pdf
```

## 실행 방법

```bash
python app.py
```

앱 실행 후 PDF를 창에 드롭하거나 `PDF 열기` 버튼으로 선택합니다.

## 패키징 방법

PyInstaller 대응을 고려한 구조입니다. 예시는 아래와 같습니다.

```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name pdf-to-md app.py
```

CSS 자산은 번들 실행도 고려해 런타임 경로 처리돼 있습니다. PyInstaller one-file 빌드 시에는 데이터 파일 포함 옵션을 함께 사용합니다.

```bash
pyinstaller --noconfirm --windowed --name pdf-to-md --add-data "assets/styles/preview.css;assets/styles" app.py
```

## 폴더 구조

```text
GovPress_PDF_MD/
├─ app.py
├─ requirements.txt
├─ README.md
├─ CONVERSION_RULES.md
├─ src/
│  ├─ __init__.py
│  ├─ converter.py
│  ├─ document_template.py
│  ├─ editor_widget.py
│  ├─ json_extractor.py
│  ├─ main_window.py
│  ├─ markdown_postprocessor.py
│  ├─ parser_rules.py
│  ├─ preview_widget.py
│  ├─ state.py
│  ├─ utils.py
│  └─ workers.py
├─ assets/
│  └─ styles/
│     └─ preview.css
└─ tests/
   ├─ test_converter.py
   └─ test_state.py
```

## 변환 및 후처리 방식

1. 사용자가 PDF를 드롭하거나 선택합니다.
2. 앱이 `opendataloader-pdf <pdf> -o <temp_dir> -f markdown,json` 형태로 로컬 CLI를 호출합니다.
3. 출력 디렉터리에서 `.json`을 우선 읽고, 없을 때만 `.md`를 사용합니다.
4. 추출 결과를 보도자료 템플릿 규칙으로 후처리합니다.
5. 편집기와 미리보기에 반영합니다.

현재 후처리 규칙은 아래 원칙으로 정리되어 있습니다.

- `보도자료`, `보도시점`, 제목, 부제, 본문, 담당부서를 구조적으로 분리합니다.
- 제목은 하나의 `#`로 병합합니다.
- `보도시점`은 blockquote 메타데이터로 출력합니다.
- 제목 아래 `-` 요약문은 bullet로 유지합니다.
- `□`는 항상 일반 문단으로 처리합니다.
- `□`가 없는 일반형 보도자료는 제목/부제 뒤 첫 서술문부터 본문으로 처리합니다.
- `○`, `ㅇ`는 기본 bullet로 처리합니다.
- `△` 하위 항목은 앞 bullet의 하위 목록으로 유지합니다.
- `<...>` 형식 라벨은 `#### <...>` 소제목으로 처리합니다.
- `<참고 : ...>`와 참고/연혁 블록은 blockquote로 유지합니다.
- 비연락처 `1행 1열` 표는 글상자형 안내 블록으로 보고 quote 블록으로 출력합니다.
- 단순 표는 Markdown table, 복잡한 표는 HTML table로 처리합니다.
- 연락처 표는 부서, 책임자, 담당자를 연결해 `## 담당부서` 아래 bullet 목록으로 정리합니다.
- 페이지 번호, 이미지 노이즈, 목차 잔재는 제거합니다.
- `붙임`, `붙 임`, `별첨`은 최종 `.md`에 포함하지 않습니다.

자세한 규칙은 [CONVERSION_RULES.md](/home/wavel/pdf_to_md_app/CONVERSION_RULES.md)를 참고합니다.

## 테스트

```bash
python -m unittest discover -s tests
```

## 알려진 제한사항

- `opendataloader-pdf`의 출력 형식이 크게 바뀌면 JSON 파서와 후처리 규칙도 함께 조정해야 할 수 있습니다.
- 표 복원은 단순 표 중심으로 안정화되어 있으며, 구조가 복잡하면 HTML table fallback으로 남을 수 있습니다.
- 스캔 PDF와 OCR 품질은 이번 버전의 핵심 범위가 아닙니다.
- 다중 PDF 드롭 시 첫 번째 PDF만 편집기로 열고 나머지는 무시합니다.
- 형식 차이가 큰 보도자료는 기존 공통 규칙에 바로 섞기보다 별도 템플릿으로 다루는 편이 안전합니다.

## 문제 해결 가이드

### `java`를 찾지 못하는 경우

- Java 11 이상 설치 여부를 확인합니다.
- 환경 변수 `PATH`에 Java 실행 파일 경로가 포함되어 있는지 확인합니다.

### `opendataloader-pdf`를 찾지 못하는 경우

- `pip install -U opendataloader-pdf`를 다시 실행합니다.
- 가상환경을 사용 중이면 동일한 가상환경에서 앱을 실행합니다.

### 변환은 끝났는데 Markdown이 비어 있는 경우

- PDF가 스캔본이거나 암호화되어 있는지 확인합니다.
- `opendataloader-pdf` 버전 차이로 출력 형식이 바뀌었을 수 있으므로 출력 디렉터리의 `.json` 또는 `.md` 생성 여부를 확인합니다.

### 저장 실패

- 대상 폴더에 쓰기 권한이 있는지 확인합니다.
- 이미 열려 있는 파일인지 확인합니다.
