# GovPress_PDF_MD Progress

## 프로젝트 목표

- Windows 데스크톱에서 동작하는 PDF → Markdown 변환 및 편집기 구현
- `PySide6` 기반 GUI, 드래그 앤 드롭, Markdown 편집/미리보기, `.md` 저장 지원
- 외부 SaaS 없이 로컬에서 동작
- `opendataloader-pdf` local 변환 결과를 기반으로, 행정기관 보도자료 템플릿에 맞춘 후처리 제공

## 초기 구현

- 기본 프로젝트 구조 생성
- 주요 모듈 분리
  - `main_window.py`: UI, 드래그 앤 드롭, 저장, 상태 표시
  - `converter.py`: PDF 변환, 의존성 확인, 임시 경로 처리
  - `workers.py`: 변환 작업 백그라운드 실행
  - `state.py`: 현재 문서 상태 관리
  - `editor_widget.py`, `preview_widget.py`: Markdown 편집/미리보기
- `README.md`, `requirements.txt`, 기본 테스트 추가

## 보도자료 템플릿 최적화

- 일반 PDF 변환기보다 “행정기관 보도자료 템플릿 전용” 후처리 품질을 우선하는 방향으로 전환
- 후처리 관련 모듈 분리
  - `document_template.py`
  - `parser_rules.py`
  - `markdown_postprocessor.py`
- 주요 규칙 반영
  - `보도자료`, `보도시점`, 제목, 부제, 본문, 담당부서 구조 인식
  - `□`는 heading으로 승격하지 않고 일반 문단 처리
  - `○`, `ㅇ`는 bullet 처리
  - 연락처 블록은 `## 담당부서` 아래 bullet 목록으로 정리
  - 페이지 번호, 이미지 노이즈, 목차 잔재 제거
  - `붙임`, `붙 임`, `별첨`은 최종 Markdown에서 제외

## 실문서 기반 규칙 고도화

- 사용자가 제공한 보도자료 PDF와 수동 수정 Markdown을 golden 기준으로 사용
- `tests/fixtures/press_release`, `tests/fixtures/press_release2`에 실문서 fixture 추가
- 변환 결과를 사용자가 직접 수정한 `.md`와 비교하면서 규칙을 반복 보정
- 반영된 대표 규칙
  - 제목 병합
  - `보도시점` 메타데이터 blockquote 처리
  - 설명형 문장은 heading 승격 금지
  - `<광주 : ...>` 같은 라벨은 소제목 처리
  - 각주성 `*`, `※` 문구는 적절한 blockquote 처리
  - `△` 하위 항목 정렬 개선
  - 본문 상자형 요소 중 비연락처 `1행 1열` 표는 quote 블록 처리
  - 단순 표는 Markdown table, 복잡한 표는 HTML table fallback

## 변환 파이프라인 전환

- 초기에는 `opendataloader-pdf`의 Markdown 산출물 후처리 중심
- 이후 JSON이 구조 보존에 더 유리하다고 판단해 JSON 우선 파이프라인으로 전환
- 현재 구조
  - `PDF -> opendataloader-pdf JSON 추출 -> 내부 규칙 적용 -> Markdown 출력`
- Markdown fallback은 유지하되 주 경로는 JSON 기반

## 테스트 체계 강화

- 핵심 로직 테스트 작성 및 확장
- fixture 기반 회귀 테스트 추가
- 사용자가 수정한 Markdown을 golden 기준으로 의미 구조 비교
- 최근 기준으로 수십 개 테스트가 지속적으로 통과하도록 유지

## Windows 배포 방향 정리

- 프로젝트 명칭을 `GovPress_PDF_MD`로 확정
- GitHub 저장소 생성 및 푸시 완료
  - `https://github.com/wavelen-jw/GovPress_PDF_MD`
- Windows 빌드를 위한 파일 추가
  - `GovPress_PDF_MD.spec`
  - `build_windows.bat`
  - `installer/GovPress_PDF_MD.iss`
- 아이콘 및 실행파일 메타데이터 추가
  - 문서/Markdown 성격을 반영한 `.ico` 생성
  - 제작자 정보, 제품 설명, GitHub URL을 exe/installer 메타데이터에 포함

## 런타임/배포 이슈와 수정

### 1. Java / opendataloader 의존성 오류

- 사용자 환경에서 Java는 인식되지만 `opendataloader=명령을 찾을 수 없습니다.` 오류 발생
- 원인
  - 배포판에서 `opendataloader-pdf.exe` 또는 runtime Python 경로 의존이 불안정함

### 2. 새 창이 뜨는 문제

- 설치본에서 PDF 열기 시 새 창이 다시 뜨는 현상 발생
- 원인
  - frozen app에서 `sys.executable -m opendataloader_pdf` fallback이 자기 자신을 다시 실행
- 수정
  - 이 fallback 제거/정리

### 3. 배포 용량 과대

- runtime Python 전체 `venv`와 Java를 함께 복사하던 구조라 용량이 큼
- 방향 수정
  - `opendataloader_pdf`를 PyInstaller에 직접 포함
  - 별도 runtime Python 제거
  - Java만 별도로 번들

### 4. 현재 변환 실행 방식

- 현재는 exe 내부에 포함된 `opendataloader_pdf` 패키지를 직접 import해서 사용
- `opendataloader-pdf.exe`나 별도 runtime Python에 의존하지 않음

### 5. UNC/WSL 경로 문제

- Windows에서 `\\wsl.localhost\...` 경로의 PDF를 열면 Java CLI가 실패하는 문제 확인
- 대응 방향
  - 변환 전에 입력 PDF를 로컬 temp 경로로 staging한 뒤 변환하도록 수정 중
  - 이 변경에 대한 테스트는 통과한 상태

## 문서화

- `README.md` 최신화
- `CONVERSION_RULES.md` 추가
  - 현재 확정된 보도자료 변환 규칙 정리
- 라이선스/고지 문서 추가
  - `licenses/README.md`
  - `licenses/THIRD_PARTY_NOTICES.txt`

## 현재 상태 요약

- 보도자료 템플릿 PDF → Markdown 후처리 품질은 실문서 기준으로 상당히 안정화됨
- GUI, 저장, 미리보기, 드래그 앤 드롭, 상태 관리, 회귀 테스트까지 갖춘 상태
- GitHub 저장소 운영 중
- Windows 배포는 구조적으로 정리됐고, 실제 사용자 환경에서 발견된 런타임 이슈를 계속 반영 중

## 현재 확인이 필요한 항목

- 최신 빌드본에서 입력 PDF를 로컬 temp로 staging하는 수정이 실제 배포 문제를 해결하는지 확인 필요
- 최신 수정이 반영된 Windows 설치본 재빌드 및 실사용 검증 필요
