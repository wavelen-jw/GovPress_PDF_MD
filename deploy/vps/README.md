# VPS 배포 (저성능 서버)

Ubuntu 24.04 / 1 vCPU / 1 GB RAM 기준 배포 가이드입니다.

## 서버 스펙 기준 튜닝 요약

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
curl -fsSL https://raw.githubusercontent.com/wavelen-jw/GovPress_PDF_MD/claude/optimize-low-performance-servers-7H90I/deploy/vps/setup.sh \
  | sudo bash
```

또는 저장소를 직접 클론한 뒤 실행할 수도 있습니다.

```bash
git clone -b claude/optimize-low-performance-servers-7H90I \
  https://github.com/wavelen-jw/GovPress_PDF_MD.git ~/GovPress_PDF_MD
sudo bash ~/GovPress_PDF_MD/deploy/vps/setup.sh ~/GovPress_PDF_MD
```

스크립트가 수행하는 작업:
1. Docker CE + Compose Plugin 설치
2. 저장소 클론 (브랜치 `claude/optimize-low-performance-servers-7H90I`)
3. `.env` 초기 파일 생성
4. `data/` 디렉터리 준비
5. systemd 서비스 등록 및 활성화
6. Docker Compose 빌드 & 시작
7. 헬스 체크

## 설치 후 필수 작업

```bash
nano ~/GovPress_PDF_MD/deploy/vps/.env
```

수정할 값:

```env
GOVPRESS_API_KEY=실제-비밀-키
GOVPRESS_CORS_ALLOW_ORIGINS=https://wavelen-jw.github.io
CLOUDFLARE_TUNNEL_TOKEN=실제-터널-토큰
```

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
git pull origin claude/optimize-low-performance-servers-7H90I
docker compose -f deploy/vps/docker-compose.yml up -d --build
```

## 메모리 모니터링

1 GB 환경에서는 메모리 여유를 주기적으로 확인합니다.

```bash
free -h
docker stats --no-stream
```

worker 컨테이너가 512 MB 한도에 도달하면 OOM으로 재시작됩니다.
그 경우 `.env`에서 `GOVPRESS_MAX_UPLOAD_BYTES`를 더 낮추거나
변환 대상 파일 크기를 줄이는 것이 좋습니다.
