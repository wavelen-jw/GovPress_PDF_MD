# VPS 배포 (저성능 서버)

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
| 업로드 크기 제한 | 25 MB | **10 MB** |
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
GOVPRESS_CORS_ALLOW_ORIGINS=https://wavelen-jw.github.io
GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK=1
GOVPRESS_CONVERTER_SPEC=
GOVPRESS_CONVERTER_EXTRA_INDEX_URL=
CLOUDFLARE_TUNNEL_TOKEN=실제-터널-토큰
```

주의:

- converter 버전은 서버별 `.env`에서 직접 태그를 바꾸지 말고 저장소의 `deploy/converter.version`을 기준으로 관리합니다.
- bare-metal 설치/재배포 스크립트는 `GOVPRESS_CONVERTER_SPEC`의 기존 태그를 `deploy/converter.version` 값으로 자동 정규화합니다.

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

## `ai.govpress.cloud` 단축 리다이렉트

구성:

- `serverV`에 초경량 Python redirect 서버를 별도 systemd 서비스로 띄웁니다.
- 단일 redirect target은 repo의 `config/read_shortlinks.json` 파일에서 관리합니다.
- 기존 `api2.govpress.cloud`와 `127.0.0.1:8080` API 경로는 건드리지 않습니다.
- Cloudflare에서 `ai.govpress.cloud` public hostname만 새로 추가합니다.
- 광고 없음, 중간 페이지 없음, DB 없음, admin 없음

설정 파일 예:

```json
{
  "default_target": "https://wavelen-jw.github.io/GovPress_PDF_MD/"
}
```

로컬 서비스 기준:

- health: `http://127.0.0.1:8091/health`
- redirect: `http://127.0.0.1:8091/`
- systemd: `govpress-read-shortener.service`

배포:

```bash
sudo bash deploy/vps/install-read-shortener-sudoers.sh
sudo bash deploy/vps/install-read-shortener.sh ~/GovPress_PDF_MD
```

검증:

```bash
curl http://127.0.0.1:8091/health
curl -I http://127.0.0.1:8091/
sudo systemctl status --no-pager govpress-read-shortener.service
```

GitHub Actions 원격배포까지 쓰려면 서버에서 한 번만 아래를 실행합니다.

```bash
cd ~/GovPress_PDF_MD
sudo bash deploy/vps/install-read-shortener-sudoers.sh
```

Cloudflare에서 추가할 것:

1. `ai.govpress.cloud` public hostname 생성
2. service/origin을 `http://127.0.0.1:8091`로 지정
3. 별도 admin 경로나 Access policy는 필요 없음

정상 기준:

- `/health`는 `200`
- `/`는 `302`와 대상 `Location` 응답
- 기존 `api2.govpress.cloud`는 영향 없음

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
  - 예: `git+https://<TOKEN>@github.com/wavelen-jw/gov-md-converter.git@v0.1.1`
- `GOVPRESS_CONVERTER_MIN_VERSION`
  - 예: `0.1.1`
- `GOVPRESS_CONVERTER_EXTRA_INDEX_URL`
  - private registry를 쓸 때만 필요
- `GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK`
  - 프로덕션 권장값은 `0`
  - private 엔진을 실제로 설치했다면 `scripts/check_converter_runtime.py`가 설치 후 버전과 시그니처를 검사합니다.
- converter 버전을 올려 배포할 때는 배포 스크립트가 기존 `storage/results/*.md`와 `storage/policy_briefing_cache/*`를 먼저 비워서 이전 엔진 결과가 재사용되지 않게 합니다.

`setup-bare.sh` 실행 예:

```bash
export GOVPRESS_CONVERTER_SPEC="git+https://<TOKEN>@github.com/wavelen-jw/gov-md-converter.git@v0.1.1"
export GOVPRESS_CONVERTER_MIN_VERSION="0.1.1"
export GOVPRESS_CONVERTER_EXTRA_INDEX_URL=""
export GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK=0
sudo bash deploy/vps/setup-bare.sh /home/wavel/projects/GovPress_PDF_MD
```
변환 대상 파일 크기를 줄이는 것이 좋습니다.
