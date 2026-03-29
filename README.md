# GovPress_PDF_MD

정부 보도자료 PDF를 Markdown으로 변환하고 편집할 수 있는 웹서비스입니다.
현재 `mobile_app` 브랜치에는 Cloudflare Tunnel로 공개되는 FastAPI 백엔드와 Expo Web 기반 반응형 클라이언트가 포함되어 있습니다.

현재 서비스는 데스크톱에서는 편집기와 미리보기를 병렬로 보여주고, 모바일/태블릿에서는 리더 중심 UI로 동작합니다. 일반 PDF 변환보다 행정기관 보도자료 형식 복원과 후처리 품질을 우선합니다.

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

### 웹 백엔드 실행

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -U opendataloader-pdf
.venv/bin/python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8011
```

워커는 별도 프로세스로 실행합니다.

```bash
.venv/bin/python -m server.run_worker --storage-root ./storage --poll-interval 1.0
```

### 웹 클라이언트 실행

```bash
cd mobile
npm install
npx expo start
```

정적 웹 빌드:

```bash
cd mobile
npm run export:web
```

## 주요 기능

- PDF 드래그 앤 드롭 입력
- JSON 우선 기반 보도자료 후처리
- Markdown 편집
- 실시간 미리보기
- 데스크톱/태블릿/모바일 반응형 UI
- PDF 또는 Markdown 파일 열기
- `.md` 저장, 복사, 공유
- 작업별 `edit_token` 기반 접근 분리
- Turnstile, 업로드 제한, TTL 정리 등 기본 보안 장치

## 저장소 구조

```text
GovPress_PDF_MD/
├─ mobile/
├─ server/
├─ src/
├─ tests/
├─ docs/
│  ├─ conversion-rules.md
│  ├─ development.md
│  ├─ packaging.md
│  ├─ troubleshooting.md
│  └─ archive/
├─ deploy/
│  └─ wsl/
└─ archive/
```

## 문서

- 개발 및 실행: [docs/development.md](/home/wavel/GovPress_PDF_MD/docs/development.md)
- 모바일 클라이언트: [mobile/README.md](/home/wavel/GovPress_PDF_MD/mobile/README.md)
- 모바일 백엔드: [docs/mobile-backend.md](/home/wavel/GovPress_PDF_MD/docs/mobile-backend.md)
- 빌드 및 배포: [docs/packaging.md](/home/wavel/GovPress_PDF_MD/docs/packaging.md)
- 변환 규칙: [docs/conversion-rules.md](/home/wavel/GovPress_PDF_MD/docs/conversion-rules.md)
- 문제 해결: [docs/troubleshooting.md](/home/wavel/GovPress_PDF_MD/docs/troubleshooting.md)

## 테스트

```bash
python -m unittest discover -s tests
```

고정 샘플은 `tests/fixtures/` 또는 테스트 파일 내부 fixture를 기준으로 관리하고, 수동 검증용 샘플은 `tests/manual_samples/` 아래에서 관리합니다.
