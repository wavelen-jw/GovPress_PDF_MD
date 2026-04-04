# VPS Auto Deploy

GitHub Actions에서 `web` 브랜치의 서버 관련 변경을 bare-metal VPS에 자동 반영합니다.

현재 운영 구조:

- 앱 경로: `/home/wavel/GovPress_PDF_MD`
- 실행 방식: `systemd --user`
- 서비스명: `govpress-api.service`
- Python 가상환경: `/home/wavel/GovPress_PDF_MD/.venv`
- 리버스 프록시: `caddy`
- 외부 노출: `cloudflared`

동작:

1. GitHub Actions가 SSH로 VPS에 접속
2. 서버의 GovPress 저장소를 `origin/web`으로 동기화
3. `.venv`에서 의존성 설치
4. `systemctl --user restart govpress-api.service`
5. 헬스체크 확인

워크플로:

- `.github/workflows/vps.yml`

필수 GitHub Secrets:

- `GOVPRESS_VPS_HOST`
- `GOVPRESS_VPS_USER`
- `GOVPRESS_VPS_SSH_KEY`

권장 GitHub Variables:

- `GOVPRESS_VPS_DEPLOY_DIR`
  예: `/home/ubuntu/GovPress_PDF_MD`
- `GOVPRESS_VPS_SERVICE`
  예: `govpress-api.service`
- `GOVPRESS_VPS_PORT`
  기본값: `22`
- `GOVPRESS_VPS_BRANCH`
  기본값: `web`
- `GOVPRESS_VPS_HEALTHCHECK_URL`
  기본값: `http://127.0.0.1:8013/health`

VPS 선행 조건:

- 서버에 GovPress 저장소가 이미 클론되어 있어야 함
- `.venv`가 이미 준비되어 있어야 함
- 배포 계정이 해당 디렉터리와 `.venv`를 직접 쓸 수 있어야 함
- `loginctl enable-linger <user>`가 이미 설정되어 있어야 함
- 배포 시 `XDG_RUNTIME_DIR=/run/user/<uid>` 환경에서 `systemctl --user`가 동작해야 함
- `deploy/vps/.env` 같은 런타임 파일은 서버에 미리 준비돼 있어야 함

최초 준비 예:

```bash
cd /home/wavel/GovPress_PDF_MD
git fetch origin
git checkout web
git reset --hard origin/web
./.venv/bin/pip install -r requirements.txt
./.venv/bin/pip install -U opendataloader-pdf
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user restart govpress-api.service
curl http://127.0.0.1:8013/health
```

주의:

- 이 자동화는 서버 체크아웃을 `origin/<branch>`로 강제 동기화합니다.
- 서버 작업 디렉터리에 수동 수정 파일이 있으면 덮어써집니다.
- user service가 멈췄을 때는 `systemctl --user status govpress-api.service`로 먼저 확인합니다.
