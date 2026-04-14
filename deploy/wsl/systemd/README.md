# systemd Autostart

이 디렉터리는 WSL Ubuntu 또는 Linux VPS에서 GovPress host-proxy 스택을 자동 시작하기 위한 서비스 파일입니다.

## 전제

- `systemd` 사용 가능
- Docker 설치 완료
- `deploy/wsl/.env` 준비 완료
- 운영 서버는 `host_proxy` 모드 사용

운영 원칙:

- compose는 `api/worker`만 관리합니다.
- `127.0.0.1:8080`은 `govpress-caddy.service`만 점유해야 합니다.
- 외부 공개는 `govpress-cloudflared.service`만 담당합니다.
- `govpress-cloudflared.service`는 반드시 `--config /dev/null`로 실행되어야 합니다.
- `/etc/systemd/system/cloudflared.service` 같은 레거시 cloudflared unit은 존재하면 안 됩니다.

## 설치

서비스 파일 복사:

```bash
DEPLOY_DIR=/home/wavel/GovPress_PDF_MD
HOME_DIR="${HOME:-$(getent passwd "$(id -u)" | cut -d: -f6)}"
sed -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" -e "s|__HOME_DIR__|$HOME_DIR|g" \
  deploy/wsl/systemd/govpress-compose.service | sudo tee /etc/systemd/system/govpress-compose.service >/dev/null
sed -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" -e "s|__HOME_DIR__|$HOME_DIR|g" \
  deploy/wsl/systemd/govpress-caddy.service | sudo tee /etc/systemd/system/govpress-caddy.service >/dev/null
sed -e "s|__DEPLOY_DIR__|$DEPLOY_DIR|g" -e "s|__HOME_DIR__|$HOME_DIR|g" \
  deploy/wsl/systemd/govpress-cloudflared.service | sudo tee /etc/systemd/system/govpress-cloudflared.service >/dev/null
```

필요하면 `WorkingDirectory`를 현재 경로에 맞게 수정합니다.

기본값:

```text
/home/wavel/GovPress_PDF_MD/deploy/wsl
```

이 서비스는 `deploy/wsl/bin/compose.sh`를 통해 Compose 실행 파일을 찾습니다.
우선순위:

- `docker-compose`
- `docker compose`
- `$HOME/.local/bin/docker-compose`

자동 시작 서비스는 `up -d`만 수행합니다.
이미지 재빌드가 필요할 때는 별도로 수동 실행합니다.

```bash
/home/wavel/GovPress_PDF_MD/deploy/wsl/bin/compose.sh up -d --build
```

## 활성화

```bash
sudo systemctl daemon-reload
sudo systemctl enable govpress-compose.service govpress-caddy.service govpress-cloudflared.service
sudo systemctl start govpress-compose.service govpress-caddy.service govpress-cloudflared.service
```

## 상태 확인

```bash
sudo systemctl status --no-pager govpress-compose.service govpress-caddy.service govpress-cloudflared.service
/home/wavel/GovPress_PDF_MD/deploy/wsl/bin/compose.sh ps
sudo lsof -iTCP:8080 -sTCP:LISTEN -n -P
curl -sS http://127.0.0.1:8013/health
curl -sS http://127.0.0.1:8080/health
```

정상 기준:

- `govpress-compose.service`는 `active (exited)` 또는 compose 갱신 직후 정상 종료
- `govpress-caddy.service`는 `python3 ... host_proxy.py`로 `active (running)`
- `govpress-cloudflared.service`는 token 기반 `cloudflared` 하나만 `active (running)`
- `8080` listener는 `python3 ... host_proxy.py`
- `docker-proxy`가 `8080`을 잡고 있으면 비정상

## 금지 상태

아래 상태는 즉시 정리해야 합니다.

- `/etc/systemd/system/cloudflared.service` 존재
- `~/.cloudflared/config.yml`을 읽는 별도 `cloudflared tunnel --config ... run` 프로세스 존재
- `docker-proxy`가 `127.0.0.1:8080`을 점유

확인:

```bash
systemctl list-unit-files | grep cloudflared
pgrep -af cloudflared
sudo lsof -iTCP:8080 -sTCP:LISTEN -n -P
```

복구:

```bash
sudo systemctl disable --now cloudflared.service || true
sudo rm -f /etc/systemd/system/cloudflared.service
sudo systemctl daemon-reload
sudo systemctl restart govpress-caddy.service
sudo systemctl restart govpress-cloudflared.service
```

## 중지

```bash
sudo systemctl stop govpress-cloudflared.service govpress-caddy.service govpress-compose.service
```

## VPS 이전

Linux VPS에서도 같은 파일을 거의 그대로 쓸 수 있습니다.

바꿀 가능성이 큰 값:

- `WorkingDirectory`
- Compose 실행 경로
