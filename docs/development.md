# Development

## 실행 환경

- Windows 10/11 권장
- Python 3.10+
- Java 11+ 별도 설치
- `pywebview` 기반 데스크톱 UI

## 사전 요구사항 확인

### Python

```bash
python --version
```

### Java 11+

```bash
java -version
```

### opendataloader-pdf

```bash
pip install -U opendataloader-pdf
opendataloader-pdf --help
```

## 로컬 설치

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
pip install -U opendataloader-pdf
```

## 로컬 실행

```bash
python app.py
```

## 구성 개요

- `app.py`: 앱 진입점
- `src/webview_app.py`: pywebview 창 실행
- `src/webview_api.py`: 프런트엔드와 브리지되는 API
- `ui/`: 웹 UI 자산
- `src/`: 변환, 후처리, 상태 관리

## 테스트

```bash
python -m unittest discover -s tests
```

수동 검증용 대용량 샘플은 `tests/manual_samples/`에 두고 자동 테스트 기준 데이터로 삼지 않습니다.
