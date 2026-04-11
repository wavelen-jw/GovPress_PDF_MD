# Policy Briefing QC Status (2026-04-12)

이 문서는 오늘 기준으로 정책브리핑 HWPX 품질개선 자동화가 어디까지 구축됐는지,  
당신 입장에서 무엇이 달라졌는지, 앞으로 무엇을 하면 되는지를 정리한 운영 메모입니다.

## 한 줄 요약

이제 정책브리핑 문서를 서비스 레포에서 가져와 `gov-md-converter` QC로 넘기고,  
실패 샘플을 자동 분류하고, 수정 힌트/패치 초안/이슈/대시보드/Telegram 알림까지 연결할 수 있습니다.

## 오늘 바뀐 것

### 1. 두 레포 역할이 실제 도구 기준으로 분리됐다

- `gov-md-converter`
  - 변환 엔진과 QC의 source of truth
  - 규칙 수정, regression, triage, `suggest-fix`, `fix-plan`, `auto-patch-draft` 담당
- `GovPress_PDF_MD`
  - 정책브리핑 원문 수집
  - private 엔진 연동
  - 운영용 QC 파이프라인 실행
  - 대시보드, 이슈, Telegram 알림 담당

즉, 품질 문제를 고치는 장소는 `gov-md-converter`이고,  
운영에서 문제를 발견하고 큐를 만드는 장소는 `GovPress_PDF_MD`입니다.

### 2. 정책브리핑 원문을 QC 입력으로 바로 내보낼 수 있게 됐다

추가된 주요 명령:

```bash
python3 scripts/export_policy_briefings_for_qc.py ...
python3 scripts/run_policy_briefing_qc_pipeline.py ...
```

이제 정책브리핑 API에서 가져온 HWPX/PDF를 기사별로 저장하고, 필요하면 곧바로 `gov-md-converter`의 scratch sample로 scaffold할 수 있습니다.

### 3. QC 파이프라인이 한 번에 이어진다

`run_policy_briefing_qc_pipeline.py`는 아래를 순서대로 실행합니다.

1. 정책브리핑 원문 export
2. `gov-md-converter` sample scaffold
3. `regression`
4. `triage`
5. `suggest-fix`
6. `patch-template`
7. `fix-plan`
8. `apply-fix-hint`
9. `auto-patch-draft`

즉, 사람이 문서를 손으로 고르고 명령을 매번 이어칠 필요가 크게 줄었습니다.

### 4. 실패 판정과 요약이 자동화됐다

추가된 주요 명령:

```bash
python3 scripts/evaluate_policy_briefing_qc_report.py ...
python3 scripts/build_policy_briefing_qc_issue.py ...
```

이제 `pipeline_report.json`을 기준으로:

- 실패 여부를 non-zero exit code로 판정
- Markdown 요약 생성
- GitHub issue payload 생성

까지 자동으로 처리됩니다.

### 5. GitHub Actions 모니터링이 생겼다

워크플로:

- [.github/workflows/policy-briefing-qc-monitor.yml](</home/wavel/projects/GovPress_PDF_MD/.github/workflows/policy-briefing-qc-monitor.yml:1>)

동작:

- 매일 한국 시간 13:15 실행
- private `gov-md-converter` checkout
- QC 파이프라인 실행
- 결과 평가
- artifact 업로드
- 실패 시 issue 생성 또는 갱신
- 실패 시 Telegram 알림 전송 가능

### 6. 대시보드가 생겼다

추가된 주요 명령:

```bash
python3 scripts/build_policy_briefing_qc_dashboard.py ...
```

산출물:

- `exports/policy_briefing_qc/dashboard/index.html`
- `exports/policy_briefing_qc/dashboard/dashboard.json`
- 서버 URL
  - `/v1/policy-briefings/qc/dashboard`
  - `/v1/policy-briefings/qc/dashboard.json`

볼 수 있는 것:

- 최근 실행 현황
- review-required 수
- defect class 상위 빈도
- 반복되는 sample
- 최근 proposal / draft 추이

### 7. Telegram 알림이 연결됐다

추가된 주요 명령:

```bash
python3 scripts/send_policy_briefing_qc_telegram.py ...
```

알림 내용:

- 날짜
- exported 수
- review-required 수
- 상위 failing sample
- 상위 fix target
- Actions run 링크
- issue 링크

### 8. GitHub issue가 “수정 착수 문서” 수준으로 강화됐다

이제 생성되는 issue에는 단순 실패 사실만이 아니라 아래가 같이 들어갑니다.

- regression failure sample
- flagged slice preview
- secondary signals (`pdf_ratio`, `runtime_error`, `rule_path` 등)
- `suggest-fix` 기반 수정 대상 파일
- `fix-plan` 기반 검색 패턴과 inspect 명령
- `apply-fix-hint` 기반 copy-paste command sequence
- `auto-patch-draft` 기반 첫 패치 방향과 회귀 명령

즉, issue 하나만 열어도 바로 `gov-md-converter`에서 수정 작업을 시작할 수 있습니다.

### 9. `gov-md-converter` QC 신호가 조금 더 구조적으로 강화됐다

추가된 신호:

- `boundary_order`
- `rule_path`

의미:

- `appendix/contact/reference` 경계 순서를 더 잘 추적
- 어떤 변환 경로가 선택됐는지 secondary signal로 남김

이 신호는 issue, dashboard, Telegram 요약의 설명력을 높입니다.

## 당신 입장에서 지금 달라진 점

이전에는:

- 변환 결과를 열어보고
- 직접 실패 샘플을 정하고
- 수동으로 golden을 만들고
- 문제를 사람 머리로 묶고
- 다음 수정 방향을 직접 떠올려야 했습니다.

지금은:

- 정책브리핑 원문을 바로 QC로 넘길 수 있고
- 실패 샘플이 자동으로 review queue에 모이고
- defect class별 수정 파일/명령/패치 방향이 자동 제안되며
- 실패가 issue와 Telegram으로 자동 통지되고
- 누적 상태를 dashboard로 볼 수 있습니다.

즉, 당신이 직접 해야 하는 일은 “결과를 모두 수작업으로 정리하는 것”에서  
“정말 수정 가치가 있는 결함을 보고 승인/수정 방향을 결정하는 것” 쪽으로 줄었습니다.

## 이미 끝난 설정

오늘 기준으로 다음은 이미 반영됐습니다.

- 로컬 WSL 운영용 `deploy/wsl/.env`에 Telegram 환경변수 반영
- GitHub repository secret 반영
  - `TELEGRAM_BOT_TOKEN`
  - `TELEGRAM_CHAT_ID`
- Telegram 테스트 메시지 실제 전송 확인
- GitHub Actions workflow 추가
- dashboard / issue / Telegram / monitor shell script 연결

## 이제 어떻게 쓰면 되는가

### 가장 기본적인 운영 흐름

```bash
python3 scripts/run_policy_briefing_qc_pipeline.py \
  --date 2026-04-12 \
  --output-root exports/policy_briefing_qc \
  --gov-md-converter-root ../gov-md-converter \
  --qc-root tests/manual_samples/policy_briefings
```

그 다음 평가:

```bash
python3 scripts/evaluate_policy_briefing_qc_report.py \
  exports/policy_briefing_qc/2026-04-12/pipeline_report.json \
  --summary-markdown exports/policy_briefing_qc/2026-04-12/qc_summary.md
```

dashboard 갱신:

```bash
python3 scripts/build_policy_briefing_qc_dashboard.py \
  --root exports/policy_briefing_qc \
  --output-html exports/policy_briefing_qc/dashboard/index.html \
  --output-json exports/policy_briefing_qc/dashboard/dashboard.json
```

Telegram 메시지 미리보기:

```bash
python3 scripts/send_policy_briefing_qc_telegram.py \
  exports/policy_briefing_qc/2026-04-12/pipeline_report.json \
  --print-only
```

### cron에서 돌릴 때

```bash
GOVPRESS_POLICY_BRIEFING_SERVICE_KEY=... \
GOV_MD_CONVERTER_ROOT=../gov-md-converter \
OUTPUT_ROOT=exports/policy_briefing_qc \
QC_ROOT=tests/manual_samples/policy_briefings \
bash scripts/run_policy_briefing_qc_monitor.sh 2026-04-12
```

### GitHub Actions에서 돌릴 때

수동 실행 또는 schedule로 `.github/workflows/policy-briefing-qc-monitor.yml`을 사용하면 됩니다.

## 추가로 당신이 해야 할 일

### 꼭 해야 하는 것

1. `GOVPRESS_POLICY_BRIEFING_SERVICE_KEY`가 Actions/운영 환경에 정상 설정되어 있는지 확인
2. private `gov-md-converter` checkout용 secret `GOV_MD_CONVERTER_REPO_TOKEN`이 유효한지 확인
3. dashboard를 실제 어디서 볼지 결정
   - artifact만 볼지
   - 별도 정적 호스팅을 붙일지
4. `gov-md-converter` 수정 담당 흐름을 정하기
   - issue만 보고 수동 수정할지
   - AI에게 issue를 읽히고 바로 `hwpx-md-qc` skill로 수정을 시킬지

### 강하게 권장하는 것

1. Telegram bot token 회전
   - 오늘 대화에 토큰이 평문으로 노출됐기 때문
2. `deploy/vps/.env`에도 Telegram 값 반영 여부 결정
   - WSL 외 운영 서버에서도 같은 알림을 쓸지 선택 필요
3. dashboard 공개 범위 결정
   - 내부 전용이면 artifact/서버 파일로 충분
   - 외부 접속이 필요하면 정적 publish 경로 필요

### 아직 남아 있는 선택 사항

1. GitHub issue 대신 Slack/Discord도 병행할지
2. dashboard를 단순 정적 파일로 둘지, pages나 내부 서버에 게시할지
3. review-required 발생 시 자동 patch draft까지 더 밀어붙일지
4. curated sample 승격 기준을 어디까지 자동화할지

## 추천 운영 방식

가장 현실적인 방식은 다음입니다.

1. 매일 13:15 KST에 workflow 실행
2. Telegram 알림으로 review-required 여부 확인
3. issue가 생기면 그 issue를 기준으로 `gov-md-converter` 수정 착수
4. 수정 후 `gov-md-converter`에서 regression 통과
5. 필요한 경우만 `promote-sample`
6. dashboard로 반복 결함 추세 확인

## 지금 기준으로 기대할 수 있는 효과

- 사람의 “문서 고르기 / 실패 묶기 / 수정 방향 정리” 부담 감소
- 복잡한 표/appendix/contact 전환 문제의 반복 탐지 용이
- 운영에서 새로 들어온 정책브리핑 문서를 regression-like 흐름에 편입 가능
- 문제 발생 시 Telegram + issue + dashboard로 동시에 관측 가능

## 참고 파일

- [README.md](/home/wavel/projects/GovPress_PDF_MD/README.md:1)
- [policy-briefing-qc-monitor.yml](/home/wavel/projects/GovPress_PDF_MD/.github/workflows/policy-briefing-qc-monitor.yml:1)
- [run_policy_briefing_qc_pipeline.py](/home/wavel/projects/GovPress_PDF_MD/scripts/run_policy_briefing_qc_pipeline.py:1)
- [run_policy_briefing_qc_monitor.sh](/home/wavel/projects/GovPress_PDF_MD/scripts/run_policy_briefing_qc_monitor.sh:1)
- [build_policy_briefing_qc_dashboard.py](/home/wavel/projects/GovPress_PDF_MD/scripts/build_policy_briefing_qc_dashboard.py:1)
- [send_policy_briefing_qc_telegram.py](/home/wavel/projects/GovPress_PDF_MD/scripts/send_policy_briefing_qc_telegram.py:1)
- [build_policy_briefing_qc_issue.py](/home/wavel/projects/GovPress_PDF_MD/scripts/build_policy_briefing_qc_issue.py:1)
- [run_hwpx_qc.py](/home/wavel/projects/gov-md-converter/scripts/run_hwpx_qc.py:1)
- [hwpx-md-qc skill](/home/wavel/projects/gov-md-converter/.agents/skills/hwpx-md-qc/SKILL.md:1)
