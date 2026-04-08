# CLAUDE.md

## 프로젝트 현재 기준

- 현재 주력 형태는 Windows 전용 데스크톱 앱보다 `웹 프론트 + FastAPI 백엔드 + worker` 구조입니다.
- 공개 프론트는 GitHub Pages, 공개 백엔드는 Cloudflare Tunnel 뒤의 `https://api.govpress.cloud`를 사용합니다.
- 이 로컬 기기 기준 `serverW`의 공개 주소는 `https://api4.govpress.cloud`입니다.

## UI 작업 규칙

- UI/UX 수정 중에는 기본적으로 GitHub에 바로 푸시하지 않습니다.
- 먼저 로컬 미리보기에서 확인합니다.
  - 로컬 정적 프리뷰 서버의 `/GovPress_PDF_MD/` 경로 사용
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
- 업로드 전 Turnstile 검증은 현재 사용하지 않습니다.
- 서버 측 업로드 rate limit과 TTL cleanup이 적용돼 있습니다.
- 공개 자료 서비스이므로 기밀성보다 가용성/남용 방지가 우선입니다.

## 변환 개선 원칙

- 변환 품질 개선은 `tests/problem/`의 문제 파일을 우선 기준으로 삼습니다.
- 문제 파일 작업 시에는 PDF 결과를 자동으로 정답으로 간주하지 않습니다.
- `.pdf`, `.hwpx`, 현재 변환 결과를 함께 보고 원문에 가장 가까운 Markdown을 정답으로 판단합니다.
- 정답 `.md`는 같은 문제 파일명으로 `tests/problem/` 아래에 직접 저장합니다.
- 규칙 수정 후에는 반드시 같은 문제 파일을 다시 변환해 정답 `.md`와 비교합니다.
- 남는 차이는 `파서 문제`, `후처리 문제`, `원문 자체 손상`으로 구분해서 기록합니다.
- HWPX는 `긴 병합 문단 + 뒤의 분리 문단`이 동시에 존재할 수 있으므로, 병합본 제거 규칙을 우선 점검합니다.
- 보도자료의 `참고`/부록은 본문과 별개로 보존해야 하며, 표와 요약표도 가능한 한 Markdown으로 복원합니다.

## 문제 파일 작업 절차

1. `tests/problem/`에서 대상 `.pdf`, `.hwpx`, 기존 `.md`를 확인합니다.
2. PDF/HWPX를 각각 변환하고, 원문과 출력 차이를 줄 단위로 비교합니다.
3. 둘 중 하나를 정답으로 고정하지 말고, 더 원문에 가까운 쪽을 부분적으로 채택합니다.
4. 정답 Markdown을 `tests/problem/<원본파일명>.md`로 갱신합니다.
5. 규칙 수정은 가능한 한 일반화해서 `src/markdown_postprocessor.py`, `src/parser_rules.py`, `src/hwpx_postprocessor.py`, `server/app/adapters/hwpx_converter.py`에 반영합니다.
6. 수정 후 동일 문제 파일로 재변환하여 정답 `.md`와 다시 비교합니다.
7. 사용자가 요청할 때만 커밋, 푸시, 운영 배포를 진행합니다.

## 현재 알려진 문제 파일 메모

- `tests/problem/260331 (국무회의 종료시) 2025년 공공데이터 제공 운영실태 평가결과 공개(공공데이터정책과).hwpx`
- 이 문서는 `참고` 부록과 표 보존이 중요합니다.
- HWPX 원문에는 일부 줄이 잘린 흔적이 있어, 예를 들어 `최근 3년간 우수 이상 등급 비중` 수치가 `(23년)`까지만 남아 있을 수 있습니다.
- 따라서 이 파일은 PDF/HWPX를 교차 확인하며 정답 `.md`를 관리해야 합니다.

## 운영 메모

- 공개 프론트:
  - `https://wavelen-jw.github.io/GovPress_PDF_MD`
- 공개 백엔드:
  - `https://api.govpress.cloud`
- WSL 운영 문서:
  - `deploy/wsl/README.md`
- 오늘 작업 상세 요약:
  - `docs/work-log-2026-03-30.md`
