# 읽힘

정부문서가 막힌 곳에서, 사람과 AI 모두 통하게 한다.

- 서비스 주소: `https://wavelen-jw.github.io/GovPress_PDF_MD`

![읽힘 랜딩 1페이지](assets/landing-section-1.png)

## 정부문서 포맷의 현실

형식은 달라도 결과는 같지 않습니다.  
정부 문서를 그대로 다루면, 사람도 읽기 어렵고 AI에 넣어도 맥락이 쉽게 무너집니다.

- `HWPX`는 내부 구조가 복잡해서 바로 다루기 어렵습니다.
- 제공기관 `HTML API`는 태그와 공백 노이즈가 많아 입력이 지저분해지기 쉽습니다.
- 기존 PDF 변환 결과는 표, 문단, 참고자료가 중간에 손실될 수 있습니다.

![읽힘 랜딩 2페이지](assets/landing-section-2.png)

## 읽힘이면 다르다

같은 문서라도, 읽히는 구조로 바꾸면 결과가 달라집니다.

읽힘은 문서를 단순 텍스트로만 바꾸지 않고, 사람이 다시 읽고 수정할 수 있으며 AI에도 바로 넣기 쉬운 Markdown으로 정리합니다.

- 제목, 문단, 목록 흐름을 유지합니다.
- 표와 참고 블록을 읽을 수 있는 형태로 복원합니다.
- 사람이 보는 화면과 AI 입력 모두를 고려해 정리합니다.

![읽힘 랜딩 3페이지](assets/landing-section-3.png)

## 핵심 흐름

`HWPX / PDF / HTML API` → `Markdown`

## 할 수 있는 일

- PDF/HWPX 보도자료를 Markdown으로 변환
- Markdown을 다시 열어 수정하고 미리보기로 확인
- 정책브리핑 보도자료 목록을 불러와 바로 열기
- Markdown 파일로 저장, 복사, 공유

![읽힘 랜딩 핵심 지표](assets/landing-section-4.png)

## 사용하는 방법

1. 서비스에 접속합니다.
2. `파일 열기`로 PDF, HWPX, Markdown 파일을 엽니다.
3. 또는 `정책브리핑` 목록에서 보도자료를 불러옵니다.
4. 변환 결과를 확인하고 필요한 부분을 수정합니다.
5. Markdown 파일로 저장하거나 복사합니다.

## 운영 QC 내보내기

오늘 작업 기준 운영 정리는 아래 문서에 따로 정리했습니다.

- [docs/policy-briefing-qc-status-2026-04-12.md](/home/wavel/projects/GovPress_PDF_MD/docs/policy-briefing-qc-status-2026-04-12.md:1)
- [docs/release-notes-2026-04-13-edge-stabilization.md](/home/wavel/projects/GovPress_PDF_MD/docs/release-notes-2026-04-13-edge-stabilization.md:1)

운영 중 발견한 정책브리핑 원문을 `gov-md-converter` QC 코퍼스로 넘기려면 서비스 레포에서 원문을 export한 뒤 private 엔진 레포로 scaffold하면 됩니다.
현재 경계는 아래처럼 나뉩니다.

- `GovPress_PDF_MD`: 정책브리핑 export, 운영 storage bridge, OpenClaw 운영 래퍼
- `gov-md-converter`: 범용 QC 파이프라인, dashboard, issue payload, Telegram 요약, 로컬 corpus QC

원문만 export:

```bash
python3 scripts/export_policy_briefings_for_qc.py \
  --date 2026-04-09 \
  --output-root exports/policy_briefing_qc \
  --limit 5
```

export와 동시에 `gov-md-converter` scratch 샘플 생성:

```bash
python3 scripts/export_policy_briefings_for_qc.py \
  --date 2026-04-09 \
  --output-root exports/policy_briefing_qc \
  --gov-md-converter-root ../gov-md-converter \
  --qc-root tests/manual_samples/policy_briefings
```

이 스크립트는 각 기사별로 `source.hwpx`, `source.pdf`, `metadata.json`을 만들고, 필요하면 `gov-md-converter/scripts/run_hwpx_qc.py scaffold-local ...`까지 호출합니다.

export부터 QC 분석 산출물까지 한 번에 돌리려면 현재는 `gov-md-converter`에서 파이프라인을 실행합니다.
먼저 이 레포에서 원문을 export하고:

```bash
python3 scripts/export_policy_briefings_for_qc.py \
  --date 2026-04-09 \
  --output-root exports/policy_briefing_qc \
  --gov-md-converter-root ../gov-md-converter \
  --qc-root tests/manual_samples/policy_briefings
```

그 다음 `gov-md-converter`에서 QC 후속 단계를 실행합니다.

```bash
cd ../gov-md-converter
python3 scripts/evaluate_policy_briefing_qc_report.py \
  ../GovPress_PDF_MD/exports/policy_briefing_qc/2026-04-09/pipeline_report.json \
  --summary-markdown ../GovPress_PDF_MD/exports/policy_briefing_qc/2026-04-09/qc_summary.md
```

정책브리핑 export와 QC 후속 실행을 한 번에 묶는 orchestration은 현재 서비스 레포 어댑터에서 제공하지만, 범용 QC CLI의 기준 구현과 유지보수 위치는 `gov-md-converter`입니다.

정책브리핑 API가 죽어 있을 때는 로컬 HWPX/PDF 코퍼스로 같은 형식의 `pipeline_report.json`을 만듭니다.

```bash
cd ../gov-md-converter
python3 scripts/run_local_hwpx_qc_pipeline.py \
  --date 2026-04-09 \
  --output-root ../GovPress_PDF_MD/exports/policy_briefing_qc \
  --qc-root tests/manual_samples/local_batch \
  --source-root tests/problem \
  --limit 5
```

이 명령은 `batch-local`을 먼저 실행해 scratch 샘플을 만들고, 같은 QC 후속 단계들을 돌린 뒤 기존 dashboard/OpenClaw/issue가 그대로 읽을 수 있는 `pipeline_report.json`을 남깁니다.

운영 storage의 `originals/results/golden`을 직접 QC 코퍼스로 쓰려면:

```bash
python3 scripts/run_storage_qc_pipeline.py \
  --date 2026-04-12 \
  --output-root exports/policy_briefing_qc \
  --gov-md-converter-root ../gov-md-converter \
  --qc-root ../gov-md-converter/tests/manual_samples/storage_batch \
  --storage-root deploy/wsl/data/storage \
  --limit 10
```

이 명령은 `deploy/wsl/data/storage/originals`에서 원문을 찾아 scratch sample을 만들고, 같은 sample 디렉터리에 아래 sidecar 자산도 함께 붙입니다.

- `storage_rendered.md` from `storage/results`
- `golden.md` from `storage/golden`
- `storage_bridge.json` with original/result/golden mapping

즉 자동 QC는 현재 변환기 기준으로 계속 돌리고, 사람이 보는 운영 결과와 수동 golden은 같은 sample 디렉터리에서 바로 대조할 수 있습니다.

CI나 cron에서 실패 여부만 판정하고 Markdown 요약을 남기려면 `gov-md-converter` CLI를 사용합니다.

```bash
cd ../gov-md-converter
python3 scripts/evaluate_policy_briefing_qc_report.py \
  exports/policy_briefing_qc/2026-04-09/pipeline_report.json \
  --summary-markdown exports/policy_briefing_qc/2026-04-09/qc_summary.md
```

기본값은 아래 조건에서 non-zero로 종료합니다.

- `review_required_count > 0`
- `regression` 결과에 실패 샘플이 있음
- QC 하위 명령 중 하나라도 non-zero 반환

GitHub Actions로 주기 실행하려면 `.github/workflows/policy-briefing-qc-monitor.yml`을 사용합니다.
필요한 secret:

- `GOVPRESS_POLICY_BRIEFING_SERVICE_KEY`
- `GOV_MD_CONVERTER_REPO_TOKEN`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

이 워크플로는 private `gov-md-converter`를 checkout하고, 파이프라인 실행 뒤 `pipeline_report.json`, `qc_summary.md`, `gov_md_reports/`를 artifact로 업로드합니다.
평가 결과가 실패이면 `issue_payload.json`도 만들고, 같은 날짜의 open QC issue를 갱신하거나 새로 생성합니다.
생성된 issue에는 `gov-md-converter`의 `suggest-fix`와 `auto-patch-draft`를 바탕으로 수정 대상 파일, 첫 패치 방향, 회귀 테스트 명령까지 함께 적습니다.
또한 `exports/policy_briefing_qc/dashboard/` 아래에 정적 HTML 대시보드와 집계 JSON을 생성하고, Telegram 알림이 설정되어 있으면 상위 샘플과 수정 대상 파일 요약을 전송합니다.

대시보드를 수동으로 다시 만들려면 `gov-md-converter`에서 실행합니다.

```bash
cd ../gov-md-converter
python3 scripts/build_policy_briefing_qc_dashboard.py \
  --root exports/policy_briefing_qc \
  --output-html exports/policy_briefing_qc/dashboard/index.html \
  --output-json exports/policy_briefing_qc/dashboard/dashboard.json
```

서버가 떠 있으면 브라우저에서 바로 아래 경로로 볼 수 있습니다.

- HTML dashboard: `/v1/policy-briefings/qc/dashboard`
- JSON dashboard: `/v1/policy-briefings/qc/dashboard.json`

Telegram 메시지를 실제 전송 전에 확인하려면 `gov-md-converter`에서 실행합니다.

```bash
cd ../gov-md-converter
python3 scripts/send_policy_briefing_qc_telegram.py \
  exports/policy_briefing_qc/2026-04-09/pipeline_report.json \
  --print-only
```

## OpenClaw 운영 콘솔

OpenClaw를 함께 쓰고 있다면 Telegram DM에서 GovPress QC 운영 명령과 원격 QC 검토 작업을 바로 수행할 수 있습니다.
실제 명령 실행기는 [scripts/openclaw_ops.py](/home/wavel/projects/GovPress_PDF_MD/scripts/openclaw_ops.py:1)이며, `job 선택 → review/source/rendered 다운로드 → golden.md 업로드 → 통과/보류`까지 이 래퍼가 처리합니다.
모델 역할은 분리합니다.

- `govpress_qc_ops`: `gpt-5.4-mini` 라우터
- `govpress_qc_worker`: `gpt-5.4` 내부 QC 작업

즉 파일 전달과 상태 작업은 `mini`가 처리하고, `수정: ...` 같은 실제 QC 수정 지시는 wrapper가 로컬 `codex exec -m gpt-5.4` 작업기로 handoff합니다.
QC 수정은 완전 장기세션이 아니라 `배치 단위 Codex 세션 + 파일 메모리`로 운영합니다.

- 같은 QC 배치 안의 `수정:` 요청은 기존 Codex thread를 `resume`
- 배치가 바뀌거나 turn/sample 수가 커지면 새 세션으로 리셋
- 공식 기억은 `<gov-md-root>/tests/manual_samples/qc_memory` 아래 파일에 남깁니다.

직접 실행 예시:

```bash
python3 <repo-root>/scripts/openclaw_ops.py qc-status --date latest
python3 <repo-root>/scripts/openclaw_ops.py qc-failures --date latest
python3 <repo-root>/scripts/openclaw_ops.py server-status
python3 <repo-root>/scripts/openclaw_ops.py telegram-dispatch --chat-scope dm --message "/qc today"
```

Telegram DM 명령 계약:

- `/qc today`
- `/qc rerun 2026-04-12`
- `/qc failures`
- `/qc issue`
- `/qc promote 2026-04-12 policy_briefing_2026_04_12_1234567890`
- `/server status`
- `/server failover-check`

원격 QC 작업 계약:

- `job 목록 보여줘`
- `review 필요한 job만 보여줘`
- `<sample-id> 열어줘`
- `다음 job 보여줘`
- `source 보내줘`
- `rendered 보내줘`
- `review 보내줘`
- `golden 보내줘`
- `golden.md` 업로드
- `통과`
- `보류`
- `수정: ...`

기본 정책:

- 명령은 owner DM에서만 허용
- owner DM 식별은 `GOVPRESS_QC_DEFAULT_SENDER_ID` 또는 `TELEGRAM_CHAT_ID`로 설정
- 슬래시 명령은 상태 조회/재실행/승격용
- 원격 QC는 `storage_batch` 샘플을 기준으로 동작
- `golden.md` 업로드는 현재 선택된 job에만 붙음
- 서버 관련 명령은 상태 점검만 수행

OpenClaw cron digest를 등록하려면:

```bash
bash scripts/setup_openclaw_qc_ops.sh
```

이 스크립트는 dedicated agent `govpress_qc_ops`와 `govpress-qc-digest` cron job을 만들고, `/qc today`를 매일 한국 시간 `13:20`에 owner DM으로 요약 전송하도록 등록합니다.

로컬에서 dedicated agent를 직접 테스트하려면:

```bash
openclaw agent --agent govpress_qc_ops --message "/server status" --json
openclaw agent --agent govpress_qc_ops --message "/qc today" --json
```

서버 cron에서 직접 돌릴 때는 아래 스크립트를 사용하면 됩니다.

```bash
GOVPRESS_POLICY_BRIEFING_SERVICE_KEY=... \
GOV_MD_CONVERTER_ROOT=../gov-md-converter \
OUTPUT_ROOT=exports/policy_briefing_qc \
QC_ROOT=tests/manual_samples/policy_briefings \
bash scripts/run_policy_briefing_qc_monitor.sh 2026-04-09
```

인자를 생략하면 UTC 기준 오늘 날짜를 사용합니다.
대시보드 산출물 기본 경로는 `exports/policy_briefing_qc/dashboard/index.html`과 `exports/policy_briefing_qc/dashboard/dashboard.json`입니다.

## 참고

- 변환 결과는 초안입니다. 공개 전에는 제목, 표, 목록, 숫자, 링크를 한 번 더 확인하는 것이 좋습니다.
- 정책브리핑 목록은 제공기관 API 상태에 따라 지연되거나 실패할 수 있습니다.
- 정책브리핑 목록 기능은 공공데이터포털(`data.go.kr`)의 `pressReleaseService` Open API를 사용합니다.
- 이 서비스의 개발과 개선 과정에는 AI 도구가 활용되었습니다.

## 라이선스

이 저장소는 [MIT License](LICENSE)를 따릅니다.
