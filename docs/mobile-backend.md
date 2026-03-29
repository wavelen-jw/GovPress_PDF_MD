# Mobile Backend

웹/모바일용 백엔드는 API 프로세스와 워커 프로세스를 분리해 실행합니다.

## 구성

- API 서버: 작업 생성, 상태 조회, 결과 조회/수정
- Polling Worker: SQLite 작업 저장소에서 `queued` 작업을 가져와 변환 수행
- 저장소: `storage/` 아래 원본 PDF, 결과 Markdown, SQLite DB 저장
- 선택적 API 키 인증, `edit_token` 기반 작업 분리, CORS, 업로드 제한 지원

## 요구사항

- Python 3.10+
- Java 11+
- `opendataloader-pdf`

## 설치

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -U opendataloader-pdf
```

## API 실행

```bash
.venv/bin/python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8011
```

환경 변수:

- `GOVPRESS_API_KEY`: 설정하면 모든 `/v1/jobs` API에 `X-API-Key` 헤더가 필요합니다.
- `GOVPRESS_CORS_ALLOW_ORIGINS`: 허용 origin 목록. 쉼표로 구분합니다.
- `GOVPRESS_MAX_UPLOAD_BYTES`: 업로드 허용 최대 크기. 기본값은 `25000000` 바이트입니다.
- `GOVPRESS_UPLOAD_RATE_LIMIT_COUNT`: 업로드 rate limit 횟수. 기본값은 `12`입니다.
- `GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS`: 업로드 rate limit 시간창. 기본값은 `60`초입니다.
- `GOVPRESS_JOB_TTL_HOURS`: 완료/실패 작업 자동 정리 시간. 기본값은 `72`시간입니다.
- `GOVPRESS_TURNSTILE_SECRET_KEY`: 설정하면 업로드 시 Cloudflare Turnstile 검증을 수행합니다.

배포 시 주의:

- `GOVPRESS_CORS_ALLOW_ORIGINS`는 실제 프론트 주소로 제한해야 합니다.
- 값이 비어 있으면 기본 허용 origin이 없으므로 브라우저 접근이 막힙니다.
- GitHub Pages를 사용할 경우 예시는 `https://wavelen-jw.github.io/GovPress_PDF_MD`입니다.
- Cloudflare Tunnel 같은 reverse proxy 뒤에 둘 때도 API 키는 유지하는 편이 안전합니다.
- 공개 웹서비스라면 `/v1/jobs` 업로드 경로에 Cloudflare rate limiting을 같이 거는 것이 좋습니다.

기본 엔드포인트:

- `GET /health`
- `POST /v1/jobs`
- `GET /v1/jobs/{job_id}`
- `POST /v1/jobs/{job_id}/retry`
- `GET /v1/jobs/{job_id}/result`
- `PATCH /v1/jobs/{job_id}/result`

작업 접근:

- `POST /v1/jobs` 응답으로 `job_id`와 `edit_token`이 함께 반환됩니다.
- 이후 상태 조회, 결과 조회, 수정 저장, 재시도는 `X-Edit-Token` 헤더가 있어야 합니다.
- 공개 최근 작업 목록은 제공하지 않습니다.

## 워커 실행

```bash
.venv/bin/python -m server.run_worker --storage-root ./storage --poll-interval 1.0
```

워커는 `storage/jobs.sqlite3`를 읽어 `queued` 상태 작업을 `processing`으로 claim한 뒤 변환합니다.

## 저장 경로

- 원본 PDF: `storage/originals/`
- 변환 결과: `storage/results/`
- 사용자 수정본: `storage/edited/`
- 작업 DB: `storage/jobs.sqlite3`

## 재시작 복구

- 서버 또는 워커가 재시작되면 `queued`, `processing` 상태 작업은 다시 `queued`로 복구됩니다.
- 재시작 시 `processing`이던 작업은 `error_code=RECOVERED_AFTER_RESTART`로 표시됩니다.
- 앱 시작 시 완료/실패 작업 중 TTL이 지난 항목은 자동 정리됩니다.

## 테스트

```bash
.venv/bin/python -m unittest tests.test_server_services tests.test_server_api
```

## 운영 권장

- 배포 환경에서는 API와 worker를 `docker compose` 또는 `systemd`로 자동 시작되게 구성합니다.
- WSL2 Ubuntu를 운영 환경으로 쓸 경우 `systemd=true`를 켠 뒤 compose 서비스 자동 시작을 권장합니다.
- Cloudflare에서는 `POST /v1/jobs`에만 rate limiting을 거는 것이 좋습니다.
- 시작점 예:
  - expression: `http.request.uri.path eq "/v1/jobs" and http.request.method eq "POST"`
  - `5 requests / 10 seconds`
  - action: `Block`
  - duration: `10 seconds`
