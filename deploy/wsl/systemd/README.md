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
```

필요하면 `WorkingDirectory`를 현재 경로에 맞게 수정합니다.

현재 기본값:

```text
/home/wavel/GovPress_PDF_MD/deploy/wsl
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
docker compose -f /home/wavel/GovPress_PDF_MD/deploy/wsl/docker-compose.yml ps
```

## 중지

```bash
sudo systemctl stop govpress-compose.service
```

## VPS 이전

Linux VPS에서도 같은 파일을 거의 그대로 쓸 수 있습니다.

바꿀 가능성이 큰 값:

- `WorkingDirectory`
- Docker 실행 경로
