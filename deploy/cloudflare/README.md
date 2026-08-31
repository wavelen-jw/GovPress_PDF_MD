# 읽힘 Cloudflare Pages 수동 배포

이 디렉터리는 읽힘의 정적 웹만 Cloudflare Pages로 옮긴다. 변환 API는 계속
`https://api4.govpress.cloud`를 사용한다. 스크립트에는 cron, 파일 감시, push 트리거,
DNS 변경이 없다. 운영자가 명시적으로 명령을 실행할 때만 배포된다.

## 범위

- `/`: 읽힘 랜딩 페이지
- `/app/`: Expo 정적 웹 앱
- 벤치마크와 비교 페이지
- Cloudflare Web Analytics, 캐시 헤더, Pages 제한 사전 검증
- API 및 변환기는 배포 대상에서 제외

## 1. 권한 확인

Cloudflare API 토큰은 `Account / Cloudflare Pages / Edit` 권한과 계정 범위가
필요하다. 토큰 값은 파일이나 로그에 기록하지 않고 환경 변수로만 전달한다.

```bash
export CLOUDFLARE_ACCOUNT_ID='...'
export CLOUDFLARE_API_TOKEN='...'
deploy/cloudflare/pages_manual.sh auth
```

Wrangler OAuth 로그인이 이미 존재하면 API 토큰 대신 사용할 수 있다.

## 2. 빌드만 실행

```bash
deploy/cloudflare/pages_manual.sh build
```

산출물은 `/home/wavel/.govpress-pages/releases/<commit-sha>`에 불변 디렉터리로
저장된다. Pages의 무료 제한인 20,000개 파일과 파일당 25 MiB를 빌드 시 검사한다.

## 3. 프로젝트 생성과 미리보기

프로젝트 생성은 최초 한 번만 실행한다.

```bash
GOVPRESS_PAGES_CONFIRM_PROJECT=readhim-web \
  deploy/cloudflare/pages_manual.sh create-project

deploy/cloudflare/pages_manual.sh preview
```

미리보기 URL에서 `/`, `/app/`, HWP/HWPX/MD 업로드 UI와 API CORS를 확인한다.

API는 `readhim-web.pages.dev`와 그 1단계 미리보기 하위 도메인만 정규식으로 허용한다.
다른 Pages 프로젝트나 `pages.dev` 전체를 허용하지 않는다. 정규식은
`GOVPRESS_CORS_ALLOW_ORIGIN_REGEX`로 재정의하거나 빈 값으로 비활성화할 수 있다.

## 4. 운영 배포

운영 배포는 정확한 커밋 SHA 확인값이 일치해야 실행된다.

```bash
sha=$(git rev-parse HEAD)
GOVPRESS_PAGES_CONFIRM_SHA="$sha" \
  deploy/cloudflare/pages_manual.sh production
```

미리보기 검증 후 Cloudflare Pages 대시보드에서 `govpress.cloud`를 Custom Domain으로
연결한다. DNS 전환은 스크립트가 자동 수행하지 않는다. 문제가 있으면 Pages의 이전
production deployment로 rollback하고, 필요하면 기존 Tunnel DNS로 되돌린다.

## 비용 기준

현재 구성은 정적 Pages 자산만 사용하므로 무료 범위다. Pages Functions를 추가하면
Workers 요청 한도가 적용되지만 이 전환안에는 Functions가 없다. 실제 요금제와 제한은
변경될 수 있으므로 운영 전 Cloudflare 공식 가격표를 다시 확인한다.
