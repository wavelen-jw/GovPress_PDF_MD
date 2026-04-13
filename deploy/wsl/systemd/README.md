# systemd Autostart

이 디렉터리는 WSL Ubuntu 또는 Linux VPS에서 GovPress 스택을 자동 시작하기 위한 예시 서비스 파일입니다.

## 전제

- `systemd` 사용 가능
- Docker 설치 완료
- `deploy/wsl/.env` 준비 완료

## 설치

서비스 파일 복사:

```bash
sudo cp deploy/wsl/systemd/govpress-compose.service /etc/systemd/system/govpress-compose.service
sudo cp deploy/wsl/systemd/govpress-caddy.service /etc/systemd/system/govpress-caddy.service
sudo cp deploy/wsl/systemd/govpress-cloudflared.service /etc/systemd/system/govpress-cloudflared.service
```

필요하면 `WorkingDirectory`를 현재 경로에 맞게 수정합니다.

현재 기본값:

```text
/home/wavel/projects/GovPress_PDF_MD/deploy/wsl
```

이 서비스는 `deploy/wsl/bin/compose.sh`를 통해 Compose 실행 파일을 찾습니다.
우선순위:

- `docker-compose`
- `docker compose`
- `$HOME/.local/bin/docker-compose`

자동 시작 서비스는 `up -d`만 수행합니다.
이미지 재빌드가 필요할 때는 별도로 수동 실행합니다.

```bash
/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/bin/compose.sh up -d --build
```

## 활성화

```bash
sudo systemctl daemon-reload
sudo systemctl enable govpress-compose.service
sudo systemctl start govpress-compose.service
```

## 상태 확인

```bash
sudo systemctl status govpress-compose.service
/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/bin/compose.sh ps
```

## 중지

```bash
sudo systemctl stop govpress-compose.service
```

## VPS 이전

Linux VPS에서도 같은 파일을 거의 그대로 쓸 수 있습니다.

바꿀 가능성이 큰 값:

- `WorkingDirectory`
- Compose 실행 경로
