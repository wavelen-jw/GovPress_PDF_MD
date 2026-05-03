window.HARDEST_POLICY_BRIEFINGS_DATA = {
  "title": "AI가 고른 어려운 보도자료 10선",
  "subtitle": "표, 붙임, 각주가 복잡하게 섞인 정책브리핑 문서를 여러 변환 도구로 비교합니다.",
  "generated_at": "2026-04-29",
  "engines": [
    {
      "key": "readhim",
      "label": "읽힘"
    },
    {
      "key": "kordoc",
      "label": "Kordoc"
    },
    {
      "key": "opendataloader",
      "label": "OpenDataLoader PDF"
    },
    {
      "key": "opendataloader-hybrid",
      "label": "OpenDataLoader Hybrid"
    },
    {
      "key": "docling",
      "label": "Docling"
    },
    {
      "key": "chatgpt-5.4-medium",
      "label": "ChatGPT 5.4 medium"
    },
    {
      "key": "gemini",
      "label": "Gemini"
    }
  ],
  "documents": [
    {
      "rank": 1,
      "title": "2024년 가계생산위성계정 (무급 가사노동 가치 평가)",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156759031",
      "department": "국가데이터처",
      "difficulty_note": "통계 보고서처럼 긴 문서입니다. 목차, 설명문, 수백 개의 표, 부록이 이어져서 제목과 표를 끝까지 일관되게 구분해야 합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156759031.md",
          "error": "",
          "assessment": "대형 통계표와 목차가 많은 문서에서도 제목과 표 흐름을 가장 안정적으로 유지해 검토 기준으로 쓰기 좋습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156759031.md",
          "error": "",
          "assessment": "대형 통계표와 목차의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156759031.md",
          "error": "",
          "assessment": "대형 통계표와 목차의 원문 배치를 비교적 따라가지만, 문단 연결과 표 제목 분리는 추가 검토가 필요합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156759031.md",
          "error": "",
          "assessment": "대형 통계표와 목차의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156759031.md",
          "error": "",
          "assessment": "대형 통계표와 목차를 폭넓게 잡아내지만 결과가 길고 이미지·표가 커져 핵심 본문을 찾는 데 시간이 걸립니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156759031.md",
          "error": "",
          "assessment": "대형 통계표와 목차의 문장 흐름은 가장 자연스럽지만, 정확한 원문 변환본으로 쓰려면 표와 목록 대조가 필요합니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 2,
      "title": "2026년 3월 정보통신산업(ICT) 수출입 동향",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754934",
      "department": "과학기술정보통신부",
      "difficulty_note": "수출입 수치와 품목별 표가 매우 많습니다. 비슷한 표 제목과 숫자가 반복되어 표의 경계와 증감률 표기를 흐트러뜨리기 쉽습니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156754934.md",
          "error": "",
          "assessment": "수출입 통계표가 많은 문서에서도 제목과 표 흐름을 가장 안정적으로 유지해 검토 기준으로 쓰기 좋습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156754934.md",
          "error": "",
          "assessment": "수출입 통계표를 텍스트로 많이 끌어오지만, 긴 표에서는 셀 경계와 제목 계층이 흔들리는 구간이 있습니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156754934.md",
          "error": "",
          "assessment": "수출입 통계표의 표 형태는 많이 보존되지만, 넓은 표에서 읽기 순서가 어긋나는지 확인해야 합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156754934.md",
          "error": "",
          "assessment": "수출입 통계표의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156754934.md",
          "error": "",
          "assessment": "수출입 통계표의 시각 구조를 잘 포착하지만 이미지 비중이 높아 Markdown 재편집성은 낮아질 수 있습니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156754934.md",
          "error": "",
          "assessment": "수출입 통계표를 읽기 좋은 문서로 정돈하지만, 표 숫자와 셀 경계는 원문 재현보다 요약·재구성에 가깝습니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 3,
      "title": "지난해 디지털성범죄 피해자 1만 637명에게 35만여 건 원스톱 지원",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156756008",
      "department": "성평등가족부",
      "difficulty_note": "피해자 현황과 지원 건수 표가 길게 이어지고, 별표·쌍별표·참고 문장이 많습니다. 설명문이 표나 목록 안으로 섞이지 않게 분리해야 합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156756008.md",
          "error": "",
          "assessment": "피해자 지원 현황 표가 많은 문서에서도 제목과 표 흐름을 가장 안정적으로 유지해 검토 기준으로 쓰기 좋습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156756008.md",
          "error": "",
          "assessment": "피해자 지원 현황 표의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156756008.md",
          "error": "",
          "assessment": "피해자 지원 현황 표의 표 형태는 많이 보존되지만, 넓은 표에서 읽기 순서가 어긋나는지 확인해야 합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156756008.md",
          "error": "",
          "assessment": "피해자 지원 현황 표의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156756008.md",
          "error": "",
          "assessment": "피해자 지원 현황 표의 시각 구조를 잘 포착하지만 이미지 비중이 높아 Markdown 재편집성은 낮아질 수 있습니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156756008.md",
          "error": "",
          "assessment": "피해자 지원 현황 표를 읽기 좋은 문서로 정돈하지만, 표 숫자와 셀 경계는 원문 재현보다 요약·재구성에 가깝습니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 4,
      "title": "전국 공공도서관 연간 2억 3천만 명 찾아, 지역 공동체 거점으로 안착",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757632",
      "department": "문화체육관광부",
      "difficulty_note": "본문은 보도자료 형식이지만 뒤쪽에는 조사 개요와 지역별 통계표가 이어집니다. 본문 설명, 그림 제목, 붙임 표의 구조를 각각 다르게 보존해야 합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156757632.md",
          "error": "",
          "assessment": "도서관 통계와 조사 개요가 많은 문서에서도 제목과 표 흐름을 가장 안정적으로 유지해 검토 기준으로 쓰기 좋습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156757632.md",
          "error": "",
          "assessment": "도서관 통계와 조사 개요를 텍스트로 많이 끌어오지만, 긴 표에서는 셀 경계와 제목 계층이 흔들리는 구간이 있습니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757632.md",
          "error": "",
          "assessment": "도서관 통계와 조사 개요의 표 형태는 많이 보존되지만, 넓은 표에서 읽기 순서가 어긋나는지 확인해야 합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156757632.md",
          "error": "",
          "assessment": "도서관 통계와 조사 개요의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156757632.md",
          "error": "",
          "assessment": "도서관 통계와 조사 개요의 시각 구조를 잘 포착하지만 이미지 비중이 높아 Markdown 재편집성은 낮아질 수 있습니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757632.md",
          "error": "",
          "assessment": "도서관 통계와 조사 개요를 읽기 좋은 문서로 정돈하지만, 표 숫자와 셀 경계는 원문 재현보다 요약·재구성에 가깝습니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 5,
      "title": "교육부 소관 법안 「평생교육법」 등 11건, 국회 본회의 통과",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757541",
      "department": "교육부",
      "difficulty_note": "법률별 요약표와 11개 법안 설명이 이어집니다. 표 안의 긴 문장과 목록을 본문 목록으로 잘못 빼내지 않고 셀 안에 유지해야 합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156757541.md",
          "error": "",
          "assessment": "법안별 요약표가 많은 문서에서도 제목과 표 흐름을 가장 안정적으로 유지해 검토 기준으로 쓰기 좋습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156757541.md",
          "error": "",
          "assessment": "법안별 요약표의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757541.md",
          "error": "",
          "assessment": "법안별 요약표의 표 형태는 많이 보존되지만, 넓은 표에서 읽기 순서가 어긋나는지 확인해야 합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156757541.md",
          "error": "",
          "assessment": "법안별 요약표의 표와 배치를 함께 살리려는 장점이 있으나, 그림화된 구간과 텍스트 표를 구분해 봐야 합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156757541.md",
          "error": "",
          "assessment": "법안별 요약표를 폭넓게 잡아내지만 결과가 길고 이미지·표가 커져 핵심 본문을 찾는 데 시간이 걸립니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757541.md",
          "error": "",
          "assessment": "법안별 요약표를 읽기 좋은 문서로 정돈하지만, 표 숫자와 셀 경계는 원문 재현보다 요약·재구성에 가깝습니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 6,
      "title": "'20년 말 외국인 보유 토지는 253.3㎢, 전 국토의 0.25%",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156448349",
      "department": "국토교통부",
      "difficulty_note": "외국인 토지 보유 현황 표가 본문과 붙임에 반복됩니다. 예시 번호처럼 보이는 문장과 실제 번호 목록을 구분하고, 넓은 다단 표를 보존해야 합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156448349.md",
          "error": "",
          "assessment": "외국인 토지 보유 표 중심의 본문 구조를 깔끔하게 정리했지만, 세부 표 숫자는 원문 대조가 필요합니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156448349.md",
          "error": "",
          "assessment": "외국인 토지 보유 표의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156448349.md",
          "error": "",
          "assessment": "외국인 토지 보유 표의 원문 배치를 비교적 따라가지만, 문단 연결과 표 제목 분리는 추가 검토가 필요합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156448349.md",
          "error": "",
          "assessment": "외국인 토지 보유 표에서는 기본 PDF 추출보다 시각 구조가 늘었지만, 이미지와 본문 중복 여부를 확인해야 합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156448349.md",
          "error": "",
          "assessment": "외국인 토지 보유 표의 구조 인식은 양호하나, 표와 문단이 과하게 분리되는 구간은 원문과 비교해야 합니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156448349.md",
          "error": "",
          "assessment": "외국인 토지 보유 표의 문장 흐름은 가장 자연스럽지만, 정확한 원문 변환본으로 쓰려면 표와 목록 대조가 필요합니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 7,
      "title": "'26년 1분기 전국 지가 0.58% 상승",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757495",
      "department": "국토교통부",
      "difficulty_note": "지가 변동률과 토지 거래량 표가 번갈아 나오고, 그림을 대신하는 표도 섞여 있습니다. 그림 설명과 실제 데이터 표를 구분해야 합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156757495.md",
          "error": "",
          "assessment": "지가·거래량 표가 많은 문서에서도 제목과 표 흐름을 가장 안정적으로 유지해 검토 기준으로 쓰기 좋습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156757495.md",
          "error": "",
          "assessment": "지가·거래량 표의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757495.md",
          "error": "",
          "assessment": "지가·거래량 표의 표 형태는 많이 보존되지만, 넓은 표에서 읽기 순서가 어긋나는지 확인해야 합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156757495.md",
          "error": "",
          "assessment": "지가·거래량 표의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156757495.md",
          "error": "",
          "assessment": "지가·거래량 표의 시각 구조를 잘 포착하지만 이미지 비중이 높아 Markdown 재편집성은 낮아질 수 있습니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757495.md",
          "error": "",
          "assessment": "지가·거래량 표의 문장 흐름은 가장 자연스럽지만, 정확한 원문 변환본으로 쓰려면 표와 목록 대조가 필요합니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 8,
      "title": "국무총리, 생명대사·천명수호처 위촉 자살자 1,000명 감축을 위한 천명지킴 발대식",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757844",
      "department": "국무조정실",
      "difficulty_note": "행사 일정, 참여 기관, 인물 명단이 큰 표로 들어 있습니다. 표 셀 안에 긴 소개문과 줄바꿈이 많아 표 형태가 무너지기 쉽습니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156757844.md",
          "error": "",
          "assessment": "행사 일정과 참여자 표가 많은 문서에서도 제목과 표 흐름을 가장 안정적으로 유지해 검토 기준으로 쓰기 좋습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156757844.md",
          "error": "",
          "assessment": "행사 일정과 참여자 표의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757844.md",
          "error": "",
          "assessment": "행사 일정과 참여자 표의 표 형태는 많이 보존되지만, 넓은 표에서 읽기 순서가 어긋나는지 확인해야 합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156757844.md",
          "error": "",
          "assessment": "행사 일정과 참여자 표의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156757844.md",
          "error": "",
          "assessment": "행사 일정과 참여자 표의 시각 구조를 잘 포착하지만 이미지 비중이 높아 Markdown 재편집성은 낮아질 수 있습니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757844.md",
          "error": "",
          "assessment": "행사 일정과 참여자 표를 읽기 좋은 문서로 정돈하지만, 표 숫자와 셀 경계는 원문 재현보다 요약·재구성에 가깝습니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 9,
      "title": "「국가바이오혁신위원회」 출범, 바이오 정책 총괄 민관협력 플랫폼 본격 가동",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156755997",
      "department": "국무조정실",
      "difficulty_note": "보도자료 뒤에 정책 설명서에 가까운 긴 붙임이 이어집니다. 본문, 로드맵, 해외 사례, 담당부서 표를 각각 다른 구조로 읽어야 합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156755997.md",
          "error": "",
          "assessment": "바이오 정책 붙임 자료의 장별 구분과 본문 순서가 비교적 잘 살아 있어 원문 대조 부담이 낮습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156755997.md",
          "error": "",
          "assessment": "바이오 정책 붙임 자료의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156755997.md",
          "error": "",
          "assessment": "바이오 정책 붙임 자료의 표 형태는 많이 보존되지만, 넓은 표에서 읽기 순서가 어긋나는지 확인해야 합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156755997.md",
          "error": "",
          "assessment": "바이오 정책 붙임 자료의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156755997.md",
          "error": "",
          "assessment": "바이오 정책 붙임 자료의 시각 구조를 잘 포착하지만 이미지 비중이 높아 Markdown 재편집성은 낮아질 수 있습니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156755997.md",
          "error": "",
          "assessment": "바이오 정책 붙임 자료를 읽기 좋은 문서로 정돈하지만, 표 숫자와 셀 경계는 원문 재현보다 요약·재구성에 가깝습니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    },
    {
      "rank": 10,
      "title": "펀드 투자로 해외소득 얻은 금융소득종합과세 대상자는 5월 종합소득세 신고 때 펀드가 낸 세금 공제받으세요",
      "source_url": "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156757801",
      "department": "국세청",
      "difficulty_note": "본문은 짧지만 참고자료가 제도 설명서처럼 길게 이어집니다. 카드뉴스, 신청 기준, 법령 인용, 별표 설명을 서로 섞지 않는 것이 중요합니다.",
      "engines": [
        {
          "key": "readhim",
          "label": "읽힘",
          "status": "available",
          "path": "outputs/readhim/156757801.md",
          "error": "",
          "assessment": "펀드 과세 참고자료의 장별 구분과 본문 순서가 비교적 잘 살아 있어 원문 대조 부담이 낮습니다."
        },
        {
          "key": "kordoc",
          "label": "Kordoc",
          "status": "available",
          "path": "outputs/kordoc/156757801.md",
          "error": "",
          "assessment": "펀드 과세 참고자료의 기본 내용은 따라오지만, 목록과 표 안 문장이 본문으로 풀리는 부분을 확인해야 합니다."
        },
        {
          "key": "opendataloader",
          "label": "OpenDataLoader PDF",
          "status": "available",
          "path": "outputs/opendataloader/156757801.md",
          "error": "",
          "assessment": "펀드 과세 참고자료의 원문 배치를 비교적 따라가지만, 문단 연결과 표 제목 분리는 추가 검토가 필요합니다."
        },
        {
          "key": "opendataloader-hybrid",
          "label": "OpenDataLoader Hybrid",
          "status": "available",
          "path": "outputs/opendataloader-hybrid/156757801.md",
          "error": "",
          "assessment": "펀드 과세 참고자료의 시각 요소를 적극 보존하지만 이미지가 많이 남아 실제 텍스트 재사용성은 선별 확인이 필요합니다."
        },
        {
          "key": "docling",
          "label": "Docling",
          "status": "available",
          "path": "outputs/docling/156757801.md",
          "error": "",
          "assessment": "펀드 과세 참고자료의 시각 구조를 잘 포착하지만 이미지 비중이 높아 Markdown 재편집성은 낮아질 수 있습니다."
        },
        {
          "key": "chatgpt-5.4-medium",
          "label": "ChatGPT 5.4 medium",
          "status": "available",
          "path": "outputs/chatgpt-5.4-medium/156757801.md",
          "error": "",
          "assessment": "펀드 과세 참고자료의 문장 흐름은 가장 자연스럽지만, 정확한 원문 변환본으로 쓰려면 표와 목록 대조가 필요합니다."
        },
        {
          "key": "gemini",
          "label": "Gemini",
          "status": "manual_missing",
          "path": "",
          "error": "",
          "assessment": "결과가 없어 이 문서에서는 변환 품질을 평가하지 않았습니다."
        }
      ]
    }
  ]
};
