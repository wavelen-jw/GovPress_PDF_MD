# VPS 배포 (저성능 서버)

> 운영 상태(2026-09-05): `serverV`는 단계적 퇴역 대상입니다.
> 신규 배포·키 추가·단축 URL 배포에는 이 서버를 사용하지 않습니다.
> 아래 serverV 항목은 롤백 창 동안의 역사적 참고이며,
> 실제 절차와 완료 기록은 `docs/server-v-retirement.md`를 따릅니다.

Ubuntu 24.04 / 1 vCPU / 1 GB RAM 기준 배포 가이드입니다.

## 서버 스펙 기준 튜닝 요약

이 문서는 자동배포 경로 검증 시에도 기준 참고 문서로 사용합니다.

| 항목 | 기본값 | VPS 적용값 |
|---|---|---|
| Worker 동시 변환 수 | 3 | **1** |
| 폴링 간격 | 1 s | **3 s** |
| Uvicorn 워커 | 기본값 | **1** |
| API 컨테이너 메모리 | 무제한 | **256 MB** |
| Worker 컨테이너 메모리 | 무제한 | **512 MB** |
| Java 힙 상한 | JVM 기본 | **256 MB** |
| 변환 타임아웃 | 없음 | **300 s** |
| 업로드 크기 제한 | 25 MB | **25 MB** |
| Rate limit | 12/60 s | **6/60 s** |
| Job TTL | 72 h | **24 h** |

## 최초 설치 (원클릭)

서버에 SSH 로그인 후 실행합니다.

```bash
curl -fsSL https://raw.githubusercontent.com/wavelen-jw/GovPress_PDF_MD/web/deploy/vps/setup.sh \
  | sudo bash
```

또는 저장소를 직접 클론한 뒤 실행할 수도 있습니다.

```bash
git clone https://github.com/wavelen-jw/GovPress_PDF_MD.git ~/GovPress_PDF_MD
cd ~/GovPress_PDF_MD
git checkout web
sudo bash ~/GovPress_PDF_MD/deploy/vps/setup.sh ~/GovPress_PDF_MD
```

스크립트가 수행하는 작업:
1. Docker CE + Compose Plugin 설치
2. 저장소 클론 또는 현재 체크아웃/기본 브랜치 기준 동기화
3. `.env` 초기 파일 생성
4. `data/` 디렉터리 준비
5. systemd 서비스 등록 및 활성화
6. Docker Compose 빌드 & 시작
7. 헬스 체크

특정 브랜치를 강제로 배포하려면 실행 전에 `GOVPRESS_DEPLOY_BRANCH` 를 지정합니다.

```bash
export GOVPRESS_DEPLOY_BRANCH=web
sudo bash ~/GovPress_PDF_MD/deploy/vps/setup.sh ~/GovPress_PDF_MD
```

## 설치 후 필수 작업

```bash
nano ~/GovPress_PDF_MD/deploy/vps/.env
```

수정할 값:

```env
GOVPRESS_API_KEY=실제-비밀-키
GOVPRESS_CORS_ALLOW_ORIGINS=https://govpress.cloud,https://www.govpress.cloud,https://wavelen-jw.github.io
GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK=0
GOVPRESS_CONVERTER_SPEC=git+https://<TOKEN>@github.com/wavelen-jw/gov-md-converter.git@v0.1.18
GOVPRESS_CONVERTER_MIN_VERSION=0.1.18
GOVPRESS_CONVERTER_EXTRA_INDEX_URL=
CLOUDFLARE_TUNNEL_TOKEN=실제-터널-토큰
```

주의:

- converter 버전은 서버별 `.env`에서 직접 태그를 바꾸지 말고 저장소의 `deploy/converter.version`을 기준으로 관리합니다.
- `gov-md-converter` 릴리스 태그는 `Update Converter Version` workflow를 통해 `deploy/converter.version`을 갱신하고, 이 workflow가 `Deploy API To Servers`를 직접 호출합니다.
- bare-metal 설치/재배포 스크립트는 `GOVPRESS_CONVERTER_SPEC`의 기존 태그를 `deploy/converter.version` 값으로 자동 정규화합니다.
- bare-metal 설치/재배포 스크립트는 `https://govpress.cloud`, `https://www.govpress.cloud`, `https://wavelen-jw.github.io`를 `GOVPRESS_CORS_ALLOW_ORIGINS`에 자동 보정합니다.
- 프로덕션은 `GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK=0` 고정입니다.
- 배포 후 `distribution_version`, `module_path`, `backend`를 검사하고 package backend가 아니면 실패 처리합니다.

수정 후 재시작:

```bash
sudo systemctl restart govpress-compose.service
```

## 상태 확인

```bash
# 서비스 상태
sudo systemctl status govpress-compose.service

# 컨테이너 상태
docker compose -f ~/GovPress_PDF_MD/deploy/vps/docker-compose.yml ps

# 헬스 체크
curl http://127.0.0.1:8080/health

# 로그
docker compose -f ~/GovPress_PDF_MD/deploy/vps/docker-compose.yml logs -f api
docker compose -f ~/GovPress_PDF_MD/deploy/vps/docker-compose.yml logs -f worker
```

## 업데이트

```bash
cd ~/GovPress_PDF_MD
git pull
docker compose -f deploy/vps/docker-compose.yml up -d --build
```

자동배포 성공 기준:

- `govpress-api.service` 재시작 성공
- `127.0.0.1:8013/health` `200`
- `deploy/converter.version`과 실제 `distribution_version`, `module_path`, `backend` 일치
- W/N 동일 샘플 변환 결과 hash 일치

## GitHub Actions 배포 SSH 경로 (serverV 레거시)

`serverV`의 public `:2222`는 UFW allowlist로 제한합니다. GitHub-hosted runner IP 대역은 매우 넓고 변경되므로 `2222/tcp`를 `0.0.0.0/0`으로 열지 않습니다.

Actions 배포는 Cloudflare Tunnel SSH를 사용합니다.

- hostname: `ssh-v.govpress.cloud`
- tunnel: `govpress-v-ssh`
- origin: `ssh://127.0.0.1:2222`
- user service: `cloudflared-govpress-v-ssh.service`
- workflow variable: `GOVPRESS_VPS_SSH_HOST=ssh-v.govpress.cloud`

점검:

```bash
systemctl --user status --no-pager cloudflared-govpress-v-ssh.service
cloudflared tunnel info govpress-v-ssh
ssh -o ProxyCommand='cloudflared access ssh --hostname %h' ssh-v.govpress.cloud 'hostname && systemctl is-active govpress-api.service'
```

퇴역 브랜치에서는 `deploy_target=serverV`와 V 배포 job을 제거합니다.
GitHub Actions에서 serverV를 수동 선택하는 경로는 더 이상 제공하지 않습니다.

롤백 과정에서 V 배포 자동화가 꼭 필요하면 퇴역 커밋을 되돌린 뒤
기존 workflow를 복구하고, 복구 사유를 runbook에 기록합니다.

## serverV 운영 점검 지시서 (롤백 창 전용)

관찰 및 롤백 창의 serverV는 대기 자산이며 일상 운영이나 다른 서버의
jump host로 사용하지 않습니다.

- 평상시 점검은 W와 N에 직접 접속합니다.
- `ssh-v.govpress.cloud`와 V 자격증명은 빠른 롤백 창이 끝날 때까지
  유지합니다.
- V 자체의 롤백 점검과 재기동은 `docs/server-v-retirement.md`의
  순서를 따릅니다.


## 메모리 모니터링

1 GB 환경에서는 메모리 여유를 주기적으로 확인합니다.

```bash
free -h
docker stats --no-stream
```

worker 컨테이너가 512 MB 한도에 도달하면 OOM으로 재시작됩니다.
그 경우 `.env`에서 `GOVPRESS_MAX_UPLOAD_BYTES`를 더 낮추거나

### 비공개 변환 엔진 패키지

엔진 소스를 별도 비공개 저장소로 분리했다면 아래 값을 사용합니다.

- `GOVPRESS_CONVERTER_SPEC`
  - 예: `git+https://<TOKEN>@github.com/wavelen-jw/gov-md-converter.git@v0.1.18`
- `GOVPRESS_CONVERTER_MIN_VERSION`
  - 예: `0.1.18`
- `GOVPRESS_CONVERTER_EXTRA_INDEX_URL`
  - private registry를 쓸 때만 필요
- `GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK`
  - 프로덕션은 반드시 `0`
  - private 엔진을 실제로 설치했다면 `scripts/check_converter_runtime.py`가 설치 후 버전, distribution metadata, backend를 검사합니다.
- converter 버전이 바뀌면 배포 스크립트가 기존 `storage/results/*.md`, `storage/results/*.error.log`, `storage/policy_briefing_cache/index.json`, `storage/policy_briefing_cache/originals/*`를 먼저 비워서 이전 엔진 결과가 재사용되지 않게 합니다. 날짜별 `policy_briefing_catalog/*.json`은 보존합니다.

`setup-bare.sh` 실행 예:

```bash
export GOVPRESS_CONVERTER_SPEC="git+https://<TOKEN>@github.com/wavelen-jw/gov-md-converter.git@v0.1.18"
export GOVPRESS_CONVERTER_MIN_VERSION="0.1.18"
export GOVPRESS_CONVERTER_EXTRA_INDEX_URL=""
export GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK=0
sudo bash deploy/vps/setup-bare.sh /home/wavel/projects/GovPress_PDF_MD
```
변환 대상 파일 크기를 줄이는 것이 좋습니다.
