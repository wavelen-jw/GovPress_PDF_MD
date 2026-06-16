# ServerN api5 Handoff (2026-06-16)

목적:
- 새 서버 `114.110.183.222:10022`를 `serverW`와 동일한 `host_proxy` 구조로 추가
- 공개 주소는 `https://api5.govpress.cloud`
- 이후 작업은 `serverV` 세션에서 이어서 진행

현재 상태:
- 로컬 repo `web`에서 아래 workflow 변경만 반영됨
  - `.github/workflows/_deploy-server.yml`
  - `.github/workflows/vps.yml`
- 변경 내용:
  - direct SSH reusable workflow가 `compose_file`, `deploy_mode`, `public_probe_url`, `run_policy_probe`를 받도록 확장됨
  - `deploy-n` job 추가
  - `converter-drift-smoke`, 실패 알림에 `serverN` 포함
- `git diff --check` 통과

중요 blocker:
- 네트워크/포트는 정상
- `ubuntu@114.110.183.222:10022`는 SSH handshake 성공
- 하지만 공개키 인증 거부:
  - `Permission denied (publickey,password,keyboard-interactive)`
  - 디버그상 클라이언트 key offer까지는 갔고 서버가 거절함
- 즉 `ubuntu` 계정의 `~/.ssh/authorized_keys` 내용 또는 권한/소유자 문제

서버V에서 먼저 할 일:
1. `ssh n` 별칭 추가
2. 새 서버 공개키 인증 문제 해결
3. 새 서버에 repo/bootstrap
4. Cloudflare Tunnel 신규 발급 + `api5.govpress.cloud -> http://127.0.0.1:8080`
5. GitHub repo secret/variable 등록
6. Actions 또는 수동 배포

`serverV`의 `~/.ssh/config`에 추가할 예시:

```sshconfig
Host n
    HostName 114.110.183.222
    User ubuntu
    Port 10022
    ServerAliveInterval 30
    ServerAliveCountMax 3
    StrictHostKeyChecking accept-new
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
```

새 서버에서 확인할 명령:

```bash
whoami
ls -ld ~ ~/.ssh ~/.ssh/authorized_keys
stat -c '%U %G %a %n' ~ ~/.ssh ~/.ssh/authorized_keys
grep -n 'govpress-manual' ~/.ssh/authorized_keys
```

권한 복구:

```bash
sudo chown -R ubuntu:ubuntu /home/ubuntu/.ssh
chmod 700 /home/ubuntu/.ssh
chmod 600 /home/ubuntu/.ssh/authorized_keys
grep -q 'govpress-manual' /home/ubuntu/.ssh/authorized_keys || printf '%s\n' 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFVDg/Ijog5ejIbokxC6qTRRR7qGStkdnUo3nOJpU1f9 govpress-manual' >> /home/ubuntu/.ssh/authorized_keys
```

로컬 공개키:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFVDg/Ijog5ejIbokxC6qTRRR7qGStkdnUo3nOJpU1f9 govpress-manual
```

GitHub repo에 추가할 secret:
- `GOVPRESS_N_HOST=114.110.183.222`
- `GOVPRESS_N_USER=ubuntu`
- `GOVPRESS_N_SSH_KEY=<serverV 또는 Actions에서 쓸 private key>`

GitHub repo에 추가할 variable:
- `GOVPRESS_N_PORT=10022`
- `GOVPRESS_N_DEPLOY_DIR=/home/ubuntu/projects/GovPress_PDF_MD`
- `GOVPRESS_N_BRANCH=web`
- `GOVPRESS_N_SERVICE=govpress-compose`
- `GOVPRESS_N_COMPOSE_FILE=deploy/wsl/docker-compose.host-proxy.yml`
- `GOVPRESS_N_HEALTHCHECK_URL=http://127.0.0.1:8080/health`

서버 bootstrap 목표 상태:
- repo: `/home/ubuntu/projects/GovPress_PDF_MD`
- branch: `web`
- deploy mode: `host_proxy`
- compose: `deploy/wsl/docker-compose.host-proxy.yml`
- systemd:
  - `govpress-compose.service`
  - `govpress-caddy.service`
  - `govpress-cloudflared.service`
  - `govpress-watchdog.timer`

배포 후 기대 검증:

```bash
curl -i http://127.0.0.1:8013/health
curl -i http://127.0.0.1:8080/health
curl -i https://api5.govpress.cloud/health
```

메모:
- 기존 `serverW`, `serverV` 설정은 건드리지 않음
- 새 Tunnel은 기존 `api4` tunnel과 분리해야 함
- 현재 repo에는 unrelated modified files가 있으므로 commit 시 workflow 2개만 좁게 포함하는 것이 안전함


## 완료 기록

2026-06-16 완료:

- serverV ~/.ssh/config에 Host n 추가 완료
- 신규 서버 SSH 공개키 인증 복구 완료
- 운영 계정: ubuntu
- repo: /home/ubuntu/projects/GovPress_PDF_MD
- branch/head: web / 5ff95c3
- deploy mode: host_proxy
- systemd active:
  - govpress-compose.service
  - govpress-caddy.service
  - govpress-cloudflared.service
  - govpress-watchdog.timer
- GitHub GOVPRESS_N_* secret/variable 등록 완료
- Cloudflare Tunnel:
  - name: serverN-api5
  - id: 869128a3-0251-4293-acdc-ca6c76e9e387
  - DNS: api5.govpress.cloud -> 869128a3-0251-4293-acdc-ca6c76e9e387.cfargotunnel.com
- 검증:
  - http://127.0.0.1:8013/health -> 200
  - http://127.0.0.1:8080/health -> 200
  - https://api5.govpress.cloud/health -> 200

운영 메모:

- Cloudflare API setup token은 서버나 repo에 저장하지 않음. 작업 후 Cloudflare Dashboard에서 revoke 필요.
- N 서버에는 tunnel connector token만 deploy/wsl/.env에 저장됨.
- 웹/앱 서버 설정에는 서버N / https://api5.govpress.cloud 를 추가함.

2026-06-16 추가 복구:

- GitHub Actions 직접 배포 경로가 plain `docker`를 호출하므로 `ubuntu`를 `docker` 그룹에 추가함.
- `deploy/wsl/data/storage`가 root 소유로 생성되어 배포 스크립트의 cache marker 갱신이 실패하던 문제를 `ubuntu:ubuntu` 소유권으로 복구함.
- N 서버에서 `deploy/common/remote-deploy-cf.sh`를 host_proxy 설정으로 직접 실행해 `deploy-complete` 확인.
- 최종 검증:
  - http://127.0.0.1:8013/health -> 200
  - http://127.0.0.1:8080/health -> 200
  - https://api5.govpress.cloud/health -> 200

2026-06-16 SSH 보안 강화:

- Direct SSH `10022/tcp`는 UFW allowlist로 제한함.
  - `117.111.0.0/16`
  - `49.168.0.0/16`
  - `175.121.0.0/16`
  - `211.235.0.0/16`
  - 그 외 `10022/tcp`는 deny
- SSH hardening:
  - `PasswordAuthentication no`
  - `KbdInteractiveAuthentication no`
  - `PubkeyAuthentication yes`
  - `PermitRootLogin no`
  - `AllowUsers ubuntu`
  - `MaxAuthTries 3`
- Actions/운영 배포용 Cloudflare SSH 경로 추가:
  - hostname: `ssh-n.govpress.cloud`
  - tunnel: `govpress-n-ssh`
  - id: `6a651bed-1c09-49ad-bfae-5e81dcfffc36`
  - origin: `ssh://127.0.0.1:10022`
  - user service: `cloudflared-govpress-n-ssh.service`
- serverV의 `ssh n` alias는 `ssh-n.govpress.cloud` Cloudflare SSH 경유로 전환함.
- GitHub Actions의 serverN deploy/smoke 경로도 direct SSH에서 Cloudflare SSH로 전환함.
- 검증:
  - `ssh n` -> 성공
  - direct `114.110.183.222:10022` from serverV -> timeout
  - `https://api5.govpress.cloud/health` -> 200

