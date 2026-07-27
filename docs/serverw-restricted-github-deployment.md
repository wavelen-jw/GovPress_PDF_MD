# serverW GitHub 제한 환경 배포

## 운영 전제

serverW에서는 회사 네트워크 정책으로 `https://github.com` 직접 접속이
차단되어 있다. 일시적인 TLS 장애로 취급하지 않는다.

- serverW에서 `git fetch`, `git pull`, `pip install git+https://github.com/...`
  을 실행하는 배포 경로를 사용하지 않는다.
- IP 강제 지정, TLS 검증 해제, 임의 프록시 또는 서버용 GitHub SSH 키
  추가로 정책을 우회하지 않는다.
- GitHub Actions runner와 Cloudflare SSH는 정상적으로 사용할 수 있다.
- serverW에서 `api.github.com` 아카이브 API는 현재 허용되어 있다.

## 표준 배포 경로

변환기 릴리스는 기존 `web` 브랜치 push 배포를 그대로 사용한다.
serverW에만 offline source transfer를 적용한다.

1. Actions runner가 serverW 배포 디렉터리의 현재 Git HEAD를 Cloudflare
   SSH로 읽는다.
2. runner가 현재 HEAD부터 배포 대상 `github.sha`까지의 증분 Git bundle을
   만든다.
3. bundle을 Cloudflare SSH로 serverW의 `/tmp`에 전송한다.
4. `remote-deploy-cf.sh`가 로컬 bundle에서 정확한 대상 SHA를 fetch하고
   detached checkout한다.
5. serverW의 `github.com` probe가 실패하면 변환기 Git spec을
   `api.github.com/repos/<owner>/<repo>/tarball/<ref>` 아카이브로 변환한다.
6. Docker build는 `.deploy-artifacts`에 저장된 로컬 tarball을 설치한다.
7. 기존 `gov-md-converter` 보조 소스 디렉터리는 아카이브 내용으로
   동기화하되 `.git`과 `exports`는 보존한다.

관련 구현:

- `.github/workflows/vps.yml`
  - serverW에만 `transfer_service_bundle: "true"` 설정
- `.github/workflows/_deploy-server-cf.yml`
  - 원격 HEAD 조회, 증분 bundle 생성 및 SCP
- `deploy/common/remote-deploy-cf.sh`
  - bundle 우선 fetch와 GitHub API archive fallback
- `deploy/common/materialize-github-spec.py`
  - Git spec 파싱과 API archive 다운로드
- `deploy/common/sync-source-archive.py`
  - 보조 소스 동기화
- `deploy/wsl/Dockerfile`
  - 로컬 배포 artifact 설치

serverV와 serverN은 직접 GitHub fetch가 가능하므로 bundle 전달을 사용하지
않는다. serverW 제약을 공통 경로에 강제해 다른 서버를 변경하지 않는다.

## 인증 정보

- 정상 릴리스에서 새 GitHub 로그인을 요구하지 않는다.
- Actions checkout은 workflow의 `GITHUB_TOKEN`을 사용한다.
- 변환기 archive가 인증을 요구하면 기존
  `GOVPRESS_CONVERTER_SPEC`의 토큰을 API 요청에만 사용한다.
- 토큰은 URL이나 로그에 출력하지 않는다.
- GitHub 토큰과 Cloudflare Access/Tunnel 토큰은 별개다.
- Cloudflare 토큰을 GitHub 연결 문제의 해결책으로 재발급하지 않는다.

API archive에서 `401` 또는 `403`이 발생할 때만 GitHub 토큰의 만료와
repository read 권한을 확인한다.

## 실행

일반 변환기 릴리스는 `govpress-converter-deploy` 스킬을 사용한다.

```bash
python3 /home/ubuntu/.codex/skills/govpress-converter-deploy/scripts/deploy.py vX.Y.Z
```

스크립트가 `deploy/converter.version`을 변경하고 `web` 브랜치에 push하면
`vps.yml`이 serverW offline 전달을 자동으로 수행한다. serverW에 접속해
수동 `git pull` 또는 수동 converter 설치를 하지 않는다.

## 성공 조건

아래 조건이 모두 만족되어야 배포 성공이다.

1. Actions의 serverW deploy job 성공
2. `https://api4.govpress.cloud/health`가 HTTP 200
3. `converters.govpress-hwpx-md.available`이 `true`
4. runtime converter version이 `deploy/converter.version`과 일치
5. Converter Drift Smoke 성공
6. Policy Briefing Import Smoke 성공

```bash
curl -sS --connect-timeout 5 --max-time 20 \
  https://api4.govpress.cloud/health
```

## 장애 판정

- `github.com` TLS/timeout 실패:
  알려진 정책 제약이다. retry나 토큰 재발급 대신 bundle/API archive
  경로가 활성화됐는지 확인한다.
- `Read remote service revision` 실패:
  serverW 배포 디렉터리가 Git 저장소인지, Cloudflare SSH 사용자가 해당
  디렉터리를 읽을 수 있는지 확인한다.
- `Transfer service revision bundle` 실패:
  원격 HEAD가 runner checkout의 64-commit 이력 안에 있는지와 SCP 경로를
  확인한다.
- API archive `401`/`403`:
  `GOVPRESS_CONVERTER_SPEC` 토큰의 유효성과 repository read 권한을
  확인한다.
- API archive timeout:
  `api.github.com` 허용 정책을 확인한다. 허용되지 않으면 runner가 변환기
  archive까지 SCP하는 별도 변경이 필요하다.
- health version mismatch:
  성공으로 처리하지 말고 Docker build의 local install spec과 runtime
  module path를 확인한다.

## 변경 금지

- serverW의 `transfer_service_bundle: "true"` 제거
- serverW에서 직접 `origin` fetch를 필수 경로로 복원
- `github.com` 실패를 무제한 retry로 가리기
- TLS 검증 비활성화
- 배포 토큰 또는 converter spec을 Actions 로그에 출력
- serverV/serverN에 serverW 전용 bundle 전달을 무조건 적용
