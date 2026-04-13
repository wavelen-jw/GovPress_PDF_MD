# Release Notes (2026-04-13)

이 문서는 2026-04-13에 진행한 GovPress 운영 장애 대응과 배포 구조 변경을 릴리즈 노트 형태로 요약한 메모다.

## 한 줄 요약

`serverH`와 `serverW`의 edge 경로를 안정화했고, 원격배포와 UI 상태 표시를 함께 정리했다.

## 배경

오늘 운영 중 아래 문제가 반복됐다.

- `serverH`가 잠깐 정상으로 돌아왔다가 다시 `fetch failed`로 떨어짐
- `serverW` 원격배포가 Cloudflare SSH 구간에서 반복 실패
- UI에서 서버 상태와 정책브리핑 제공기관 상태가 섞여 보여 원인 판단이 어려움

## 무엇이 바뀌었나

### 1. WSL edge 구조를 `host_proxy` 기준으로 정리했다

적용 대상:

- `serverH`
- `serverW`

핵심 변경:

- `cloudflared`는 host-level `systemd` 서비스로 유지
- `127.0.0.1:8080`은 host-level proxy가 직접 유지
- compose는 `api/worker`만 관리
- API는 `127.0.0.1:8013`으로만 publish

의미:

- 기존 `cloudflared -> Docker publish 8080 -> compose caddy -> api` 경로 의존을 제거
- `connection refused`로 인한 간헐적 빨간불 재발 가능성을 낮춤

관련 파일:

- [.github/workflows/vps.yml](/home/wavel/projects/GovPress_PDF_MD/.github/workflows/vps.yml:1)
- [deploy/common/remote-deploy-cf.sh](/home/wavel/projects/GovPress_PDF_MD/deploy/common/remote-deploy-cf.sh:1)
- [deploy/wsl/docker-compose.host-proxy.yml](/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/docker-compose.host-proxy.yml:1)
- [deploy/wsl/bin/host_proxy.py](/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/bin/host_proxy.py:1)
- [deploy/wsl/systemd/govpress-caddy.service](/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/systemd/govpress-caddy.service:1)
- [deploy/wsl/apply-host-proxy.sh](/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/apply-host-proxy.sh:1)

### 2. Cloudflare Access / tunnel 경로를 바로잡았다

`serverW`는 두 문제가 겹쳐 있었다.

- `ssh-work.govpress.cloud`가 `ssh-h` Access 앱으로 잘못 매칭됨
- W tunnel SSH ingress가 불필요하게 `host.docker.internal:22022`를 타고 있었음

조치:

- `ssh-work.govpress.cloud` 전용 Access 앱으로 분리
- serverW tunnel SSH ingress를 `ssh://127.0.0.1:22022`로 정리

의미:

- GitHub Actions 원격배포가 다시 `serverW`까지 통과 가능해짐

### 3. 원격배포 방식을 더 안정적으로 바꿨다

GitHub Actions의 WSL 원격배포는 `long-running ssh` 대신:

- 원격 스크립트 detached 실행
- 상태 파일 polling

구조로 바꿨다.

의미:

- Cloudflare Access SSH 세션이 길게 붙어 있다가 흔들리는 문제를 줄임
- `serverH`, `serverW`, `serverV` 공통 배포 안정성 개선

관련 파일:

- [.github/workflows/_deploy-server-cf.yml](/home/wavel/projects/GovPress_PDF_MD/.github/workflows/_deploy-server-cf.yml:1)
- [deploy/common/remote-deploy-cf.sh](/home/wavel/projects/GovPress_PDF_MD/deploy/common/remote-deploy-cf.sh:1)
- [deploy/wsl/install-remote-deploy-sudoers.sh](/home/wavel/projects/GovPress_PDF_MD/deploy/wsl/install-remote-deploy-sudoers.sh:1)

### 4. 정책브리핑 cache reset 범위를 줄였다

문제:

- 배포 때 `policy_briefing_catalog/*.json`까지 같이 지워져 과거 날짜 첫 조회가 cold-hit이 됨
- `serverH`는 이 직후 특정 날짜 조회에서 일시 `502`가 발생했고, 사용자는 이를 서버 장애처럼 보게 됨

조치:

- deploy 시 문서 변환 cache만 초기화
- 날짜별 정책브리핑 catalog cache는 보존

의미:

- 배포 직후 정책브리핑 과거 날짜 조회 품질 저하를 줄임

관련 파일:

- [deploy/common/remote-deploy-cf.sh](/home/wavel/projects/GovPress_PDF_MD/deploy/common/remote-deploy-cf.sh:1)

### 5. UI에서 상태 의미를 분리했다

변경:

- 정책브리핑 모달에 `서버 연결 상태 (/health)`와 `서버별 정책브리핑 조회 상태`를 분리 표시
- 서버 설정 모달에 `/health` 기준이라는 설명 추가

의미:

- 서버 자체 장애와 정책브리핑 upstream 지연을 사용자가 구분 가능

관련 파일:

- [mobile/App.tsx](/home/wavel/projects/GovPress_PDF_MD/mobile/App.tsx:1)
- [mobile/src/components/SettingsModal.tsx](/home/wavel/projects/GovPress_PDF_MD/mobile/src/components/SettingsModal.tsx:1)
- [mobile/src/constants.ts](/home/wavel/projects/GovPress_PDF_MD/mobile/src/constants.ts:1)

## 확인된 결과

최종적으로 확인한 상태:

- `serverH` 공개 `/health` 정상
- `serverW` 공개 `/health` 정상
- `serverV` 원격배포 정상
- GitHub Actions 원격배포가 `H/W/V` 전체 성공
- 정책브리핑 상태 UI가 서버 상태와 분리됨

## 대표 커밋

오늘 작업에서 핵심이 된 커밋:

- `fe24743` Preserve policy briefing catalog across deploys
- `0086864` Separate server and policy briefing status UI

이전 구조 변경과 원격배포 안정화 커밋도 같은 흐름에 포함된다.

## 남은 권장 작업

- Cloudflare 관리용 임시 API token 폐기
- Cloudflare Access / tunnel 구성을 별도 runbook으로 더 명확히 문서화
- 운영 UI에서 `/health` 재검사 버튼 또는 자동 재검사 주기 추가 검토
