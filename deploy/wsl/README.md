# WSL Deployment

이 디렉터리는 WSL Ubuntu를 1차 운영 환경으로 사용하는 배포 초안입니다.

목표:

- 지금은 Windows PC의 WSL2 Ubuntu에서 실행
- 나중에는 같은 파일을 Linux VPS로 거의 그대로 복사

구성:

- `api`: FastAPI 서버
- `worker`: SQLite polling worker
- `caddy`: 로컬 reverse proxy
- `cloudflared`: 외부 공개용 Tunnel

현재 운영 서버는 같은 `host_proxy` 계열 모드를 씁니다.

- `serverW`
  - `deploy/wsl/docker-compose.host-proxy.yml`
  - compose는 `api/worker`만 관리
  - `api`는 `127.0.0.1:8013`으로만 publish되고, host-level `caddy`가 `127.0.0.1:8080`을 유지
- `serverH`
  - `deploy/wsl/docker-compose.host-proxy.yml`
  - host-level `caddy/cloudflared`를 유지하고, compose는 `api/worker`만 관리
  - `api`는 `127.0.0.1:8013`으로만 publish되고, host-level `caddy`가 `127.0.0.1:8080`을 유지

즉 서버H와 서버W 모두 Docker가 publish한 `127.0.0.1:8080`에 `cloudflared`가 직접 의존하지 않도록 host-level `caddy/cloudflared`를 기본 전제로 두고, compose는 `api/worker`만 관리합니다.

## 운영 원칙

- 운영 서버H/W는 항상 `host_proxy` 모드만 사용합니다.
- compose는 `api/worker`만 관리합니다.
- `127.0.0.1:8080`은 host-level `govpress-caddy.service`만 점유해야 합니다.
- 외부 공개는 host-level `govpress-cloudflared.service`만 담당합니다.
- `govpress-cloudflared.service`는 반드시 `--config /dev/null`로 실행되어야 합니다.
- `/etc/systemd/system/cloudflared.service` 같은 레거시 cloudflared 서비스는 존재하면 안 됩니다.
- Cloudflare DNS와 tunnel ingress는 정상 절차에서 수시로 바꾸지 않습니다.

고정 매핑:

- `serverH`
  - public: `https://api.govpress.cloud`
  - ingress: `api.govpress.cloud -> http://127.0.0.1:8080`
- `serverW`
  - public: `https://api4.govpress.cloud`
  - ingress: `api4.govpress.cloud -> http://127.0.0.1:8080`
- `serverV`
  - public: `https://api2.govpress.cloud`

## 권장 디렉터리

WSL Linux 파일시스템 안에 프로젝트를 두는 편이 좋습니다.

현재 작업 환경 예:

```bash
/home/wavel/projects/GovPress_PDF_MD
```

배포 작업 디렉터리:

```bash
cd /home/wavel/projects/GovPress_PDF_MD/deploy/wsl
```

직접 접속 가능한 서버에서 host-proxy 구조를 즉시 적용하려면:

```bash
bash deploy/wsl/apply-host-proxy.sh
```

GitHub Actions 원격배포까지 계속 쓰려면, 서버에서 한 번만 아래를 실행해 제한된 passwordless sudo를 허용합니다.

```bash
bash deploy/wsl/install-remote-deploy-sudoers.sh
```

검증:

```bash
sudo -n true
```

이 명령이 조용히 성공해야 원격 복구까지 가능합니다.

## 준비

1. WSL2 Ubuntu 설치
2. Docker Desktop 설치 후 WSL integration 활성화
3. Cloudflare에서 Tunnel 생성
4. `api.govpress.cloud` 같은 공개 주소를 해당 Tunnel에 연결

## 환경 변수

`.env.example`을 복사해 `.env`를 만듭니다.

```bash
cp .env.example .env
```

수정할 값:

- `GOVPRESS_API_KEY`
- `GOVPRESS_CORS_ALLOW_ORIGINS`
- `GOVPRESS_UPLOAD_RATE_LIMIT_COUNT`
- `GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS`
- `GOVPRESS_JOB_TTL_HOURS`
- `GOVPRESS_TURNSTILE_SECRET_KEY`
- `EXPO_PUBLIC_CLOUDFLARE_TURNSTILE_SITE_KEY`
- `CLOUDFLARE_TUNNEL_TOKEN`

예:

```env
GOVPRESS_API_KEY=super-secret-key
GOVPRESS_CORS_ALLOW_ORIGINS=https://your-user.github.io,http://172.25.164.35:8084
GOVPRESS_UPLOAD_RATE_LIMIT_COUNT=12
GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS=60
GOVPRESS_JOB_TTL_HOURS=72
GOVPRESS_TURNSTILE_SECRET_KEY=0x4AAAA...
GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK=1
GOVPRESS_CONVERTER_SPEC=
GOVPRESS_CONVERTER_EXTRA_INDEX_URL=
EXPO_PUBLIC_CLOUDFLARE_TURNSTILE_SITE_KEY=0x4AAAA...
CLOUDFLARE_TUNNEL_TOKEN=eyJh...
```

현재 운영 중인 공개 API 예:

```text
https://api.govpress.cloud
```

이 문서는 Cloudflare Tunnel 기반 자동배포 점검 시에도 참고합니다.

serverW로 연결되는 현재 공개 주소는 `https://api4.govpress.cloud`입니다.

주의:

- `GOVPRESS_CORS_ALLOW_ORIGINS`는 실제 프론트 주소로 바꿔야 합니다.

### 비공개 변환 엔진 패키지

비공개 `govpress-converter` 패키지를 쓰려면 `.env`에 아래 값을 추가합니다.

- `GOVPRESS_CONVERTER_SPEC`
  - 예: `git+https://<TOKEN>@github.com/wavelen-jw/gov-md-converter.git@v0.1.1`
- `GOVPRESS_CONVERTER_MIN_VERSION`
  - 예: `0.1.1`
- `GOVPRESS_CONVERTER_EXTRA_INDEX_URL`
  - private registry를 쓸 때만 필요
- `GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK`
  - 프로덕션/준프로덕션 권장값은 `0`
  - private 엔진을 실제로 설치했다면 `scripts/check_converter_runtime.py`가 빌드 중에 버전과 시그니처를 검사합니다.
- converter 버전을 올려 배포할 때는 배포 스크립트가 기존 `storage/results/*.md`와 `storage/policy_briefing_cache/*`를 먼저 비워서 이전 엔진 결과가 재사용되지 않게 합니다.
- 값이 비어 있으면 기본 허용 origin이 없으므로 브라우저 접근이 막힙니다.
- 로컬 웹 테스트 중이면 `http://172.25.164.35:8084` 같은 현재 웹 주소를 임시로 추가해야 합니다.
- GitHub Pages를 쓸 경우 보통 `https://wavelen-jw.github.io/GovPress_PDF_MD` 형식입니다.
- 현재 웹 클라이언트는 GitHub Pages에서 기본 API를 `https://api.govpress.cloud`로 보도록 설정되어 있습니다.

## `read.govpress.cloud` 단축 리다이렉트

목표:

- `https://read.govpress.cloud/<slug>`를 YOURLS가 바로 `301` redirect
- 대상 URL은 기존 GitHub Pages `https://wavelen-jw.github.io/GovPress_PDF_MD/...`
- 광고 없음
- 중간 페이지 없음

최소 구성 기준:

- YOURLS는 `serverW`에 별도 compose로 띄웁니다.
- 기존 `api/worker/caddy/cloudflared` 구성은 건드리지 않습니다.
- Cloudflare Zero Trust에서 `read.govpress.cloud` public hostname을 새로 추가합니다.
- Cloudflare Access는 `https://read.govpress.cloud/admin/*`에만 적용합니다.

필요한 `.env` 값:

```env
GOVPRESS_READ_SHORTENER_PORT=8091
YOURLS_SITE=https://read.govpress.cloud
YOURLS_USER=admin
YOURLS_PASSWORD=change-me
YOURLS_PRIVATE=true
YOURLS_DB_NAME=yourls
YOURLS_DB_USER=yourls
YOURLS_DB_PASSWORD=change-me
YOURLS_DB_ROOT_PASSWORD=change-me
```

로컬 YOURLS 기동:

```bash
bash deploy/wsl/apply-read-shortener.sh
```

이 스크립트는 아래 compose 파일을 사용합니다.

- `deploy/wsl/docker-compose.yourls.yml`

기동 후 기준:

- YOURLS admin local: `http://127.0.0.1:8091/admin/`
- Cloudflare public hostname origin: `http://127.0.0.1:8091`
- public short URL base: `https://read.govpress.cloud`

Cloudflare에서 추가할 것:

1. `read.govpress.cloud` public hostname 생성
2. service/origin을 `http://127.0.0.1:8091`로 지정
3. `read.govpress.cloud/admin/*`에만 Access policy 적용
4. `read.govpress.cloud/*` 전체에 redirect rule을 추가하지 않음

검증:

```bash
curl -I http://127.0.0.1:8091/admin/
curl -I https://read.govpress.cloud/admin/
curl -I https://read.govpress.cloud/abc123
```

정상 기준:

- `/admin/`은 local에서 `200` 또는 `302`
- public `/admin/`은 Access 없이는 차단
- 공개 shortlink는 `301`로 GitHub Pages 최종 URL을 바로 가리킴

운영 메모:

- long URL은 YOURLS admin에서 `https://wavelen-jw.github.io/GovPress_PDF_MD/...` 형식으로 직접 넣습니다.
- slug 생성/수정/삭제는 YOURLS admin에서 처리합니다.
- 기존 `api.govpress.cloud`, `api4.govpress.cloud`, `api2.govpress.cloud` 경로와 무관하게 운영합니다.

## 실행

```bash
docker compose up -d --build
```

상태 확인:

```bash
docker compose ps
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f cloudflared
```

로컬 헬스체크:

```bash
curl http://127.0.0.1:8080/health
```

외부 공개 주소 예:

```text
https://api.govpress.cloud/health
```

실제 배포 검증 예:

```bash
curl -i https://api.govpress.cloud/health
```

## 안전한 배포 절차

1. 배포 전 상태 확인

```bash
sudo systemctl status --no-pager govpress-compose.service govpress-caddy.service govpress-cloudflared.service
sudo lsof -iTCP:8080 -sTCP:LISTEN -n -P
curl -sS http://127.0.0.1:8013/health
curl -sS http://127.0.0.1:8080/health
```

정상 기준:

- `8013`은 앱이 `200`
- `8080`은 host proxy가 `200`
- `8080` listener는 `python3 ... host_proxy.py`
- `docker-proxy`가 `8080`을 잡고 있으면 비정상

2. 배포 실행

직접 배포:

```bash
cd /home/wavel/GovPress_PDF_MD
bash deploy/wsl/apply-host-proxy.sh
```

또는 GitHub Actions `Deploy API To Servers`를 사용합니다.

3. 배포 직후 검증

```bash
curl -i http://127.0.0.1:8013/health
curl -i http://127.0.0.1:8080/health
curl -i -H 'X-API-Key: <API_KEY>' https://api.govpress.cloud/health
curl -i -H 'X-API-Key: <API_KEY>' https://api4.govpress.cloud/health
curl -i -H 'X-API-Key: <API_KEY>' https://api2.govpress.cloud/health
python3 scripts/openclaw_ops.py --json server-status
```

## 금지 절차

- 운영 서버H/W에서 compose로 `caddy`나 `cloudflared`를 띄우는 것
- `127.0.0.1:8080`을 Docker publish 포트로 되돌리는 것
- `api.govpress.cloud`를 다른 tunnel에 임시로 중복 연결한 채 방치하는 것
- 레거시 `/etc/systemd/system/cloudflared.service`를 남겨두는 것

## 장애 Runbook

### 1. `Address already in use`

증상:

- public health가 `502`
- `govpress-caddy.service` 로그에 `OSError: [Errno 98] Address already in use`

확인:

```bash
sudo lsof -iTCP:8080 -sTCP:LISTEN -n -P
sudo ss -ltnp '( sport = :8080 )'
```

복구:

```bash
sudo kill <docker-proxy-pid>
sudo systemctl restart govpress-caddy.service
sudo systemctl restart govpress-cloudflared.service
```

### 2. 로컬은 정상인데 public만 `502`

증상:

- `127.0.0.1:8013/health` -> `200`
- `127.0.0.1:8080/health` -> `200`
- public `https://api.govpress.cloud/health`만 `502`

이 경우는 보통 Cloudflare stale connector입니다.

확인:

- Cloudflare tunnel connections에 connector가 둘 이상 남아 있는지 확인
- 오래된 connector가 계속 재등장하면 서버 안의 stray `cloudflared`를 의심

실제 재발 원인:

- `/etc/systemd/system/cloudflared.service`
- `ExecStart=/usr/local/bin/cloudflared tunnel --config ~/.cloudflared/config.yml run`

이 레거시 서비스가 stale connector를 계속 되살렸습니다.

복구:

```bash
sudo systemctl disable --now cloudflared.service
sudo rm -f /etc/systemd/system/cloudflared.service
sudo systemctl daemon-reload
```

그 다음 Cloudflare에서 stale connector를 지우면 public health가 즉시 복구됩니다.

### 3. 원격배포는 되는데 원격복구가 안 됨

증상:

- SSH는 되지만 `sudo: a password is required`

복구:

```bash
cd /home/wavel/GovPress_PDF_MD
sudo bash deploy/wsl/install-remote-deploy-sudoers.sh
sudo -n true
```

## Cloudflare 점검 포인트

- `api.govpress.cloud` DNS는 `b73b8bf8-453e-427d-ad76-02dcb3c7448c.cfargotunnel.com`
- `api4.govpress.cloud` DNS는 `4390f5bd-3dbe-49f5-ab52-382de7670294.cfargotunnel.com`
- stale connector가 남아 있지 않은지 tunnel connections 확인

반복 점검용 스크립트:

```bash
python3 scripts/check_cloudflare_tunnel_connectors.py --json
python3 scripts/check_cloudflare_tunnel_connectors.py --tunnel serverH --cleanup-stale
```

## 저장 위치

배포 데이터는 이 디렉터리 아래에 남습니다.

- `deploy/wsl/data/storage`
- `deploy/wsl/data/caddy`
- `deploy/wsl/config/caddy`

GovPress 작업 파일:

- 원본 PDF
- 결과 Markdown
- 수정본
- `jobs.sqlite3`

## 보안 원칙

- FastAPI는 외부에 직접 포트 공개하지 않습니다.
- 호스트 공개 포트는 `127.0.0.1:8080`만 사용합니다.
- 외부 공개는 `cloudflared`만 담당합니다.
- `GOVPRESS_API_KEY`를 설정합니다.
- `GOVPRESS_CORS_ALLOW_ORIGINS`는 실제 프론트 도메인만 허용합니다.
- 업로드 요청은 서버 보조 rate limit으로 제한됩니다.
  - 기본값: `12 requests / 60 seconds`
- 완료/실패 작업은 TTL이 지나면 자동 정리됩니다.
  - 기본값: `72 hours`
- 필요하면 `Turnstile`을 켜서 업로드 전에 사람 확인 절차를 추가합니다.
- CORS는 예시값 그대로 두지 말고 실제 프론트 주소만 허용합니다.

## 작업 접근 모델

- 작업 생성 시 `job_id`와 `edit_token`이 함께 발급됩니다.
- 상태 조회, 결과 조회, 수정 저장, 재시도는 `X-Edit-Token`이 있어야만 가능합니다.
- 공개 최근 작업 목록은 제공하지 않습니다.

## Cloudflare 권장 규칙

업로드 엔드포인트만 보호하는 것이 좋습니다.

- 대상: `POST /v1/jobs`
- 표현식:

```txt
http.request.uri.path eq "/v1/jobs" and http.request.method eq "POST"
```

- 권장 시작값:
  - Requests: `5`
  - Period: `10 seconds`
  - Action: `Block`
  - Duration: `10 seconds`

이 값은 현재 Cloudflare 화면 제약에 맞춘 최소 방어선입니다.

## 현재 확인된 상태

- `https://api.govpress.cloud/health` 외부 응답 정상
- 공개 API로 PDF 업로드, 작업 완료, 결과 조회 정상
- API 키가 설정되어 있으므로 프론트에서도 같은 키를 입력해야 합니다

## 자동 시작

현재 WSL은 `systemd=true` 상태라 systemd 서비스로 자동 기동할 수 있습니다.

예시 파일:

- [deploy/wsl/systemd/govpress-compose.service](/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/systemd/govpress-compose.service)
- [deploy/wsl/systemd/README.md](/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/systemd/README.md)

핵심 절차:

```bash
sudo cp deploy/wsl/systemd/govpress-compose.service /etc/systemd/system/govpress-compose.service
sudo systemctl daemon-reload
sudo systemctl enable govpress-compose.service
sudo systemctl start govpress-compose.service
```

상태 확인:

```bash
sudo systemctl status govpress-compose.service
```

## 운영 체크리스트

### 일상 점검

```bash
sudo systemctl status --no-pager govpress-compose.service
docker-compose -f /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/docker-compose.yml ps
curl http://127.0.0.1:8080/health
curl -i -H 'X-API-Key: <API_KEY>' https://api.govpress.cloud/health
```

정상 기준:

- systemd 서비스가 `active (exited)`
- `govpress-api`, `govpress-worker`, `govpress-caddy`, `govpress-cloudflared`가 모두 실행 중
- 로컬 `8080/health` 응답 정상
- 외부 `api.govpress.cloud/health` 응답 정상

### 로그 확인

```bash
docker-compose -f /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/docker-compose.yml logs --tail=100 api
docker-compose -f /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/docker-compose.yml logs --tail=100 worker
docker-compose -f /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/docker-compose.yml logs --tail=100 cloudflared
```

### 재시작

```bash
sudo systemctl restart govpress-compose.service
sudo systemctl status --no-pager govpress-compose.service
```

또는 compose만 직접 재기동:

```bash
"/mnt/c/Program Files/Docker/Docker/resources/bin/docker-compose" -f /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/docker-compose.yml up -d
```

### API 키 교체

1. `deploy/wsl/.env` 수정
2. `GOVPRESS_API_KEY` 새 값 반영
3. 스택 재기동

```bash
nano /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/.env
sudo systemctl restart govpress-compose.service
```

4. 프론트에서도 같은 새 키 입력

### CORS 변경

프론트 주소가 바뀌면 아래 값을 같이 수정합니다.

```env
GOVPRESS_CORS_ALLOW_ORIGINS=https://wavelen-jw.github.io,http://172.25.164.35:8084
```

반영:

```bash
sudo systemctl restart govpress-compose.service
```

### 장애 복구 순서

1. `sudo systemctl status --no-pager govpress-compose.service`
2. `docker-compose ... ps`
3. `curl http://127.0.0.1:8080/health`
4. `curl -i -H 'X-API-Key: <API_KEY>' https://api.govpress.cloud/health`
5. `docker-compose ... logs --tail=100 api worker cloudflared`

### 업로드 제한 값 조정

기본값:

```env
GOVPRESS_UPLOAD_RATE_LIMIT_COUNT=12
GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS=60
GOVPRESS_JOB_TTL_HOURS=72
```

더 보수적으로 운영하려면:

```env
GOVPRESS_UPLOAD_RATE_LIMIT_COUNT=6
GOVPRESS_UPLOAD_RATE_LIMIT_WINDOW_SECONDS=60
GOVPRESS_JOB_TTL_HOURS=24
```

### 재부팅 후 확인

Windows 재부팅 후 WSL에서 아래만 확인하면 됩니다.

```bash
sudo systemctl status --no-pager govpress-compose.service
curl http://127.0.0.1:8080/health
curl -i -H 'X-API-Key: <API_KEY>' https://api.govpress.cloud/health
```

## VPS 이전

이 디렉터리 전체를 Linux VPS에 복사한 뒤 아래만 바꾸면 됩니다.

- `.env`
- 도메인
- Cloudflare Tunnel token
- 볼륨 경로

그리고 동일하게 실행합니다.

```bash
docker compose up -d --build
```
