# VPS Auto Deploy

GitHub Actions에서 `web` 브랜치의 서버 관련 변경을 VPS에 자동 반영합니다.

동작:

1. GitHub Actions가 SSH로 VPS에 접속
2. 서버의 GovPress 저장소를 `origin/web`으로 동기화
3. `docker compose up -d --build` 실행
4. 로컬 헬스체크 확인

워크플로:

- `.github/workflows/vps.yml`

필수 GitHub Secrets:

- `GOVPRESS_VPS_HOST`
- `GOVPRESS_VPS_USER`
- `GOVPRESS_VPS_SSH_KEY`

권장 GitHub Variables:

- `GOVPRESS_VPS_DEPLOY_DIR`
  예: `/home/ubuntu/GovPress_PDF_MD`
- `GOVPRESS_VPS_PORT`
  기본값: `22`
- `GOVPRESS_VPS_BRANCH`
  기본값: `web`
- `GOVPRESS_VPS_COMPOSE_FILE`
  기본값: `<DEPLOY_DIR>/deploy/vps/docker-compose.yml`
- `GOVPRESS_VPS_HEALTHCHECK_URL`
  기본값: `http://127.0.0.1:8080/health`

VPS 선행 조건:

- 서버에 GovPress 저장소가 이미 클론되어 있어야 함
- 배포 계정이 `git fetch`, `git checkout`, `git reset --hard`, `docker compose`를 실행할 수 있어야 함
- `deploy/vps/.env` 같은 런타임 파일은 서버에 미리 준비돼 있어야 함

최초 준비 예:

```bash
cd /home/ubuntu/GovPress_PDF_MD
git fetch origin
git checkout web
docker compose -f deploy/vps/docker-compose.yml up -d --build
```

주의:

- 이 자동화는 서버 체크아웃을 `origin/<branch>`로 강제 동기화합니다.
- VPS 작업 디렉터리에 수동 수정 파일이 있으면 덮어써집니다.
- `deploy/vps` 경로와 compose 파일 위치가 다르면 GitHub Variable로 별도 지정해야 합니다.
