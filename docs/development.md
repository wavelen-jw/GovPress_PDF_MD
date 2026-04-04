# Development

## 현재 구조

- 공개 프론트: GitHub Pages
- 공개 백엔드: FastAPI + worker
- 현재 주력 입력 포맷: `PDF`, `HWPX`

## 로컬 개발 환경

- Python 3.11 권장
- Java 17 권장
- `opendataloader-pdf`

## 설치

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
pip install -U opendataloader-pdf
```

## 로컬 API 실행

```bash
.venv/bin/python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8011
```

## 로컬 worker 실행

```bash
.venv/bin/python -m server.run_worker --storage-root ./storage --poll-interval 1.0
```

## 구성 개요

- `server/app/main.py`: FastAPI 진입점
- `server/app/api/`: 작업 생성, 상태 조회, 결과 수정 API
- `server/app/workers/`: 변환 worker
- `server/app/adapters/`: PDF/HWPX 변환 어댑터
- `src/`: Markdown 후처리, 문서 규칙, 렌더링 보정
- `mobile/dist/`: GitHub Pages에 배포되는 정적 웹 자산
- `tests/problem/`: 규칙 개선용 문제 파일과 정답 Markdown

## 변환 품질 개선 방식

문제 파일 기반으로 반복합니다.

1. `tests/problem/`의 `.pdf`, `.hwpx`, 기존 `.md`를 함께 확인합니다.
2. PDF/HWPX를 각각 변환해 차이를 봅니다.
3. `pdf -> md`를 자동 정답으로 두지 않습니다.
4. 원문에 더 가까운 표현을 골라 정답 `.md`를 갱신합니다.
5. 규칙은 `src/markdown_postprocessor.py`, `src/parser_rules.py`, `src/hwpx_postprocessor.py`, `server/app/adapters/hwpx_converter.py`에 일반화해서 반영합니다.
6. 같은 문제 파일로 재변환해 정답 `.md`와 다시 비교합니다.

## 테스트

전체 테스트:

```bash
.venv/bin/python -m unittest discover -s tests
```

문제 파일 확인은 자동 테스트보다 실제 변환 비교가 더 중요합니다.
- `tests/problem/` 아래 정답 `.md`와 현재 변환 결과를 직접 비교합니다.
- 수동 검증용 대용량 샘플은 `tests/manual_samples/`에 둡니다.

## 배포

- 프론트는 `mobile/dist/`를 GitHub Pages로 배포합니다.
- 백엔드는 `deploy/wsl/docker-compose.yml` 기준으로 API/worker를 재빌드해 반영합니다.
- 사용자가 요청할 때만 커밋, 푸시, Pages 배포, 운영 재기동을 진행합니다.
