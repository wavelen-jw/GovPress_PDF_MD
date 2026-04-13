window.BENCHMARK_OFFICIAL_DATA = {
  "title": "공식 벤치 방식으로 본 읽힘 PDF 성능",
  "subtitle": "OpenDataLoader 공식 벤치 코퍼스와 동일한 ground truth, 동일한 evaluator 위에서 읽힘을 하나의 PDF 변환 엔진으로 추가 비교",
  "repo": {
    "url": "https://github.com/opendataloader-project/opendataloader-bench",
    "commit": "e8647096efdb5b55818f409fc959e1c170ca5932",
    "docs_url": "https://opendataloader.org/docs/benchmark"
  },
  "corpus": {
    "pdf_count": 200,
    "ground_truth_count": 200,
    "ground_truth_path": "ground-truth/markdown",
    "pdf_path": "pdfs"
  },
  "readhim_adapter": {
    "engine_name": "readhim",
    "display_name": "읽힘",
    "adapter_note": "읽힘 행은 local clone의 opendataloader-bench에 readhim 엔진을 추가하고, govpress_converter.convert_pdf()를 통해 prediction/readhim/markdown 을 생성한 뒤 src/evaluator.py로 평가했습니다.",
    "run_environment": "WSL Ubuntu on server W"
  },
  "leaderboard": [
    {
      "engine": "opendataloader-hybrid",
      "label": "OpenDataLoader [hybrid]",
      "license": "Apache-2.0",
      "kind": "official",
      "overall": 0.9065718466674022,
      "nid": 0.9337307553293448,
      "teds": 0.9276430534097512,
      "mhs": 0.8207761855598542,
      "speed_s_per_page": 0.463,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    },
    {
      "engine": "docling",
      "label": "Docling",
      "license": "MIT",
      "kind": "official",
      "overall": 0.8816788439412203,
      "nid": 0.8983654504334178,
      "teds": 0.8870548597181608,
      "mhs": 0.8240014790562668,
      "speed_s_per_page": 0.762,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    },
    {
      "engine": "nutrient",
      "label": "Nutrient",
      "license": "Proprietary",
      "kind": "official",
      "overall": 0.8799889831805358,
      "nid": 0.9238656525312281,
      "teds": 0.6615943748630245,
      "mhs": 0.8109729837933403,
      "speed_s_per_page": 0.23,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    },
    {
      "engine": "marker",
      "label": "Marker",
      "license": "GPL-3.0",
      "kind": "official",
      "overall": 0.8608364226049575,
      "nid": 0.8897399418827387,
      "teds": 0.8076072125952004,
      "mhs": 0.7955733168260926,
      "speed_s_per_page": 53.932,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-01-06",
      "missing_predictions": 0
    },
    {
      "engine": "unstructured-hires",
      "label": "Unstructured [hi_res]",
      "license": "Apache-2.0",
      "kind": "official",
      "overall": 0.8413766149235284,
      "nid": 0.9037700890275755,
      "teds": 0.5882798735019806,
      "mhs": 0.7486065128098436,
      "speed_s_per_page": 3.008,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    },
    {
      "engine": "edgeparse",
      "label": "EdgeParse",
      "license": "Apache-2.0",
      "kind": "official",
      "overall": 0.836958632738173,
      "nid": 0.8937897795489006,
      "teds": 0.7174108707852721,
      "mhs": 0.706079055385819,
      "speed_s_per_page": 0.036,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    },
    {
      "engine": "mineru",
      "label": "MinerU",
      "license": "AGPL-3.0",
      "kind": "official",
      "overall": 0.8311354224973181,
      "nid": 0.8573619799638795,
      "teds": 0.8729915402457293,
      "mhs": 0.7429826268920451,
      "speed_s_per_page": 5.962,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-01-06",
      "missing_predictions": 0
    },
    {
      "engine": "readhim",
      "label": "읽힘",
      "license": "Proprietary",
      "kind": "local",
      "overall": 0.7573821332967173,
      "nid": 0.9085737770172119,
      "teds": 0.3914777270386865,
      "mhs": 0.4692063367894583,
      "speed_s_per_page": 0.5374117779731751,
      "processor": "12th Gen Intel(R) Core(TM) i9-12900",
      "document_count": 200,
      "date": "2026-04-13",
      "missing_predictions": 0
    },
    {
      "engine": "pymupdf4llm",
      "label": "PyMuPDF4LLM",
      "license": "AGPL-3.0",
      "kind": "official",
      "overall": 0.7316207702134215,
      "nid": 0.8851037315269882,
      "teds": 0.4009531754407035,
      "mhs": 0.4122221259490795,
      "speed_s_per_page": 0.091,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2025-11-27",
      "missing_predictions": 0
    },
    {
      "engine": "unstructured",
      "label": "Unstructured",
      "license": "Apache-2.0",
      "kind": "official",
      "overall": 0.6857767038954502,
      "nid": 0.8818117503126625,
      "teds": 0.0,
      "mhs": 0.38769956790313015,
      "speed_s_per_page": 0.077,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    },
    {
      "engine": "opendataloader",
      "label": "OpenDataLoader",
      "license": "Apache-2.0",
      "kind": "official",
      "overall": 0.6290916684882533,
      "nid": 0.9012188466436238,
      "teds": 0.6984795961807455,
      "mhs": 0.28757656264039044,
      "speed_s_per_page": 0.015,
      "processor": "12th Gen Intel(R) Core(TM) i9-12900",
      "document_count": 1,
      "date": "2026-04-13",
      "missing_predictions": 0
    },
    {
      "engine": "markitdown",
      "label": "MarkItDown",
      "license": "MIT",
      "kind": "official",
      "overall": 0.5885041533548623,
      "nid": 0.8436602457220033,
      "teds": 0.2729007862854617,
      "mhs": 0.0,
      "speed_s_per_page": 0.114,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    },
    {
      "engine": "liteparse",
      "label": "LiteParse",
      "license": "Apache-2.0",
      "kind": "official",
      "overall": 0.575604167319326,
      "nid": 0.8660311444401129,
      "teds": 0.0,
      "mhs": 0.0,
      "speed_s_per_page": 1.061,
      "processor": "Apple M4",
      "document_count": 200,
      "date": "2026-04-06",
      "missing_predictions": 0
    }
  ],
  "readhim": {
    "engine": "readhim",
    "label": "읽힘",
    "license": "Proprietary",
    "kind": "local",
    "overall": 0.7573821332967173,
    "nid": 0.9085737770172119,
    "teds": 0.3914777270386865,
    "mhs": 0.4692063367894583,
    "speed_s_per_page": 0.5374117779731751,
    "processor": "12th Gen Intel(R) Core(TM) i9-12900",
    "document_count": 200,
    "date": "2026-04-13",
    "missing_predictions": 0
  },
  "examples": [],
  "metric_help": [
    {
      "label": "Overall",
      "description": "문서별 NID, TEDS, MHS 평균입니다. 공식 벤치의 문서별 집계 규칙을 그대로 따릅니다."
    },
    {
      "label": "NID",
      "description": "읽기 순서 유사도입니다. 본문 텍스트의 순서와 내용이 ground truth에 얼마나 가까운지 봅니다."
    },
    {
      "label": "TEDS",
      "description": "표 구조 유사도입니다. 테이블 DOM 구조와 셀 내용을 함께 비교합니다."
    },
    {
      "label": "MHS",
      "description": "제목 계층 유사도입니다. heading 레벨과 구조 보존 정도를 봅니다."
    }
  ],
  "source_notes": [
    {
      "label": "공식 벤치 문서",
      "url": "https://opendataloader.org/docs/benchmark",
      "description": "지표 정의, 공식 리더보드, 재현 방법."
    },
    {
      "label": "벤치 구현 저장소",
      "url": "https://github.com/opendataloader-project/opendataloader-bench",
      "description": "이번 비교가 기반한 로컬 clone의 원격 저장소. 사용한 commit: e8647096efdb5b55818f409fc959e1c170ca5932"
    },
    {
      "label": "이번 실행 방식",
      "url": "https://github.com/wavelen-jw/GovPress_PDF_MD",
      "description": "이 리포지토리에서 readhim 어댑터와 정적 페이지를 추가하고, 공식 코퍼스 위에서 읽힘을 별도 엔진으로 실행."
    }
  ]
};
