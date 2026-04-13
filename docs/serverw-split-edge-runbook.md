# ServerW Split-Edge Runbook

이 문서는 `serverW`를 `serverH`와 같은 `split_edge` 구조로 전환할 때 참고하는 실행 지시서다.

목표:
- `api4.govpress.cloud`를 `compose(api/worker/caddy) + host-level cloudflared` 구조로 전환
- 외부 `https://api4.govpress.cloud/health`가 `200`이어야 함
- tunnel origin은 `http://127.0.0.1:8080`이어야 함
- `530 / 1033` 또는 `fetch failed` 원인을 제거

## 기준 정보

- repo: `/home/wavel/projects/GovPress_PDF_MD`
- branch: `web`
- tunnel id: `4390f5bd-3dbe-49f5-ab52-382de7670294`
- hostname: `api4.govpress.cloud`
- ssh hostname: `ssh-work.govpress.cloud`

## 작업 원칙

- unrelated 파일은 건드리지 않는다.
- UI 변경과 섞지 않는다.
- 구조 변경 커밋은 deploy/systemd/tunnel 관련 파일만 포함한다.
- `fetch failed`를 UI에서 회색 처리하지 않는다.

## 1. 현재 상태 점검

```bash
cd /home/wavel/projects/GovPress_PDF_MD
git status --short
/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/bin/compose.sh ps
curl -sS http://127.0.0.1:8080/health || true
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
systemctl status --no-pager govpress-compose.service || true
systemctl status --no-pager govpress-cloudflared.service || true
journalctl -u govpress-cloudflared.service -n 50 --no-pager || true
cloudflared tunnel info 4390f5bd-3dbe-49f5-ab52-382de7670294 || true
curl -L -sS -i https://api4.govpress.cloud/health || true
```

## 2. 저장소 파일 확인

아래 파일이 최신인지 먼저 확인한다.

- `deploy/wsl/docker-compose.yml`
- `deploy/wsl/systemd/govpress-compose.service`
- `deploy/wsl/systemd/govpress-cloudflared.service`
- `deploy/common/remote-deploy-cf.sh`
- `.github/workflows/vps.yml`
- `.github/workflows/_deploy-server-cf.yml`

조건:
- `deploy/wsl/docker-compose.yml`에는 `cloudflared` 서비스가 없어야 한다.
- `govpress-cloudflared.service`는 host-level tunnel용이어야 한다.

## 3. systemd 서비스 설치

```bash
sudo cp /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/systemd/govpress-compose.service /etc/systemd/system/govpress-compose.service
sudo cp /home/wavel/projects/GovPress_PDF_MD/deploy/wsl/systemd/govpress-cloudflared.service /etc/systemd/system/govpress-cloudflared.service
sudo systemctl daemon-reload
```

## 4. compose stack 정리

`cloudflared`는 컨테이너가 아니라 host-level systemd 서비스로 분리한다.

```bash
docker rm -f govpress-cloudflared || true
/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/bin/compose.sh up -d --remove-orphans api worker caddy
/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/bin/compose.sh ps
```

기대 상태:
- `govpress-api`
- `govpress-worker`
- `govpress-caddy`

만 떠 있어야 한다.

## 5. host-level cloudflared 기동

```bash
sudo systemctl enable govpress-cloudflared.service
sudo systemctl restart govpress-cloudflared.service
systemctl status --no-pager govpress-cloudflared.service
journalctl -u govpress-cloudflared.service -n 50 --no-pager
```

## 6. Cloudflare tunnel origin 확인 및 수정

`api4.govpress.cloud` origin은 반드시 아래 값이어야 한다.

- `http://127.0.0.1:8080`

잘못된 예:
- `http://caddy:8080`
- `http://127.0.0.1:8000`

Cloudflare Zero Trust에서 `api4.govpress.cloud` public hostname/service를 위 값으로 맞춘 뒤, 아래를 다시 실행한다.

```bash
sudo systemctl restart govpress-cloudflared.service
journalctl -u govpress-cloudflared.service -n 30 --no-pager
```

로그에서 `Updated to new configuration` 줄을 보고 실제 service URL을 확인한다.

## 7. stale connector 정리

tunnel에 예전 connector가 남아 있으면 edge가 오래된 origin으로도 트래픽을 보낼 수 있다.

```bash
cloudflared tunnel info 4390f5bd-3dbe-49f5-ab52-382de7670294
cloudflared tunnel cleanup --connector-id <old-connector-id> 4390f5bd-3dbe-49f5-ab52-382de7670294
cloudflared tunnel info 4390f5bd-3dbe-49f5-ab52-382de7670294
```

기준:
- 현재 host에서 막 뜬 connector만 남아야 한다.

## 8. 검증

```bash
curl -sS -i http://127.0.0.1:8080/health
curl -L -sS -i https://api4.govpress.cloud/health
journalctl -u govpress-cloudflared.service -n 30 --no-pager
cloudflared tunnel info 4390f5bd-3dbe-49f5-ab52-382de7670294
```

기대 결과:
- local `127.0.0.1:8080/health` -> `200`
- external `https://api4.govpress.cloud/health` -> `200`
- `govpress-cloudflared.service` active
- tunnel active connector 1개 이상
- `lookup caddy`, `127.0.0.1:8000`, `connection refused`, `1033`가 없어야 함

## 9. 결과 보고 형식

최종 결과에는 아래를 남긴다.

- root cause
- 실제 수정한 파일
- live systemd/compose 조치
- tunnel origin 값
- stale connector 정리 여부
- local/external health 결과

## 10. 커밋

성공 후 구조 변경만 커밋한다.

권장 메시지:

```text
Move serverW to split-edge tunnel
```
