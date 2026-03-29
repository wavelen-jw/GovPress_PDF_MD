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

## 권장 디렉터리

WSL Linux 파일시스템 안에 프로젝트를 두는 편이 좋습니다.

현재 작업 환경 예:

```bash
/home/wavel/GovPress_PDF_MD
```

배포 작업 디렉터리:

```bash
cd /home/wavel/GovPress_PDF_MD/deploy/wsl
```

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
- `CLOUDFLARE_TUNNEL_TOKEN`

예:

```env
GOVPRESS_API_KEY=super-secret-key
GOVPRESS_CORS_ALLOW_ORIGINS=https://your-user.github.io/GovPress_PDF_MD
CLOUDFLARE_TUNNEL_TOKEN=eyJh...
```

현재 운영 중인 공개 API 예:

```text
https://api.govpress.cloud
```

주의:

- `GOVPRESS_CORS_ALLOW_ORIGINS`는 실제 프론트 주소로 바꿔야 합니다.
- 로컬 웹 테스트 중이면 `http://172.25.164.35:8084` 같은 현재 웹 주소를 임시로 추가해야 합니다.
- GitHub Pages를 쓸 경우 보통 `https://wavelen-jw.github.io/GovPress_PDF_MD` 형식입니다.
- 현재 웹 클라이언트는 GitHub Pages에서 기본 API를 `https://api.govpress.cloud`로 보도록 설정되어 있습니다.

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
- `GOVPRESS_CORS_ALLOW_ORIGINS`는 프론트 도메인으로 제한합니다.
- CORS는 예시값 그대로 두지 말고 실제 프론트 주소만 허용합니다.

## 현재 확인된 상태

- `https://api.govpress.cloud/health` 외부 응답 정상
- 공개 API로 PDF 업로드, 작업 완료, 결과 조회 정상
- API 키가 설정되어 있으므로 프론트에서도 같은 키를 입력해야 합니다

## 자동 시작

현재 WSL은 `systemd=true` 상태라 systemd 서비스로 자동 기동할 수 있습니다.

예시 파일:

- [deploy/wsl/systemd/govpress-compose.service](/home/wavel/GovPress_PDF_MD/deploy/wsl/systemd/govpress-compose.service)
- [deploy/wsl/systemd/README.md](/home/wavel/GovPress_PDF_MD/deploy/wsl/systemd/README.md)

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
