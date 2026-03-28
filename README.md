# GovPress_PDF_MD

정부 보도자료 PDF를 Markdown으로 변환하고 편집할 수 있는 Windows용 데스크톱 앱입니다.

현재 앱은 `pywebview` 기반 UI와 로컬 변환 파이프라인을 사용합니다. 일반 PDF 변환보다 행정기관 보도자료 형식 복원과 후처리 품질을 우선합니다.

## 빠른 시작

### 요구사항

- Windows 10/11
- Python 3.10+
- Java 11+
- `opendataloader-pdf`

### 설치

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -U opendataloader-pdf
```

### 실행

```bash
python app.py
```

## 주요 기능

- PDF 드래그 앤 드롭 입력
- JSON 우선 기반 보도자료 후처리
- Markdown 편집
- HTML 미리보기
- Windows용 경량 `pywebview` UI
- `.md` 다른 이름으로 저장

## 저장소 구조

```text
GovPress_PDF_MD/
├─ app.py
├─ src/
├─ ui/
├─ assets/
├─ tests/
├─ docs/
│  ├─ conversion-rules.md
│  ├─ development.md
│  ├─ packaging.md
│  ├─ troubleshooting.md
│  └─ archive/
├─ packaging/
│  ├─ build_windows.bat
│  ├─ build_windows_nuitka.bat
│  ├─ pyinstaller/
│  └─ inno/
└─ archive/
```

## 문서

- 개발 및 실행: [docs/development.md](/home/wavel/GovPress_PDF_MD/docs/development.md)
- 빌드 및 배포: [docs/packaging.md](/home/wavel/GovPress_PDF_MD/docs/packaging.md)
- 변환 규칙: [docs/conversion-rules.md](/home/wavel/GovPress_PDF_MD/docs/conversion-rules.md)
- 문제 해결: [docs/troubleshooting.md](/home/wavel/GovPress_PDF_MD/docs/troubleshooting.md)

## 테스트

```bash
python -m unittest discover -s tests
```

고정 샘플은 `tests/fixtures/` 또는 테스트 파일 내부 fixture를 기준으로 관리하고, 수동 검증용 샘플은 `tests/manual_samples/` 아래에서 관리합니다.
