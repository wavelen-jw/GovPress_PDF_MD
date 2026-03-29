# CLAUDE.md

## 프로젝트 현재 기준

- 현재 주력 형태는 Windows 전용 데스크톱 앱보다 `웹 프론트 + FastAPI 백엔드 + worker` 구조입니다.
- 공개 프론트는 GitHub Pages, 공개 백엔드는 Cloudflare Tunnel 뒤의 `https://api.govpress.cloud`를 사용합니다.

## UI 작업 규칙

- UI/UX 수정 중에는 기본적으로 GitHub에 바로 푸시하지 않습니다.
- 먼저 로컬 미리보기에서 확인합니다.
  - `http://172.25.164.35:8084/GovPress_PDF_MD/`
- 사용자가 요청할 때만 커밋, 푸시, GitHub Pages 배포를 진행합니다.

## 레이아웃 원칙

- 데스크톱: 편집기 + 미리보기 병렬 작업형
- 태블릿: 상하 분할 하이브리드
- 모바일: 리더형, 상단 `미리보기 / 편집` 전환 중심

## 웹 기본 설정

- 웹 기본 백엔드는 항상 `https://api.govpress.cloud`
- 웹에서는 저장된 API 키를 신뢰하지 않고, 현재 공개용 기본 API 키를 사용합니다.
- 모바일에서는 다크모드 버튼을 숨깁니다.

## 보안 구조

- 작업 접근은 `job_id + edit_token` 기반입니다.
- 공용 작업 목록 API는 제거된 상태입니다.
- 업로드 전 Turnstile 검증을 사용합니다.
- 서버 측 업로드 rate limit과 TTL cleanup이 적용돼 있습니다.
- 공개 자료 서비스이므로 기밀성보다 가용성/남용 방지가 우선입니다.

## 운영 메모

- 공개 프론트:
  - `https://wavelen-jw.github.io/GovPress_PDF_MD`
- 공개 백엔드:
  - `https://api.govpress.cloud`
- WSL 운영 문서:
  - `deploy/wsl/README.md`
- 오늘 작업 상세 요약:
  - `docs/work-log-2026-03-30.md`
