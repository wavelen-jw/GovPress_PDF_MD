window.HARDEST_POLICY_BRIEFINGS_DATA = {
  "title": "AI가 고른 어려운 보도자료 10선",
  "subtitle": "표, 붙임, 각주가 복잡하게 섞인 정책브리핑 문서를 여러 변환 도구로 비교합니다.",
  "generated_at": "2026-04-29",
  "source_doc": "gov-md-converter/docs/qc-v2-hardest-curated-press-releases.md",
  "engines": [
    {
      "key": "readhim",
      "label": "읽힘",
      "input": "HWPX"
    },
    {
      "key": "kordoc",
      "label": "Kordoc",
      "input": "HWPX"
    },
    {
      "key": "opendataloader",
      "label": "OpenDataLoader PDF",
      "input": "PDF"
    },
    {
      "key": "docling",
      "label": "Docling",
      "input": "PDF"
    },
    {
      "key": "chatgpt-5.4-medium",
      "label": "ChatGPT 5.4 medium",
      "input": "원문 추출"
    },
    {
      "key": "gemini",
      "label": "Gemini",
      "input": "수동 산출물"
    }
  ],
  "documents": [
    {
      "rank": 1,
      "sample_id": "policy_briefing_2026_04_29_156759031",
      "title": "2024년 가계생산위성계정 (무급 가사노동 가치 평가)",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156759031",
      "qc_status": "deferred",
      "difficulty_reason": "대형 통계 보고서형 보도자료, 1,000줄 이상, 표 200개 수준, 공통규칙 한계로 보류",
      "news_id": "156759031",
      "department": "",
      "details": {
        "section_title": "2024년 가계생산위성계정 (무급 가사노동 가치 평가)",
        "feature": "보도자료라기보다 통계 보고서에 가까운 구조다. `일 러 두 기`, `목 차`, 계정 개요, 결과 요약, 지역별/성별 통계표, 추계 방법 설명이 장문으로 이어진다.",
        "qc_point": "press 문서 안에서 report-like 구조를 어디까지 허용할지 결정해야 한다. 목차 항목과 본문 heading, 대형 통계표, 수식형 문장, 부록성 표 제목을 모두 공통규칙으로 안정화해야 한다.",
        "deferred_reason": "단일 문서 예외로는 맞출 수 있으나, 통계 보고서형 보도자료 전체에 적용 가능한 공통규칙 경계가 아직 명확하지 않다."
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156759031.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156759031.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_29_156759031/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156759031.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156759031.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156759031.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 2,
      "sample_id": "policy_briefing_2026_04_14_156754934",
      "title": "2026년 3월 정보통신산업(ICT) 수출입 동향",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754934",
      "qc_status": "passed",
      "difficulty_reason": "17회 수정 반복, 대형 통계 부록, 150개 이상 표 블록",
      "news_id": "156754934",
      "department": "과학기술정보통신부",
      "details": {
        "section_title": "2026년 3월 정보통신산업(ICT) 수출입 동향",
        "feature": "통계 보도자료 중에서도 표 밀도가 매우 높다. 본문, 목차, `동향 세부자료`, 품목별/지역별 표, 수출입 수치가 반복되고 표 제목과 본문 heading의 경계가 자주 바뀐다.",
        "qc_point": "통계 부록의 목차 항목을 지역 heading으로 오인하지 않기, 2열 그림/표 블록 보존, 수식형 문장 보존, 대량 표의 소수점/증감률 spacing 안정화.",
        "deferred_reason": ""
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156754934.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156754934.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_14_156754934/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156754934.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156754934.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156754934.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 3,
      "sample_id": "policy_briefing_2026_04_16_156756008",
      "title": "지난해 디지털성범죄 피해자 1만 637명에게 35만여 건 원스톱 지원",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156756008",
      "qc_status": "pending",
      "difficulty_reason": "rule risk 78, 장문 통계표 다수, 각주성 quote 다수",
      "news_id": "156756008",
      "department": "",
      "details": {
        "section_title": "지난해 디지털성범죄 피해자 1만 637명에게 35만여 건 원스톱 지원",
        "feature": "피해자 수, 지원 건수, 피해유형, 연령대별 통계가 긴 표로 반복된다. 표 주변에 `*`, `**`, `※` 설명문이 많고, quote와 plain note의 구분이 중요하다.",
        "qc_point": "다단 헤더 표를 깨지 않기, 주석성 문장을 이전 bullet에 흡수하지 않기, 피해 유형 표의 빈 셀/비율 행 보존.",
        "deferred_reason": ""
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156756008.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156756008.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_16_156756008/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156756008.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156756008.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156756008.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 4,
      "sample_id": "policy_briefing_2026_04_24_156757632",
      "title": "전국 공공도서관 연간 2억 3천만 명 찾아, 지역 공동체 거점으로 안착",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757632",
      "qc_status": "ai pass, manual pending",
      "difficulty_reason": "rule risk 54, 본문 통계표와 붙임 통계조사 표가 모두 큼",
      "news_id": "156757632",
      "department": "문화체육관광부",
      "details": {
        "section_title": "전국 공공도서관 연간 2억 3천만 명 찾아, 지역 공동체 거점으로 안착",
        "feature": "본문에 연도별 핵심 지표 표가 있고, 붙임에는 통계조사 개요와 지역별/설립주체별 세부 표가 이어진다.",
        "qc_point": "본문 press 규칙과 붙임 report-like 규칙의 전환, 그림 제목과 표 제목의 heading 레벨, `* 1관당 인구수` 같은 표 내부 주석 보존.",
        "deferred_reason": ""
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156757632.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156757632.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_24_156757632/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156757632.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757632.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757632.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 5,
      "sample_id": "policy_briefing_2026_04_23_156757541",
      "title": "교육부 소관 법안 「평생교육법」 등 11건, 국회 본회의 통과",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757541",
      "qc_status": "pending",
      "difficulty_reason": "rule risk 43, 법률별 요약표와 11개 법안 설명 섹션",
      "news_id": "156757541",
      "department": "교육부",
      "details": {
        "section_title": "교육부 소관 법안 「평생교육법」 등 11건, 국회 본회의 통과",
        "feature": "처음에는 법률명/주요내용/효과 요약표가 나오고, 뒤에는 11개 법률별 상세 설명이 이어진다. 표 안의 bullet과 본문 heading이 함께 나온다.",
        "qc_point": "표 셀 내부 bullet을 외부 본문 list로 빼내지 않기, 법률별 번호 heading 유지, 시행일 괄호 문구와 각주성 설명 보존.",
        "deferred_reason": ""
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156757541.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156757541.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_23_156757541/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156757541.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757541.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757541.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 6,
      "sample_id": "policy_briefing_2021_04_23_156448349",
      "title": "'20년 말 외국인 보유 토지는 253.3㎢, 전 국토의 0.25%",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156448349",
      "qc_status": "deferred",
      "difficulty_reason": "과거 golden 기반 보류, 외국인 토지보유 통계표와 각주형 번호 문단 처리 난점",
      "news_id": "156448349",
      "department": "국토교통부",
      "details": {
        "section_title": "'20년 말 외국인 보유 토지는 253.3㎢, 전 국토의 0.25%",
        "feature": "본문과 붙임 모두 외국인 토지보유 통계표 중심이다. 필지 수 집계 설명처럼 번호 문단처럼 보이지만 실제로는 각주 설명인 문장이 나온다.",
        "qc_point": "`1.`, `2.` 형태가 항상 numbered list인지, 각주 내부 예시 번호인지 구분해야 한다. 넓은 시도별 표의 다단 헤더와 증감률 표기도 보존해야 한다.",
        "deferred_reason": "과거 golden을 가진 샘플이지만 최근 규칙과 충돌하는 구간이 있어, 기존 assertion을 그대로 유지할지 재생성할지 판단이 필요하다."
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156448349.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156448349.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2021_04_23_156448349/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156448349.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156448349.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156448349.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 7,
      "sample_id": "policy_briefing_2026_04_23_156757495",
      "title": "'26년 1분기 전국 지가 0.58% 상승",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757495",
      "qc_status": "pending",
      "difficulty_reason": "rule risk 34, 그림 대체 표와 다층 통계표 혼재",
      "news_id": "156757495",
      "department": "국토교통부",
      "details": {
        "section_title": "'26년 1분기 전국 지가 0.58% 상승",
        "feature": "본문이 지가변동률과 토지 거래량 두 축으로 나뉘고, 그림 대체 블록과 통계표가 번갈아 나온다.",
        "qc_point": "`<그림>` 대체 표와 실제 데이터 표 구분, 권역별/용도지역별 다단 헤더 보존, `△`, `%p`, 소수점 spacing 유지.",
        "deferred_reason": ""
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156757495.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156757495.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_23_156757495/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156757495.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757495.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757495.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 8,
      "sample_id": "policy_briefing_2026_04_24_156757844",
      "title": "국무총리, 생명대사·천명수호처 위촉 자살자 1,000명 감축을 위한 천명지킴 발대식",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757844",
      "qc_status": "deferred",
      "difficulty_reason": "행사 일정표와 대형 명단표, 긴 인물 설명 셀, 보류 가중치 반영",
      "news_id": "156757844",
      "department": "국무조정실",
      "details": {
        "section_title": "국무총리, 생명대사·천명수호처 위촉 자살자 1,000명 감축을 위한 천명지킴 발대식",
        "feature": "행사 개요, 시간표, 부스 일정, 생명대사/기관 현황 명단표가 포함된다. 명단표 셀 안에 이름, 소속, 데뷔 정보, 대표활동, 선정사유가 길게 들어간다.",
        "qc_point": "행사 일정표의 셀 내부 bullet 보존, 긴 인물 설명 셀의 줄바꿈 안정화, 보도자료 본문 quote와 붙임 report-like 구조의 전환.",
        "deferred_reason": "명단형 대형 표를 Markdown 표로 유지할 때 가독성과 원문 충실성의 균형이 좋지 않아 수동 판단이 필요하다."
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156757844.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156757844.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_24_156757844/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156757844.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757844.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757844.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 9,
      "sample_id": "policy_briefing_2026_04_16_156755997",
      "title": "「국가바이오혁신위원회」 출범, 바이오 정책 총괄 민관협력 플랫폼 본격 가동",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156755997",
      "qc_status": "pending",
      "difficulty_reason": "rule risk 44, 붙임이 사실상 보고서형 장문 구조",
      "news_id": "156755997",
      "department": "",
      "details": {
        "section_title": "「국가바이오혁신위원회」 출범, 바이오 정책 총괄 민관협력 플랫폼 본격 가동",
        "feature": "보도자료 본문 뒤에 붙임1, 붙임2가 사실상 정책 보고서 형식으로 붙는다. 로드맵, 해외 사례, 클러스터 유형 표, 로마자 장 제목이 섞인다.",
        "qc_point": "담당부서 이후 붙임의 report-like heading 전환, 원문자/화살표 heading 처리, quote 박스와 표형 설명 박스 구분.",
        "deferred_reason": ""
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156755997.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156755997.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_16_156755997/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156755997.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156755997.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156755997.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    },
    {
      "rank": 10,
      "sample_id": "policy_briefing_2026_04_24_156757801",
      "title": "펀드 투자로 해외소득 얻은 금융소득종합과세 대상자는 5월 종합소득세 신고 때 펀드가 낸 세금 공제받으세요",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757801",
      "qc_status": "passed",
      "difficulty_reason": "13회 수정 반복, 본문 press와 참고 report-like 규칙 경계가 복잡",
      "news_id": "156757801",
      "department": "국세청",
      "details": {
        "section_title": "펀드 투자로 해외소득 얻은 금융소득종합과세 대상자는 5월 종합소득세 신고 때 펀드가 낸 세금 공제받으세요",
        "feature": "본문은 일반 press 구조지만 참고1~3은 제도 설명서에 가깝다. 그림 placeholder, 카드뉴스, 제도변경 연혁, 신청대상 판단기준이 섞인다.",
        "qc_point": "본문 `□`는 plain/press 규칙으로 두고, 참고 이후 `□`는 report-like heading으로 전환한다. 별표 각주와 표 제목을 bullet 깊이에 오염시키지 않는 것이 핵심이다.",
        "deferred_reason": ""
      },
      "has_hwpx": true,
      "has_pdf": true,
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/readhim/156757801.md",
          "error": ""
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "input": "HWPX",
          "status": "available",
          "path": "outputs/kordoc/156757801.md",
          "error": "Command '['npx', 'kordoc', '/home/wavel/projects/gov-md-converter/tests/qc_samples_qc_v2/policy_briefing_2026_04_24_156757801/source.hwpx', '-o', '/home/wavel/projects/GovPress_PDF_MD/artifacts/hardest_policy_briefings/outputs/kordoc/156757801.md', '--silent']' returned non-zero exit status 1."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "input": "PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757801.md",
          "error": ""
        },
        {
          "key": "docling",
          "label": "Docling",
          "input": "PDF",
          "status": "missing_tool",
          "path": "",
          "error": "docling command not found"
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "input": "원문 추출",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757801.md",
          "error": ""
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "input": "수동 산출물",
          "status": "manual_missing",
          "path": "",
          "error": ""
        }
      ]
    }
  ]
};
