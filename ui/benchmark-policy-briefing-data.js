window.BENCHMARK_POLICY_BRIEFING_DATA = {
  "title": "정책브리핑 99건 벤치마크",
  "subtitle": "정책브리핑 보도자료를 기준으로 Ground Truth를 직접 만들고, 읽힘(HWPX->MD)과 OpenDataLoader(PDF->MD)를 같은 지표로 비교한 결과",
  "corpus": {
    "document_count": 100,
    "ground_truth_count": 99,
    "failure_count": 1,
    "generated_at": "2026-04-13T17:29:03.494093",
    "note": "최신 정책브리핑 보도자료 중 PDF와 HWPX가 모두 있는 문서를 대상으로 docViewer HTML을 Markdown으로 정규화해 ground truth를 생성했습니다."
  },
  "metrics": {
    "readhim": {
      "score": {
        "overall_mean": 0.4742850194212338,
        "nid_mean": 0.6956765088384246,
        "nid_s_mean": 0.7483935502144294,
        "teds_mean": 0.31752862474292975,
        "teds_s_mean": 0.40432300993371617,
        "mhs_mean": 0.28680277259123527,
        "mhs_s_mean": 0.6132708869719975
      },
      "nid_count": 99,
      "teds_count": 40,
      "mhs_count": 99,
      "missing_predictions": 5,
      "table_timeouts": 2
    },
    "opendataloader": {
      "score": {
        "overall_mean": 0.36292146805658065,
        "nid_mean": 0.660103554386143,
        "nid_s_mean": 0.7293614663345928,
        "teds_mean": 0.21831175874723385,
        "teds_s_mean": 0.33266423574241183,
        "mhs_mean": 0.11289516328418778,
        "mhs_s_mean": 0.4434848187418372
      },
      "nid_count": 99,
      "teds_count": 42,
      "mhs_count": 99,
      "missing_predictions": 1
    }
  },
  "summary": {
    "readhim": {
      "engine_name": "readhim",
      "engine_version": "0.1.0-hwpx",
      "document_count": 94,
      "total_elapsed": 4.343007564544678,
      "elapsed_per_doc": 0.04620220813345402,
      "date": "2026-04-13"
    },
    "opendataloader": {
      "engine_name": "opendataloader",
      "engine_version": "custom-policy-briefing",
      "document_count": 98,
      "total_elapsed": 47.37656879425049,
      "elapsed_per_doc": 0.4834343754515356,
      "date": "2026-04-13"
    }
  },
  "documents": [
    {
      "document_id": "156754291",
      "title": "\"중동발 공사 지연, 민간 건설현장도 공기연장 길 열린다\"",
      "department": "국토교통부",
      "approve_date": "04/13/2026 16:31:00",
      "readhim": {
        "overall": 0.5450433239997295,
        "nid": 0.7776591960156529,
        "teds": null,
        "mhs": 0.31242745198380617,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4421345674270777,
        "nid": 0.7212894560107455,
        "teds": null,
        "mhs": 0.16297967884340991,
        "prediction_available": true
      },
      "delta_overall": 0.10290875657265186
    },
    {
      "document_id": "156754290",
      "title": "훈장의 가치 바로잡는다 부적절한 정부포상 전면 재검토 착수",
      "department": "행정안전부",
      "approve_date": "04/13/2026 16:00:00",
      "readhim": {
        "overall": 0.7382277179775549,
        "nid": 0.8887991927346115,
        "teds": null,
        "mhs": 0.5876562432204983,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.6466463258142388,
        "nid": 0.8511295616914463,
        "teds": null,
        "mhs": 0.44216308993703135,
        "prediction_available": true
      },
      "delta_overall": 0.09158139216331618
    },
    {
      "document_id": "156754287",
      "title": "\"새만금에 일자리·주거·교통 함께 들어선다\" 새만금 투자지원 TF 본격 가동",
      "department": "국토교통부",
      "approve_date": "04/13/2026 16:00:00",
      "readhim": {
        "overall": 0.6007132441217895,
        "nid": 0.817174515235457,
        "teds": null,
        "mhs": 0.38425197300812197,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4641457183798352,
        "nid": 0.7600314712824547,
        "teds": null,
        "mhs": 0.16825996547721567,
        "prediction_available": true
      },
      "delta_overall": 0.1365675257419543
    },
    {
      "document_id": "156754286",
      "title": "중동전쟁 관련 반려동물 의료제품 수급상황 점검",
      "department": "농림축산식품부",
      "approve_date": "04/13/2026 16:00:00",
      "readhim": {
        "overall": 0.5793447540756742,
        "nid": 0.779031670913724,
        "teds": null,
        "mhs": 0.3796578372376245,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.43941561399837675,
        "nid": 0.7210508123055652,
        "teds": null,
        "mhs": 0.15778041569118828,
        "prediction_available": true
      },
      "delta_overall": 0.13992914007729745
    },
    {
      "document_id": "156754285",
      "title": "주민이 직접 가꾸는 '살고 싶은 농촌' 농식품부, '클린농촌 만들기' 본격 가동",
      "department": "농림축산식품부",
      "approve_date": "04/13/2026 16:00:00",
      "readhim": {
        "overall": 0.0,
        "nid": 0.0,
        "teds": 0.0,
        "mhs": 0.0,
        "prediction_available": false,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.0,
        "nid": 0.0,
        "teds": 0.0,
        "mhs": 0.0,
        "prediction_available": false
      },
      "delta_overall": 0.0
    },
    {
      "document_id": "156754282",
      "title": "홍지선 2차관, 중동상황 극복을 위한 시·도 교통물류 관계자 회의 개최",
      "department": "국토교통부",
      "approve_date": "04/13/2026 15:38:00",
      "readhim": {
        "overall": 0.5285355458818656,
        "nid": 0.7398305084745762,
        "teds": null,
        "mhs": 0.31724058328915494,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.42391460963058114,
        "nid": 0.6747474747474748,
        "teds": null,
        "mhs": 0.17308174451368752,
        "prediction_available": true
      },
      "delta_overall": 0.10462093625128444
    },
    {
      "document_id": "156754281",
      "title": "2026년 재외동포정책 시행계획 확정",
      "department": "외교부",
      "approve_date": "04/13/2026 15:30:14",
      "readhim": {
        "overall": 0.5689172927901633,
        "nid": 0.8238297872340425,
        "teds": null,
        "mhs": 0.31400479834628414,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3913759956056029,
        "nid": 0.7827519912112058,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.17754129718456046
    },
    {
      "document_id": "156754280",
      "title": "(동정) 청년 공무원 만나 조직문화·업무 혁신 이끈다",
      "department": "해양수산부",
      "approve_date": "04/13/2026 15:26:00",
      "readhim": {
        "overall": 0.5623752987607282,
        "nid": 0.7632743362831859,
        "teds": null,
        "mhs": 0.3614762612382707,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4397560479083683,
        "nid": 0.6905370843989771,
        "teds": null,
        "mhs": 0.18897501141775952,
        "prediction_available": true
      },
      "delta_overall": 0.12261925085235992
    },
    {
      "document_id": "156754279",
      "title": "농식품부 기획조정실장, 추경 예산 신속 집행을 위한 재정집행점검회의 개최",
      "department": "농림축산식품부",
      "approve_date": "04/13/2026 15:23:36",
      "readhim": {
        "overall": 0.5666621587822105,
        "nid": 0.7483588621444202,
        "teds": null,
        "mhs": 0.3849654554200008,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.34808157621845837,
        "nid": 0.6961631524369167,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.21858058256375212
    },
    {
      "document_id": "156754278",
      "title": "면세유 이용 현장 및 시설채소 생육동향 점검",
      "department": "농림축산식품부",
      "approve_date": "04/13/2026 15:21:28",
      "readhim": {
        "overall": 0.5509608601317943,
        "nid": 0.7307908020190691,
        "teds": null,
        "mhs": 0.3711309182445197,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.34955633234740524,
        "nid": 0.6991126646948105,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.2014045277843891
    },
    {
      "document_id": "156754277",
      "title": "기상청, '케이(K)-기상' 선진 예보기술로 아시아 기후위기 대응 지원",
      "department": "기상청",
      "approve_date": "04/13/2026 15:00:00",
      "readhim": {
        "overall": 0.5283211284201619,
        "nid": 0.7145328719723183,
        "teds": null,
        "mhs": 0.34210938486800546,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4207275458382129,
        "nid": 0.6309904153354633,
        "teds": null,
        "mhs": 0.21046467634096255,
        "prediction_available": true
      },
      "delta_overall": 0.10759358258194895
    },
    {
      "document_id": "156754275",
      "title": "제2차 외국인 증권투자 유치 자문위원회 개최",
      "department": "재정경제부",
      "approve_date": "04/13/2026 15:00:00",
      "readhim": {
        "overall": 0.5748795378561673,
        "nid": 0.8120016785564413,
        "teds": null,
        "mhs": 0.33775739715589337,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.44022193233404544,
        "nid": 0.7470068694798823,
        "teds": null,
        "mhs": 0.13343699518820862,
        "prediction_available": true
      },
      "delta_overall": 0.13465760552212186
    },
    {
      "document_id": "156754268",
      "title": "석유화학제품 생산현장 릴레이 점검",
      "department": "산업통상부",
      "approve_date": "04/13/2026 14:44:28",
      "readhim": {
        "overall": 0.0,
        "nid": 0.0,
        "teds": 0.0,
        "mhs": 0.0,
        "prediction_available": false,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.26601277432466314,
        "nid": 0.6644562334217506,
        "teds": 0.13358208955223871,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": -0.26601277432466314
    },
    {
      "document_id": "156754267",
      "title": "민간의 우수한 AI소프트웨어, '다수공급자계약'으로 공공시장에 더 빠르게 진입한다",
      "department": "조달청",
      "approve_date": "04/13/2026 14:11:17",
      "readhim": {
        "overall": 0.5394940664886323,
        "nid": 0.7061874768432752,
        "teds": null,
        "mhs": 0.3728006561339894,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.42660098904085975,
        "nid": 0.6640401146131805,
        "teds": null,
        "mhs": 0.18916186346853903,
        "prediction_available": true
      },
      "delta_overall": 0.11289307744777255
    },
    {
      "document_id": "156754265",
      "title": "고유가 피해지원금의 신속한 지급 위해 중앙·지방 총력 대응",
      "department": "행정안전부",
      "approve_date": "04/13/2026 14:00:00",
      "readhim": {
        "overall": 0.5975347208821933,
        "nid": 0.8203866432337434,
        "teds": null,
        "mhs": 0.374682798530643,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4931342800011472,
        "nid": 0.7638522427440633,
        "teds": null,
        "mhs": 0.22241631725823108,
        "prediction_available": true
      },
      "delta_overall": 0.10440044088104611
    },
    {
      "document_id": "156754261",
      "title": "도매시장법인, 한농대 발전기금 기부 잇달아",
      "department": "농림축산식품부",
      "approve_date": "04/13/2026 14:00:00",
      "readhim": {
        "overall": 0.31008862826865596,
        "nid": 0.6171458998935038,
        "teds": 0.0,
        "mhs": 0.3131199849124642,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3045426531791484,
        "nid": 0.7588703837798696,
        "teds": 0.15475757575757565,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.005545975089507549
    },
    {
      "document_id": "156754263",
      "title": "봄에 내리는 순백의 눈꽃···이팝나무길 '봄의 낭만' 선사",
      "department": "산림청",
      "approve_date": "04/13/2026 13:59:01",
      "readhim": {
        "overall": 0.5597883415243682,
        "nid": 0.7497835497835497,
        "teds": null,
        "mhs": 0.3697931332651867,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3406414941128705,
        "nid": 0.681282988225741,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.2191468474114977
    },
    {
      "document_id": "156754259",
      "title": "소비로 꽃피우는 4월, 2026 동행축제 개막",
      "department": "중소벤처기업부",
      "approve_date": "04/13/2026 13:44:07",
      "readhim": {
        "overall": 0.6480914895815524,
        "nid": 0.9033733562035448,
        "teds": null,
        "mhs": 0.39280962295956,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.42513996749142136,
        "nid": 0.8502799349828427,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.22295152209013103
    },
    {
      "document_id": "156754250",
      "title": "관세청, 중동 상황 대응 긴급 수요물품 신속통관 및 물류지원 등 5,070건 조치 및 관세 2,407억원 납기연장 세정지원 실시",
      "department": "관세청",
      "approve_date": "04/13/2026 13:25:12",
      "readhim": {
        "overall": 0.5686679832358277,
        "nid": 0.7968292262622783,
        "teds": null,
        "mhs": 0.3405067402093772,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4243740834974856,
        "nid": 0.7075722092115535,
        "teds": null,
        "mhs": 0.14117595778341774,
        "prediction_available": true
      },
      "delta_overall": 0.14429389973834206
    },
    {
      "document_id": "156754249",
      "title": "관세청, 국제통화기금(IMF)과 디지털 정부 협력 강화 ··· '글로벌 인공지능(AI) 허브' 도약",
      "department": "관세청",
      "approve_date": "04/13/2026 13:23:53",
      "readhim": {
        "overall": 0.5586852281328958,
        "nid": 0.7997951868919612,
        "teds": null,
        "mhs": 0.3175752693738305,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.46479734740456063,
        "nid": 0.7345348270823187,
        "teds": null,
        "mhs": 0.19505986772680262,
        "prediction_available": true
      },
      "delta_overall": 0.09388788072833515
    },
    {
      "document_id": "156754248",
      "title": "국립수목원, 종자은행 20년 보전 야생식물 종자 발아력 확인",
      "department": "산림청",
      "approve_date": "04/13/2026 13:18:27",
      "readhim": {
        "overall": 0.4978852809359419,
        "nid": 0.7305110996386164,
        "teds": null,
        "mhs": 0.26525946223326746,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.5040531208192957,
        "nid": 0.7346617724174096,
        "teds": null,
        "mhs": 0.2734444692211817,
        "prediction_available": true
      },
      "delta_overall": -0.006167839883353732
    },
    {
      "document_id": "156754253",
      "title": "고용노동부, 산업재해 고위험  사업장 10만개소 전수조사",
      "department": "고용노동부",
      "approve_date": "04/13/2026 13:16:55",
      "readhim": {
        "overall": 0.3723994912935155,
        "nid": 0.8885120813904197,
        "teds": 0.0,
        "mhs": 0.2286863924901268,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.32979600362382216,
        "nid": 0.8518743667679839,
        "teds": 0.13235294117647056,
        "mhs": 0.005160702927012095,
        "prediction_available": true
      },
      "delta_overall": 0.04260348766969335
    },
    {
      "document_id": "156754252",
      "title": "2026년 3월 고용행정 통계로 본 노동시장 동향",
      "department": "고용노동부",
      "approve_date": "04/13/2026 13:15:25",
      "readhim": {
        "overall": 0.2694406804121451,
        "nid": 0.45108833352527933,
        "teds": null,
        "mhs": 0.08779302729901084,
        "prediction_available": true,
        "table_timed_out": true
      },
      "opendataloader": {
        "overall": 0.15737768888361736,
        "nid": 0.34903803757514495,
        "teds": 0.09658052542250128,
        "mhs": 0.026514503653205845,
        "prediction_available": true
      },
      "delta_overall": 0.11206299152852772
    },
    {
      "document_id": "156754251",
      "title": "행복도시 개발 경험 세계로... 4개국과 글로벌 협력 강화",
      "department": "행정중심복합도시건설청",
      "approve_date": "04/13/2026 13:12:00",
      "readhim": {
        "overall": 0.5792101425838594,
        "nid": 0.8569182389937108,
        "teds": null,
        "mhs": 0.3015020461740081,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.47444969181714847,
        "nid": 0.7756300464888671,
        "teds": null,
        "mhs": 0.1732693371454298,
        "prediction_available": true
      },
      "delta_overall": 0.10476045076671092
    },
    {
      "document_id": "156754256",
      "title": "경찰, 부패비리 특별단속 결과 총 1,997명 송치, 56명 구속",
      "department": "경찰청",
      "approve_date": "04/13/2026 13:04:57",
      "readhim": {
        "overall": 0.25851163187883053,
        "nid": 0.4204118173679498,
        "teds": 0.046719077454312474,
        "mhs": 0.30840400081422936,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.18517551994683104,
        "nid": 0.38590163934426225,
        "teds": 0.06292127835115746,
        "mhs": 0.10670364214507344,
        "prediction_available": true
      },
      "delta_overall": 0.07333611193199949
    },
    {
      "document_id": "156754246",
      "title": "종량제봉투, 재생원료 사용 확대로 공급망 위기의 파고를 넘는다",
      "department": "기후에너지환경부",
      "approve_date": "04/13/2026 13:00:00",
      "readhim": {
        "overall": 0.6460508410656766,
        "nid": 0.8904593639575971,
        "teds": 0.7906976744186046,
        "mhs": 0.2569954848208281,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.30481448929526106,
        "nid": 0.7899268887083672,
        "teds": 0.0728682170542636,
        "mhs": 0.05164836212315238,
        "prediction_available": true
      },
      "delta_overall": 0.3412363517704155
    },
    {
      "document_id": "156754241",
      "title": "행안부-기후부, 남원시 람천 불법공사 관련 정부합동감사 결과 통보",
      "department": "행정안전부",
      "approve_date": "04/13/2026 12:00:00",
      "readhim": {
        "overall": 0.7285017680858137,
        "nid": 0.8764215314632299,
        "teds": null,
        "mhs": 0.5805820047083974,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.5853921664346164,
        "nid": 0.8338467113607537,
        "teds": null,
        "mhs": 0.33693762150847917,
        "prediction_available": true
      },
      "delta_overall": 0.14310960165119724
    },
    {
      "document_id": "156754239",
      "title": "행안부-기후부, 남원시 람천 불법공사 관련 정부합동감사 결과 통보",
      "department": "기후에너지환경부",
      "approve_date": "04/13/2026 12:00:00",
      "readhim": {
        "overall": 0.7284068598002869,
        "nid": 0.8771662540468482,
        "teds": null,
        "mhs": 0.5796474655537255,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.5858410463239545,
        "nid": 0.834608378870674,
        "teds": null,
        "mhs": 0.33707371377723494,
        "prediction_available": true
      },
      "delta_overall": 0.14256581347633235
    },
    {
      "document_id": "156754238",
      "title": "전력망 안정성 확보 위해 기술기준 고도화 및 전력감독체계 개선 공감대 형성",
      "department": "기후에너지환경부",
      "approve_date": "04/13/2026 12:00:00",
      "readhim": {
        "overall": 0.5163810066195803,
        "nid": 0.9304920677601506,
        "teds": 0.4543237250554324,
        "mhs": 0.16432722704315805,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.40712320151432796,
        "nid": 0.893430460002698,
        "teds": -0.006796924145602512,
        "mhs": 0.33473606868588834,
        "prediction_available": true
      },
      "delta_overall": 0.10925780510525235
    },
    {
      "document_id": "156754237",
      "title": "태양광 기술 전문가, 정부 민간인재 영입지원 발탁",
      "department": "인사혁신처",
      "approve_date": "04/13/2026 12:00:00",
      "readhim": {
        "overall": 0.7491740428700173,
        "nid": 0.8504356243949661,
        "teds": 0.98796992481203,
        "mhs": 0.4091165794030559,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3426129533929508,
        "nid": 0.7971371057928875,
        "teds": 0.23070175438596485,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.40656108947706654
    },
    {
      "document_id": "156754235",
      "title": "봄철 참진드기 활동 시작, 전국 감시체계 가동",
      "department": "질병관리청",
      "approve_date": "04/13/2026 12:00:00",
      "readhim": {
        "overall": 0.31270954080307156,
        "nid": 0.5865022267899966,
        "teds": 0.0,
        "mhs": 0.35162639561921805,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.34119238549466885,
        "nid": 0.7322233465182596,
        "teds": 0.13910243028981506,
        "mhs": 0.15225137967593205,
        "prediction_available": true
      },
      "delta_overall": -0.028482844691597287
    },
    {
      "document_id": "156754228",
      "title": "에이치엘홀딩스(주)의 지주회사  행위제한규정 위반 제재",
      "department": "공정거래위원회",
      "approve_date": "04/13/2026 12:00:00",
      "readhim": {
        "overall": 0.43850102337471153,
        "nid": 0.8310862654828456,
        "teds": 0.3815479352937585,
        "mhs": 0.10286886934753059,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.40078650954474426,
        "nid": 0.8170769073639056,
        "teds": 0.31596449710993,
        "mhs": 0.06931812416039729,
        "prediction_available": true
      },
      "delta_overall": 0.03771451382996727
    },
    {
      "document_id": "156754224",
      "title": "(참고자료)산업부 '26년 제1회 추가경정예산안 1조 980억원 확정",
      "department": "산업통상부",
      "approve_date": "04/13/2026 11:23:48",
      "readhim": {
        "overall": 0.0,
        "nid": 0.0,
        "teds": 0.0,
        "mhs": 0.0,
        "prediction_available": false,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.15809006192996658,
        "nid": 0.4535776182223322,
        "teds": 0.020692567567567544,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": -0.15809006192996658
    },
    {
      "document_id": "156754222",
      "title": "국립고궁박물관, 세계박람회 조선 최초 출품작 '의장기' 5건 보존처리",
      "department": "국가유산청",
      "approve_date": "04/13/2026 11:20:02",
      "readhim": {
        "overall": 0.4856142340100826,
        "nid": 0.7486385783892233,
        "teds": null,
        "mhs": 0.22258988963094184,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.04719600222098835,
        "nid": 0.0943920044419767,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.4384182317890942
    },
    {
      "document_id": "156754216",
      "title": "회화와 유적으로 만나는 '조선 왕실의 말(馬)'",
      "department": "국가유산청",
      "approve_date": "04/13/2026 11:13:08",
      "readhim": {
        "overall": 0.5653013755679708,
        "nid": 0.790818536162841,
        "teds": null,
        "mhs": 0.33978421497310063,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.054469273743016744,
        "nid": 0.10893854748603349,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.510832101824954
    },
    {
      "document_id": "156754214",
      "title": "1937년과 2020년 경주 월성 수습 비편들(돌비석 조각) 원래 하나였다",
      "department": "국가유산청",
      "approve_date": "04/13/2026 11:10:18",
      "readhim": {
        "overall": 0.6165018613456994,
        "nid": 0.894589028271859,
        "teds": null,
        "mhs": 0.33841469441953975,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.0660146699266504,
        "nid": 0.1320293398533008,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.550487191419049
    },
    {
      "document_id": "156754212",
      "title": "국립문화유산연구원-한국고고학회 『2026 여름 발굴캠프』 참가자 모집",
      "department": "국가유산청",
      "approve_date": "04/13/2026 11:06:51",
      "readhim": {
        "overall": 0.576521050638684,
        "nid": 0.827891156462585,
        "teds": null,
        "mhs": 0.325150944814783,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.058337919647771075,
        "nid": 0.11667583929554215,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.5181831309909128
    },
    {
      "document_id": "156754211",
      "title": "경력법조인 출신 신임검사 임용 대상자 명단 공개",
      "department": "법무부",
      "approve_date": "04/13/2026 11:04:01",
      "readhim": {
        "overall": 0.23548018262817835,
        "nid": 0.3094170403587444,
        "teds": 0.0,
        "mhs": 0.39702350752579063,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.13351057567790292,
        "nid": 0.2681787858572382,
        "teds": 0.13235294117647056,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.10196960695027543
    },
    {
      "document_id": "156754266",
      "title": "김민석 국무총리, 완도 화재 순직 소방관 조문",
      "department": "국무조정실",
      "approve_date": "04/13/2026 11:00:00",
      "readhim": {
        "overall": 0.5414754717201827,
        "nid": 0.7236119585112875,
        "teds": null,
        "mhs": 0.359338984929078,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.41986226494979306,
        "nid": 0.6636311895276039,
        "teds": null,
        "mhs": 0.1760933403719822,
        "prediction_available": true
      },
      "delta_overall": 0.12161320677038967
    },
    {
      "document_id": "156754210",
      "title": "아시아 5개국에서 '한국형 인공지능(AI) 도시 기술'의 실증 본격화",
      "department": "국토교통부",
      "approve_date": "04/13/2026 11:00:00",
      "readhim": {
        "overall": 0.31240548296502396,
        "nid": 0.6983559685489635,
        "teds": 0.0,
        "mhs": 0.2388604803461084,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.2871240193059997,
        "nid": 0.7236124702921852,
        "teds": 0.13775958762581375,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.025281463659024284
    },
    {
      "document_id": "156754209",
      "title": "농식품 스타트업기업 16개사, 팁스 R&D 별도 선정으로 최대 60억원 지원 받는다.",
      "department": "농림축산식품부",
      "approve_date": "04/13/2026 11:00:00",
      "readhim": {
        "overall": 0.4078029732350068,
        "nid": 0.7295240936893927,
        "teds": 0.4171747269440099,
        "mhs": 0.07671009907161774,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4303521763940621,
        "nid": 0.8059739434381952,
        "teds": 0.40412085958274546,
        "mhs": 0.08096172616124575,
        "prediction_available": true
      },
      "delta_overall": -0.022549203159055287
    },
    {
      "document_id": "156754206",
      "title": "보훈부, 2026년 국외 보훈사적지 답사 참가자 13일부터 모집",
      "department": "국가보훈부",
      "approve_date": "04/13/2026 10:56:17",
      "readhim": {
        "overall": 0.40287081920187,
        "nid": 0.5992217898832685,
        "teds": null,
        "mhs": 0.20651984852047156,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3149438371678301,
        "nid": 0.538735647353834,
        "teds": null,
        "mhs": 0.09115202698182623,
        "prediction_available": true
      },
      "delta_overall": 0.08792698203403992
    },
    {
      "document_id": "156754205",
      "title": "보훈부, 성과 중심 공직문화 확산 추진 특별성과 포상 실시",
      "department": "국가보훈부",
      "approve_date": "04/13/2026 10:55:02",
      "readhim": {
        "overall": 0.5979142669912563,
        "nid": 0.8267498267498268,
        "teds": null,
        "mhs": 0.36907870723268577,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.38237221494102225,
        "nid": 0.7647444298820445,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.21554205205023402
    },
    {
      "document_id": "156754194",
      "title": "플라스틱 가공 중소기업 원가 상승 부담 완화를 위해 대·중소기업 상생협약 체결",
      "department": "중소벤처기업부",
      "approve_date": "04/13/2026 10:46:30",
      "readhim": {
        "overall": 0.3491049061452401,
        "nid": 0.7811111111111111,
        "teds": 0.06138813396877907,
        "mhs": 0.20481547335583017,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3438246654500004,
        "nid": 0.7590852685694025,
        "teds": 0.1411290322580645,
        "mhs": 0.13125969552253414,
        "prediction_available": true
      },
      "delta_overall": 0.005280240695239691
    },
    {
      "document_id": "156754191",
      "title": "\"통역사 없어도 OK\" 외국인 건설근로자, 퇴직공제금 신청 '인공지능(AI)로 해결'",
      "department": "고용노동부",
      "approve_date": "04/13/2026 10:26:55",
      "readhim": {
        "overall": 0.5454644754624718,
        "nid": 0.7098265895953757,
        "teds": null,
        "mhs": 0.3811023613295679,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.2932067932067932,
        "nid": 0.5864135864135864,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.2522576822556786
    },
    {
      "document_id": "156754190",
      "title": "건설근로자공제회, 대규모 건설현장서 복지·금융지원 홍보 캠페인 전개",
      "department": "고용노동부",
      "approve_date": "04/13/2026 10:26:05",
      "readhim": {
        "overall": 0.3689664973800064,
        "nid": 0.6863373957665169,
        "teds": 0.047254150702426445,
        "mhs": 0.37330794567107606,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.31875896294318007,
        "nid": 0.7002755714054142,
        "teds": 0.06849315068493156,
        "mhs": 0.18750816673919446,
        "prediction_available": true
      },
      "delta_overall": 0.05020753443682635
    },
    {
      "document_id": "156754189",
      "title": "한국기술교육대 '참여형 캠퍼스 안전문화' 선도",
      "department": "고용노동부",
      "approve_date": "04/13/2026 10:24:48",
      "readhim": {
        "overall": 0.5762727282612515,
        "nid": 0.8424242424242423,
        "teds": 0.5606271777003484,
        "mhs": 0.32576676465916365,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.45504265735610955,
        "nid": 0.8018467220683287,
        "teds": 0.56328125,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.12123007090514198
    },
    {
      "document_id": "156754188",
      "title": "한국고용노동교육원 노사관계전문가과정 재개",
      "department": "고용노동부",
      "approve_date": "04/13/2026 10:23:16",
      "readhim": {
        "overall": 0.6980140014700692,
        "nid": 0.9081901223099551,
        "teds": 0.9961904761904762,
        "mhs": 0.18966140590977643,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.5761794165742636,
        "nid": 0.8867294260552687,
        "teds": 0.5929705215419501,
        "mhs": 0.248838302125572,
        "prediction_available": true
      },
      "delta_overall": 0.12183458489580556
    },
    {
      "document_id": "156754187",
      "title": "인공지능(AI) 전환 과정에서 일자리와 공존을 위해 지혜를 모으다.",
      "department": "고용노동부",
      "approve_date": "04/13/2026 10:21:44",
      "readhim": {
        "overall": 0.6306467284688905,
        "nid": 0.9341101694915256,
        "teds": 0.7928743961352657,
        "mhs": 0.16495561977987994,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.36946043810055595,
        "nid": 0.864554539655539,
        "teds": 0.08904136280131392,
        "mhs": 0.15478541184481487,
        "prediction_available": true
      },
      "delta_overall": 0.2611862903683345
    },
    {
      "document_id": "156754185",
      "title": "\"방송·미디어·통신 정책 제안해 주세요\"",
      "department": "방송미디어통신위원회",
      "approve_date": "04/13/2026 10:07:00",
      "readhim": {
        "overall": 0.5452352293888556,
        "nid": 0.7225732337736932,
        "teds": null,
        "mhs": 0.3678972250040181,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.32519893899204244,
        "nid": 0.6503978779840849,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.22003629039681316
    },
    {
      "document_id": "156754181",
      "title": "원안위, 제10차 원자력안전협약(CNS) 이행검토회의 참석",
      "department": "원자력안전위원회",
      "approve_date": "04/13/2026 10:05:01",
      "readhim": {
        "overall": 0.6009085901997981,
        "nid": 0.8205317577548006,
        "teds": null,
        "mhs": 0.3812854226447956,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.409890104712515,
        "nid": 0.7600700525394045,
        "teds": null,
        "mhs": 0.05971015688562553,
        "prediction_available": true
      },
      "delta_overall": 0.19101848548728312
    },
    {
      "document_id": "156754183",
      "title": "경찰청, 봄 행락철 버스전용차로 위반 · 대형버스 법규 위반 집중단속 실시",
      "department": "경찰청",
      "approve_date": "04/13/2026 10:04:20",
      "readhim": {
        "overall": 0.578697874613856,
        "nid": 0.8568329718004338,
        "teds": 0.6,
        "mhs": 0.27926065204113426,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3657426651276234,
        "nid": 0.6965527902303292,
        "teds": 0.20285714285714285,
        "mhs": 0.1978180622953981,
        "prediction_available": true
      },
      "delta_overall": 0.21295520948623264
    },
    {
      "document_id": "156754182",
      "title": "개인정보 유출한 공공기관 대상 패널티 대폭 확대한다",
      "department": "개인정보보호위원회",
      "approve_date": "04/13/2026 10:00:00",
      "readhim": {
        "overall": 0.10421707158984139,
        "nid": 0.17761188774252612,
        "teds": 0.004413892908827766,
        "mhs": 0.1306254341181703,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.09802964484987646,
        "nid": 0.1779616078057058,
        "teds": 0.004109323512308638,
        "mhs": 0.11201800323161493,
        "prediction_available": true
      },
      "delta_overall": 0.006187426739964932
    },
    {
      "document_id": "156754180",
      "title": "중동전쟁으로 인한 현장의 고용위기, 신속한 제도개선을 통해 빈틈없이 지원한다.",
      "department": "고용노동부",
      "approve_date": "04/13/2026 09:48:19",
      "readhim": {
        "overall": 0.4845176247729291,
        "nid": 0.8440869132526123,
        "teds": 0.2956145017248606,
        "mhs": 0.3138514593413144,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3759596334447606,
        "nid": 0.8186743148502231,
        "teds": 0.20621133763299626,
        "mhs": 0.10299324785106223,
        "prediction_available": true
      },
      "delta_overall": 0.10855799132816851
    },
    {
      "document_id": "156754155",
      "title": "K-브랜드 정부인증제도 도입... 추경 95억원 확정",
      "department": "지식재산처",
      "approve_date": "04/13/2026 09:34:29",
      "readhim": {
        "overall": 0.49447007850275765,
        "nid": 0.7308934337997848,
        "teds": null,
        "mhs": 0.2580467232057305,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4221998801877787,
        "nid": 0.6408518877057116,
        "teds": null,
        "mhs": 0.20354787266984586,
        "prediction_available": true
      },
      "delta_overall": 0.07227019831497894
    },
    {
      "document_id": "156754151",
      "title": "세계보건기구(WHO), 대한민국 합동외부평가 최종보고서 공개(4.13.월)",
      "department": "질병관리청",
      "approve_date": "04/13/2026 09:30:00",
      "readhim": {
        "overall": 0.343532908226909,
        "nid": 0.5119826886664863,
        "teds": 0.12592286501377414,
        "mhs": 0.39269317100046663,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.24296782597601033,
        "nid": 0.5615660685154975,
        "teds": 0.10762052628702945,
        "mhs": 0.05971688312550405,
        "prediction_available": true
      },
      "delta_overall": 0.10056508225089869
    },
    {
      "document_id": "156754154",
      "title": "국민의 생각으로 지식재산 정책을 바꿔주세요!",
      "department": "지식재산처",
      "approve_date": "04/13/2026 09:29:14",
      "readhim": {
        "overall": 0.5350049207899068,
        "nid": 0.8006496142915144,
        "teds": null,
        "mhs": 0.2693602272882992,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4873060245068898,
        "nid": 0.7378347793285552,
        "teds": null,
        "mhs": 0.2367772696852244,
        "prediction_available": true
      },
      "delta_overall": 0.04769889628301699
    },
    {
      "document_id": "156754146",
      "title": "걷고, 인증하고, 특별한 경험까지",
      "department": "산림청",
      "approve_date": "04/13/2026 09:19:01",
      "readhim": {
        "overall": 0.5580824708253538,
        "nid": 0.7320379575237235,
        "teds": null,
        "mhs": 0.3841269841269841,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.33262621977089524,
        "nid": 0.6652524395417905,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.22545625105445855
    },
    {
      "document_id": "156754148",
      "title": "지식재산처, 박현희 첫 여성 기획조정관 임명",
      "department": "지식재산처",
      "approve_date": "04/13/2026 09:15:00",
      "readhim": {
        "overall": 0.5064184365244159,
        "nid": 0.8023868023868023,
        "teds": null,
        "mhs": 0.21045007066202948,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.583519780353432,
        "nid": 0.7745969068772622,
        "teds": null,
        "mhs": 0.39244265382960186,
        "prediction_available": true
      },
      "delta_overall": -0.07710134382901612
    },
    {
      "document_id": "156754147",
      "title": "2026년 4월 1일 ~ 4월 10일 수출입 현황 [잠정치]",
      "department": "관세청",
      "approve_date": "04/13/2026 09:14:18",
      "readhim": {
        "overall": 0.49103634433728266,
        "nid": 0.6610611084793936,
        "teds": 0.5465971201065394,
        "mhs": 0.26545080442591507,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4701591366806028,
        "nid": 0.6770013882461822,
        "teds": 0.6068017316017316,
        "mhs": 0.12667429019389442,
        "prediction_available": true
      },
      "delta_overall": 0.020877207656679886
    },
    {
      "document_id": "156754144",
      "title": "조달청, 국민의 마음을 사로잡은 심(心)스틸러 발굴",
      "department": "조달청",
      "approve_date": "04/13/2026 09:11:04",
      "readhim": {
        "overall": 0.574681956207082,
        "nid": 0.754414125200642,
        "teds": null,
        "mhs": 0.3949497872135219,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.33578431372549017,
        "nid": 0.6715686274509803,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.2388976424815918
    },
    {
      "document_id": "156754143",
      "title": "\"윤리경영이 곧 조직의 경쟁력!\",  2026년 윤리경영 자율준수 프로그램 지원 사업 대상 모집 실시",
      "department": "국민권익위원회",
      "approve_date": "04/13/2026 09:07:04",
      "readhim": {
        "overall": 0.5820191648390253,
        "nid": 0.7944676744934063,
        "teds": null,
        "mhs": 0.36957065518464427,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4495417121216,
        "nid": 0.7194502539587692,
        "teds": null,
        "mhs": 0.17963317028443082,
        "prediction_available": true
      },
      "delta_overall": 0.13247745271742528
    },
    {
      "document_id": "156754142",
      "title": "\"모두의 생각, '국민생각함'에 모여라\"… 국민 눈높이에 맞는 정책 발굴 나서",
      "department": "국민권익위원회",
      "approve_date": "04/13/2026 09:04:21",
      "readhim": {
        "overall": 0.5272739137596636,
        "nid": 0.8490661282180717,
        "teds": null,
        "mhs": 0.20548169930125537,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4319178526553788,
        "nid": 0.7941738299904489,
        "teds": null,
        "mhs": 0.06966187532030865,
        "prediction_available": true
      },
      "delta_overall": 0.0953560611042848
    },
    {
      "document_id": "156754139",
      "title": "우리나라 '이동형 재난통신 차량 기술', 아시아·태평양지역 국제표준 됐다",
      "department": "행정안전부",
      "approve_date": "04/13/2026 09:00:00",
      "readhim": {
        "overall": 0.5599504442925496,
        "nid": 0.7962121212121211,
        "teds": null,
        "mhs": 0.3236887673729779,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4863338523343844,
        "nid": 0.7365398420674802,
        "teds": null,
        "mhs": 0.2361278626012886,
        "prediction_available": true
      },
      "delta_overall": 0.07361659195816517
    },
    {
      "document_id": "156754137",
      "title": "국가재난안전교육원-EBS, 재난안전 교육 발전을 위한 업무협약 체결",
      "department": "행정안전부",
      "approve_date": "04/13/2026 09:00:00",
      "readhim": {
        "overall": 0.5781197268421059,
        "nid": 0.7729220222793487,
        "teds": null,
        "mhs": 0.3833174314048631,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.45790139778121336,
        "nid": 0.7102204408817634,
        "teds": null,
        "mhs": 0.20558235468066333,
        "prediction_available": true
      },
      "delta_overall": 0.12021832906089253
    },
    {
      "document_id": "156754135",
      "title": "생명을 존중하는 안전 사회 위해, 대통령 소속 '국민생명안전위원회' 만든다",
      "department": "행정안전부",
      "approve_date": "04/13/2026 09:00:00",
      "readhim": {
        "overall": 0.514669562903443,
        "nid": 0.7962007020441875,
        "teds": null,
        "mhs": 0.23313842376269844,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3998792623652269,
        "nid": 0.7491704079640836,
        "teds": null,
        "mhs": 0.050588116766370206,
        "prediction_available": true
      },
      "delta_overall": 0.1147903005382161
    },
    {
      "document_id": "156754132",
      "title": "'체크인, 검역' 우리가 만드는 여행건강 이야기, 국민 생각 공모전 개최(4.13.월)",
      "department": "질병관리청",
      "approve_date": "04/13/2026 08:50:00",
      "readhim": {
        "overall": 0.5695586271316437,
        "nid": 0.8148511612692182,
        "teds": 0.7144128466238853,
        "mhs": 0.17941187350182763,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.42616996129621204,
        "nid": 0.7864659219685932,
        "teds": 0.3303832520807872,
        "mhs": 0.16166070983925585,
        "prediction_available": true
      },
      "delta_overall": 0.1433886658354317
    },
    {
      "document_id": "156754131",
      "title": "고위공무원 신규임용",
      "department": "방위사업청",
      "approve_date": "04/13/2026 08:40:15",
      "readhim": {
        "overall": 0.44125277896031406,
        "nid": 0.5157750342935528,
        "teds": null,
        "mhs": 0.36673052362707537,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.2009345794392524,
        "nid": 0.4018691588785048,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.24031819952106168
    },
    {
      "document_id": "156754130",
      "title": "(동정) 부산공동어시장에서 수산분야 현장 목소리 청취",
      "department": "해양수산부",
      "approve_date": "04/13/2026 08:40:00",
      "readhim": {
        "overall": 0.3705792761333135,
        "nid": 0.7290813341135167,
        "teds": 0.0,
        "mhs": 0.3826564942864237,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.2720420646891235,
        "nid": 0.6720085470085471,
        "teds": 0.14411764705882346,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.09853721144418998
    },
    {
      "document_id": "156754128",
      "title": "범정부·기업 방산협력 사절단 칠레·브라질에서 K-방산 세일즈 활동",
      "department": "방위사업청",
      "approve_date": "04/13/2026 08:27:46",
      "readhim": {
        "overall": 0.6128820095298513,
        "nid": 0.8497560975609756,
        "teds": null,
        "mhs": 0.3760079214987271,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.49668171398214683,
        "nid": 0.7942897261876901,
        "teds": null,
        "mhs": 0.19907370177660355,
        "prediction_available": true
      },
      "delta_overall": 0.11620029554770445
    },
    {
      "document_id": "156754127",
      "title": "K-유통 산업, 이제는 해외로 나간다",
      "department": "산업통상부",
      "approve_date": "04/13/2026 08:23:04",
      "readhim": {
        "overall": 0.0,
        "nid": 0.0,
        "teds": 0.0,
        "mhs": 0.0,
        "prediction_available": false,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3861018247330295,
        "nid": 0.7490174059517125,
        "teds": 0.21749907032149973,
        "mhs": 0.19178899792587634,
        "prediction_available": true
      },
      "delta_overall": -0.3861018247330295
    },
    {
      "document_id": "156754126",
      "title": "\"표시량 믿고 샀는데...\" 4개중 1개는 내용량 부족",
      "department": "산업통상부",
      "approve_date": "04/13/2026 08:22:04",
      "readhim": {
        "overall": 0.2858537461308005,
        "nid": 0.5707987824078933,
        "teds": 0.01639839034205226,
        "mhs": 0.27036406564245596,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.19708371759142082,
        "nid": 0.5447376402790416,
        "teds": 0.018269778030734263,
        "mhs": 0.02824373446448658,
        "prediction_available": true
      },
      "delta_overall": 0.08877002853937968
    },
    {
      "document_id": "156754125",
      "title": "한-방글라데시 포괄적경제동반자협정(CEPA) 제3차 공식협상(4.12.(일) ~ 17.(금)) 개최",
      "department": "산업통상부",
      "approve_date": "04/13/2026 08:21:08",
      "readhim": {
        "overall": 0.0,
        "nid": 0.0,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": false,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.45992310875012293,
        "nid": 0.7315384615384615,
        "teds": null,
        "mhs": 0.1883077559617844,
        "prediction_available": true
      },
      "delta_overall": -0.45992310875012293
    },
    {
      "document_id": "156754122",
      "title": "'반값 여행' 혜택, 놓치지 말고 얼른 사전 신청하세요",
      "department": "문화체육관광부",
      "approve_date": "04/13/2026 08:14:51",
      "readhim": {
        "overall": 0.36013874166645227,
        "nid": 0.7804042480301473,
        "teds": 0.0,
        "mhs": 0.30001197696920945,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.26990461260529214,
        "nid": 0.7090965538652592,
        "teds": 0.10061728395061731,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.09023412906116013
    },
    {
      "document_id": "156754121",
      "title": "일상에서 '인문 가치'를 더 깊고, 넓게 나눌 기관 찾아요",
      "department": "문화체육관광부",
      "approve_date": "04/13/2026 08:14:04",
      "readhim": {
        "overall": 0.5675132845203422,
        "nid": 0.842363324344202,
        "teds": 0.6918701599577959,
        "mhs": 0.16830636925902864,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.492274487618221,
        "nid": 0.8352713178294574,
        "teds": 0.4863669656128895,
        "mhs": 0.15518517941231613,
        "prediction_available": true
      },
      "delta_overall": 0.07523879690212121
    },
    {
      "document_id": "156754124",
      "title": "중기부, 탄소 감축 희망 공급망 내 협력기업에  에너지 고효율・탄소 저감 설비 구축 지원한다!",
      "department": "중소벤처기업부",
      "approve_date": "04/13/2026 08:13:25",
      "readhim": {
        "overall": 0.39841861800487194,
        "nid": 0.767162471395881,
        "teds": 0.26887969549607493,
        "mhs": 0.15921368712265982,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3419125317880772,
        "nid": 0.7606294864715628,
        "teds": 0.08834800923408526,
        "mhs": 0.17676009965858364,
        "prediction_available": true
      },
      "delta_overall": 0.05650608621679476
    },
    {
      "document_id": "156754120",
      "title": "'케이-그림책', '2026 볼로냐아동도서전'에서 세계 시장 공략",
      "department": "문화체육관광부",
      "approve_date": "04/13/2026 08:13:18",
      "readhim": {
        "overall": 0.12503151256063047,
        "nid": 0.20608350651804275,
        "teds": 0.013814601832229267,
        "mhs": 0.15519642933161937,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.14273228808216828,
        "nid": 0.24765817584223504,
        "teds": 0.019918125130755415,
        "mhs": 0.16062056327351437,
        "prediction_available": true
      },
      "delta_overall": -0.017700775521537815
    },
    {
      "document_id": "156754119",
      "title": "법무부, 제32회「외국인 인권보호 및 권익증진협의회」 개최",
      "department": "법무부",
      "approve_date": "04/13/2026 07:32:35",
      "readhim": {
        "overall": 0.3663370325307789,
        "nid": 0.7478502080443827,
        "teds": 0.0,
        "mhs": 0.3511608895479541,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.2510511470286833,
        "nid": 0.703862660944206,
        "teds": 0.04929078014184385,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.11528588550209562
    },
    {
      "document_id": "156754117",
      "title": "기후위기 대응 등 10개 국정과제 이행 공로자 대상으로 특별성과 포상",
      "department": "기후에너지환경부",
      "approve_date": "04/13/2026 06:00:00",
      "readhim": {
        "overall": 0.445332201760926,
        "nid": 0.6461282264779351,
        "teds": null,
        "mhs": 0.24453617704391695,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3874115070001597,
        "nid": 0.6322740404457284,
        "teds": null,
        "mhs": 0.14254897355459095,
        "prediction_available": true
      },
      "delta_overall": 0.057920694760766334
    },
    {
      "document_id": "156754244",
      "title": "성평등가족부, 2026년 성평등 조직문화 조성 사업설명회 개최",
      "department": "성평등가족부",
      "approve_date": "04/13/2026 00:00:00",
      "readhim": {
        "overall": 0.4351860989084077,
        "nid": 0.6958915713680645,
        "teds": null,
        "mhs": 0.17448062644875095,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4043873144160171,
        "nid": 0.648129625925185,
        "teds": null,
        "mhs": 0.16064500290684924,
        "prediction_available": true
      },
      "delta_overall": 0.030798784492390596
    },
    {
      "document_id": "156754178",
      "title": "제266차 대외경제장관회의 개최",
      "department": "재정경제부",
      "approve_date": "04/13/2026 00:00:00",
      "readhim": {
        "overall": 0.23283545153136803,
        "nid": 0.3758506368871052,
        "teds": null,
        "mhs": 0.08982026617563088,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.43475943288256663,
        "nid": 0.78599487617421,
        "teds": null,
        "mhs": 0.08352398959092322,
        "prediction_available": true
      },
      "delta_overall": -0.2019239813511986
    },
    {
      "document_id": "156754149",
      "title": "제1회 '금융위人상' 시상, 탁월한 성과에 파격포상",
      "department": "금융위원회",
      "approve_date": "04/13/2026 00:00:00",
      "readhim": {
        "overall": 0.3378246864511772,
        "nid": 0.9174093879976233,
        "teds": 0.0,
        "mhs": 0.09606467135590835,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3489539132847252,
        "nid": 0.8862252663622526,
        "teds": 0.07512019230769229,
        "mhs": 0.0855162811842306,
        "prediction_available": true
      },
      "delta_overall": -0.011129226833548
    },
    {
      "document_id": "156754116",
      "title": "국제경제관리관, 홍콩·싱가포르 금융기관 대상으로 투자자 설명(IR) 실시",
      "department": "재정경제부",
      "approve_date": "04/12/2026 19:50:11",
      "readhim": {
        "overall": 0.5900978839621367,
        "nid": 0.8035410282601293,
        "teds": null,
        "mhs": 0.376654739664144,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3719512195121951,
        "nid": 0.7439024390243902,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.21814666444994157
    },
    {
      "document_id": "156754103",
      "title": "범정부·기업 방산협력 사절단 칠레·브라질에서 K-방산 세일즈 활동",
      "department": "외교부",
      "approve_date": "04/12/2026 14:00:00",
      "readhim": {
        "overall": 0.5371230945075747,
        "nid": 0.8262393590385578,
        "teds": null,
        "mhs": 0.24800682997659151,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3888354186717999,
        "nid": 0.7776708373435998,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.1482876758357748
    },
    {
      "document_id": "156754129",
      "title": "2025년 가맹사업 현황 통계 발표",
      "department": "공정거래위원회",
      "approve_date": "04/12/2026 12:00:00",
      "readhim": {
        "overall": 0.3080369057480827,
        "nid": 0.5235837094892732,
        "teds": null,
        "mhs": 0.09249010200689212,
        "prediction_available": true,
        "table_timed_out": true
      },
      "opendataloader": {
        "overall": 0.2540562926254108,
        "nid": 0.5548681211331814,
        "teds": 0.14164334970878423,
        "mhs": 0.06565740703426681,
        "prediction_available": true
      },
      "delta_overall": 0.05398061312267188
    },
    {
      "document_id": "156754101",
      "title": "환경분야 시험·검사 전문성 높인다… 현장 요구 반영한 맞춤형 교육 본격 확대",
      "department": "기후에너지환경부",
      "approve_date": "04/12/2026 12:00:00",
      "readhim": {
        "overall": 0.7542674244449302,
        "nid": 0.873968705547653,
        "teds": 0.9611743611321931,
        "mhs": 0.4276592066549445,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.5948167010871991,
        "nid": 0.8477990892783221,
        "teds": 0.7647299661562704,
        "mhs": 0.1719210478270048,
        "prediction_available": true
      },
      "delta_overall": 0.15945072335773114
    },
    {
      "document_id": "156754098",
      "title": "우리 동네 교통·안전 문제,  '도시 데이터'로 똑똑하게 해결한다",
      "department": "국토교통부",
      "approve_date": "04/12/2026 11:00:00",
      "readhim": {
        "overall": 0.5942111598678295,
        "nid": 0.8125359401955147,
        "teds": null,
        "mhs": 0.37588637954014437,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.45168761029296994,
        "nid": 0.7524966261808366,
        "teds": null,
        "mhs": 0.15087859440510332,
        "prediction_available": true
      },
      "delta_overall": 0.14252354957485952
    },
    {
      "document_id": "156754097",
      "title": "수산물 수출 포장비 최대 2천만 원 지원… 4월 13일부터 참여업체 모집",
      "department": "해양수산부",
      "approve_date": "04/12/2026 11:00:00",
      "readhim": {
        "overall": 0.34291496520413095,
        "nid": 0.6179832793038731,
        "teds": 0.19166740094575152,
        "mhs": 0.21909421536276807,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3229509943764039,
        "nid": 0.7065073041168659,
        "teds": 0.26234567901234573,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.01996397082772705
    },
    {
      "document_id": "156754096",
      "title": "이상기후에 맞서, 벼 키다리병원균 4종 한 번에 찾는다!",
      "department": "농림축산식품부",
      "approve_date": "04/12/2026 11:00:00",
      "readhim": {
        "overall": 0.5982857666646998,
        "nid": 0.8208744710860367,
        "teds": 0.6705882352941176,
        "mhs": 0.30339459361394483,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.4010905424755578,
        "nid": 0.7763037511436415,
        "teds": 0.2923152715985863,
        "mhs": 0.13465260468444573,
        "prediction_available": true
      },
      "delta_overall": 0.19719522418914198
    },
    {
      "document_id": "156754141",
      "title": "전남 완도군 냉동창고 화재 관련 긴급 지시",
      "department": "행정안전부",
      "approve_date": "04/12/2026 10:30:00",
      "readhim": {
        "overall": 0.47272205469001255,
        "nid": 0.6139455782312926,
        "teds": null,
        "mhs": 0.3314985311487325,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.30042707478165726,
        "nid": 0.5276532137518685,
        "teds": null,
        "mhs": 0.07320093581144604,
        "prediction_available": true
      },
      "delta_overall": 0.1722949799083553
    },
    {
      "document_id": "156754105",
      "title": "김민석 국무총리, 완도 냉동창고 화재 관련 긴급지시",
      "department": "국무조정실",
      "approve_date": "04/12/2026 10:30:00",
      "readhim": {
        "overall": 0.5129038073267473,
        "nid": 0.6656050955414012,
        "teds": null,
        "mhs": 0.36020251911209356,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3893150852619435,
        "nid": 0.5902621722846442,
        "teds": null,
        "mhs": 0.18836799823924288,
        "prediction_available": true
      },
      "delta_overall": 0.12358872206480381
    },
    {
      "document_id": "156754104",
      "title": "12·29 여객기 참사 현장 전면 재수색 추진 보도자료",
      "department": "국무조정실",
      "approve_date": "04/12/2026 10:00:00",
      "readhim": {
        "overall": 0.2935452112272641,
        "nid": 0.31935694112535307,
        "teds": null,
        "mhs": 0.2677334813291752,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3194104815627866,
        "nid": 0.44236176194939086,
        "teds": null,
        "mhs": 0.19645920117618232,
        "prediction_available": true
      },
      "delta_overall": -0.025865270335522494
    },
    {
      "document_id": "156754095",
      "title": "고유가 피해지원금 4월 27일 지급 시작",
      "department": "행정안전부",
      "approve_date": "04/12/2026 09:00:00",
      "readhim": {
        "overall": 0.49730644716265454,
        "nid": 0.8334939759036143,
        "teds": 0.34833157709870044,
        "mhs": 0.31009378848564895,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.36323368493516955,
        "nid": 0.7686916749658809,
        "teds": 0.158926282051282,
        "mhs": 0.16208309778834573,
        "prediction_available": true
      },
      "delta_overall": 0.134072762227485
    },
    {
      "document_id": "156754093",
      "title": "2026년 행정안전부 추가경정예산 9조 4,880억원 확정",
      "department": "행정안전부",
      "approve_date": "04/12/2026 09:00:00",
      "readhim": {
        "overall": 0.49438096595405706,
        "nid": 0.6426076833527357,
        "teds": null,
        "mhs": 0.34615424855537846,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.313905325443787,
        "nid": 0.627810650887574,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "delta_overall": 0.18047564051027004
    },
    {
      "document_id": "156754077",
      "title": "중동 위기 선제 대응 위한  문체부 2026년 1회 추경 4,614억 원 확정",
      "department": "문화체육관광부",
      "approve_date": "04/11/2026 08:54:46",
      "readhim": {
        "overall": 0.6709302060184231,
        "nid": 0.9216522480809065,
        "teds": 0.8932529711750491,
        "mhs": 0.19788539879931377,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.615033438632619,
        "nid": 0.895448079658606,
        "teds": 0.7379128948277884,
        "mhs": 0.21173934141146245,
        "prediction_available": true
      },
      "delta_overall": 0.05589676738580418
    },
    {
      "document_id": "156754060",
      "title": "중기부 '26년 추경예산 1조 6,903억원 확정",
      "department": "중소벤처기업부",
      "approve_date": "04/11/2026 07:18:57",
      "readhim": {
        "overall": 0.2617692462022902,
        "nid": 0.20553592461719672,
        "teds": null,
        "mhs": 0.31800256778738367,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.15925382404775446,
        "nid": 0.16212321364236815,
        "teds": null,
        "mhs": 0.15638443445314076,
        "prediction_available": true
      },
      "delta_overall": 0.10251542215453574
    },
    {
      "document_id": "156754133",
      "title": "(참고) 기후에너지환경부, 추가경정예산 6,162억 원 증액 확정",
      "department": "기후에너지환경부",
      "approve_date": "04/10/2026 22:50:00",
      "readhim": {
        "overall": 0.5729948856538565,
        "nid": 0.8343313373253494,
        "teds": null,
        "mhs": 0.3116584339823635,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3431436727877521,
        "nid": 0.5356636750118091,
        "teds": null,
        "mhs": 0.15062367056369508,
        "prediction_available": true
      },
      "delta_overall": 0.22985121286610438
    },
    {
      "document_id": "156754052",
      "title": "(참고) 2026년 고용노동부 소관 제1회 추가경정예산 주요 내용",
      "department": "고용노동부",
      "approve_date": "04/10/2026 22:43:22",
      "readhim": {
        "overall": 0.6286881409558279,
        "nid": 0.7245349867139061,
        "teds": 0.8214389713898937,
        "mhs": 0.3400904647636841,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.49347197968332396,
        "nid": 0.6918690601900738,
        "teds": 0.6718136000746562,
        "mhs": 0.11673327878524176,
        "prediction_available": true
      },
      "delta_overall": 0.13521616127250397
    },
    {
      "document_id": "156754053",
      "title": "'26년 국토교통부 제1회 추가경정예산 확정",
      "department": "국토교통부",
      "approve_date": "04/10/2026 22:42:00",
      "readhim": {
        "overall": 0.5625976865476716,
        "nid": 0.7592397043294613,
        "teds": null,
        "mhs": 0.3659556687658818,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.38077895946871726,
        "nid": 0.6534173533688804,
        "teds": null,
        "mhs": 0.10814056556855411,
        "prediction_available": true
      },
      "delta_overall": 0.18181872707895436
    }
  ],
  "examples": [
    {
      "document_id": "156754125",
      "title": "한-방글라데시 포괄적경제동반자협정(CEPA) 제3차 공식협상(4.12.(일) ~ 17.(금)) 개최",
      "department": "산업통상부",
      "approve_date": "04/13/2026 08:21:08",
      "readhim": {
        "overall": 0.0,
        "nid": 0.0,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": false,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.45992310875012293,
        "nid": 0.7315384615384615,
        "teds": null,
        "mhs": 0.1883077559617844,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 한-방글라데시 포괄적경제동반자협정(CEPA) 제3차 공식협상(4.12.(일) ~ 17.(금)) 개최\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 산업통상부\n- 게시 시각: 04/13/2026 08:21:08\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754125&call_from=openData\n- HWPX 첨부: 0410(13조간)통상협정협상총괄과, 한-방글라데시 CEPA 제3차 공식협상 개최.hwpx\n- PDF 첨부: 0410(13조간)통상협정협상총괄과, 한-방글라데시 CEPA 제3차 공식협상 개최.pdf\n\n## 본문\n\n대 내외 통상환경의 불확실성이 증대되면서 수출시장 다변화 필요성이 높아지는 가운데, 세계 8 위 인구대국이자 서남아의 핵심 잠재시장인 방글라데시와의 포괄적경제동반자협정(CEPA *) 체결을 위한 제 3 차 공식 협상이 4.12(일)~17(금) 서울에서 개최된다.\n\n* 포괄적경제동반자협정(CEPA, Comprehensive Economic Partnership Agreement): 기존 FTA 구조와 개방수준에 유연성을 부여하고 협력을 강화하는 형태의 통상협정\n\n산업통상부(장관 김정관) 통상교섭본부는 이번 협상에 우리측 박근오 통상협정정책 관과 방글라데시 측 아예샤 아크터(Ayesha Akther) 상공부 대외 무역협정실장을 각각 수석대표로 하는 60 여 명의 양국 대표단이 참석한다고 밝혔다.\n\n양국은 ’ 24 년 11월 협상 개시를 선언한 후, 두 차례의 공식 협상을 통해 분과별로 전반적인 입장을 교환하고 주요 쟁점을 확인하였다. 이번 제 3 차 협상에서는 이를 바탕으로 상품양허, 서비스, 원산지 등 13 개 분야에서 보다 밀도 있는 논의를 진행하여 협정문안에 대한 입장차를 좁혀 나갈 계획이다.\n\n지난 3월 카메룬에서 개최된 WTO 각료회의 계기에, 여한구 통상교섭본부장은 방글라데시 칸다카르(Khandaker) 상무부 장관과의 면담에서 1.7 억명의 거대 시장을 보유한 방글라데시와 CEPA 의 조속한 타결을 추진하기로 한 바 있다. 박근오 통상협정정책관은 “빠르게 성장하는 유망 신흥시장인 방글라데 시와의 CEPA 체결은 우리 기업의 서남아 시장 내 경쟁력 강화에 기여할 것”이라며, “협상이 조속히 마무리될 수 있도록 적극적으로 협상에 임하겠다 ”고 밝혔다.\n\n## 담당 부서\n\n- 담당 부서: 통상협정교섭관 / 책임자 과장 손호영 / (044-203-5830)\n- 통상협정협상총괄과: 담당자 / 사무관 김은지\n\n## 첨부파일\n\n- 0410(13조간)통상협정협상총괄과, 한-방글라데시 CEPA 제3차 공식협상 개최.hwpx\n- 0410(13조간)통상협정협상총괄과, 한-방글라데시 CEPA 제3차 공식협상 개최.pdf\n",
      "readhim_markdown": "",
      "opendataloader_markdown": "|보도자료|\n|---|\n\n\n2026. 4. 12.(일) 11:00 < 4. 13.(월) 조간 >\n\n보도시점\n\n배포 2026. 4. 10.(금)\n\n|한-방글라데시 포괄적경제동반자협정(CEPA) 제3차 공식협상(4.12.(일) ~ 17.(금)) 개최<br><br>- 상품 양허, 서비스, 원산지, 경제협력 등 13개 분과 협상 -|\n|---|\n\n\n## 대내외 통상환경의 불확실성이 증대되면서 수출시장 다변화 필요성이 높아지는 가운데, 세계 8위 인구대국이자 서남아의 핵심 잠재시장인 방글라데시와의 포괄적경제동반자협정(CEPA*) 체결을 위한 제3차 공식 협상이 4.12(일)~17(금) 서울에서 개최된다.\n\n* 포괄적경제동반자협정(CEPA, Comprehensive Economic Partnership Agreement) : 기존 FTA 구조와 개방수준에 유연성을 부여하고 협력을 강화하는 형태의 통상협정\n\n산업통상부(장관 김정관) 통상교섭본부는 이번 협상에 우리측 박근오 통상협정 정책관과 방글라데시 측 아예샤 아크터(Ayesha Akther) 상공부 대외무역협정실장을 각각 수석대표로 하는 60여 명의 양국 대표단이 참석한다고 밝혔다.\n\n양국은 ’24년 11월 협상 개시를 선언한 후, 두 차례의 공식 협상을 통해 분과별로 전반적인 입장을 교환하고 주요 쟁점을 확인하였다. 이번 제3차 협상에서는 이를 바탕으로 상품양허, 서비스, 원산지 등 13개 분야에서 보다 밀도 있는 논의를 진행하여 협정문안에 대한 입장차를 좁혀 나갈 계획이다.\n\n지난 3월 카메룬에서 개최된 WTO 각료회의 계기에, 여한구 통상교섭본부장은 방글라데시 칸다카르(Khandaker) 상무부 장관과의 면담에서 1.7억명의 거대 시장을 보유한 방글라데시와 CEPA의 조속한 타결을 추진하기로 한 바 있다. 박근오 통상협정정책관은 “빠르게 성장하는 유망 신흥시장인 방글라데시와의 CEPA 체결은 우리 기업의 서남아 시장 내 경쟁력 강화에 기여할 것”이라며, “협상이 조속히 마무리될 수 있도록 적극적으로 협상에 임하겠다”고 밝혔다.\n\n|담당 부서|통상협정교섭관 통상협정협상총괄과|책임자|과 장 손호영 (044-203-5830)|\n|---|---|---|---|\n| | |담당자|사무관 김은지 (044-203-5837)|\n\n\n"
    },
    {
      "document_id": "156754101",
      "title": "환경분야 시험·검사 전문성 높인다… 현장 요구 반영한 맞춤형 교육 본격 확대",
      "department": "기후에너지환경부",
      "approve_date": "04/12/2026 12:00:00",
      "readhim": {
        "overall": 0.7542674244449302,
        "nid": 0.873968705547653,
        "teds": 0.9611743611321931,
        "mhs": 0.4276592066549445,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.5948167010871991,
        "nid": 0.8477990892783221,
        "teds": 0.7647299661562704,
        "mhs": 0.1719210478270048,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 환경분야 시험·검사 전문성 높인다… 현장 요구 반영한 맞춤형 교육 본격 확대\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 기후에너지환경부\n- 게시 시각: 04/12/2026 12:00:00\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754101&call_from=openData\n- HWPX 첨부: (과학원 4.12.) 환경분야 시험·검사 전문성 높인다…현장 요구 반영한 맞춤형 교육 본격 확대(보도자료).hwpx\n- PDF 첨부: (과학원 4.12.) 환경분야 시험·검사 전문성 높인다…현장 요구 반영한 맞춤형 교육 본격 확대(보도자료).pdf\n\n## 본문\n\n환경 시험· 검사의 전문성을 높이고 산업계에서 필요로 하는 고숙련 인력을 양성하기 위해 전국의 시험· 검사기관 재직자를 대상으로 고난도 분석기술 중심의 현장 맞춤형 실습 교육이 확대 추진된다.\n\n기후에너지환경부 소속 국립환경과학원(원장 박연재) 은 환경오염공정시험 기준의 신뢰성 제고와 현장 적용성 강화를 위해 전국 시험· 검사기관 기술인력을 대상으로 하는 전문 교육훈련을 4월 13 일부터 확대 추진한다고 밝혔다.\n\n환경오염공정시험기준은 국가 환경정책 이행을 위한 핵심적인 기술규정으로, 이에 근거한 측정 및 분석 결과의 정확성과 신뢰성 확보가 중요하다. 특히 최근 분석기술의 고도화와 신규 오염물질 증가로 시험방법 개발이 활발해지면서, 이를 수행할 전문 인력의 역량 강화와 체계적인 교육의 중요성이 더욱 강조되고 있다.\n\n이번 교육은 국립환경과학원과 고용노동부의 국가인적자원개발 협의체(컨소시엄) 사업 * 을 통해 마련됐으며, 전국의 환경분야 시험· 검사기관 재직자 3 천여 명 이상을 대상으로 고난도 분석기술 및 신규 시험방법 중심의 실습 교육으로 진행된다.\n\n* 국립환경과학원, 고용노동부, 한국화학융합시험연구원 등 협의체 구성\n\n교육과정은 환경오염공정시험기준 13개 분야 1,251종의 시험방법을 대상으로 올해 10 개 과정 * 을 개설하며, 향후 매년 단계적으로 확대될 예정이다.\n\n이번에 개설되는 첫 번째 교육과정은 ‘현장 맞춤형 굴뚝먼지 시료채취 및 분석관리 실무’로 굴뚝먼지 시료채취 및 분석을 시작으로 배출가스 자동측정, 수질 시료 중 과불화화합물 분석 등을 진행한다.\n\n* 공통 3개와 실습 7개의 과정으로 구성\n\n특히 교육에는 경기도보건환경연구원을 비롯해 환경분야 시험· 검사기관인 코티티(KOTITI) 시험연구원 등의 실무전문가가 강사진으로 참여하여 산업계 수요를 반영한 실효성 높은 교육과정을 제공할 계획이다.\n\n국립환경과학원은 이번 교육과정 운영과 직무분석 결과를 바탕으로 고숙련 과정을 확대하는 등 단계별 인력양성 체계를 지속적으로 고도화해 나갈 예정이다.\n\n교육 참여를 희망하는 기관 및 종사자는 한국화학융합시험연구원과 협약을 체결한 후, 국가인적자원 개발컨소시엄 교육 누리집(hrd.ktr.or.kr)을 통해 신청할 수 있다.\n\n박연재 국립환경과학원장은 “이번 교육을 통해 현장 중심의 맞춤형 실습 기회를 제공하여 시험· 검사 인력의 전문성을 강화하겠다”라며, “관계기관과의 협업을 바탕으로 환경분야 인력양성 기반을 지속적으로 확대해 나가겠다”라고 밝혔다.\n\n## 붙임 2026년 환경분야 국가인적자원개발컨소시엄 교육과정. 끝.\n\n## 담당 부서\n\n- 담당 부서: 국립환경과학원 / 책임자 과장 허유정 / (032-560-8383)\n- 환경표준연구과: 담당자 / 연구관 김은미\n- 담당자: 연구사 / 정민재(032-560-8391)\n\n## 붙임 2026 년 환경분야 국가인적자원개발컨소시엄 교육과정\n\n| 연번 | 훈련과정명 | 방법 | 횟수 | 시간 | 정원 | 인원 | 장소 |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| 1 | 환경법, 정책, 판례 한눈에 이해하기(4.28., 7.28., 10.28.) | 집체 | 3 | 7 | 30 | 90 | KTR 과천 |\n| 2 | 실무자가 꼭 알아야할 환경분석 QA/QC: 개념부터 실무절차, 사례까지(4.29., 7.29., 10.29.) | 집체 | 3 | 6 | 30 | 90 | KTR 과천 |\n| 3 | 시험검사 품질관리 내실화를 위한 문서·기록의 이해와 내부심사 실습 심화과정(4.30., 7.30., 10.30.) | 집체 | 3 | 6 | 30 | 90 | KTR 과천 |\n| 4 | 현장 맞춤형 굴뚝먼지 시료채취 및 분석관리 실무(4.13. ~ 16.) | 집체 | 4 | 5 | 50 | 200 | KTR 과천 |\n| 5 | 배출가스 중 자동측정법 분석 장비 실무 활용(8.7., 11.3.) | 집체 | 2 | 5 | 30 | 60 | KTR 과천 |\n| 6 | 수질 분석가를 위한 BOD: 현장 문제 해결 심화 과정(9.29.) | 집체 | 1 | 6 | 15 | 15 | KTR 과천 |\n| 7 | 수질오염공정시험기준에 따른 과불화화합물 정밀분석 실무(8.19., 11.12.) | 집체 | 2 | 7 | 15 | 30 | KOTITI 과천 |\n| 8 | 특정 수질 유해물질(벤젠, 클로로포름) 정밀 분석 직무 역량 강화(미정) | 집체 | 1 | 7 | 15 | 15 | KTR 과천 |\n| 9 | 먹는물 중금속 분석 심화 과정; ICP-MS를 활용한 극미량원소 분석 실습(미정) | 집체 | 1 | 7 | 15 | 15 | KTR 과천 |\n| 10 | 폐기물오염공정시험기준에 따른 중금속(납) 분석 심화과정: 전처리부터 분석장비(ICP-OES,AAS) 실습까지(미정) | 집체 | 1 | 7 | 15 | 15 | KTR 과천 |\n| 총 계 | 21 | 63 | 245 | 620 | - | | |\n\n## 첨부파일\n\n- (과학원 4.12.) 환경분야 시험·검사 전문성 높인다…현장 요구 반영한 맞춤형 교육 본격 확대(보도자료).hwpx\n- (과학원 4.12.) 환경분야 시험·검사 전문성 높인다…현장 요구 반영한 맞춤형 교육 본격 확대(보도자료).pdf\n",
      "readhim_markdown": "# 환경분야 시험·검사 전문성 높인다… 현장 요구 반영한 맞춤형 교육 본격 확대\n\n기후에너지환경부 보도자료 /\n보도시점: 2026. 4. 12.(일) 12:00 / (월요일 조간) / 배포 2026. 4. 10.(금)\n\n> - 산업계 수요 반영해 고난도 분석기술 배울 기회 제공\n> - 기후에너지환경부·고용노동부, 신규 훈련 및 실무 중심 인력양성 체계 구축\n---\n환경 시험·검사의 전문성을 높이고 산업계에서 필요로 하는 고숙련 인력을 양성하기 위해 전국의 시험·검사기관 재직자를 대상으로 고난도 분석기술 중심의 현장 맞춤형 실습 교육이 확대 추진된다.\n\n기후에너지환경부 소속 국립환경과학원(원장 박연재)은 환경오염공정시험기준의 신뢰성 제고와 현장 적용성 강화를 위해 전국 시험·검사기관 기술인력을 대상으로 하는 전문 교육훈련을 4월 13일부터 확대 추진한다고 밝혔다.\n\n환경오염공정시험기준은 국가 환경정책 이행을 위한 핵심적인 기술규정으로, 이에 근거한 측정 및 분석 결과의 정확성과 신뢰성 확보가 중요하다. 특히 최근 분석기술의 고도화와 신규 오염물질 증가로 시험방법 개발이 활발해지면서, 이를 수행할 전문 인력의 역량 강화와 체계적인 교육의 중요성이 더욱 강조되고 있다.\n\n이번 교육은 국립환경과학원과 고용노동부의 국가인적자원개발 협의체(컨소시엄) 사업*을 통해 마련됐으며, 전국의 환경분야 시험·검사기관 재직자 3천여 명 이상을 대상으로 고난도 분석기술 및 신규 시험방법 중심의 실습 교육으로 진행된다.\n> * 국립환경과학원, 고용노동부, 한국화학융합시험연구원 등 협의체 구성\n\n교육과정은 환경오염공정시험기준 13개 분야 1,251종의 시험방법을 대상으로 올해 10개 과정*을 개설하며, 향후 매년 단계적으로 확대될 예정이다.\n\n이번에 개설되는 첫 번째 교육과정은 ‘현장 맞춤형 굴뚝먼지 시료채취 및 분석관리 실무’로 굴뚝먼지 시료채취 및 분석을 시작으로 배출가스 자동측정, 수질 시료 중 과불화화합물 분석 등을 진행한다.\n> * 공통 3개와 실습 7개의 과정으로 구성\n\n특히 교육에는 경기도보건환경연구원을 비롯해 환경분야 시험·검사기관인 코티티(KOTITI) 시험연구원 등의 실무전문가가 강사진으로 참여하여 산업계 수요를 반영한 실효성 높은 교육과정을 제공할 계획이다.\n\n국립환경과학원은 이번 교육과정 운영과 직무분석 결과를 바탕으로 고숙련 과정을 확대하는 등 단계별 인력양성 체계를 지속적으로 고도화해 나갈 예정이다.\n\n교육 참여를 희망하는 기관 및 종사자는 한국화학융합시험연구원과 협약을 체결한 후, 국가인적자원 개발컨소시엄 교육 누리집(hrd.ktr.or.kr)을 통해 신청할 수 있다.\n\n박연재 국립환경과학원장은 “이번 교육을 통해 현장 중심의 맞춤형 실습 기회를 제공하여 시험·검사 인력의 전문성을 강화하겠다”라며, “관계기관과의 협업을 바탕으로 환경분야 인력양성 기반을 지속적으로 확대해 나가겠다”라고 밝혔다.\n\n---\n\n### 담당부서\n\n- 국립환경과학원 환경표준연구과 책임자: 과장 허유정 (032-560-8383)\n- 국립환경과학원 환경표준연구과 담당자: 연구관 김은미 (032-560-7902)\n- 국립환경과학원 환경표준연구과 담당자: 연구사 정민재 (032-560-8391)\n---\n\n## 붙임 2026년 환경분야 국가인적자원개발컨소시엄 교육과정. 끝.\n\n< 그림 >\n\n붙임\n2026년 환경분야 국가인적자원개발컨소시엄 교육과정\n\n| 연번 | 훈련과정명 | 방법 | 횟수 | 시간 | 정원 | 인원 | 장소 |\n| --- | --- | --- | --- | --- | --- | --- | --- |\n| 1 | 환경법, 정책, 판례 한눈에 이해하기<br>(4.28., 7.28., 10.28.) | 집체 | 3 | 7 | 30 | 90 | KTR<br>과천 |\n| 2 | 실무자가 꼭 알아야 할 환경분석 QA/QC: 개념부터 실무절차, 사례까지<br>(4.29., 7.29., 10.29.) | 집체 | 3 | 6 | 30 | 90 | KTR<br>과천 |\n| 3 | 시험검사 품질관리 내실화를 위한 문서·기록의 이해와 내부심사 실습 심화과정<br>(4.30., 7.30., 10.30.) | 집체 | 3 | 6 | 30 | 90 | KTR<br>과천 |\n| 4 | 현장 맞춤형 굴뚝먼지 시료채취 및 분석관리 실무<br>(4.13. ~ 16.) | 집체 | 4 | 5 | 50 | 200 | KTR<br>과천 |\n| 5 | 배출가스 중 자동측정법 분석 장비 실무 활용<br>(8.7., 11.3.) | 집체 | 2 | 5 | 30 | 60 | KTR<br>과천 |\n| 6 | 수질 분석가를 위한 BOD: 현장 문제 해결 심화 과정<br>(9.29.) | 집체 | 1 | 6 | 15 | 15 | KTR<br>과천 |\n| 7 | 수질오염공정시험기준에 따른 과불화화합물 정밀분석 실무<br>(8.19., 11.12.) | 집체 | 2 | 7 | 15 | 30 | KOTITI<br>과천 |\n| 8 | 특정 수질 유해물질(벤젠, 클로로포름) 정밀 분석 직무 역량 강화<br>(미정) | 집체 | 1 | 7 | 15 | 15 | KTR<br>과천 |\n| 9 | 먹는물 중금속 분석 심화 과정; ICP-MS를 활용한 극미량원소 분석 실습<br>(미정) | 집체 | 1 | 7 | 15 | 15 | KTR<br>과천 |\n| 10 | 폐기물오염공정시험기준에 따른 중금속(납) 분석 심화과정: 전처리부터 분석장비(ICP-OES,AAS) 실습까지<br>(미정) | 집체 | 1 | 7 | 15 | 15 | KTR<br>과천 |\n| 총 계 | | | 21 | 63 | 245 | 620 | - |\n",
      "opendataloader_markdown": "|보도자료|\n|---|\n\n\n보도시점 2026. 4. 12.(일) 12:00 (월요일 조간) 배포 2026. 4. 10.(금)\n\n|환경분야 시험·검사 전문성 높인다… 현장 요구 반영한 맞춤형 교육 본격 확대<br><br>- 산업계 수요 반영해 고난도 분석기술 배울 기회 제공<br>- 기후에너지환경부·고용노동부, 신규 훈련 및 실무 중심 인력양성 체계 구축<br>|\n|---|\n\n\n환경 시험·검사의 전문성을 높이고 산업계에서 필요로 하는 고숙련 인력을 양성하기 위해 전국의 시험·검사기관 재직자를 대상으로 고난도 분석기술 중심의 현장 맞춤형 실습 교육이 확대 추진된다.\n\n기후에너지환경부 소속 국립환경과학원(원장 박연재)은 환경오염공정시험 기준의 신뢰성 제고와 현장 적용성 강화를 위해 전국 시험·검사기관 기술인력을 대상으로 하는 전문 교육훈련을 4월 13일부터 확대 추진한다고 밝혔다.\n\n환경오염공정시험기준은 국가 환경정책 이행을 위한 핵심적인 기술규정 으로, 이에 근거한 측정 및 분석 결과의 정확성과 신뢰성 확보가 중요하 다. 특히 최근 분석기술의 고도화와 신규 오염물질 증가로 시험방법 개발 이 활발해지면서, 이를 수행할 전문 인력의 역량 강화와 체계적인 교육의 중요성이 더욱 강조되고 있다.\n\n이번 교육은 국립환경과학원과 고용노동부의 국가인적자원개발 협의체 (컨소시엄) 사업*을 통해 마련됐으며, 전국의 환경분야 시험·검사기관 재직자 3천여 명 이상을 대상으로 고난도 분석기술 및 신규 시험방법 중심의 실습 교육으로 진행된다.\n\n* 국립환경과학원, 고용노동부, 한국화학융합시험연구원 등 협의체 구성\n\n## 교육과정은 환경오염공정시험기준 13개 분야 1,251종의 시험방법을 대 상으로 올해 10개 과정*을 개설하며, 향후 매년 단계적으로 확대될 예정이다.\n\n## 이번에 개설되는 첫 번째 교육과정은 ‘현장 맞춤형 굴뚝먼지 시료채취 및 분 석관리 실무’로 굴뚝먼지 시료채취 및 분석을 시작으로 배출가스 자동측정, 수질 시료 중 과불화화합물 분석 등을 진행한다.\n\n* 공통 3개와 실습 7개의 과정으로 구성\n\n특히 교육에는 경기도보건환경연구원을 비롯해 환경분야 시험·검사기관인 코티티(KOTITI) 시험연구원 등의 실무전문가가 강사진으로 참여하여 산업계 수요를 반영한 실효성 높은 교육과정을 제공할 계획이다.\n\n국립환경과학원은 이번 교육과정 운영과 직무분석 결과를 바탕으로 고숙련 과정을 확대하는 등 단계별 인력양성 체계를 지속적으로 고도화해 나갈 예정이다.\n\n교육 참여를 희망하는 기관 및 종사자는 한국화학융합시험연구원과 협 약을 체결한 후, 국가인적자원 개발컨소시엄 교육 누리집(hrd.ktr.or.kr)을 통해 신청할 수 있다.\n\n박연재 국립환경과학원장은 “이번 교육을 통해 현장 중심의 맞춤형 실습 기회를 제공하여 시험·검사 인력의 전문성을 강화하겠다”라며, “관계기관과의 협업을 바탕으로 환경분야 인력양성 기반을 지속적으로 확대해 나가겠다” 라고 밝혔다.\n\n붙임 2026년 환경분야 국가인적자원개발컨소시엄 교육과정. 끝.\n\n|담당 부서|국립환경과학원 환경표준연구과|책임자|과 장 허유정 (032-560-8383)|\n|---|---|---|---|\n| | |담당자|연구관 김은미 (032-560-7902)|\n| | |담당자|연구사 정민재 (032-560-8391)|\n\n\n|붙임|\n|---|\n\n\n|2026년 환경분야 국가인적자원개발컨소시엄 교육과정|\n|---|\n\n\n|연번<br><br>|훈련과정명<br><br>|방법<br><br>|횟수<br><br>|시간<br><br>|정원<br><br>|인원<br><br>|장소<br><br>|\n|---|---|---|---|---|---|---|---|\n|1|환경법, 정책, 판례 한눈에 이해하기 (4.28., 7.28., 10.28.)|집체|3|7|30|90|KTR 과천|\n|2|실무자가 꼭 알아야 할 환경분석 QA/QC: 개념부터 실무절차, 사례까지 (4.29., 7.29., 10.29.)|집체|3|6|30|90|KTR 과천|\n|3|시험검사 품질관리 내실화를 위한 문서·기록의 이해와 내부심사 실습 심화과정 (4.30., 7.30., 10.30.)|집체|3|6|30|90|KTR 과천|\n|4|현장 맞춤형 굴뚝먼지 시료채취 및 분석관리 실무 (4.13. ~ 16.)|집체|4|5|50|200|KTR 과천|\n|5|배출가스 중 자동측정법 분석 장비 실무 활용 (8.7., 11.3.)|집체|2|5|30|60|KTR 과천|\n|6|수질 분석가를 위한 BOD: 현장 문제 해결 심화 과정 (9.29.)|집체|1|6|15|15|KTR 과천|\n|7|수질오염공정시험기준에 따른 과불화화합물 정밀분석 실무 (8.19., 11.12.)|집체|2|7|15|30|KOTITI 과천|\n|8|특정 수질 유해물질(벤젠, 클로로포름) 정밀 분석 직무 역량 강화 (미정)|집체|1|7|15|15|KTR 과천|\n|9|먹는물 중금속 분석 심화 과정; ICP-MS를 활용한 극미량원소 분석 실습 (미정)|집체|1|7|15|15|KTR 과천|\n|10|폐기물오염공정시험기준에 따른 중금속(납) 분석 심화과정: 전처리부터 분석장비(ICP-OES,AAS) 실습까지 (미정)|집체|1|7|15|15|KTR 과천|\n|총 계| | |21|63|245|620|-|\n\n\n"
    },
    {
      "document_id": "156754237",
      "title": "태양광 기술 전문가, 정부 민간인재 영입지원 발탁",
      "department": "인사혁신처",
      "approve_date": "04/13/2026 12:00:00",
      "readhim": {
        "overall": 0.7491740428700173,
        "nid": 0.8504356243949661,
        "teds": 0.98796992481203,
        "mhs": 0.4091165794030559,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.3426129533929508,
        "nid": 0.7971371057928875,
        "teds": 0.23070175438596485,
        "mhs": 0.0,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 태양광 기술 전문가, 정부 민간인재 영입지원 발탁\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 인사혁신처\n- 게시 시각: 04/13/2026 12:00:00\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754237&call_from=openData\n- HWPX 첨부: 260413 (인재정보담당관) 태양광 기술 전문가, 정부 민간인재 영입지원 발탁.hwpx\n- PDF 첨부: 260413 (인재정보담당관) 태양광 기술 전문가, 정부 민간인재 영입지원 발탁.pdf\n\n## 본문\n\n정부 민간인재 영입지원(정부 헤드헌팅) 을 활용해 태양광 기술 분야 현장 전문가가 산업통상부 국가기술표준원 기술규제협력과장에 임용 됐다.\n\n인사혁신처(처장 최동석) 는 윤주환 전 한화솔루션 상무를 산업부 국표원 기술규제협력과장으로 발탁 했다고 13일 밝혔다.\n\n기술규제협력과장은 국내외 기술 규제 관련 정보 관리, 기업 애로사항 발굴‧대응 및 유관기관 협력을 통한 규제대응 지원 등 기업의 활력을 제고하는 기술 규제 관련 협력 업무를 총괄 하게 된다.\n\n이번 인사는 산업부의 요청에 따라 인사처가 적격자를 직접 발굴해 추천하는 정부 민간인재 영입지원으로 진행됐으며 지난 2018 년 이후, 산업부의 세 번째 임용 사례다.\n\n윤주환 신임 과장은 약 25 년간 엘지전자 태양광 상품기획팀‧기술전략팀, 한화솔루션 재생에너지 부문 상무 등을 역임하며 태양광 상품기획부터 기술 전략 수립, 시스템 개발 까지 두루 경험한 실무형 전문가 다.\n\n특히 그는 한화솔루션에서 전력변환장치(마이크로인버터) 등 차세대 태양광 시스템 개발을 주도하며 미국 안전 인증(UL 인증) 취득 등 국내외 기술 규제 관련 풍부한 경험을 보유하고 있다.\n\n또한, 엘지전자 기술전략팀장 재직 당시 국표원의 ‘태양광 발전기술 표준화 및 보급 활성화 기반 구축’ 과제에 표준 전문가로 참여 하는 등 정부 정책과 산업현장을 잇는 가교역할도 수행했다.\n\n윤주환 과장은 “현장에서 규제가 기업의 성패에 얼마나 큰 영향을 미치는지 몸소 경험했다 ”며 “그간 쌓아온 전문성과 경험을 바탕으로 기업의 애로 사항을 발굴하고, 유관기관과 긴밀히 협력해 불합리한 기술 규제를 해소하는 데 기여하겠다”고 포부를 밝혔다.\n\n인사처 최시영 인재정보담당관은 “ 신기술 개발부터 표준․인증 까지 전 과정을 두루 경험한 전문가를 영입함으로써 기술 규제 정책의 실효성이 한층 높아질 것으로 기대한다”며 “앞으로도 민간의 우수 인재가 공직에서 역량을 펼칠 수 있도록 적극 지원 하겠다”고 말했다.\n\n한편, 정부 민간인재 영입지원은 공직 경쟁력 강화를 위해 중앙부처와 지방자치단체 등 공공기관의 요청에 따라 전문성이 요구되는 주요 직위에 대해 인사처가 직접 발굴해 추천 하는 맞춤형 인재 발굴 제도 다.\n\n지난 2015 년 제도 도입 이후 현재까지 총 132 명의 민간 전문가가 공직에 진출했다.\n\n※ (붙임) 윤주환 산업통상부 국가기술표준원 기술규제협력과장 주요 업무 및 약력\n\n## 담당 부서\n\n- 담당 부서: 인재정보기획관 / 책임자 과장 최시영 / (044-201-8060)\n- 인재정보담당관: 담당자 / 서기관 원민아\n\n## 붙임 윤주환 산업통상부 국가기술표준원 기술규제협력과장 주요 업무 및 약력\n\n□ 국가기술표준원 기술규제협력과장 주요업무\n\n| 구분 | 주요 업무 |\n| --- | --- |\n| 주요 업무 | ○ 국내 기술규제 관련 기업 애로사항 발굴 및 대응 ○ 국내외 표준 ‧ 인증 관련 정보 수집 ‧ 제공 ‧ 관리 ‧ 활용 및 대외 협력 ○ 기술규제 관련 업체 ‧ 유관기관 및 중앙행정기관 간 협력 ○ 국내 기술규제 관련 실태조사 ‧ 분석 및 연구, 모범규제관행 발굴 ‧ 전파 및 정착 ○ 국내 기술규제의 국제표준 부합화 조사 ‧ 분석 및 평가 |\n\n□ 윤주환 기술규제협력과장 약력\n\n○ 성명: 윤주환\n\n○ 주요 경력\n\n- 2025.: 한화솔루션 고문\n\n- 2021. ~ 2024.: 한화솔루션 큐셀부문 MLPE 개발팀 팀장(상무)\n\n- 2006. ~ 2021.: 엘지 전자 솔라사업부 상품기획팀‧기술전략팀‧시스템 개 발팀 팀장\n\n  - 2000. ~ 2005.: 엘지전자 TFA 그룹 선임연구원, DAD 그룹 수석연구원\n\n## 첨부파일\n\n- 260413 (인재정보담당관) 태양광 기술 전문가, 정부 민간인재 영입지원 발탁.hwpx\n- 260413 (인재정보담당관) 태양광 기술 전문가, 정부 민간인재 영입지원 발탁.pdf\n",
      "readhim_markdown": "# 태양광 기술 전문가, 정부 민간인재 영입지원 발탁\n\n정부 보도자료 /\n보도시점: | 보도일시 | 2026. 4. 13.(월) 12:00 |\n\n> - 국가기술표준원 기술규제협력과장에 엘지전자‧한화솔루션 출신 윤주환 전 상무 임용\n---\n정부 민간인재 영입지원(정부 헤드헌팅)을 활용해 태양광 기술 분야 현장 전문가가 산업통상부 국가기술표준원 기술규제협력과장에 임용됐다.\n\n인사혁신처(처장 최동석)는 윤주환 전 한화솔루션 상무를 산업부 국표원 기술규제협력과장으로 발탁했다고 13일 밝혔다.\n\n기술규제협력과장은 국내외 기술 규제 관련 정보 관리, 기업 애로사항 발굴‧대응 및 유관기관 협력을 통한 규제대응 지원 등 기업의 활력을 제고하는 기술 규제 관련 협력 업무를 총괄하게 된다.\n\n이번 인사는 산업부의 요청에 따라 인사처가 적격자를 직접 발굴해 추천하는 정부 민간인재 영입지원으로 진행됐으며 지난 2018년 이후, 산업부의 세 번째 임용 사례다.\n\n윤주환 신임 과장은 약 25년간 엘지전자 태양광 상품기획팀‧기술전략팀, 한화솔루션 재생에너지 부문 상무 등을 역임하며 태양광 상품기획부터 기술 전략 수립, 시스템 개발까지 두루 경험한 실무형 전문가다.\n\n특히 그는 한화솔루션에서 전력변환장치(마이크로인버터) 등 차세대 태양광 시스템 개발을 주도하며 미국 안전 인증(UL 인증) 취득 등 국내외 기술 규제 관련 풍부한 경험을 보유하고 있다.\n\n또한, 엘지전자 기술전략팀장 재직 당시 국표원의 ‘태양광 발전기술 표준화 및 보급 활성화 기반 구축’ 과제에 표준 전문가로 참여하는 등 정부 정책과 산업현장을 잇는 가교역할도 수행했다.\n\n윤주환 과장은 “현장에서 규제가 기업의 성패에 얼마나 큰 영향을 미치는지 몸소 경험했다”며 “그간 쌓아온 전문성과 경험을 바탕으로 기업의 애로사항을 발굴하고, 유관기관과 긴밀히 협력해 불합리한 기술 규제를 해소하는 데 기여하겠다”고 포부를 밝혔다.\n\n인사처 최시영 인재정보담당관은 “신기술 개발부터 표준․인증까지 전 과정을 두루 경험한 전문가를 영입함으로써 기술 규제 정책의 실효성이 한층 높아질 것으로 기대한다”며 “앞으로도 민간의 우수 인재가 공직에서 역량을 펼칠 수 있도록 적극 지원하겠다”고 말했다.\n\n한편, 정부 민간인재 영입지원은 공직 경쟁력 강화를 위해 중앙부처와 지방자치단체 등 공공기관의 요청에 따라 전문성이 요구되는 주요 직위에 대해 인사처가 직접 발굴해 추천하는 맞춤형 인재 발굴 제도다.\n\n지난 2015년 제도 도입 이후 현재까지 총 132명의 민간 전문가가 공직에 진출했다.\n- (붙임) 윤주환 산업통상부 국가기술표준원 기술규제협력과장 주요 업무 및 약력\n\n---\n\n### 담당부서\n\n- 인재정보기획관 인재정보담당관 책임자: 과장 최시영 (044-201-8060)\n- 인재정보기획관 인재정보담당관 담당자: 서기관 원민아 (044-201-8062)\n\n< 그림 >\n\n### 국가기술표준원 기술규제협력과장 주요업무\n\n| 구분 | 주요 업무 |\n| --- | --- |\n| 주요<br>업무 | ○ 국내 기술규제 관련 기업 애로사항 발굴 및 대응<br>○ 국내외 표준‧인증 관련 정보 수집‧제공‧관리‧활용 및 대외 협력<br>○ 기술규제 관련 업체‧유관기관 및 중앙행정기관 간 협력<br>○ 국내 기술규제 관련 실태조사‧분석 및 연구, 모범규제관행 발굴‧전파 및 정착<br>○ 국내 기술규제의 국제표준 부합화 조사‧분석 및 평가 |\n\n### 윤주환 기술규제협력과장 약력\n\n- 성명 : 윤주환\n- 주요 경력\n  - 2025. : 한화솔루션 고문\n  - 2021. ~ 2024. : 한화솔루션 큐셀부문 MLPE개발팀 팀장(상무)\n  - 2006. ~ 2021. : 엘지전자 솔라사업부 상품기획팀‧기술전략팀‧시스템개발팀 팀장\n  - 2000. ~ 2005. : 엘지전자 TFA그룹 선임연구원, DAD그룹 수석연구원\n",
      "opendataloader_markdown": "|광부 보도자료<br><br>|\n|---|\n\n\n보도일시 2026. 4. 13.(월) 12:00\n\n|태양광 기술 전문가, 정부 민간인재 영입지원 발탁<br><br>- 국가기술표준원 기술규제협력과장에 엘지전자‧한화솔루션 출신 윤주환 전 상무 임용 -|\n|---|\n\n\n## 정부 민간인재 영입지원(정부 헤드헌팅)을 활용해 태양광 기술 분야 현장 전문가가 산업통상부 국가기술표준원 기술규제협력과장에 임용됐다.\n\n## 인사혁신처(처장 최동석)는 윤주환 전 한화솔루션 상무를 산업부 국표원 기술 규제협력과장으로 발탁했다고 13일 밝혔다.\n\n## 기술규제협력과장은 국내외 기술 규제 관련 정보 관리, 기업 애로사항 발굴‧ 대응 및 유관기관 협력을 통한 규제대응 지원 등 기업의 활력을 제고하는 기술 규제 관련 협력 업무를 총괄하게 된다.\n\n이번 인사는 산업부의 요청에 따라 인사처가 적격자를 직접 발굴해 추천 하는 정부 민간인재 영입지원으로 진행됐으며 지난 2018년 이후, 산업부의 세 번째 임용 사례다.\n\n윤주환 신임 과장은 약 25년간 엘지전자 태양광 상품기획팀‧기술전략팀, 한화솔루션 재생에너지 부문 상무 등을 역임하며 태양광 상품기획부터 기술 전략 수립, 시스템 개발까지 두루 경험한 실무형 전문가다.\n\n특히 그는 한화솔루션에서 전력변환장치(마이크로인버터) 등 차세대 태양광 시스템 개발을 주도하며 미국 안전 인증(UL 인증) 취득 등 국내외 기술 규제 관련 풍부한 경험을 보유하고 있다.\n\n## 또한, 엘지전자 기술전략팀장 재직 당시 국표원의 ‘태양광 발전기술 표준화 및 보급 활성화 기반 구축’ 과제에 표준 전문가로 참여하는 등 정부 정책과 산업현장을 잇는 가교역할도 수행했다.\n\n## 윤주환 과장은 “현장에서 규제가 기업의 성패에 얼마나 큰 영향을 미치는지 몸소 경험했다”며 “그간 쌓아온 전문성과 경험을 바탕으로 기업의 애로사항을 발굴하고, 유관기관과 긴밀히 협력해 불합리한 기술 규제를 해소하는 데 기여 하겠다”고 포부를 밝혔다.\n\n## 인사처 최시영 인재정보담당관은 “신기술 개발부터 표준․인증까지 전 과정을 두루 경험한 전문가를 영입함으로써 기술 규제 정책의 실효성이 한층 높아질 것 으로 기대한다”며 “앞으로도 민간의 우수 인재가 공직에서 역량을 펼칠 수 있도록 적극 지원하겠다”고 말했다.\n\n한편, 정부 민간인재 영입지원은 공직 경쟁력 강화를 위해 중앙부처와 지방 자치단체 등 공공기관의 요청에 따라 전문성이 요구되는 주요 직위에 대해 인사처가 직접 발굴해 추천하는 맞춤형 인재 발굴 제도다.\n\n## 지난 2015년 제도 도입 이후 현재까지 총 132명의 민간 전문가가 공직에 진출했다.\n\n※ (붙임) 윤주환 산업통상부 국가기술표준원 기술규제협력과장 주요 업무 및 약력\n\n|담당 부서|인재정보기획관 인재정보담당관|책임자|과 장 최시영 (044-201-8060)|\n|---|---|---|---|\n| | |담당자|서기관 원민아 (044-201-8062)|\n\n\n|붙임|\n|---|\n\n\n|윤주환 산업통상부 국가기술표준원 기술규제협력과장 주요 업무 및 약력|\n|---|\n\n\n- □ 국가기술표준원 기술규제협력과장 주요업무\n\n|구분<br><br>|주요 업무<br><br>|\n|---|---|\n|주요 업무|○ 국내 기술규제 관련 기업 애로사항 발굴 및 대응<br>○ 국내외 표준‧인증 관련 정보 수집‧제공‧관리‧활용 및 대외 협력<br>○ 기술규제 관련 업체‧유관기관 및 중앙행정기관 간 협력<br>○ 국내 기술규제 관련 실태조사‧분석 및 연구, 모범규제관행 발굴‧ 전파 및 정착<br>○ 국내 기술규제의 국제표준 부합화 조사‧분석 및 평가<br>|\n\n\n- □ 윤주환 기술규제협력과장 약력\n\n\n- ○ 성명 : 윤주환\n- ○ 주요 경력\n\n\n- - 2025. : 한화솔루션 고문\n- - 2021. ~ 2024. : 한화솔루션 큐셀부문 MLPE개발팀 팀장(상무)\n- - 2006. ~ 2021. : 엘지전자 솔라사업부 상품기획팀‧기술전략팀‧시스템 개발팀 팀장\n- - 2000. ~ 2005. : 엘지전자 TFA그룹 선임연구원, DAD그룹 수석연구원\n\n\n"
    },
    {
      "document_id": "156754095",
      "title": "고유가 피해지원금 4월 27일 지급 시작",
      "department": "행정안전부",
      "approve_date": "04/12/2026 09:00:00",
      "readhim": {
        "overall": 0.49730644716265454,
        "nid": 0.8334939759036143,
        "teds": 0.34833157709870044,
        "mhs": 0.31009378848564895,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.36323368493516955,
        "nid": 0.7686916749658809,
        "teds": 0.158926282051282,
        "mhs": 0.16208309778834573,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 고유가 피해지원금 4월 27일 지급 시작\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 행정안전부\n- 게시 시각: 04/12/2026 09:00:00\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754095&call_from=openData\n- HWPX 첨부: 260411 (11시) 고유가 피해지원금 4월 27일 지급 시작(재정정책과).hwpx\n- PDF 첨부: 260411 (11시) 고유가 피해지원금 4월 27일 지급 시작(재정정책과).pdf\n\n## 본문\n\n□ 정부는 4월 11일(토) 정부서울청사에서 관계부처 합동 브리핑을 개최하고, 고유가 피해지원금의 신청기간· 지원규모 등 지급 방안을 담은 ｢고유가 피해지원금 지급계획｣을 발표했다.\n\n※ 추가경정예산안 발표 후 행안부, 기획처, 복지부 등 관계부처 합동으로 고유가 피해지원금 범정부 TF 구성(3.31.), 총 2회 회의 개최(단장: 행정안전부 차관)\n\n□ 지난 10일 국회에서 확정된 이번 고유가 피해지원금 사업은 중동전쟁으로 인한 고유가· 고물가 등 국민 부담 경감을 목적으로하며, 국민의 70%를 대상으로 소득계층별· 지역별로 1인당 10만원에서 최대 60만원까지 차등 지원한다.\n\n○ 위기 대응 여력이 부족한 취약계층을 보다 신속하게 보호하기 위하여 기초생활수급자, 차상위계층·한부모가족 대상자에 대해서는 4월 27일(월) 부터 피해지원금을 우선 지급하고, 5월 18일(월) 부터는 그 외 70%의 국민을 소득 기준 등으로 선별하여 지급한다.\n\n□ 지원 대상· 규모, 신청· 지급 기간 및 방식 등을 담은 ｢고유가 피해지원금 지급계획｣의 구체적인 내용은 다음과 같다.\n\n## 지원 대상 및 규모\n\n□ 고유가 피해지원금은 추가경정예산안의 국무회의 의결 전날인 2026년 3월 30일(월) 을 기준으로하여, 국내에 거주하는 70%의 국민에게 지급하는 것을 원칙으로 한다.\n\n□ 지방으로 갈수록, 그리고 취약계층일수록 두텁게 지원한다는 원칙 하에, 기초생활수급자에는 55만원, 차상위계층· 한부모가족 대상자에는 45만원을 지급하되, 지원 대상자가 비수도권 및 인구감소지역 주민인 경우 1인당 5만원씩 추가 지급한다.\n\n□ 그 외 70%의 국민에 대하여는 거주 지역별로 수도권 10만원, 비수도권 15만원, 인구감소지역 중 우대지원지역 20만원, 인구감소지역 중 특별지원지역 25만원을 지급한다.\n\n## 신청 주체 및 지역\n\n□ 고유가 피해지원금은 기준일 당시의 주민등록상 주소지 관할 지방정부에서 신청할 수 있으며, 2007년 12월 31일 이전에 출생한 성인은 개인별로 신청하고 지급받을 수 있다.\n\n○ 미성년자의 피해지원금은 주민등록표상 세대주가 신청하여 수령하는 것이 원칙이나, 주민등록표에 성인인 구성원이 없는 미성년 세대주는 예외적으로 직접 신청하여 지급받을 수 있다.\n\n## 신청 및 사용 기간\n\n□ 고유가 피해지원금 신청· 지급은 1 차와 2 차 * 로 나누어 운영된다.\n\n* (1차) 4.27.(월) ~ 5. 8.(금) / (2차) 5.18.(월) ~ 7.3.(금)\n\n○ 기초생활수급자, 차상위계층· 한부모가족은 1 차 신청· 지급 기간에 피해지원금을 온· 오프라인으로 우선 신청할 수 있다.\n\n○ 1 차 기간 내에 피해지원금을 신청하지 못한 기초생활수급자, 차상위계층· 한부모가족 대상자와, 그 외 70%의 국민의 경우 2 차 신청· 지급 기간에 온· 오프라인으로 지원금을 신청할 수 있다.\n\n※ 1 차 기간 내에 피해지원금을 지급받은 경우, 2 차 기간에 중복으로 신청할 수 없음\n\n□ 온라인 신청은 신청· 지급 기간 동안 24시간 가능 * 하고, 오프라인 신청은 평일 오전 9시부터 오후 6 시까지(은행영업점은 오후 4 시까지) 운영된다.\n\n* 단, 신청 마감일에는 오후 6시까지 신청 가능\n\n○ 온· 오프라인 모두 신청 첫 주에는 혼잡 및 시스템 과부하를 막기 위해 출생 연도 끝자리를 기준으로 요일제가 적용되며, 오프라인의 경우 지역 여건에 따라 요일제 적용이 연장될 수 있다.\n\n○ 다만, 4월 27일(월) 부터 이루어지는 1 차 지급의 경우 5월 1일(금) 노동절이 공휴일로 지정됨에 따라, 전날인 4월 30일(목)에 출생 연도 끝자리가 4, 9인 경우뿐만 아니라 5, 0인 경우까지 신청 가능하도록 조정하였다.\n\n□ 1차 및 2차 기간에 지급된 피해지원금은 모두 8월 31일(월) 24시까지 사용하여야 한다.\n\n## 신청 및 지급 방식\n\n□ 먼저, 신용· 체크카드 지급을 원하는 국민은 자신이 이용 중인 카드사 * 의 누리집이나 앱 **, 콜센터와 ARS 등을 통해 온라인으로 신청하거나, 카드와 연계된 은행영업점 *** 을 방문(09:00~16:00) 해 신청할 수 있다.\n\n* 총 9 개 카드사(KB 국민카드, NH 농협카드, 롯데카드, 삼성카드, 신한카드, 우리카드, 하나카드, 현대카드, BC카드)\n\n** 9 개 카드사 앱과 카카오뱅크, 토스(토스뱅크), 케이뱅크, 카카오페이 간편결제, 네이버페이 간편결제 앱을 통해 신청 가능\n\n*** IBK 기업·KB 국민·NH 농협· 하나· 신한· 우리· 수협· 신협 은행, iM 뱅크, 부산· 경남· 광주· 제주 은행, 새마을금고, 우체국, 저축은행(체크카드취급점)에서 신청이 가능하나, 영업점마다 신청 가능 여부가 상이할 수 있으므로 사전 확인 필요\n\n○ 신용· 체크카드로 신청한 고유가 피해지원금은 신청일 다음 날 충전되며, 충전이 이루어지면 문자메시지로 통보된다.\n\n○ 충전된 피해지원금은 카드포인트와 구별되고, 사용처에서 해당 신용· 체크카드로 결제할 경우 피해지원금이 일반 카드결제에 우선하여 사용되며 문자메시지, 앱 알림서비스 등을 통해 잔액이 안내된다.\n\n※ 알림 여부 및 방식은 카드사에 따라 상이할 수 있으므로 사전 확인 필요\n\n□ 모바일 또는 카드형 지역사랑상품권 지급을 희망하는 국민은 주소지 관할 지방정부의 지역사랑상품권 앱 또는 누리집에서 온라인으로 신청할 수 있으며, 신청한 다음 날 지급된다.\n\n○ 지류형 지역사랑상품권 또는 선불카드 수령을 원하는 국민은 주소지 관할 읍면동 행정복지센터(또는 주민센터, 읍· 면사무소)를 방문하면 피해지원금 신청과 수령이 가능하다.\n\n## 사용처 및 사용 지역\n\n□ 고유가 피해지원금은 지역 민생경제 회복에 기여하고 지역 내 소상공인에게 도움이될 수 있도록 사용 지역을 주소지 관할 지방자치단체로 제한한다.\n\n○ 특별시· 광역시(세종, 제주 포함) 주민은 해당 특별시 또는 광역시에서, 도(道) 지역 주민은 주소지에 해당하는 시· 군에서 사용할 수 있다.\n\n※ (예시) 주소지가 서울특별시 중구인 경우 → 서울특별시 내에서 사용 가능 주소지가 충청북도 청주시인 경우 → 청주시 내에서 사용 가능\n\n□ 한편, 사용처 및 업종은 영세 소상공인 지원이라는 취지를 살리면서도, 사용자인 국민이 각자의 소비 성향과 여건에 따라 선택하여 편리하게 사용할 수 있도록 설정했다.\n\n○ 지역사랑상품권으로 지급받은 국민은 기존에 구매한 지역사랑상품권과 마찬가지로 주소지 관할 지방자치단체에 소재한 모든 가맹점에서 자유롭게 이용할 수 있다.\n\n○ 신용· 체크카드 또는 선불카드로 지급받은 국민은, 일부 업종을 제외하고 연 매출액이 30억원 이하인 소상공인 매장 등에서 피해지원금을 사용할 수 있다.\n\n※ 그 외 소비여건이 열악한 읍· 면지역 하나로마트, 로컬푸드직매장(공공형, 면지역 농협· 민간형), 지역소비자생활협동조합, 아름다운 가게는 매출액 제한과 관계없이 사용처에 포함\n\n  - 사용이 제한되는 업종은 대표적으로 온라인 쇼핑몰· 배달앱 *, 유흥· 사행 업종, 환금성 업종 등이 해당하며, 일반적인 지역사랑상품권 사용 가능 업종과 유사한 수준이다.\n\n* 가맹점 자체 단말기를 사용하여 대면 결제(‘만나서 결제’ 방식 등) 하는 경우 사용 가능\n\n## 이의신청\n\n□ 지급 대상자 선정 결과 및 지원 금액에 이의가 있는 국민을 위한 이의 신청 및 처리 절차도 마련되어 있으며, 이의신청 접수 기간은 5월 18일(월) 부터 7월 17일(금)까지이다.\n\n※ 다만, 지급 대상 변동이 없는 이의신청(자녀 부양관계 조정, 미성년자 본인 신청, 수도권과 비수도권 간 이사)은 1차 기간(4.27. ~ 5. 8.)에도 접수 가능\n\n○ 이의신청은 국민신문고(https://www.epeople.go.kr)를 통한 온라인 접수와 읍면동 행정복지센터(또는 주민센터, 읍· 면사무소) 를 통한 오프라인 접수가 모두 가능하며, 피해지원금 신청과 마찬가지로 첫 주에는 요일제가 적용된다.\n\n○ 접수된 이의신청은 지방정부의 심사를 거쳐 처리가 완료되면 개별적으로 통보될 예정이다.\n\n## 국민 편의 제고\n\n□ 국민비서 알림서비스를 신청한 국민은 지급 금액, 신청 기간과 방법, 사용기한 및 지역 등 맞춤형 정보를 미리 안내받을 수 있다.\n\n○ 국민비서 알림서비스는 오는 4월 20일(월)부터 네이버앱, 카카오톡, 토스 및 ‘국민비서 누리집(https://ips.go.kr) ’ 등을 통해 신청할 수 있으며, 1차 지급 시작보다 앞선 4월 25일(토)부터 관련 내용을 안내받을 수 있다.\n\n□ 또한, 거동이 불편한 고령자 등 접근성이 낮은 국민의 편의를 위해 지방정부별로 담당자가 직접 방문해 신청을 접수하고 피해지원금을 지급하는 ‘찾아가는 신청’을 운영해, 사각지대 관리에 소홀함이 없게 준비한다.\n\n□ 아울러, 정부는 1 차 지급 시작까지 남은 약 2주의 기간 동안 신청· 지급 시스템 등 제반 사항을 철저히 점검하는 한편, 국민 불편을 최소화하기 위한 콜센터 * 도 조속히 운영을 시작한다.\n\n* 국민콜110 가동, 고유가 피해지원금 전담 콜센터도 구축 예정(4월 중)\n\n## 국민 70% 선별 기준\n\n□ 5월 18일(월)부터 시작되는 2차 지급은 건강보험료 등을 활용한 소득 선별 과정을 거쳐 국민의 70%를 대상자로 선정하여 지급한다.\n\n○ 건강보험료를 기준으로 국민의 70%를 대상자로 선정하되, 건강보험료 외의 고액자산가를 제외할 수 있는 기준을 추가로 검토하는 등 대상자 선정 기준을 마련하여 5월 중 발표할 예정이다.\n\n□ 한편, 정부나 금융기관 등을 사칭한 스미싱(smishing) 피해를 막기 위해, 정부· 카드사· 지역사랑상품권 운영대행사는 고유가 피해지원금과 관련하여 URL이나 링크가 포함된 문자는 일절 발송하지 않는다.\n\n○ 따라서, 인터넷 주소 클릭을 유도하는 문자를 받았다면 해당 사이트에 절대 접속하지 않고 즉시 삭제하는 등 각별한 주의가 필요하다.\n\n□ 윤호중 행정안전부 장관은 “엄중한 비상경제 상황에서 재정이 민생 경제를 지키는 방파제가 되어야 한다. ”며, “정부는 고유가 피해지원금이 중동전쟁이 몰고 온 거대한 경제적 충격으로부터 서민의 삶을 지켜내는 든든한 버팀목이될 수 있도록 만전을 기하겠다.”라고 밝혔다.\n\n## 담당 부서\n\n- 담당부서: 행정안전부 / 책임자 과장 김수경 / (044-205-3702)\n- 재정정책과: 담당자 / 서기관 조석훈\n- 담당자: 사무관 / 정솔희(044-205-3723)\n- 담당자: 사무관 / 임문성(044-205-3725)\n- 행정안전부: 책임자 / 과장 채영주\n- 지역디지털협력과: 담당자 / 서기관 이관석\n- 담당자: 사무관 / 백경록(044-205-2766)\n- 기획예산처: 책임자 / 과장 진민규\n- 국민복지예산과: 담당자 / 사무관 김준성\n- 보건복지부: 책임자 / 과장 송영조\n- 급여기준과: 담당자 / 사무관 박종철\n\n## 붙임1 인구감소지역 우대지원 지역 및 특별지원 지역\n\n| 구 분 | 인구감소지역(89개) | |\n| --- | --- | --- |\n| 우대지원 지역(49개) | 특별지원 지역 * (40개) | |\n| 부산 | 동구, 서구, 영도구 | |\n| 대구 | 군위, 남구, 서구 | |\n| 인천 | 강화, 옹진 | |\n| 경기 | 가평, 연천 | |\n| 강원 | 고성, 삼척, 양양, 영월, 정선, 철원, 태백, 평창, 홍천, 횡성 | 양구, 화천 |\n| 충북 | 옥천, 제천 | 괴산, 단양, 보은, 영동 |\n| 충남 | 공주, 금산, 논산, 보령, 예산, 태안 | 부여, 서천, 청양 |\n| 전북 | 김제, 남원, 정읍 | 고창, 무주, 부안, 순창, 임실, 장수, 진안 |\n| 전남 | 담양, 영광, 영암, 진도, 화순 | 강진, 고흥, 곡성, 구례, 보성, 신안, 완도, 장성, 장흥, 함평, 해남 |\n| 경북 | 고령, 문경, 성주, 안동, 영주, 영천, 울릉, 울진 | 봉화, 상주, 영덕, 영양, 의성, 청도, 청송 |\n| 경남 | 거창, 밀양, 산청, 창녕, 함안 | 고성, 남해, 의령, 하동, 함양, 합천 |\n\n* 인구감소지역 중 균형발전 하위지역 및 예비타당성조사 낙후도평가 하위지역에 공통으로 해당하는 시･군\n\n## 붙임2 스미싱 피해예방 요령 및 주의 카드뉴스\n\n_이미지형 부록이라 본문 ground-truth에서 제외_\n\n## 붙임4 고유가 피해지원금 지급 관련 주요 Q&A\n\n## 1. 고유가 피해지원금 지급 금액은 얼마인가요?\n\n○ 기초생활수급자는 55만원, 차상위계층과 한부모가족 대상자는 45만원을 지급하되, 비수도권 및 인구감소지역에 거주하는 경우 1인당 5만원을 추가 지급 합니다.\n\n○ 그 외 70%의 국민께는 거주 지역별로 수도권 10만원, 비수도권 15만원, 인구감소 우대지역 20만원, 인구감소 특별지역 25만원을 지급할 예정입니다.\n\n## 2. 인구감소지역 중 특별지원 지역은 어디인가요?\n\n○ 인구감소 지역(89 개) 중 균형발전 하위지역(58 개), 예타 낙후도 평가 하위지역(58 개) 에 공통으로 해당하는 40 개 시· 군을 인구감소 특별지역으로 구분하여 지원하게 됩니다.\n\n## 3. 지급 금액을 사전에 알 수 있는 방법이 있나요?\n\n○ 4월 20 일부터 네이버앱 ‧ 카카오톡 ‧ 토스 등 20 개 모바일 앱 * 또는 국민비서 홈페이지(https://ips.go.kr) 에서 고유가 피해지원금 알림서비스를 사전 요청 하면,\n\n* 네이버(Naver)· 카카오(카카오톡)· 토스(토스)· 국민은행(KB 스타뱅킹)· 국민카드(KB Pay)· 신한은행(신한 SOL)· 우리은행(우리 WON 뱅킹)· 우리카드(우리 WON 카드)· 카카오뱅크(카카오뱅크)· 하나은행(하나원큐)· 하나카드(하나 Pay)·IBK 기업은행(i-ONE Bank)· 농협은행(NH 올원 뱅크)· 농협(NH 콕뱅크)· PASS(SKT, KT, LGU+)·SKT(Tworld)· 현대카드(현대카드)· 농협카드(NHpay)\n\n  - 지급 신청일 이틀 전 ＊ 에 지급 금액, 신청방법, 사용 기한 등을 사전 안내 해드립니다. * (1차) 4.25.(토) / (2차) 5.16.(토)\n\n## 4. 신청은 어느 때에나 가능한가요?\n\n○ 피해지원금은 1 차와 2 차로 나누어 지급 됩니다.\n\n  - 1 차는 기초생활수급자, 차상위계층과 한부모가족이 대상이며 4월 27일(월) 부터 5월 8일(금) 까지 신청 하신 경우 지급 됩니다.\n\n  - 2 차는 70%의 국민과 1 차에 미처 신청하지 못한 분들이 대상이며, 5월 18일(수) 부터 7월 3일(금) 까지 신청 하신 경우 지급 됩니다.\n\n○ 마감 시한인 7월 3일(금) 18시가 지나면, 신청할 수 없기 때문에 지급 대상자는 반드시 기간 내에 신청해야 지급받을 수 있습니다.\n\n○ 온라인･오프라인 신청 모두 시행 첫 주 ＊ 에는 원활한 신청을 위해 ‘ 요 일제 ’ 를 적용 합니다. (출생 연도 끝자리 기준)\n\n  - 다만, 읍면동 주민센터를 통한 오프라인 신청은 지역별 여건에 따라 요일제 적용이 연장될 수 있습니다.\n\n※ 지방정부별 읍면동 주민센터 요일제 운영 기간은 해당 지방정부 홈페이지 또는 전화 문의 등을 통해 확인하시기 바랍니다.\n\n## 5. 누가 신청할 수 있나요?\n\n○ (온라인) 신용· 체크카드 및 모바일 ‧ 카드형 지역사랑상품권은 대상자(성인) 본인이, ‘ 본인 명의 ’ 로만 신청하고, 충전금을받을 수 있습니다.\n\n  - 다만, 미성년 자녀(2008.1.1. 이후 출생자) 는 주민등록 상 세대주 명의로 신청할 수 있습니다.\n\n○ (오프라인) 신용· 체크카드는 카드와 연계된 은행창구에서 신청이 가능하며, ‘ 본인 명의 ’ 로 신청· 수령만 가능합니다.\n\n  - 선불카드, 지류· 카드형 지역사랑상품권은 읍면동 주민센터에서 신청할 수 있고, 신청자 개인 및 대리인 신청 및 수령이 가능합니다.\n\n  - 은행창구, 읍면동 주민센터에서 신청하는 경우 모두 미성년 자녀는 주민등록 상 세대주 명의로 신청 가능합니다.\n\n※ 본인 신청시 신분증(주민등록증, 운전면허증, 여권, 모바일신분증 등) 지참\n\n※ 대리인 신청시 대리인 신분증, 위임장, 본인 - 대리인 관계 증명서류 지참\n\n## 6. 온라인으로 카드 신청을 할 수 없거나, 고령자· 장애인 등 거동이 불편한 주민은 어떻게 신청해야 하나요?\n\n○ 거동이 불편하여 주민센터를 방문할 수 없는 경우에는 해당 지방정부에 ‘ 찾아가는 신청 ’ 을 전화로 요청할 수 있습니다.\n\n  - 단, 다른 가구원이 있는 경우에는 대리 신청이 가능하므로, 찾아가는 신청 요청이 제한될 수 있습니다.\n\n○ 전화를받은 지방정부는 대상자 여부를 조회한 후, 대상자를 방문하여 신청서를 접수 한 후, 지급 준비가 완료되면 재방문하여 상품권 / 선불카드를 지급 하게 됩니다.\n\n※ ‘찾아가는 신청’의 구체적 일정･절차 및 접수처는 지방정부별 자율적으로 안내 예정\n\n## 7. 1 차 신청· 지급 기간에 피해지원금을 지급받은 경우, 2 차 신청· 지급 기간에 다시 신청할 수 있나요?\n\n○ 1 차 신청· 지급 기간(´26. 4.27.~5. 8.) 에 피해지원금을 지급받으신 경우, 2 차 기간(´26. 5.18.~7. 17.) 에는 신청· 지급이 불가 합니다.\n\n## 8. 기초수급자에 해당하지만, 1 차 신청· 지급 시기에 신청을 하지 못하였습니다. 이 경우 지원금을받을 수 없나요?\n\n○ 기초생활수급자, 차상위계층· 한부모가족에 해당하는 경우, 1 차 신청· 지급 기간(´26. 4.27.~5. 8.) 에 신청을 하지 못하였더라도,\n\n  - 2 차 신청· 지급 기간(´26. 5.18.~7. 17.) 에 신청하시면, 피해지원금을 지급받으실 수 있습니다.\n\n※ (기초생활수급자) 55만원, (차상위· 한부모) 45만원 / 비수도권 및 인구감소지역 거주시 5만원 추가지급\n\n## 9. 외국인도 고유가 피해지원금을 신청할 수 있나요?\n\n○ 고유가 피해지원금은 고유가· 고물가로 인한 국민의 부담을 덜어드 리기 위한 것으로, 외국인은 원칙적으로 대상에서 제외됩니다.\n\n○ 다만, 내국인과 연관성이 큰 다음의 경우는 예외적으로 지급대상에 포함됩니다.\n\n① 외국인이 내국인이 1 인 이상 포함 된 주민등록표에 등재 되어 있고, 건강보험 가입자, 피부양자, 의료급여 수급자인 경우\n\n② 외국인만으로 구성된 가구라도 영주권자(F-5), 결혼이민자(F-6) 또는 난민인정자(F-2-4) 가 ‘ 건강보험 가입자, 피부양자, 의료급여 수급자 ’ 인 경우\n\n## 10. 해외에 체류 중인 국민입니다. 고유가 피해지원금을 지급받을 수 있나요?\n\n○ 국외에 체류 중이던 국민이 3월 30일(월) 이후부터 7월 17일(금) 사이에 귀국 하였다면, 이의신청 기한(7.17.) 내에 이의신청을 거쳐 피해지원금을 지급받을 수 있습니다.\n\n## 11. 지급기준일(´26. 3.30.) 이후에 기초수급자 자격 책정이 이루어진 경우, 기초수급자에 해당하는 금액을 지급받을 수 있나요?\n\n○ 지급기준일(´26.3.30.) 에는 기초수급자가 아니었으나, 이후에 자격 책정이 이루어진 경우 라면, 이의신청 기한(7.17.) 내에 이의신청을 거쳐 그에 해당하는 지원금을 지급받으실 수 있습니다.\n\n## 12. 신용· 체크카드로 고유가 피해지원금을 받으려면 어떻게 해야 하나요?\n\n○ 고유가 피해지원금은 온 ‧ 오프라인 신청을 통해 신용･체크카드, 선불카드 및 지역사랑상품권(지류･모바일･카드) 중 선택하여 수령할 수 있습니다.\n\n○ 신용･체크카드로 지급받고 싶은 국민들께서는,\n\n  - 신청기간 내에 충전을 희망하는 카드의 카드사 홈페이지, 앱, 콜센터･ ARS 및 카카오뱅크･토스･카카오페이 간편결제 ･네이버페이 간편결제 앱을 통해 온라인으로 신청하실 수 있습니다.\n\n  - 온라인으로 신청하기 어려운 경우 신청기간 내 각 카드사와 연계된 은행영업점 * 을 방문하여 신청하실 수 있습니다.\n\n* (예시) KB국민카드-KB국민은행, NH농협카드-농협은행 및 농축협\n\n  - 충전금은 신청일로부터 신청 다음날 해당 카드에 지급되며, 피해지원금이 지급되면 문자 등을 통해 알려드릴 예정입니다.\n\n## 13. 선불카드 또는 지역사랑상품권으로 고유가 피해지원금을 받 으려면 어떻게 해야 하나요?\n\n○ 모바일･카드형 지역사랑상품권으로 받길 희망하는 국민들께서는,\n\n  - 신청기간 내에 지방정부별 지역사랑상품권 앱에 접속하여 고유가 피해지원금을 신청 하실 수 있습니다.\n\n※ 단, 온라인 신청이 불가한 일부 지역사랑상품권은 읍면동 주민센터 통해 오프라인 신청이 필요하므로 해당 지방정부 홈페이지 또는 전화 문의 등을 통해 확인하시기 바랍니다.\n\n○ 선불카드 또는 지류형 지역사랑상품권을 받길 희망하시는 경우,\n\n  - 신청기간 내 주소지 관할 읍면동 주민센터를 방문하여 피해지원금을 신청 하실 수 있습니다.\n\n  - 가급적 신청하시는 현장에서 선불카드 또는 지역사랑상품권을 받으실 수 있도록 계획하고 있으나, 부득이한 경우(수량 부족 등) 받으실 장소와 일시를 문자 등으로 안내 해 드릴 예정입니다.\n\n## 14. 고유가 피해지원금 사용 지역 제한이 있나요?\n\n○ 고유가 피해지원금을 지급받은 지역이 특· 광역시 지역(세종･제주 포함) 이라면 해당 특· 광역시 내에서 사용이 가능하고,\n\n  - 지급받은 지역이도 지역이 라면, 도 소재 시· 군 지역 내에서 사용이 가능합니다.\n\n※ (예시) 주소지가 서울특별시 중구인 경우 → 서울특별시 내에서 사용가능 주소지가 충청북도 청주시인 경우 → 청주시 내에서 사용가능\n\n## 15. 고유가 피해지원금은 언제까지 사용 가능한가요?\n\n○ 고유가 피해지원금은 사용 기한이 제한 되어 있습니다.\n\n○ 신용· 체크카드에 충전된 피해지원금, 선불카드, 지역사랑상품권은 8.31.(월) 까지 사용할 수 있습니다.\n\n  - 8.31.(월) 까지 사용하지 못한 피해지원금은 소멸 됩니다.\n\n## 첨부파일\n\n- 260411 (11시) 고유가 피해지원금 4월 27일 지급 시작(재정정책과).hwpx\n- 260411 (11시) 고유가 피해지원금 4월 27일 지급 시작(재정정책과).pdf\n",
      "readhim_markdown": "# 고유가 피해지원금 4월 27일 지급 시작 「고유가 피해지원금」 범정부 TF, 지급계획 발표\n\n정부 보도자료 /\n보도시점: (온라인, 지면) 2026. 4. 11.(토) 11:00\n\n> - 지방으로 갈수록, 취약계층일수록 두텁게 지원\n> - 신속한 피해지원금 지급을 위해 취약계층에 4월 27일부터 지급 시작, 그 외 70% 국민은 5월 18일부터 7월 3일까지 지급\n> - 연 매출액 30억 원 이하 소상공인 업체 등에서 8월 말까지 사용 가능\n---\n정부는 4월 11일(토) 정부서울청사에서 관계부처 합동 브리핑을 개최하고, 고유가 피해지원금의 신청기간·지원규모 등 지급 방안을 담은 ｢고유가 피해지원금 지급계획｣을 발표했다.\n> 추가경정예산안 발표 후 행안부, 기획처, 복지부 등 관계부처 합동으로 고유가 피해지원금 범정부 TF 구성(3.31.), 총 2회 회의 개최(단장: 행정안전부 차관)\n\n지난 10일 국회에서 확정된 이번 고유가 피해지원금 사업은 중동전쟁으로 인한 고유가·고물가 등 국민 부담 경감을 목적으로 하며, 국민의 70%를 대상으로 소득계층별·지역별로 1인당 10만원에서 최대 60만원까지 차등 지원한다.\n- 위기 대응 여력이 부족한 취약계층을 보다 신속하게 보호하기 위하여 기초생활수급자, 차상위계층·한부모가족 대상자에 대하여는 4월 27일(월)부터 피해지원금을 우선 지급하고, 5월 18일(월)부터는 그 외 70%의 국민을 소득 기준 등으로 선별하여 지급한다.\n\n지원 대상·규모, 신청·지급 기간 및 방식 등을 담은 ｢고유가 피해지원금 지급계획｣의 구체적인 내용은 다음과 같다.\n\n#### < 지원 대상 및 규모 >\n\n고유가 피해지원금은 추가경정예산안의 국무회의 의결 전날인 2026년 3월 30일(월)을 기준으로 하여, 국내에 거주하는 70%의 국민에게 지급하는 것을 원칙으로 한다.\n\n지방으로 갈수록, 그리고 취약계층일수록 두텁게 지원한다는 원칙 하에, 기초생활수급자에는 55만원, 차상위계층·한부모가족 대상자에는 45만원을 지급하되, 지원 대상자가 비수도권 및 인구감소지역 주민인 경우 1인당 5만원씩 추가 지급한다.\n\n그 외 70%의 국민에 대하여는 거주 지역별로 수도권 10만원, 비수도권 15만원, 인구감소지역 중 우대지원지역 20만원, 인구감소지역 중 특별지원지역 25만원을 지급한다.\n\n#### < 신청 주체 및 지역 >\n\n고유가 피해지원금은 기준일 당시의 주민등록상 주소지 관할 지방정부에서 신청할 수 있으며, 2007년 12월 31일 이전에 출생한 성인은 개인별로 신청하고 지급 받을 수 있다.\n- 미성년자의 피해지원금은 주민등록표상 세대주가 신청하여 수령하는 것이 원칙이나, 주민등록표에 성인인 구성원이 없는 미성년 세대주는 예외적으로 직접 신청하여 지급 받을 수 있다.\n\n#### < 신청 및 사용 기간 >\n\n고유가 피해지원금 신청·지급은 1차와 2차*로 나누어 운영된다.\n> * (1차) 4. 27.(월) ~ 5. 8.(금) / (2차) 5. 18.(월) ~ 7. 3.(금)\n\n- 기초생활수급자, 차상위계층·한부모가족은 1차 신청·지급 기간에 피해지원금을 온·오프라인으로 우선 신청할 수 있다.\n- 1차 기간 내에 피해지원금을 신청하지 못한 기초생활수급자, 차상위계층·한부모가족 대상자와, 그 외 70%의 국민의 경우 2차 신청·지급 기간에 온·오프라인으로 지원금을 신청할 수 있다.\n> 1차 기간 내에 피해지원금을 지급 받은 경우, 2차 기간에 중복으로 신청할 수 없음\n\n온라인 신청은 신청·지급 기간 동안 24시간 가능*하고, 오프라인 신청은 평일 오전 9시부터 오후 6시까지(은행영업점은 오후 4시까지) 운영된다.\n> * 단, 신청 마감일에는 오후 6시까지 신청 가능\n\n- 온·오프라인 모두 신청 첫 주에는 혼잡 및 시스템 과부하를 막기 위해 출생 연도 끝자리를 기준으로 요일제가 적용되며, 오프라인의 경우 지역 여건에 따라 요일제 적용이 연장될 수 있다.\n- 다만, 4월 27일(월)부터 이루어지는 1차 지급의 경우 5월 1일(금) 노동절이 공휴일로 지정됨에 따라, 전날인 4월 30일(목)에 출생 연도 끝자리가 4, 9인 경우뿐만 아니라 5, 0인 경우까지 신청 가능하도록 조정하였다.\n\n| 1차 | 요일제 구분 / 출생연도 끝자리 | 4.27.(월) / 1,6 | 4.28.(화) / 2,7 | 4.29.(수) / 3,8 | 4.30.(목) / 4,9, 5, 0 | 5.1.(금) / 요일제 해제 |\n| --- | --- | --- | --- | --- | --- | --- |\n| 2차 | 요일제 구분 | 5.18.(월) | 5.19.(화) | 5.20.(수) | 5.21.(목) | 5.22.(금) |\n| 2차 | 출생연도 끝자리 | 1,6 | 2,7 | 3,8 | 4,9 | 5,0 |\n\n1차 및 2차 기간에 지급된 피해지원금은 모두 8월 31일(월) 24시까지 사용하여야 한다.\n\n#### < 신청 및 지급 방식 >\n\n먼저, 신용·체크카드 지급을 원하는 국민은 자신이 이용 중인 카드사*의 누리집이나 앱**, 콜센터와 ARS 등을 통해 온라인으로 신청하거나, 카드와 연계된 은행영업점***을 방문(09:00~16:00)해 신청할 수 있다.\n> * 총 9개 카드사(KB국민카드, NH농협카드, 롯데카드, 삼성카드, 신한카드, 우리카드, 하나카드, 현대카드, BC카드)\n> ** 9개 카드사 앱과 카카오뱅크, 토스(토스뱅크), 케이뱅크, 카카오페이간편결제, 네이버페이간편결제 앱을 통해 신청 가능\n> *** IBK기업·KB국민·NH농협·하나·신한·우리·수협·신협 은행, iM뱅크, 부산·경남·광주·제주 은행, 새마을금고, 우체국, 저축은행(체크카드취급점)에서 신청이 가능하나, 영업점마다 신청 가능 여부가 상이할 수 있으므로 사전 확인 필요\n\n- 신용·체크카드로 신청한 고유가 피해지원금은 신청일 다음 날 충전되며, 충전이 이루어지면 문자메시지로 통보된다.\n- 충전된 피해지원금은 카드포인트와 구별되고, 사용처에서 해당 신용·체크카드로 결제할 경우 피해지원금이 일반 카드결제에 우선하여 사용되며 문자메시지, 앱 알림서비스 등을 통해 잔액이 안내된다.\n> 알림 여부 및 방식은 카드사에 따라 상이할 수 있으므로 사전 확인 필요\n\n모바일 또는 카드형 지역사랑상품권 지급을 희망하는 국민은 주소지 관할 지방정부의 지역사랑상품권 앱 또는 누리집에서 온라인으로 신청할 수 있으며, 신청한 다음 날 지급된다.\n- 지류형 지역사랑상품권 또는 선불카드 수령을 원하는 국민은 주소지 관할 읍면동 행정복지센터(또는 주민센터, 읍·면사무소)를 방문하면 피해지원금 신청과 수령이 가능하다.\n\n#### < 사용처 및 사용 지역 >\n\n고유가 피해지원금은 지역 민생경제 회복에 기여하고 지역 내 소상공인에게 도움이 될 수 있도록 사용 지역을 주소지 관할 지방자치단체로 제한한다.\n- 특별시·광역시(세종, 제주 포함) 주민은 해당 특별시 또는 광역시에서, 도(道) 지역 주민은 주소지에 해당하는 시·군에서 사용할 수 있다.\n> (예시) 주소지가 서울특별시 중구인 경우 → 서울특별시 내에서 사용 가능주소지가 충청북도 청주시인 경우 → 청주시 내에서 사용 가능\n\n한편, 사용처 및 업종은 영세 소상공인 지원이라는 취지를 살리면서도, 사용자인 국민이 각자의 소비 성향과 여건에 따라 선택하여 편리하게 사용할 수 있도록 설정했다.\n- 지역사랑상품권으로 지급 받은 국민은 기존에 구매한 지역사랑상품권과 마찬가지로 주소지 관할 지방자치단체에 소재한 모든 가맹점에서 자유롭게 이용할 수 있다.\n- 신용·체크카드 또는 선불카드로 지급 받은 국민은, 일부 업종을 제외하고 연 매출액이 30억원 이하인 소상공인 매장 등에서 피해지원금을 사용할 수 있다.\n> 그 외 소비여건이 열악한 읍·면지역 하나로마트, 로컬푸드직매장(공공형, 면지역 농협·민간형), 지역소비자생활협동조합, 아름다운 가게는 매출액 제한과 관계없이 사용처에 포함\n\n- 사용이 제한되는 업종은 대표적으로 온라인 쇼핑몰·배달앱*, 유흥·사행업종, 환금성 업종 등이 해당하며, 일반적인 지역사랑상품권 사용 가능 업종과 유사한 수준이다.\n> * 가맹점 자체 단말기를 사용하여 대면 결제(‘만나서 결제’ 방식 등)하는 경우 사용 가능\n\n신용･체크･선불카드 고유가 피해지원금 사용 업종\n󰋻전통시장, 동네마트, 식당, 카페\n󰋻의류점, 미용실, 안경원\n󰋻교습소･학원, 약국･의원\n󰋻대형마트·백화점 내 소상공인이 독립적으로 운영하는 임대매장(꽃집, 안경원 등)\n󰋻프랜차이즈 가맹점(편의점, 치킨집 등)\n󰋻택시는 연 매출액 30억원 이하, 지역제한(면허등록증 차고지 또는 법인 소재지) 충족 시 사용 가능(단, PG 결제시스템 사용시 사용 제한)\n\n#### < 이의신청 >\n\n지급 대상자 선정 결과 및 지원 금액에 이의가 있는 국민을 위한 이의신청 및 처리 절차도 마련되어 있으며, 이의신청 접수 기간은 5월 18일(월)부터 7월 17일(금)까지이다.\n> 다만, 지급 대상 변동이 없는 이의신청(자녀 부양관계 조정, 미성년자 본인 신청, 수도권과 비수도권 간 이사)은 1차 기간(4. 27. ~ 5. 8.)에도 접수 가능\n\n- 이의신청은 국민신문고(https://www.epeople.go.kr)를 통한 온라인 접수와 읍면동 행정복지센터(또는 주민센터, 읍·면사무소)를 통한 오프라인 접수가 모두 가능하며, 피해지원금 신청과 마찬가지로 첫 주에는 요일제가 적용된다.\n\n| 요일제 구분 | 5.18.(월) | 5.19.(화) | 5.20.(수) | 5.21.(목) | 5.22.(금) |\n| --- | --- | --- | --- | --- | --- |\n| 출생연도 끝자리 | 1,6 | 2,7 | 3,8 | 4,9 | 5,0 |\n\n- 접수된 이의신청은 지방정부의 심사를 거쳐 처리가 완료되면 개별적으로 통보될 예정이다.\n\n#### < 국민 편의 제고 >\n\n국민비서 알림서비스를 신청한 국민은 지급 금액, 신청 기간과 방법, 사용기한 및 지역 등 맞춤형 정보를 미리 안내받을 수 있다.\n- 국민비서 알림서비스는 오는 4월 20일(월)부터 네이버앱, 카카오톡, 토스 및 ‘국민비서 누리집(https://ips.go.kr)’ 등을 통해 신청할 수 있으며, 1차 지급 시작보다 앞선 4월 25일(토)부터 관련 내용을 안내받을 수 있다.\n\n또한, 거동이 불편한 고령자 등 접근성이 낮은 국민의 편의를 위해 지방정부별로 담당자가 직접 방문해 신청을 접수하고 피해지원금을 지급하는 ‘찾아가는 신청’을 운영해, 사각지대 관리에 소홀함이 없게 준비한다.\n\n아울러, 정부는 1차 지급 시작까지 남은 약 2주의 기간 동안 신청·지급 시스템 등 제반 사항을 철저히 점검하는 한편, 국민 불편을 최소화하기 위한 콜센터*도 조속히 운영을 시작한다.\n> * 국민콜110 가동, 고유가 피해지원금 전담 콜센터도 구축 예정(4월 중)\n\n#### < 국민 70% 선별 기준 >\n\n5월 18일(월)부터 시작되는 2차 지급은 건강보험료 등을 활용한 소득 선별 과정을 거쳐 국민의 70%를 대상자로 선정하여 지급한다.\n- 건강보험료를 기준으로 국민의 70%를 대상자로 선정하되, 건강보험료 외의 고액자산가를 제외할 수 있는 기준을 추가로 검토하는 등 대상자 선정 기준을 마련하여 5월 중 발표할 예정이다.\n\n한편, 정부나 금융기관 등을 사칭한 스미싱(smishing) 피해를 막기 위해, 정부·카드사·지역사랑상품권 운영대행사는 고유가 피해지원금과 관련하여 URL이나 링크가 포함된 문자는 일절 발송하지 않는다.\n- 따라서, 인터넷 주소 클릭을 유도하는 문자를 받았다면 해당 사이트에 절대 접속하지 않고 즉시 삭제하는 등 각별한 주의가 필요하다.\n\n윤호중 행정안전부장관은 “엄중한 비상경제 상황에서 재정이 민생 경제를 지키는 방파제가 되어야 한다.”며,\n\n“정부는 고유가 피해지원금이 중동전쟁이 몰고 온 거대한 경제적 충격으로부터 서민의 삶을 지켜내는 든든한 버팀목이 될 수 있도록 만전을 기하겠다.”라고 밝혔다.\n\n---\n\n### 담당부서\n\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 책임자: 과장 김수경 (044-205-3702)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 담당자: 서기관 조석훈 (044-205-3727)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 담당자: 사무관 정솔희 (044-205-3723)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 담당자: 사무관 임문성 (044-205-3725)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 책임자: 과장 채영주 (044-205-2761)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 담당자: 서기관 이관석 (044-205-2774)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 담당자: 사무관 백경록 (044-205-2766)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 책임자: 과장 진민규 (044-214-2910)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 담당자: 사무관 김준성 (044-214-2912)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 책임자: 과장 송영조 (044-202-3140)\n- 행정안전부 재정정책과 지역디지털협력과 기획예산처 국민복지예산과 보건복지부 급여기준과 담당자: 사무관 박종철 (044-202-3145)\n---\n\n## 붙임1 인구감소지역 우대지원 지역 및 특별지원 지역\n\n| 구 분 | 인구감소지역(89개) | |\n| --- | --- | --- |\n| 구 분 | 우대지원 지역<br>(49개) | 특별지원 지역*<br>(40개) |\n| 부산 | 동구, 서구, 영도구 | |\n| 대구 | 군위, 남구, 서구 | |\n| 인천 | 강화, 옹진 | |\n| 경기 | 가평, 연천 | |\n| 강원 | 고성, 삼척, 양양, 영월, 정선, 철원, 태백, 평창, 홍천, 횡성 | 양구, 화천 |\n| 충북 | 옥천, 제천 | 괴산, 단양, 보은, 영동 |\n| 충남 | 공주, 금산, 논산, 보령, 예산, 태안 | 부여, 서천, 청양 |\n| 전북 | 김제, 남원, 정읍 | 고창, 무주, 부안, 순창, 임실, 장수, 진안 |\n| 전남 | 담양, 영광, 영암, 진도, 화순 | 강진, 고흥, 곡성, 구례, 보성, 신안, 완도, 장성, 장흥, 함평, 해남 |\n| 경북 | 고령, 문경, 성주, 안동, 영주, 영천, 울릉, 울진 | 봉화, 상주, 영덕, 영양, 의성, 청도, 청송 |\n| 경남 | 거창, 밀양, 산청, 창녕, 함안 | 고성, 남해, 의령, 하동, 함양, 합천 |\n\n> 인구감소지역 중 균형발전 하위지역 및 예비타당성조사 낙후도평가 하위지역에 공통으로 해당하는 시･군\n\n1. 스미싱 피해예방 요령\n\n> □ 정부, 카드사 및 지역화폐사 등은 온라인 신청 시 문자메시지를 악용하는 개인정보 피해(스미싱)를 예방하기 위해 국민께 URL, 링크 등이 포함된 문자메시지를 보내지 않습니다.\n> [고유가 피해지원금 스미싱 주의 안내 문자메시지]고유가 피해지원금 신청·지급시기와 맞물려 정부나 카드사 등을 사칭하여 고유가 피해지원금 지급대상·금액, 카드 사용 승인, 충전 등 안내 정보를 가장하여 의심스러운 인터넷 주소 클릭을 유도(앱 설치 유도)하는 스미싱 시도가 빈번하게 일어날 것으로 예상됩니다. 원칙적으로 정부 및 카드사 등은 고유가 피해지원금 온라인 신청 시 피해를 예방하기 위해 국민께 URL, 링크 등이 포함된 문자메시지를 보내지 않습니다. 그러므로, 문자 속 인터넷 주소(URL)을 클릭하거나, 전화를 할 경우 피해를 입을 수 있으니 각별히 주의하시기 바라며 아래 유의 사항을 반드시 숙지 하시기 바랍니다. ➀ 발신인이 불명확하거나 의심스러운 인터넷 주소(URL)를 포함한 문자는 절대 클릭 하지 마세요. ➁ 의심 문자를 받았거나, 악성앱 감염이 의심되는 경우, 한국인터넷진흥원 118센터(☎118)로 신고하시기 바랍니다.\n> <그림>\n\n2. 스미싱 주의 카드뉴스\n---\n\n## 붙임3 고유가 피해지원금 인포그래픽\n\n---\n\n## 붙임4 고유가 피해지원금 지급 관련 주요 Q&A > 1. 고유가 피해지원금 지급 금액은 얼마인가요?\n\n- 기초생활수급자는 55만원, 차상위계층과 한부모가족 대상자는 45만원을 지급하되, 비수도권 및 인구감소지역에 거주하는 경우 1인당 5만원을 추가 지급합니다.\n- 그 외 70%의 국민께는 거주 지역별로 수도권 10만원, 비수도권 15만원, 인구감소 우대지역 20만원, 인구감소 특별지역 25만원을 지급할 예정입니다.\n> 2. 인구감소지역 중 특별지원 지역은 어디인가요?\n\n- 인구감소지역(89개) 중 균형발전 하위지역(58개), 예타 낙후도 평가 하위지역(58개)에 공통으로 해당하는 40개 시·군을 인구감소 특별지역으로 구분하여 지원하게 됩니다.\n\n| 구 분 | 인구감소지역(89개) | |\n| --- | --- | --- |\n| 구 분 | 우대지원 지역<br>(49개) | 특별지원 지역<br>(40개) |\n| 부산 | 동구, 서구, 영도구 | |\n| 대구 | 군위, 남구, 서구 | |\n| 인천 | 강화, 옹진 | |\n| 경기 | 가평, 연천 | |\n| 강원 | 고성, 삼척, 양양, 영월, 정선, 철원, 태백, 평창, 홍천, 횡성 | 양구, 화천 |\n| 충북 | 옥천, 제천 | 괴산, 단양, 보은, 영동 |\n| 충남 | 공주, 금산, 논산, 보령, 예산, 태안 | 부여, 서천, 청양 |\n| 전북 | 김제, 남원, 정읍 | 고창, 무주, 부안, 순창, 임실, 장수, 진안 |\n| 전남 | 담양, 영광, 영암, 진도, 화순 | 강진, 고흥, 곡성, 구례, 보성, 신안, 완도, 장성, 장흥, 함평, 해남 |\n| 경북 | 고령, 문경, 성주, 안동, 영주, 영천, 울릉, 울진 | 봉화, 상주, 영덕, 영양, 의성, 청도, 청송 |\n| 경남 | 거창, 밀양, 산청, 창녕, 함안 | 고성, 남해, 의령, 하동, 함양, 합천 |\n\n> 3. 지급 금액을 사전에 알 수 있는 방법이 있나요?\n\n- 4월 20일부터 네이버앱‧카카오톡‧토스 등 20개 모바일 앱* 또는 국민비서 홈페이지(https://ips.go.kr)에서 고유가 피해지원금 알림서비스를 사전 요청하면,\n> 네이버(Naver)·카카오(카카오톡)·토스(토스)·국민은행(KB스타뱅킹)·국민카드(KB Pay)·신한은행(신한SOL)·우리은행(우리WON뱅킹)·우리카드(우리WON카드)·카카오뱅크(카카오뱅크)·하나은행(하나원큐)·하나카드(하나Pay)·IBK기업은행(i-ONE Bank)·농협은행(NH올원뱅크)·농협(NH콕뱅크)·PASS(SKT, KT, LGU+)·SKT(Tworld)·현대카드(현대카드)·농협카드(NHpay)\n\n- 지급 신청일 이틀 전＊에 지급 금액, 신청방법, 사용기한 등을 사전 안내해드립니다. * (1차) 4.25.(토) / (2차) 5.16.(토)\n> 4. 신청은 어느 때에나 가능한가요?\n\n- 피해지원금은 1차와 2차로 나누어 지급됩니다.\n- 1차는 기초생활수급자, 차상위계층과 한부모가족이 대상이며 4월 27일(월)부터 5월 8일(금)까지 신청하신 경우 지급됩니다.\n- 2차는 70%의 국민과 1차에 미처 신청하지 못한 분들이 대상이며, 5월 18일(수)부터 7월 3일(금)까지 신청하신 경우 지급됩니다.\n- 마감 시한인 7월 3일(금) 18시가 지나면, 신청할 수 없기 때문에 지급 대상자는 반드시 기간 내에 신청해야 지급 받을 수 있습니다.\n- 온라인･오프라인 신청 모두 시행 첫 주＊에는 원활한 신청을 위해 ‘요일제’를 적용합니다.(출생 연도 끝자리 기준)\n> * <1차> (월)1,6 (화)2,7 (수)3,8 (목)4,9, 5, 0 / 금요일부터 요일제 해제(5.1.노동절)<2차> (월)1,6 (화)2,7 (수)3,8 (목)4,9 (금) 5, 0 / 토요일부터 요일제 해제\n\n- 다만, 읍면동 주민센터를 통한 오프라인 신청은 지역별 여건에 따라 요일제 적용이 연장될 수 있습니다.\n> 지방정부별 읍면동 주민센터 요일제 운영 기간은 해당 지방정부 홈페이지 또는 전화 문의 등을 통해 확인하시기 바랍니다.\n> 5. 누가 신청할 수 있나요?\n\n- (온라인) 신용·체크카드 및 모바일‧카드형 지역사랑상품권은 대상자(성인) 본인이, ‘본인 명의’로만 신청하고, 충전금을 받을 수 있습니다.\n- 다만, 미성년 자녀(2008.1.1. 이후 출생자)는 주민등록 상 세대주 명의로 신청할 수 있습니다.\n- (오프라인) 신용·체크카드는 카드와 연계된 은행창구에서 신청이 가능하며, ‘본인 명의’로 신청·수령만 가능합니다.\n- 선불카드, 지류·카드형 지역사랑상품권은 읍면동 주민센터에서 신청할 수 있고, 신청자 개인 및 대리인 신청 및 수령이 가능합니다.\n- 은행창구, 읍면동 주민센터에서 신청하는 경우 모두 미성년 자녀는 주민등록 상 세대주 명의로 신청 가능합니다.\n> 본인 신청시 신분증(주민등록증, 운전면허증, 여권, 모바일신분증 등) 지참\n> 대리인 신청시 대리인 신분증, 위임장, 본인-대리인 관계 증명서류 지참\n\n#### 6. 온라인으로 카드 신청을 할 수 없거나, 고령자·장애인 등거동이 불편한 주민은 어떻게 신청해야 하나요?\n\n- 거동이 불편하여 주민센터를 방문할 수 없는 경우에는 해당 지방정부에 ‘찾아가는 신청’을 전화로 요청할 수 있습니다.\n- 단, 다른 가구원이 있는 경우에는 대리 신청이 가능하므로, 찾아가는 신청 요청이 제한될 수 있습니다.\n- 전화를 받은 지방정부는 대상자 여부를 조회한 후, 대상자를 방문하여 신청서를 접수한 후, 지급 준비가 완료되면 재방문하여 상품권/선불카드를 지급하게 됩니다.\n> ‘찾아가는 신청’의 구체적 일정･절차 및 접수처는 지방정부별 자율적으로 안내 예정\n> 7. 1차 신청·지급 기간에 피해지원금을 지급받은 경우, 2차 신청·지급 기간에 다시 신청할 수 있나요?\n\n- 1차 신청·지급 기간(´26.4.27.~5.8.)에 피해지원금을 지급받으신 경우, 2차 기간(´26.5.18.~7.17.)에는 신청·지급이 불가합니다.\n> 8. 기초수급자에 해당하지만, 1차 신청·지급 시기에 신청을 하지 못하였습니다. 이 경우 지원금을 받을 수 없나요?\n\n- 기초생활수급자, 차상위계층·한부모가족에 해당하는 경우, 1차 신청·지급 기간(´26.4.27.~5.8.)에 신청을 하지 못하였더라도,\n- 2차 신청·지급 기간(´26.5.18.~7.17.)에 신청하시면, 피해지원금을 지급받으실 수 있습니다.\n> (기초생활수급자) 55만원, (차상위·한부모) 45만원 / 비수도권 및 인구감소지역 거주시 5만원 추가지급\n> 9. 외국인도 고유가 피해지원금을 신청할 수 있나요?\n\n- 고유가 피해지원금은 고유가·고물가로 인한 국민의 부담을 덜어드리기 위한 것으로, 외국인은 원칙적으로 대상에서 제외됩니다.\n- 다만, 내국인과 연관성이 큰 다음의 경우는 예외적으로 지급대상에 포함됩니다.\n1. 외국인이 내국인이 1인 이상 포함된 주민등록표에 등재되어 있고, 건강보험 가입자, 피부양자, 의료급여 수급자인 경우\n\n2. 외국인만으로 구성된 가구라도 영주권자(F-5), 결혼이민자(F-6) 또는 난민인정자(F-2-4)가 ‘건강보험 가입자, 피부양자, 의료급여 수급자’인 경우\n\n> 10. 해외에 체류 중인 국민입니다. 고유가 피해지원금을 지급받을 수 있나요?\n\n- 국외에 체류 중이던 국민이 3월 30일(월) 이후부터 7월 17일(금) 사이에 귀국하였다면, 이의신청 기한(7.17.) 내에 이의신청을 거쳐 피해지원금을 지급받을 수 있습니다.\n> 11. 지급기준일(´26.3.30.) 이후에 기초수급자 자격 책정이 이루어진 경우, 기초수급자에 해당하는 금액을 지급받을 수 있나요?\n\n- 지급기준일(´26.3.30.)에는 기초수급자가 아니었으나, 이후에 자격 책정이 이루어진 경우라면, 이의신청 기한(7.17.) 내에 이의신청을 거쳐 그에 해당하는 지원금을 지급받으실 수 있습니다.\n> 12. 신용·체크카드로 고유가 피해지원금을 받으려면 어떻게 해야 하나요?\n\n- 고유가 피해지원금은 온‧오프라인 신청을 통해 신용･체크카드, 선불카드 및 지역사랑상품권(지류･모바일･카드) 중 선택하여 수령할 수 있습니다.\n- 신용･체크카드로 지급받고 싶은 국민들께서는,\n- 신청기간 내에 충전을 희망하는 카드의 카드사 홈페이지, 앱, 콜센터･ARS 및 카카오뱅크･토스･카카오페이간편결제･네이버페이간편결제 앱을 통해 온라인으로 신청하실 수 있습니다.\n- 온라인으로 신청하기 어려운 경우 신청기간 내 각 카드사와 연계된 은행영업점*을 방문하여 신청하실 수 있습니다.\n> (예시) KB국민카드-KB국민은행, NH농협카드-농협은행 및 농축협\n\n- 충전금은 신청일로부터 신청 다음날 해당 카드에 지급되며, 피해지원금이 지급되면 문자 등을 통해 알려드릴 예정입니다.\n> 13. 선불카드 또는 지역사랑상품권으로 고유가 피해지원금을 받으려면 어떻게 해야 하나요?\n\n- 모바일･카드형 지역사랑상품권으로 받길 희망하는 국민들께서는,\n- 신청기간 내에 지방정부별 지역사랑상품권 앱에 접속하여 고유가 피해지원금을 신청하실 수 있습니다.\n> 단, 온라인 신청이 불가한 일부 지역사랑상품권은 읍면동 주민센터 통해 오프라인 신청이 필요하므로 해당 지방정부 홈페이지 또는 전화 문의 등을 통해 확인하시기 바랍니다.\n\n- 선불카드 또는 지류형 지역사랑상품권을 받길 희망하시는 경우,\n- 신청기간 내 주소지 관할 읍면동 주민센터를 방문하여 피해지원금을 신청하실 수 있습니다.\n- 가급적 신청하시는 현장에서 선불카드 또는 지역사랑상품권을 받으실 수 있도록 계획하고 있으나, 부득이한 경우(수량 부족 등) 받으실 장소와 일시를 문자 등으로 안내해 드릴 예정입니다.\n> 14. 고유가 피해지원금 사용 지역 제한이 있나요?\n\n- 고유가 피해지원금을 지급받은 지역이 특·광역시 지역(세종･제주 포함)이라면 해당 특·광역시 내에서 사용이 가능하고,\n- 지급받은 지역이 도 지역이라면, 도 소재 시·군 지역 내에서 사용이 가능합니다.\n> (예시) 주소지가 서울특별시 중구인 경우 → 서울특별시 내에서 사용가능주소지가 충청북도 청주시인 경우 → 청주시 내에서 사용가능\n> 15. 고유가 피해지원금은 언제까지 사용 가능한가요?\n\n- 고유가 피해지원금은 사용 기한이 제한되어 있습니다.\n- 신용·체크카드에 충전된 피해지원금, 선불카드, 지역사랑상품권은 8.31.(월)까지 사용할 수 있습니다.\n- 8.31.(월)까지 사용하지 못한 피해지원금은 소멸됩니다.\n",
      "opendataloader_markdown": "|보도자료|\n|---|\n\n\n보도시점 (온라인, 지면) 2026. 4. 11.(토) 11:00\n\n|고유가 피해지원금 4월 27일 지급 시작<br><br>- 「고유가 피해지원금」 범정부 TF, 지급계획 발표<br>- 지방으로 갈수록, 취약계층일수록 두텁게 지원<br>- 신속한 피해지원금 지급을 위해 취약계층에 4월 27일부터 지급 시작, 그 외 70% 국민은 5월 18일부터 7월 3일까지 지급<br>- 연 매출액 30억 원 이하 소상공인 업체 등에서 8월 말까지 사용 가능<br>|\n|---|\n\n\n- □ 정부는 4월 11일(토) 정부서울청사에서 관계부처 합동 브리핑을 개최 하고, 고유가 피해지원금의 신청기간 · 지원규모 등 지급 방안을 담은 ｢고유가 피해지원금 지급계획｣을 발표했다.\n\n※ 추가경정예산안 발표 후 행안부, 기획처, 복지부 등 관계부처 합동으로 고유가 피해지원금 범정부 TF 구성(3.31.), 총 2회 회의 개최(단장: 행정안전부 차관)\n\n- □ 지난 10일 국회에서 확정된 이번 고유가 피해지원금 사업은 중동전쟁 으로 인한 고유가 · 고물가 등 국민 부담 경감을 목적으로 하며, 국민의 70%를 대상으로 소득계층별 · 지역별로 1인당 10만원에서 최대 60만원까지 차등 지원한다.\n\n○ 위기 대응 여력이 부족한 취약계층을 보다 신속하게 보호하기 위하여 기초생활수급자, 차상위계층·한부모가족 대상자에 대하여는 4월 27일 (월)부터 피해지원금을 우선 지급하고, 5월 18일(월)부터는 그 외 70%의 국민을 소득 기준 등으로 선별하여 지급한다.\n\n- □ 지원 대상 · 규모, 신청 · 지급 기간 및 방식 등을 담은 ｢고유가 피해지원금 지급계획｣의 구체적인 내용은 다음과 같다.\n\n\n- 1 -\n\n#### < 지원 대상 및 규모 >\n\n- □ 고유가 피해지원금은 추가경정예산안의 국무회의 의결 전날인 2026년 3월 30일(월)을 기준으로 하여, 국내에 거주하는 70%의 국민에게 지급 하는 것을 원칙으로 한다.\n- □ 지방으로 갈수록, 그리고 취약계층일수록 두텁게 지원한다는 원칙 하에, 기초생활수급자에는 55만원, 차상위계층 · 한부모가족 대상자에는 45만원을 지급하되, 지원 대상자가 비수도권 및 인구감소지역 주민인 경우 1인당 5만원씩 추가 지급한다.\n- □ 그 외 70%의 국민에 대하여는 거주 지역별로 수도권 10만원, 비수도권 15만원, 인구감소지역 중 우대지원지역 20만원, 인구감소지역 중 특별 지원지역 25만원을 지급한다.\n\n\n#### < 신청 주체 및 지역 >\n\n□ 고유가 피해지원금은 기준일 당시의 주민등록상 주소지 관할 지방정부에서 신청할 수 있으며, 2007년 12월 31일 이전에 출생한 성인은 개인별로 신청하고 지급 받을 수 있다.\n\n○ 미성년자의 피해지원금은 주민등록표상 세대주가 신청하여 수령하는 것이 원칙이나, 주민등록표에 성인인 구성원이 없는 미성년 세대주는 예외적으로 직접 신청하여 지급 받을 수 있다.\n\n#### < 신청 및 사용 기간 >\n\n##### □ 고유가 피해지원금 신청 · 지급은 1차와 2차*로 나누어 운영된다.\n\n* (1차) 4. 27.(월) ~ 5. 8.(금) / (2차) 5. 18.(월) ~ 7. 3.(금)\n\n- ○ 기초생활수급자, 차상위계층 · 한부모가족은 1차 신청 · 지급 기간에 피해 지원금을 온 · 오프라인으로 우선 신청할 수 있다.\n- ○ 1차 기간 내에 피해지원금을 신청하지 못한 기초생활수급자, 차상위계층 · 한부모가족 대상자와, 그 외 70%의 국민의 경우 2차 신청 · 지급 기간에 온 · 오프라인으로 지원금을 신청할 수 있다.\n\n\n※ 1차 기간 내에 피해지원금을 지급 받은 경우, 2차 기간에 중복으로 신청할 수 없음\n\n##### □ 온라인 신청은 신청 · 지급 기간 동안 24시간 가능*하고, 오프라인 신청은평일 오전 9시부터 오후 6시까지(은행영업점은 오후 4시까지) 운영된다.\n\n* 단, 신청 마감일에는 오후 6시까지 신청 가능\n\n- ○ 온 · 오프라인 모두 신청 첫 주에는 혼잡 및 시스템 과부하를 막기 위해 출생 연도 끝자리를 기준으로 요일제가 적용되며, 오프라인의 경우 지역 여건에 따라 요일제 적용이 연장될 수 있다.\n- ○ 다만, 4월 27일(월)부터 이루어지는 1차 지급의 경우 5월 1일(금) 노동절이 공휴일로 지정됨에 따라, 전날인 4월 30일(목)에 출생 연도 끝자리가 4, 9인 경우뿐만 아니라 5, 0인 경우까지 신청 가능하도록 조정하였다.\n\n\n|1차|요일제 구분|4.27.(월)|4.28.(화)|4.29.(수)|4.30.(목)|5.1.(금)|\n|---|---|---|---|---|---|---|\n| |출생연도 끝자리|1, 6|2, 7|3, 8|4, 9, 5, 0|요일제 해제|\n|2차|요일제 구분|5.18.(월)|5.19.(화)|5.20.(수)|5.21.(목)|5.22.(금)|\n| |출생연도 끝자리|1, 6|2, 7|3, 8|4, 9|5, 0|\n\n\n##### □ 1차 및 2차 기간에 지급된 피해지원금은 모두 8월 31일(월) 24시까지사용하여야 한다.\n\n#### < 신청 및 지급 방식 >\n\n##### □ 먼저, 신용 · 체크카드 지급을 원하는 국민은 자신이 이용 중인 카드사*의누리집이나 앱**, 콜센터와 ARS 등을 통해 온라인으로 신청하거나,카드와 연계된 은행영업점***을 방문(09:00~16:00)해 신청할 수 있다.\n\n- * 총 9개 카드사(KB국민카드, NH농협카드, 롯데카드, 삼성카드, 신한카드, 우리카드, 하나카드, 현대카드, BC카드)\n- ** 9개 카드사 앱과 카카오뱅크, 토스(토스뱅크), 케이뱅크, 카카오페이간편결제, 네이버 페이간편결제 앱을 통해 신청 가능\n\n\n*** IBK기업·KB국민·NH농협·하나·신한·우리·수협·신협 은행, iM뱅크, 부산·경남·광주·제주 은행, 새마을금고, 우체국, 저축은행(체크카드취급점)에서 신청이 가능하나, 영업점마다 신청 가능 여부가 상이할 수 있으므로 사전 확인 필요\n\n##### ○ 신용 · 체크카드로 신청한 고유가 피해지원금은 신청일 다음 날 충전되며,충전이 이루어지면 문자메시지로 통보된다.\n\n##### ○ 충전된 피해지원금은 카드포인트와 구별되고, 사용처에서 해당 신용 ·체크카드로 결제할 경우 피해지원금이 일반 카드결제에 우선하여 사용되며 문자메시지, 앱 알림서비스 등을 통해 잔액이 안내된다.\n\n※ 알림 여부 및 방식은 카드사에 따라 상이할 수 있으므로 사전 확인 필요\n\n- □ 모바일 또는 카드형 지역사랑상품권 지급을 희망하는 국민은 주소지 관할 지방정부의 지역사랑상품권 앱 또는 누리집에서 온라인으로 신청할 수 있으며, 신청한 다음 날 지급된다.\n\n\n○ 지류형 지역사랑상품권 또는 선불카드 수령을 원하는 국민은 주소지 관할 읍면동 행정복지센터(또는 주민센터, 읍 · 면사무소)를 방문하면 피해지원금 신청과 수령이 가능하다.\n\n#### < 사용처 및 사용 지역 >\n\n##### □ 고유가 피해지원금은 지역 민생경제 회복에 기여하고 지역 내 소상공인에게도움이 될 수 있도록 사용 지역을 주소지 관할 지방자치단체로 제한한다.\n\n○ 특별시 · 광역시(세종, 제주 포함) 주민은 해당 특별시 또는 광역시에서, 도(道) 지역 주민은 주소지에 해당하는 시 · 군에서 사용할 수 있다.\n\n※ (예시) 주소지가 서울특별시 중구인 경우 → 서울특별시 내에서 사용 가능 주소지가 충청북도 청주시인 경우 → 청주시 내에서 사용 가능\n\n##### □ 한편, 사용처 및 업종은 영세 소상공인 지원이라는 취지를 살리면서도,사용자인 국민이 각자의 소비 성향과 여건에 따라 선택하여 편리하게사용할 수 있도록 설정했다.\n\n- ○ 지역사랑상품권으로 지급 받은 국민은 기존에 구매한 지역사랑상품권과 마찬가지로 주소지 관할 지방자치단체에 소재한 모든 가맹점에서 자유롭게 이용할 수 있다.\n- ○ 신용 · 체크카드 또는 선불카드로 지급 받은 국민은, 일부 업종을 제외하고 연 매출액이 30억원 이하인 소상공인 매장 등에서 피해지원금을 사용할 수 있다.\n\n\n※ 그 외 소비여건이 열악한 읍·면지역 하나로마트, 로컬푸드직매장(공공형, 면지역 농협·민간형), 지역소비자생활협동조합, 아름다운 가게는 매출액 제한과 관계없이 사용처에 포함\n\n##### - 사용이 제한되는 업종은 대표적으로 온라인 쇼핑몰 · 배달앱*, 유흥 · 사행 업종, 환금성 업종 등이 해당하며, 일반적인 지역사랑상품권 사용 가능 업종과 유사한 수준이다.\n\n* 가맹점 자체 단말기를 사용하여 대면 결제(‘만나서 결제’ 방식 등)하는 경우 사용 가능\n\n< 신용･체크･선불카드 고유가 피해지원금 사용 업종 >\n\n|사용가능 가맹점 (예시)|사용제한 업종|\n|---|---|\n|전통시장, 동네마트, 식당, 카페 의류점, 미용실, 안경원 교습소･학원, 약국･의원 대형마트 · 백화점 내 소상공인이 독립적으로<br><br>운영하는 임대매장(꽃집, 안경원 등) 프랜차이즈 가맹점(편의점, 치킨집 등) 택시는 연 매출액 30억원 이하, 지역제한<br><br>(면허등록증 차고지 또는 법인 소재지) 충족 시 사용 가능(단, PG 결제시스템 사용시 사용 제한)|유흥･사행업종, 환금성 업종 온라인 전자상거래(쇼핑몰, 배달앱* 등)<br><br>* 가맹점 자체 단말기를 사용하여 대면결제 (‘만나서 결제’)하는 경우는 사용 가능<br><br>대형 외국계 매장 조세･공공요금, 교통･통신요금 자동이체 PG 결제 시스템을 사용하는 키오스크･<br><br>테이블주문시스템<br><br>생명보험, 국민연금, 건강보험 등 보험업 종교단체 기부금, 학술단체, 협회 등<br><br>비소비성 지출|\n\n\n#### < 이의신청 >\n\n##### □ 지급 대상자 선정 결과 및 지원 금액에 이의가 있는 국민을 위한 이의 신청 및 처리 절차도 마련되어 있으며, 이의신청 접수 기간은 5월 18일(월) 부터 7월 17일(금)까지이다.\n\n※ 다만, 지급 대상 변동이 없는 이의신청(자녀 부양관계 조정, 미성년자 본인 신청, 수도권과 비수도권 간 이사)은 1차 기간(4. 27. ~ 5. 8.)에도 접수 가능\n\n- ○ 이의신청은 국민신문고(https://www.epeople.go.kr)를 통한 온라인 접수와 읍면동 행정복지센터(또는 주민센터, 읍·면사무소)를 통한 오프라인 접수가 모두 가능하며, 피해지원금 신청과 마찬가지로 첫 주에는 요일제가 적용된다.\n\n|요일제 구분|5.18.(월)|5.19.(화)|5.20.(수)|5.21.(목)|5.22.(금)|\n|---|---|---|---|---|---|\n|출생연도 끝자리|1, 6|2, 7|3, 8|4, 9|5, 0|\n\n\n- ○ 접수된 이의신청은 지방정부의 심사를 거쳐 처리가 완료되면 개별적 으로 통보될 예정이다.\n\n\n#### < 국민 편의 제고 >\n\n- □ 국민비서 알림서비스를 신청한 국민은 지급 금액, 신청 기간과 방법, 사용기한 및 지역 등 맞춤형 정보를 미리 안내받을 수 있다.\n\n\n○ 국민비서 알림서비스는 오는 4월 20일(월)부터 네이버앱, 카카오톡, 토스 및 ‘국민비서 누리집(https://ips.go.kr)’ 등을 통해 신청할 수 있으며, 1차 지급 시작보다 앞선 4월 25일(토)부터 관련 내용을 안내 받을 수 있다.\n\n- □ 또한, 거동이 불편한 고령자 등 접근성이 낮은 국민의 편의를 위해 지방 정부별로 담당자가 직접 방문해 신청을 접수하고 피해지원금을 지급하는 ‘찾아가는 신청’을 운영해, 사각지대 관리에 소홀함이 없게 준비한다.\n- □ 아울러, 정부는 1차 지급 시작까지 남은 약 2주의 기간 동안 신청 · 지급 시스템 등 제반 사항을 철저히 점검하는 한편, 국민 불편을 최소화하기 위한 콜센터*도 조속히 운영을 시작한다.\n\n\n* 국민콜110 가동, 고유가 피해지원금 전담 콜센터도 구축 예정(4월 중)\n\n#### < 국민 70% 선별 기준 >\n\n- □ 5월 18일(월)부터 시작되는 2차 지급은 건강보험료 등을 활용한 소득 선별 과정을 거쳐 국민의 70%를 대상자로 선정하여 지급한다.\n\n○ 건강보험료를 기준으로 국민의 70%를 대상자로 선정하되, 건강보험료 외의 고액자산가를 제외할 수 있는 기준을 추가로 검토하는 등 대상자 선정 기준을 마련하여 5월 중 발표할 예정이다.\n\n- □ 한편, 정부나 금융기관 등을 사칭한 스미싱(smishing) 피해를 막기 위해, 정부 · 카드사 · 지역사랑상품권 운영대행사는 고유가 피해지원금과 관련하여 URL이나 링크가 포함된 문자는 일절 발송하지 않는다.\n\n○ 따라서, 인터넷 주소 클릭을 유도하는 문자를 받았다면 해당 사이트에 절대 접속하지 않고 즉시 삭제하는 등 각별한 주의가 필요하다.\n\n- □ 윤호중 행정안전부 장관은 “엄중한 비상경제 상황에서 재정이 민생 경제를 지키는 방파제가 되어야 한다.”며, “정부는 고유가 피해지원금이 중동전쟁이 몰고 온 거대한 경제적 충격으로부터 서민의 삶을 지켜내는 든든한 버팀목이 될 수 있도록 만전을 기하겠다.”라고 밝혔다.\n\n\n|담당부서|행정안전부 재정정책과|책임자|과 장 김수경 (044-205-3702)|\n|---|---|---|---|\n| | |담당자|서기관 조석훈 (044-205-3727)|\n| | |담당자|사무관 정솔희 (044-205-3723)|\n| | |담당자|사무관 임문성 (044-205-3725)|\n| |행정안전부 지역디지털협력과|책임자|과 장 채영주 (044-205-2761)|\n| | |담당자|서기관 이관석 (044-205-2774)|\n| | |담당자|사무관 백경록 (044-205-2766)|\n| |기획예산처 국민복지예산과|책임자|과 장 진민규 (044-214-2910)|\n| | |담당자|사무관 김준성 (044-214-2912)|\n| |보건복지부 급여기준과|책임자|과 장 송영조 (044-202-3140)|\n| | |담당자|사무관 박종철 (044-202-3145)|\n\n\n|붙임1|\n|---|\n\n\n|인구감소지역 우대지원 지역 및 특별지원 지역|\n|---|\n\n\n|구 분|인구감소지역(89개)| |\n|---|---|---|\n| |우대지원 지역 (49개)|특별지원 지역* (40개)|\n|부산|동구, 서구, 영도구| |\n|대구|군위, 남구, 서구| |\n|인천|강화, 옹진| |\n|경기|가평, 연천| |\n|강원|고성, 삼척, 양양, 영월, 정선, 철원, 태백, 평창, 홍천, 횡성|양구, 화천|\n|충북|옥천, 제천|괴산, 단양, 보은, 영동|\n|충남|공주, 금산, 논산, 보령, 예산, 태안|부여, 서천, 청양|\n|전북|김제, 남원, 정읍|고창, 무주, 부안, 순창, 임실, 장수, 진안|\n|전남|담양, 영광, 영암, 진도, 화순|강진, 고흥, 곡성, 구례, 보성, 신안, 완도, 장성, 장흥, 함평, 해남|\n|경북|고령, 문경, 성주, 안동, 영주, 영천, 울릉, 울진|봉화, 상주, 영덕, 영양, 의성, 청도, 청송|\n|경남|거창, 밀양, 산청, 창녕, 함안|고성, 남해, 의령, 하동, 함양, 합천|\n\n\n* 인구감소지역 중 균형발전 하위지역 및 예비타당성조사 낙후도평가 하위지역에 공통으로 해당하는 시･군\n\n|붙임2|\n|---|\n\n\n|스미싱 피해예방 요령 및 주의 카드뉴스|\n|---|\n\n\n##  스미싱 피해예방 요령\n\n□ 정부, 카드사 및 지역화폐사 등은 온라인 신청 시 문자메시지를 악용하는 개인정보 피해(스미싱)를 예방하기 위해 국민께 URL, 링크 등이 포함된 문자메시지를 보내지 않습니다.\n\n|[고유가 피해지원금 스미싱 주의 안내 문자메시지]<br><br>고유가 피해지원금 신청·지급시기와 맞물려 정부나 카드사 등을 사칭하여 고유가 피해 지원금 지급대상·금액, 카드 사용 승인, 충전 등 안내 정보를 가장하여 의심스러운 인 터넷 주소 클릭을 유도(앱 설치 유도)하는 스미싱 시도가 빈번하게 일어날 것으로 예상됩니다. 원칙적으로 정부 및 카드사 등은 고유가 피해지원금 온라인 신청 시 피해를 예방하기 위해 국민께 URL, 링크 등이 포함된 문자메시지를 보내지 않습니다. 그러므로, 문자 속 인터넷 주소(URL)을 클릭하거나, 전화를 할 경우 피해를 입을 수 있으니 각별히 주의하시기 바라며 아래 유의 사항을 반드시 숙지 하시기 바랍니다.<br><br>➀ 발신인이 불명확하거나 의심스러운 인터넷 주소(URL)를 포함한 문자는 절대 클릭 하지 마세요.<br><br>➁ 의심 문자를 받았거나, 악성앱 감염이 의심되는 경우, 한국인터넷진흥원 118센터(☎118)로 신고하시기 바랍니다.<br><br>|\n|---|\n\n\n##  스미싱 주의 카드뉴스\n\n| | |\n|---|---|\n| | |\n| | |\n| | |\n\n\n|붙임3|\n|---|\n\n\n|고유가 피해지원금 인포그래픽|\n|---|\n\n\n|붙임4|\n|---|\n\n\n|고유가 피해지원금 지급 관련 주요 Q&A|\n|---|\n\n\n||1. 고유가 피해지원금 지급 금액은 얼마인가요?|\n|---|\n|\n|---|\n\n\n- ○ 기초생활수급자는 55만원, 차상위계층과 한부모가족 대상자는 45만원을 지급하되, 비수도권 및 인구감소지역에 거주하는 경우 1인당 5만원을 추가 지급합니다.\n- ○ 그 외 70%의 국민께는 거주 지역별로 수도권 10만원, 비수도권 15만원, 인구감소 우대지역 20만원, 인구감소 특별지역 25만원을 지급할 예정입니다.\n\n||2. 인구감소지역 중 특별지원 지역은 어디인가요?|\n|---|\n|\n|---|\n\n\n- ○ 인구감소지역(89개) 중 균형발전 하위지역(58개), 예타 낙후도 평가 하 위지역(58개)에 공통으로 해당하는 40개 시·군을 인구감소 특별지역 으로 구분하여 지원하게 됩니다.\n\n\n|구 분|인구감소지역(89개)| |\n|---|---|---|\n| |우대지원 지역 (49개)|특별지원 지역 (40개)|\n|부산|동구, 서구, 영도구| |\n|대구|군위, 남구, 서구| |\n|인천|강화, 옹진| |\n|경기|가평, 연천| |\n|강원|고성, 삼척, 양양, 영월, 정선, 철원, 태백, 평창, 홍천, 횡성|양구, 화천|\n|충북|옥천, 제천|괴산, 단양, 보은, 영동|\n|충남|공주, 금산, 논산, 보령, 예산, 태안|부여, 서천, 청양|\n|전북|김제, 남원, 정읍|고창, 무주, 부안, 순창, 임실, 장수, 진안|\n|전남|담양, 영광, 영암, 진도, 화순|강진, 고흥, 곡성, 구례, 보성, 신안, 완도, 장성, 장흥, 함평, 해남|\n|경북|고령, 문경, 성주, 안동, 영주, 영천, 울릉, 울진|봉화, 상주, 영덕, 영양, 의성, 청도, 청송|\n|경남|거창, 밀양, 산청, 창녕, 함안|고성, 남해, 의령, 하동, 함양, 합천|\n\n\n||3. 지급 금액을 사전에 알 수 있는 방법이 있나요?|\n|---|\n|\n|---|\n\n\n- ○ 4월 20일부터 네이버앱‧카카오톡‧토스 등 20개 모바일 앱* 또는 국민비서 홈페이지(https://ips.go.kr)에서 고유가 피해지원금 알림 서비스를 사전 요청하면,\n\n* 네이버(Naver)·카카오(카카오톡)·토스(토스)·국민은행(KB스타뱅킹)·국민카드(KB Pay)·신한은행 (신한SOL)·우리은행(우리WON뱅킹)·우리카드(우리WON카드)·카카오뱅크(카카오뱅크)· 하나은행(하나원큐)·하나카드(하나Pay)·IBK기업은행(i-ONE Bank)·농협은행(NH올원뱅크)· 농협(NH콕뱅크)·PASS(SKT, KT, LGU+)·SKT(Tworld)·현대카드(현대카드)·농협카드(NHpay)\n\n- 지급 신청일 이틀 전＊에 지급 금액, 신청방법, 사용기한 등을 사\n\n전 안내해드립니다. * (1차) 4.25.(토) / (2차) 5.16.(토)\n\n||4. 신청은 어느 때에나 가능한가요?|\n|---|\n|\n|---|\n\n\n- ○ 피해지원금은 1차와 2차로 나누어 지급됩니다.\n\n- - 1차는 기초생활수급자, 차상위계층과 한부모가족이 대상이며 4월 27일(월)부터 5월 8일(금)까지 신청하신 경우 지급됩니다.\n\n- - 2차는 70%의 국민과 1차에 미처 신청하지 못한 분들이 대상이며, 5 월 18일(수)부터 7월 3일(금)까지 신청하신 경우 지급됩니다.\n\n\n- ○ 마감 시한인 7월 3일(금) 18시가 지나면, 신청할 수 없기 때문에 지급 대상자는 반드시 기간 내에 신청해야 지급 받을 수 있습니다.\n\n- ○ 온라인･오프라인 신청 모두 시행 첫 주＊에는 원활한 신청을 위해 ‘요일제’를 적용합니다.(출생 연도 끝자리 기준)\n\n\n* <1차> (월) 1, 6 (화) 2, 7 (수) 3, 8 (목)4,9, 5, 0 / 금요일부터 요일제 해제(5.1.노동절) <2차> (월) 1, 6 (화) 2, 7 (수) 3, 8 (목) 4, 9 (금) 5, 0 / 토요일부터 요일제 해제\n\n### - 다만, 읍면동 주민센터를 통한 오프라인 신청은 지역별 여건에 따라 요일제 적용이 연장될 수 있습니다.\n\n※ 지방정부별 읍면동 주민센터 요일제 운영 기간은 해당 지방정부 홈페이지 또는 전화 문의 등을 통해 확인하시기 바랍니다.\n\n||5. 누가 신청할 수 있나요?|\n|---|\n|\n|---|\n\n\n## ○ (온라인) 신용·체크카드 및 모바일‧카드형 지역사랑상품권은 대상자(성인) 본인이, ‘본인 명의’로만 신청하고, 충전금을 받을수 있습니다.\n\n- 다만, 미성년 자녀(2008.1.1. 이후 출생자)는 주민등록 상 세대주 명 의로 신청할 수 있습니다.\n\n## ○ (오프라인) 신용·체크카드는 카드와 연계된 은행창구에서 신청이가능하며, ‘본인 명의’로 신청·수령만 가능합니다.\n\n- - 선불카드, 지류·카드형 지역사랑상품권은 읍면동 주민센터에서 신청할 수 있고, 신청자 개인 및 대리인 신청 및 수령이 가능합니다.\n\n- - 은행창구, 읍면동 주민센터에서 신청하는 경우 모두 미성년 자녀는 주민등록 상 세대주 명의로 신청 가능합니다.\n\n\n- ※ 본인 신청시 신분증(주민등록증, 운전면허증, 여권, 모바일신분증 등) 지참\n- ※ 대리인 신청시 대리인 신분증, 위임장, 본인-대리인 관계 증명서류 지참\n\n\n||6. 온라인으로 카드 신청을 할 수 없거나, 고령자·장애인 등<br><br>거동이 불편한 주민은 어떻게 신청해야 하나요?<br><br>|\n|---|\n|\n|---|\n\n\n### ○ 거동이 불편하여 주민센터를 방문할 수 없는 경우에는 해당 지방정부에 ‘찾아가는 신청’을 전화로 요청할 수 있습니다.\n\n- 단, 다른 가구원이 있는 경우에는 대리 신청이 가능하므로, 찾아가는 신청 요청이 제한될 수 있습니다.\n\n### ○ 전화를 받은 지방정부는 대상자 여부를 조회한 후, 대상자를 방문하여신청서를 접수한 후, 지급 준비가 완료되면 재방문하여 상품권/선불카드를 지급하게 됩니다.\n\n※ ‘찾아가는 신청’의 구체적 일정･절차 및 접수처는 지방정부별 자율적으로 안내 예정\n\n||7. 1차 신청 · 지급 기간에 피해지원금을 지급받은 경우, 2차 신청 · 지급 기간에 다시 신청할 수 있나요?|\n|---|\n|\n|---|\n\n\n### ○ 1차 신청· 지급 기간(´26. 4.27.~5. 8.)에 피해지원금을 지급받으신 경우,2차 기간(´26. 5.18.~7. 17.)에는 신청·지급이 불가합니다.\n\n||8. 기초수급자에 해당하지만, 1차 신청·지급 시기에 신청을 하지<br><br>못하였습니다. 이 경우 지원금을 받을 수 없나요?|\n|---|\n|\n|---|\n\n\n## ○ 기초생활수급자, 차상위계층·한부모가족에 해당하는 경우,1차 신청 · 지급 기간(´26. 4.27.~5. 8.)에 신청을 하지 못하였더라도,\n\n- 2차 신청 · 지급 기간(´26. 5.18.~7. 17.)에 신청하시면, 피해지원금을\n\n## 지급받으실 수 있습니다.\n\n※ (기초생활수급자) 55만원, (차상위· 한부모) 45만원 / 비수도권 및 인구감소지역 거주시 5만원 추가지급\n\n||9. 외국인도 고유가 피해지원금을 신청할 수 있나요?|\n|---|\n|\n|---|\n\n\n- ○ 고유가 피해지원금은 고유가·고물가로 인한 국민의 부담을 덜어 드리기 위한 것으로, 외국인은 원칙적으로 대상에서 제외됩니다.\n- ○ 다만, 내국인과 연관성이 큰 다음의 경우는 예외적으로 지급대상에 포함됩니다.\n\n- ① 외국인이 내국인이 1인 이상 포함된 주민등록표에 등재되어 있 고, 건강보험 가입자, 피부양자, 의료급여 수급자인 경우\n- ② 외국인만으로 구성된 가구라도 영주권자(F-5), 결혼이민자(F-6) 또는 난민인정자(F-2-4)가 ‘건강보험 가입자, 피부양자, 의료급여 수급자’인 경우\n\n\n||10. 해외에 체류 중인 국민입니다. 고유가 피해지원금을 지급받을<br><br>수 있나요?|\n|---|\n|\n|---|\n\n\n- ○ 국외에 체류 중이던 국민이 3월 30일(월) 이후부터 7월 17일(금) 사 이에 귀국하였다면, 이의신청 기한(7.17.) 내에 이의신청을 거쳐 피 해지원금을 지급받을 수 있습니다.\n\n\n||11. 지급기준일(´26. 3.30.) 이후에 기초수급자 자격 책정이 이루어진<br><br>경우, 기초수급자에 해당하는 금액을 지급받을 수 있나요?|\n|---|\n|\n|---|\n\n\n- ○ 지급기준일(´26.3.30.)에는 기초수급자가 아니었으나, 이후에 자격 책정이 이루어진 경우라면, 이의신청 기한(7.17.) 내에 이의신청을 거쳐 그에 해당하는 지원금을 지급받으실 수 있습니다.\n\n||12. 신용·체크카드로 고유가 피해지원금을 받으려면 어떻게 해야<br><br>하나요?|\n|---|\n|\n|---|\n\n\n- ○ 고유가 피해지원금은 온‧오프라인 신청을 통해 신용･체크카드, 선불카드 및 지역사랑상품권(지류･모바일･카드) 중 선택하여 수령할 수 있습니다.\n- ○ 신용･체크카드로 지급받고 싶은 국민들께서는,\n\n\n- - 신청기간 내에 충전을 희망하는 카드의 카드사 홈페이지, 앱, 콜센터･ ARS 및 카카오뱅크･토스･카카오페이간편결제･네이버페이간편결제 앱을 통해 온라인으로 신청하실 수 있습니다.\n- - 온라인으로 신청하기 어려운 경우 신청기간 내 각 카드사와 연 계된 은행영업점*을 방문하여 신청하실 수 있습니다.\n\n* (예시) KB국민카드-KB국민은행, NH농협카드-농협은행 및 농축협\n\n- - 충전금은 신청일로부터 신청 다음날 해당 카드에 지급되며, 피해 지원금이 지급되면 문자 등을 통해 알려드릴 예정입니다.\n\n\n||13. 선불카드 또는 지역사랑상품권으로 고유가 피해지원금을<br><br>받으려면 어떻게 해야 하나요?|\n|---|\n|\n|---|\n\n\n- ○ 모바일･카드형 지역사랑상품권으로 받길 희망하는 국민들께서는,\n\n- 신청기간 내에 지방정부별 지역사랑상품권 앱에 접속하여 고유가 피해지원금을 신청하실 수 있습니다.\n\n※ 단, 온라인 신청이 불가한 일부 지역사랑상품권은 읍면동 주민센터 통해 오프라인 신청이 필요하므로 해당 지방정부 홈페이지 또는 전화 문의 등을 통해 확인하시기 바랍니다.\n\n- ○ 선불카드 또는 지류형 지역사랑상품권을 받길 희망하시는 경우,\n\n\n- - 신청기간 내 주소지 관할 읍면동 주민센터를 방문하여 피해지원금을 신청하실 수 있습니다.\n- - 가급적 신청하시는 현장에서 선불카드 또는 지역사랑상품권을 받 으실 수 있도록 계획하고 있으나, 부득이한 경우(수량 부족 등) 받 으실 장소와 일시를 문자 등으로 안내해 드릴 예정입니다.\n\n\n||14. 고유가 피해지원금 사용 지역 제한이 있나요?|\n|---|\n|\n|---|\n\n\n- ○ 고유가 피해지원금을 지급받은 지역이 특·광역시 지역(세종･제주 포함)이라면 해당 특·광역시 내에서 사용이 가능하고,\n\n- 지급받은 지역이 도 지역이라면, 도 소재 시·군 지역 내에서\n\n사용이 가능합니다.\n\n※ (예시) 주소지가 서울특별시 중구인 경우 → 서울특별시 내에서 사용가능 주소지가 충청북도 청주시인 경우 → 청주시 내에서 사용가능\n\n||15. 고유가 피해지원금은 언제까지 사용 가능한가요?|\n|---|\n|\n|---|\n\n\n- ○ 고유가 피해지원금은 사용 기한이 제한되어 있습니다.\n- ○ 신용·체크카드에 충전된 피해지원금, 선불카드, 지역사랑상품권은 8.31.(월)까지 사용할 수 있습니다.\n\n\n- 8.31.(월)까지 사용하지 못한 피해지원금은 소멸됩니다.\n\n"
    },
    {
      "document_id": "156754246",
      "title": "종량제봉투, 재생원료 사용 확대로 공급망 위기의 파고를 넘는다",
      "department": "기후에너지환경부",
      "approve_date": "04/13/2026 13:00:00",
      "readhim": {
        "overall": 0.6460508410656766,
        "nid": 0.8904593639575971,
        "teds": 0.7906976744186046,
        "mhs": 0.2569954848208281,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.30481448929526106,
        "nid": 0.7899268887083672,
        "teds": 0.0728682170542636,
        "mhs": 0.05164836212315238,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 종량제봉투, 재생원료 사용 확대로 공급망 위기의 파고를 넘는다\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 기후에너지환경부\n- 게시 시각: 04/13/2026 13:00:00\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754246&call_from=openData\n- HWPX 첨부: 종량제봉투  재생원료 사용 확대로 공급망 위기의 파고를 넘는다(보도자료)(생활폐기물 4.13).hwpx\n- PDF 첨부: 종량제봉투  재생원료 사용 확대로 공급망 위기의 파고를 넘는다(보도자료)(생활폐기물 4.13).pdf\n\n## 본문\n\n## 종량제봉투, 재생원료 사용 확대로 공급망 위기의 파고를 넘는다\n- 기후부, 재생원료 생산 및 종량제봉투 제작 업계와 재생원료 사용 확대 협약 - - 품질 검증부터 기술· 생산 정보 공유까지 다각적인 상생협력 체계 구축\n\n기후에너지환경부(장관 김성환)는 4월 13일 오후 한국농수산재활용사업 공제조합 대회의실(서울시 영등포구 소재) 에서 재생원료 생산 및 종량제봉투 제작 업계를 비롯한 관련 기관과 ‘재생원료 사용 종량제봉투 제작 확대를 위한 업무협약’을 체결한다고 밝혔다.\n\n이날 협약에 참여하는 업계 및 기관은 한국프라스틱공업협동조합연합회, 한국농수산재활용사업공제조합, 한국환경공단, 인테크, 동성이다.\n\n이번 협약은 최근 중동전쟁의 장기화로 인해 종량제봉투 원료인 폴리에틸렌의 공급이 원활하지 않은 상황에서, 폐자원으로 만드는 대체 원료인 재생원료가 위기 극복의 타개책으로 부상함에 따라 마련되었다.\n\n협약은 정부와 재생원료 생산업계, 종량제봉투 제작 업계가 고품질 재생 원료를 사용한 종량제봉투의 생산과 보급을 확대하는 데 뜻을 모으고, 나아가 유관 생산 정보· 기술 등을 공유하며 종량제봉투 산업생태계 전반의 상생협력을 강화하는 내용을 담았다.\n\n우선 기후에너지환경부는 재생원료 종량제봉투 보급 활성화를 위해 종량제봉 투 생산설비 교체 비용 지원 예산을 올해 ‘전쟁추경’에 138 억 원을 반영하는 등 행정적·재정적 지원에 역량을 집중한다.\n\n한국농수산재활용사업공제조합은 균일한 품질의 재생원료가 안정적으로 공급될 수 있도록 재활용 체계 구축, 시설 개선 지원 등에 힘쓴다.\n\n한국프라스틱공업협동조합연합회는 봉투에 재생원료 투입을 확대하고, 나아가 한국농수산재활용공제조합과 함께 재생원료의 품질에 대한 검증을 실시한다.\n\n인테크, 동성 등 재생원료 사용 우수업체도 상생협력 차원에서 협약에 참여해 종량제봉투 제작업계에 기술 자문· 지원을 제공하며, 한국 환경공단은 재생원료 생산정보를 종량제봉투 제작업체에 제공하는 등 수요와 공급이 원활히 연계되도록 관리체계를 구축 및 운영할 계획이다.\n\n기후에너지환경부는 이번 협약을 제품 제조업계와 재활용업계 간 원활한 연계를 위한 협력 체계를 구축하는 모범사례로 삼아, 타 품목 등에 재생원료 사용을 지속적으로 확대하는 방안을 검토할 예정이다.\n\n김성환 기후에너지환경부 장관은 “국내 폐자원으로 만든 재생원료는 우리 자원 공급망의 든든한 기초”라며 “업계와 협력해 종량제봉투부터 재생원료 사용을 늘려가며, 이를 통해 중동전쟁 같은 외부 충격에도 흔들리지 않는 ‘순환경제’의 모범사례로 만들겠다”라고 밝혔다.\n\n## 붙임 협약서 전문. 끝.\n\n## 담당 부서\n\n- 담당 부서: 기후에너지환경부 / 책임자 과장 황남경 / (044-201-7421)\n- 생활폐기물과: 담당자 / 사무관 배영균\n\n재생원료 사용 종량제봉투 제작 확대를 위한 업무협약서\n\n기후에너지환경부, 한국프라스틱공업협동조합연합회, 한국농수산재활용 사업공제조합, 한국환경공단, 인테크· ㈜동성(이하 ‘협약 당사자’라한다) 은 고품질 재생원료 생산 및 종량제봉투 내 재생원료 사용을 확대함으로써 순환경제로의 전환에 기여하기 위해 다음과 같이 업무협약을 체결한다.\n\n1. 협약 당사자는 재생원료를 사용한 지속가능한 종량제봉투 생산체계를 확대 하기 위해 다음과 같이 유기적으로 협력한다.\n\n가. 기후에너지환경부는 재생원료 사용 종량제봉투의 제작· 이용을 확대 하기 위해 행정적· 제도적 지원이 이루어질 수 있도록 적극 노력한다.\n\n나. 한국프라스틱공업협동조합연합회는 재생원료 사용 종량제봉투의 제작· 공급을 확대하기 위해 적극 노력하며, 재생원료의 수요 관리 체계를 구축·운영한다.\n\n다. 한국농수산재활용사업공제조합은 균질한 품질의 재생원료가 원활히 공급될 수 있도록 안정적인 재활용 체계 구축 및 재활용 시설개선 등에 적극 노력하며, 재생원료의 공급 관리 체계를 구축· 운영한다.\n\n라. 한국환경공단은 재생원료 생산 정보 등을 종량제봉투 제작업체에 제공하는 등 효율적인 재생원료 수요-공급의 연계 체계를 적극 구축한다.\n\n마. 인테크·㈜동성은 재생원료 사용 종량제봉투 제작 우수업체로서 종량제봉투 제작업체에 기술 자문· 지원을 제공하는 등 상생형 산업 생태계 구축을 위해 적극 협력한다.\n\n바. 한국프라스틱공업협동조합연합회와 한국농수산재활용사업공제조합은 공급되는 재생원료의 품질에 대한 검증을 실시하고 구체적인 기준 등에 대해서는 상호 협의하여 정한다.\n\n1. 본 협약은 협약 당사자가 서명한 날로부터 효력이 발생하며, 어느 일방이 서면을 통해 해지 의사를 표시하지 않는 한 효력이 지속된다.\n\n1. 협약 사항의 변경이 필요한 경우, 상호 협의에 따라 조정· 결정 절차를 거쳐 협약 사항을 변경할 수 있다.\n\n1. 본 협약은 당사자의 상호 업무에 관한 협력 사항으로 법적 구속력을 가지지 않으며, 협약 당사자는 신의성실 원칙에 따라 협약 내용의 이행을 위해 최선의 노력을 다한다.\n\n2026년 4월 13일\n\n| 기후에너지환경부 | 한국프라스틱공업협동조합연합회 | | | | |\n| --- | --- | --- | --- | --- | --- |\n| | 장관 | | | 회장 | |\n| 한국농수산재활용사업공제조합 | 한국환경공단 | | | | |\n| | 이사장 | | | 이사장 | |\n| 인테크 | ㈜동성 | | | | |\n| | 대표 | | | 대표이사 | |\n\n## 첨부파일\n\n- 종량제봉투  재생원료 사용 확대로 공급망 위기의 파고를 넘는다(보도자료)(생활폐기물 4.13).hwpx\n- 종량제봉투  재생원료 사용 확대로 공급망 위기의 파고를 넘는다(보도자료)(생활폐기물 4.13).pdf\n",
      "readhim_markdown": "# 종량제봉투, 재생원료 사용 확대로 공급망 위기의 파고를 넘는다\n\n기후에너지환경부 보도자료 /\n보도시점: 2026. 4. 13.(월) 13:00 / 배포 2026. 4. 13.(월)\n\n> - 기후부, 재생원료 생산 및 종량제봉투 제작 업계와 재생원료 사용 확대 협약\n> - 품질 검증부터 기술·생산 정보 공유까지 다각적인 상생협력 체계 구축\n---\n기후에너지환경부(장관 김성환)는 4월 13일 오후 한국농수산재활용사업공제조합 대회의실(서울시 영등포구 소재)에서 재생원료 생산 및 종량제봉투 제작 업계를 비롯한 관련 기관과 ‘재생원료 사용 종량제봉투 제작 확대를 위한 업무협약’을 체결한다고 밝혔다.\n\n이날 협약에 참여하는 업계 및 기관은 한국프라스틱공업협동조합연합회, 한국농수산재활용사업공제조합, 한국환경공단, 인테크, 동성이다.\n\n이번 협약은 최근 중동전쟁의 장기화로 인해 종량제봉투 원료인 폴리에틸렌의 공급이 원활하지 않은 상황에서, 폐자원으로 만드는 대체 원료인 재생원료가 위기 극복의 타개책으로 부상함에 따라 마련되었다.\n\n협약은 정부와 재생원료 생산업계, 종량제봉투 제작 업계가 고품질 재생원료를 사용한 종량제봉투의 생산과 보급을 확대하는 데 뜻을 모으고, 나아가 유관 생산 정보·기술 등을 공유하며 종량제봉투 산업생태계 전반의 상생협력을 강화하는 내용을 담았다.\n\n우선 기후에너지환경부는 재생원료 종량제봉투 보급 활성화를 위해 종량제봉투 생산설비 교체 비용 지원 예산을 올해 ‘전쟁추경’에 138억 원을 반영하는 등 행정적·재정적 지원에 역량을 집중한다.\n\n한국농수산재활용사업공제조합은 균일한 품질의 재생원료가 안정적으로 공급될 수 있도록 재활용 체계 구축, 시설 개선 지원 등에 힘쓴다.\n\n한국프라스틱공업협동조합연합회는 봉투에 재생원료 투입을 확대하고, 나아가 한국농수산재활용공제조합과 함께 재생원료의 품질에 대한 검증을 실시한다.\n\n인테크, 동성 등 재생원료 사용 우수업체도 상생협력 차원에서 협약에 참여해 종량제봉투 제작업계에 기술 자문·지원을 제공하며, 한국환경공단은 재생원료 생산정보를 종량제봉투 제작업체에 제공하는 등 수요와 공급이 원활히 연계되도록 관리체계를 구축 및 운영할 계획이다.\n\n기후에너지환경부는 이번 협약을 제품 제조업계와 재활용업계 간 원활한 연계를 위한 협력 체계를 구축하는 모범사례로 삼아, 타 품목 등에 재생원료 사용을 지속적으로 확대하는 방안을 검토할 예정이다.\n\n김성환 기후에너지환경부장관은 “국내 폐자원으로 만든 재생원료는 우리 자원 공급망의 든든한 기초”라며 “업계와 협력해 종량제봉투부터 재생원료 사용을 늘려가며, 이를 통해 중동전쟁 같은 외부 충격에도 흔들리지 않는 ‘순환경제’의 모범사례로 만들겠다”라고 밝혔다.\n\n### 붙임 협약서 전문. 끝.\n\n---\n\n### 담당부서\n\n- 기후에너지환경부 생활폐기물과 책임자: 과장 황남경 (044-201-7421)\n- 기후에너지환경부 생활폐기물과 담당자: 사무관 배영균 (044-201-7425)\n---\n\n## 붙임 협약서 전문. 끝.\n\n붙임\n협약서 전문\n재생원료 사용 종량제봉투 제작 확대를 위한 업무협약서\n기후에너지환경부, 한국프라스틱공업협동조합연합회, 한국농수산재활용사업공제조합, 한국환경공단, 인테크·㈜동성(이하 ‘협약 당사자’라 한다)은 고품질 재생원료 생산 및 종량제봉투 내 재생원료 사용을 확대함으로써 순환경제로의 전환에 기여하기 위해 다음과 같이 업무협약을 체결한다.\n\n#### 1. 협약 당사자는 재생원료를 사용한 지속가능한 종량제봉투 생산체계를 확대하기 위해 다음과 같이 유기적으로 협력한다.\n\n가. 기후에너지환경부는 재생원료 사용 종량제봉투의 제작·이용을 확대하기 위해 행정적·제도적 지원이 이루어질 수 있도록 적극 노력한다.\n나. 한국프라스틱공업협동조합연합회는 재생원료 사용 종량제봉투의 제작·공급을 확대하기 위해 적극 노력하며, 재생원료의 수요 관리 체계를 구축·운영한다.\n다. 한국농수산재활용사업공제조합은 균질한 품질의 재생원료가 원활히 공급될 수 있도록 안정적인 재활용 체계 구축 및 재활용 시설개선 등에 적극 노력하며, 재생원료의 공급 관리 체계를 구축·운영한다.\n라. 한국환경공단은 재생원료 생산 정보 등을 종량제봉투 제작업체에 제공하는 등 효율적인 재생원료 수요-공급의 연계 체계를 적극 구축한다.\n마. 인테크·㈜동성은 재생원료 사용 종량제봉투 제작 우수업체로서 종량제봉투 제작업체에 기술 자문·지원을 제공하는 등 상생형 산업 생태계 구축을 위해 적극 협력한다.\n바. 한국프라스틱공업협동조합연합회와 한국농수산재활용사업공제조합은 공급되는 재생원료의 품질에 대한 검증을 실시하고 구체적인 기준 등에 대해서는 상호 협의하여 정한다.\n\n#### 1. 본 협약은 협약 당사자가 서명한 날로부터 효력이 발생하며, 어느 일방이 서면을 통해 해지 의사를 표시하지 않는 한 효력이 지속된다.\n\n#### 1. 협약 사항의 변경이 필요한 경우, 상호 협의에 따라 조정·결정 절차를 거쳐 협약 사항을 변경할 수 있다.\n\n1. 본 협약은 당사자의 상호 업무에 관한 협력 사항으로 법적 구속력을 가지지 않으며, 협약 당사자는 신의성실 원칙에 따라 협약 내용의 이행을 위해 최선의 노력을 다한다.\n\n2026년 4월 13일\n\n| 기후에너지환경부 | | | 한국프라스틱공업협동조합연합회 | |\n| --- | --- | --- | --- | --- |\n| | 장관 | | | 회장 |\n| 한국농수산재활용사업공제조합 | | | 한국환경공단 | |\n| | 이사장 | | | 이사장 |\n| 인테크 | | | ㈜동성 | |\n| | 대표 | | | 대표이사 |\n",
      "opendataloader_markdown": "|보도자료|\n|---|\n\n\n보도시점 2026. 4. 13.(월) 13:00 배포 2026. 4. 13.(월)\n\n|종량제봉투, 재생원료 사용 확대로 공급망 위기의 파고를 넘는다<br><br>- 기후부, 재생원료 생산 및 종량제봉투 제작 업계와 재생원료 사용 확대 협약<br><br>-<br><br>- 품질 검증부터 기술·생산 정보 공유까지 다각적인 상생협력 체계 구축<br>|\n|---|\n\n\n기후에너지환경부(장관 김성환)는 4월 13일 오후 한국농수산재활용사업 공제조합 대회의실(서울시 영등포구 소재)에서 재생원료 생산 및 종량제봉투 제작 업계를 비롯한 관련 기관과 ‘재생원료 사용 종량제봉투 제작 확대를 위한 업무협약’을 체결한다고 밝혔다.\n\n이날 협약에 참여하는 업계 및 기관은 한국프라스틱공업협동조합연합회, 한국농수산재활용사업공제조합, 한국환경공단, 인테크, 동성이다.\n\n이번 협약은 최근 중동전쟁의 장기화로 인해 종량제봉투 원료인 폴리에 틸렌의 공급이 원활하지 않은 상황에서, 폐자원으로 만드는 대체 원료인 재생원료가 위기 극복의 타개책으로 부상함에 따라 마련되었다.\n\n협약은 정부와 재생원료 생산업계, 종량제봉투 제작 업계가 고품질 재생 원료를 사용한 종량제봉투의 생산과 보급을 확대하는 데 뜻을 모으고, 나아가 유관 생산 정보·기술 등을 공유하며 종량제봉투 산업생태계 전반의 상생협력을 강화하는 내용을 담았다.\n\n우선 기후에너지환경부는 재생원료 종량제봉투 보급 활성화를 위해 종량제 봉투 생산설비 교체 비용 지원 예산을 올해 ‘전쟁추경’에 138억 원을 반영하는 등 행정적·재정적 지원에 역량을 집중한다.\n\n한국농수산재활용사업공제조합은 균일한 품질의 재생원료가 안정적으로 공급될 수 있도록 재활용 체계 구축, 시설 개선 지원 등에 힘쓴다.\n\n한국프라스틱공업협동조합연합회는 봉투에 재생원료 투입을 확대하고, 나아가 한국농수산재활용공제조합과 함께 재생원료의 품질에 대한 검증을 실시한다.\n\n인테크, 동성 등 재생원료 사용 우수업체도 상생협력 차원에서 협약에 참여해 종량제봉투 제작업계에 기술 자문·지원을 제공하며, 한국환경공단은 재생원료 생산정보를 종량제봉투 제작업체에 제공하는 등 수요와 공급이 원활히 연계되도록 관리체계를 구축 및 운영할 계획이다.\n\n기후에너지환경부는 이번 협약을 제품 제조업계와 재활용업계 간 원활한 연계를 위한 협력 체계를 구축하는 모범사례로 삼아, 타 품목 등에 재생원료 사용을 지속적으로 확대하는 방안을 검토할 예정이다.\n\n김성환 기후에너지환경부 장관은 “국내 폐자원으로 만든 재생원료는 우리 자원 공급망의 든든한 기초”라며 “업계와 협력해 종량제봉투부터 재생원료 사용을 늘려가며, 이를 통해 중동전쟁 같은 외부 충격에도 흔들리지 않는 ‘순환경제’의 모범사례로 만들겠다”라고 밝혔다.\n\n붙임 협약서 전문. 끝.\n\n|담당 부서|기후에너지환경부 생활폐기물과|책임자|과 장 황남경 (044-201-7421)|\n|---|---|---|---|\n| | |담당자|사무관 배영균 (044-201-7425)|\n\n\n|붙임|\n|---|\n\n\n|협약서 전문|\n|---|\n\n\n## 재생원료 사용 종량제봉투 제작 확대를 위한 업무협약서\n\n기후에너지환경부, 한국프라스틱공업협동조합연합회, 한국농수산재활용 사업공제조합, 한국환경공단, 인테크·㈜동성(이하 ‘협약 당사자’라 한 다)은 고품질 재생원료 생산 및 종량제봉투 내 재생원료 사용을 확대함으 로써 순환경제로의 전환에 기여하기 위해 다음과 같이 업무협약을 체 결한다.\n\n1. 협약 당사자는 재생원료를 사용한 지속가능한 종량제봉투 생산체계를 확대 하기 위해 다음과 같이 유기적으로 협력한다.\n\n- 가. 기후에너지환경부는 재생원료 사용 종량제봉투의 제작·이용을 확대 하기 위해 행정적·제도적 지원이 이루어질 수 있도록 적극 노력한다.\n- 나. 한국프라스틱공업협동조합연합회는 재생원료 사용 종량제봉투의 제작·공급을 확대하기 위해 적극 노력하며, 재생원료의 수요 관 리 체계를 구축·운영한다.\n- 다. 한국농수산재활용사업공제조합은 균질한 품질의 재생원료가 원활히 공급될 수 있도록 안정적인 재활용 체계 구축 및 재활용 시설개선 등에 적극 노력하며, 재생원료의 공급 관리 체계를 구축·운영한다.\n- 라. 한국환경공단은 재생원료 생산 정보 등을 종량제봉투 제작업체에 제공하는 등 효율적인 재생원료 수요-공급의 연계 체계를 적극 구축한다.\n- 마. 인테크·㈜동성은 재생원료 사용 종량제봉투 제작 우수업체로서 종량제봉투 제작업체에 기술 자문·지원을 제공하는 등 상생형 산 업 생태계 구축을 위해 적극 협력한다.\n\n\n### 바. 한국프라스틱공업협동조합연합회와 한국농수산재활용사업공제조합은공급되는 재생원료의 품질에 대한 검증을 실시하고 구체적인 기준등에 대해서는 상호 협의하여 정한다.\n\n### 1. 본 협약은 협약 당사자가 서명한 날로부터 효력이 발생하며, 어느 일방이 서면을 통해 해지 의사를 표시하지 않는 한 효력이 지속된다.\n\n### 1. 협약 사항의 변경이 필요한 경우, 상호 협의에 따라 조정·결정 절차를 거쳐 협약 사항을 변경할 수 있다.\n\n### 1. 본 협약은 당사자의 상호 업무에 관한 협력 사항으로 법적 구속력을 가지지 않으며, 협약 당사자는 신의성실 원칙에 따라 협약 내용의 이행을 위해 최선의 노력을 다한다.\n\n2026년 4월 13일\n\n기후에너지환경부 한국프라스틱공업협동조합연합회\n\n장관 회장\n\n### 한국농수산재활용사업공제조합 한국환경공단\n\n이사장 이사장\n\n### 인테크 ㈜동성\n\n대표 대표이사\n\n"
    },
    {
      "document_id": "156754187",
      "title": "인공지능(AI) 전환 과정에서 일자리와 공존을 위해 지혜를 모으다.",
      "department": "고용노동부",
      "approve_date": "04/13/2026 10:21:44",
      "readhim": {
        "overall": 0.6306467284688905,
        "nid": 0.9341101694915256,
        "teds": 0.7928743961352657,
        "mhs": 0.16495561977987994,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.36946043810055595,
        "nid": 0.864554539655539,
        "teds": 0.08904136280131392,
        "mhs": 0.15478541184481487,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 인공지능(AI) 전환 과정에서 일자리와 공존을 위해 지혜를 모으다.\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 고용노동부\n- 게시 시각: 04/13/2026 10:21:44\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754187&call_from=openData\n- PDF 첨부: 260413_보도자료_AI 전환과 노동의 미래_최종본.pdf\n- HWPX 첨부: 260413_보도자료_AI 전환과 노동의 미래_최종본.hwpx\n\n## 본문\n\n| 고용노동부 | 보도자료 | |\n| --- | --- | --- |\n\n고용노동부(장관 김영훈) 는 기후노동위 더불어민주당과 공동으로 4월 13일(월) 10시 국회 의원회관에서 ｢AI 전환과 노동의 미래｣ 토론회를 개최했다.\n\n생성형 AI의 발전이 신규 사무직 종사자들의 일자리에 영향을 미치는 와중 휴머노이드 등 피지컬 AI 까지 등장 함에 따라 제조업· 물류업 종사자 등 광범위한 분야로 일자리에 대한 우려가 확산되고 있다. 이번 토론회는 산업 현장의 AI 도입 상황 및 전망을 살펴보고 AI 와 일자리가 서로 공존할 수 있는 방안을 논의 하기 위해 마련하였다.\n\n이날 토론회는 ‘ 피지컬 AI 시대 산업인력 전략’ (카이스트 장영재 교수) 과 ‘ 피지컬 AI의 현재와 미래’ (디든로보틱스 김준하 대표)에 대한 발제로 시작되었다.\n\n먼저 첫 번째 발제를 맡은 장영재 교수는 AI 로 사라질 직업을 걱정하기보다, AI 로 창출되는 일자리와 기회에 집중할 필요가 있다고 강조하였다. 특히 피지컬 AI 도입 초기 창업 지원 및 인력양성을 위한 정부의 역할이 필요 하다고 설명하였다. 아울러, 우리나라의 제조업 역량을 활용해 피지컬 AI 생태계를 구축하고, AI 기반의 ‘제조 소프트웨어 기반 공장 구축 운영 노하우’ 수출을 새로운 먹거리로 삼을 필요가 있다고하였다.\n\n두 번째 발제를 진행한 김준하 대표는 피지컬 AI 도입 상황과 일자리 전망을 설명했다. 현재 피지컬 AI 가 상용화 단계에 도달한 것은 맞으나, 도입 비용 및 기술적 한계로 휴머노이드가 단시일 내에 도입되기는 어렵다 고 말했다. 특히, 생산가능 인구 감소로 인력난이 있을 분야, 위험한 작업 등에 로봇 투입이 도움이될 수 있으며, 로봇과 관련된 일자리가 새로이 창출되는 등 피지컬 AI가 일자리에 부정적으로만 작용하지는 않을 것으로 설명했다.\n\n이어 김주영 의원(더불어민주당)이 직접 좌장을 맡은 토론회에서 노사 및 전문가 등 토론자들은 AI 전환을 피할 수 없는 상황에서 직무전환 지원, AI 직무 역량 강화 및 사회안전망 강화 등 정부의 역할에 대하여 공통적으로 제언했다.\n\n김영훈 고용노동부 장관은 “최근 중동지역 군사적 충돌은 AI 가 산업적 도구를 넘어 국가의 전략 및 안보 자산 이라는 것을 시사하고 있다.”라면서 “세계 주요국들이 앞다투어 AI 를 발전시키는 상황에서 AI 도입과 발전을 주저할 수는 없다. ”라고 밝혔다. 그럼에도, “ ‘사람을 위한 AI, 모두의 AI ’라는 원칙 ”을 강조 하면서 “AI는 인간을 대체하지 않지만, AI를 사용하는 사람이 그렇지 않은 사람을 대체할 것이다. ”라는 카림 카리니 하버드대 교수의 말을 인용해 “ 국민 들이 AI 기술을 가진 인력으로 성장하고, 고용안전망을 확충하여 직무 전환 과정이 일자리 양극화로 연결되지 않도록 정부도 적극 지원 하겠다. ”라고 강조했다.\n\n## 담당 부서\n\n- 담당 부서: 고용노동부 / 책임자 과장 이상임 / (044-202-7210)\n- 노동시장정책관 고용정책총괄과: 담당자 / 서기관 이상혁\n\n## 붙임1 ‘ AI 전환과 노동의 미래’토론회 개요\n\n□ 일시: ’ 26. 4. 13. (월) 10:00 ∼ 12:00\n\n□ 장소: 국회 의원회관 제 1 세미나실\n\n□ 주최: 고용노동부ㆍ더불어민주당 기후에너지환경노동위원회ㆍ 국회 내일의 공공과 에너지· 노동을 생각하는 의원모임 공동주최\n\n□ 후원: 과학기술정보통신부, 산업통상부\n\n□ 참석자: [좌장] 김주영 의원(민주당)\n\nㅇ [발제] 장영재 교수(카이스트), 김준하 대표(디든로보틱스)\n\nㅇ [토론] 박수민 한국노동연구원 박사 우상범 한국노총 중앙연구원 박사 오삼일 한국은행 조사국 고용분석팀장 김동희 경총 근로기준정책팀장 김형민 ㈜좋은일자리 고용지원사업부장\n\nㅇ [정부] 김형광 고용노동부 노동시장정책관 최우석 과학기술정보통신부 인공지능안전신뢰지원과장 권순목 산업통상부 산업인공지능정책과장\n\n□ 행사 주요 순서\n\n| 시 간 | 내 용 | 비고 | |\n| --- | --- | --- | --- |\n| 10:00~10:20 | `20 | 개회 및 인사말, 축사 | 장관 더불어민주당 의원 |\n| 10:20~10:30 | `10 | 기념촬영 및 장내정리 | |\n| 10:30~11:00 | `15 | 【 발제 1 】 피지컬 AI 시대 산업 인력 전략 | 장영재 교수 |\n| `15 | 【 발제 2 】 피지컬 AI 의 현재와 미래 | 김준하 대표 | |\n| 11:00~11:45 | `45 | 토론 | |\n| 11:45~12:00 | ‘ 15 | 정부발언 | 고용노동부 과학기술정보통신부 산업통상부 |\n| 11:50~12:00 | `10 | 마무리 | |\n\n## 붙임2 고용노동부 장관 축사 * 현장발언은 이와 다를 수 있음\n\n안녕하십니까.\n\n고용노동부 장관 김영훈입니다.\n\nAI가 우리 사회, 우리 삶에 가져오는 변화를\n\n직접 체감하고 있는이 시점에\n\n토론회를 같이 준비해주신\n\n기후노동위 더불어민주당 그리고 국회 내일의 공공과 에너지·노동을 생각하는 의원모임\n\n소속 의원님들 모두에 감사말씀을 드립니다.\n\n아울러 발제를 맡아주신 장영재 카이스트 교수님,\n\n김준하 디든로보틱스 대표님은 물론,\n\n열띤 토론을 해주실 참석자 여러분들에게도\n\n깊이 감사드립니다.\n\n최근 중동 지역의 군사적 충돌로 인해 정세 불안이 심화되고 있습니다.\n\n이런 충돌은 글로벌 공급망의 불안정성을 넘어,\n\n우리가 이번 사태에서 직시해야할\n\n새로운 모습을 보여주고 있습니다.\n\n미국 등 AI 선진국들은 본격적으로\n\n전황을 AI로 분석하여 의사 결정에 참고하고 있으며,\n\n중동의 AI 기업과 데이터센터와 같은\n\n첨단 기술 인프라가\n\n주요 공격대상이되고 있는 상황입니다.\n\n이는 AI가 단순한 산업적 도구를 넘어,\n\n국가의 핵심 전략 자산이자 안보의 최전선이 되었음을\n\n전 세계에 강력하게 시사하고 있습니다.\n\n이러한 AI 경쟁의 파고는\n\n국경 너머의 일만이 아닙니다.\n\nAI 기술의 급격한 발전은\n\n우리 산업의 변화를 가져오는 동시에, 노동시장에도 구조적 변화를 일으키고 있습니다.\n\n많은 국민들께서 생성형 AI를 넘어 자율주행 자동차, 휴머노이드 로봇과 같은\n\n피지컬 AI의 도입을 지켜보며\n\n일자리의 미래를 걱정하고 계십니다.\n\n특히, 사회에 첫발을 내디뎌야할\n\n우리 청년들의 우려는 실로 지대합니다.\n\n내가 애써 준비한 직무가\n\n당장 AI로 대체되어\n\n일할 기회조차 갖지 못하는 것이 아닐지,\n\n기술의 발전 속도에 잘 적응할 수 있을지,\n\n청년들이 현장에서 느끼실\n\n막막함과 불안감을\n\n정부도 매우 무겁고 엄중하게 받아들이고 있습니다.\n\n그러나, AI 전환은 선택의 문제가 아닙니다.\n\n세계 주요국들이 앞다투어\n\nAI를 발전시키는 상황에서\n\nAI 도입과 발전을 주저할 순 없습니다.\n\n이러한 상황에서 우리가 나아갈 방향은 명확합니다.\n\nAI의 혜택이 모두에게 돌아가고, AI로 발생하는 비용은 함께 분담할 수 있도록\n\n'사람을 위한 AI, 모두의 AI'를 위한\n\n패러다임을 구축해야 합니다.\n\n카림 카리니 하버드대 교수의\n\n“AI는 인간을 대체하지 않지만,\n\nAI를 사용하는 사람이 그렇지 않은\n\n사람을 대체할 것이다.”라는 말처럼\n\n국민들이 AI 기술을 가진 인력으로 성장하여\n\nAI와 인간이 협력·공존하며\n\n지속가능한 성장을 이끌어낼 수 있도록\n\n정부도 적극 지원하겠습니다.\n\n이를 위해 고용노동부는\n\n국민 누구나 AI와 함께 일하는 인력이될 수 있도록\n\n전폭적인 지원과 정책적 역량을 집중하고 있습니다.\n\n우선, 지난 12월 발표한 AI 인재육성 방안에 따라\n\n청년들이 AI 시대의\n\n핵심 인재로 도약할 수 있도록\n\n'K-디지털 트레이닝' 등 첨단 산업 분야 직업훈련을\n\n대폭 확대하고 그 질을 고도화하고 있습니다.\n\n나아가, 기술 격차가 일자리 양극화로 연결되지 않도록\n\n취약계층을 보듬는 튼튼한 고용안전망을\n\n지속적으로 확충해 나갈 것입니다.\n\n그 첫걸음으로 고용보험 기준을\n\n근로시간에서 소득기반으로 개편하고 있고\n\nAI가 노동현장에 가져올 수 있는\n\n알고리즘 편향 등 부작용을 방지하기 위한\n\n‘노동분야AI윤리가이드라인’도 마련할 예정입니다.\n\n정부는 이러한 내용들을 포함하여\n\n‘산업전환 고용안정 기본계획’을 마련 중에 있습니다.\n\nAI 대전환 과정에서\n\n더 많은 일자리를 유지·창출하기 위한 대책들이\n\n기본계획에 담길 수 있도록\n\n다양한 이해관계자들의 의견을 경청할 예정입니다.\n\n그러한 점에서,\n\n오늘 국회에서 열리는이 토론회의 의미는\n\n참으로 각별합니다.\n\n이 자리에 함께하신 여러 의원님과\n\n각계 전문가 여러분의 혜안이 모여\n\n우리 국민과 청년들의 불안을\n\n희망으로 바꿀 수 있는\n\n깊이 있는 논의가 이루어지기를 진심으로 기대합니다.\n\n고용노동부 역시 오늘 제시된\n\n소중한 고견들을 정책에 적극 반영하여\n\n국민 모두가 AI 시대에 안심하고 든든한 일자리를 영위할 수 있도록\n\n최선을 다하겠습니다.\n\n경청해 주셔서 감사합니다.\n\n## 첨부파일\n\n- 260413_보도자료_AI 전환과 노동의 미래_최종본.pdf\n- 260413_보도자료_AI 전환과 노동의 미래_최종본.hwpx\n",
      "readhim_markdown": "# 인공지능(AI) 전환 과정에서 일자리와 공존을 위해 지혜를 모으다.\n\n고용노동부 보도자료 /\n보도시점: 2026. 4. 13.(월) 10:00\n\n> - ‘AI 전환과 노동의 미래 토론회’ 4.13.(월) 개최\n---\n고용노동부(장관 김영훈)는 기후노동위 더불어민주당과 공동으로 4월 13일(월) 10시 국회 의원회관에서 ｢AI 전환과 노동의 미래｣ 토론회를 개최했다.\n\n생성형 AI의 발전이 신규 사무직 종사자들의 일자리에 영향을 미치는 와중 휴머노이드 등 피지컬 AI까지 등장함에 따라 제조업·물류업 종사자 등 광범위한 분야로 일자리에 대한 우려가 확산되고 있다. 이번 토론회는 산업 현장의 AI 도입 상황 및 전망을 살펴보고 AI와 일자리가 서로 공존할 수 있는 방안을 논의하기 위해 마련하였다.\n\n이날 토론회는 ‘피지컬 AI시대 산업인력 전략’(카이스트 장영재 교수)과 ‘피지컬 AI의 현재와 미래’(디든로보틱스 김준하 대표)에 대한 발제로 시작되었다.\n\n먼저 첫 번째 발제를 맡은 장영재 교수는 AI로 사라질 직업을 걱정하기보다, AI로 창출되는 일자리와 기회에 집중할 필요가 있다고 강조하였다. 특히 피지컬 AI 도입 초기 창업 지원 및 인력양성을 위한 정부의 역할이 필요하다고 설명하였다. 아울러, 우리나라의 제조업 역량을 활용해 피지컬 AI 생태계를 구축하고, AI 기반의 ‘제조 소프트웨어 기반 공장 구축 운영 노하우’ 수출을 새로운 먹거리로 삼을 필요가 있다고 하였다.\n\n두 번째 발제를 진행한 김준하 대표는 피지컬 AI 도입 상황과 일자리 전망을 설명했다. 현재 피지컬 AI가 상용화 단계에 도달한 것은 맞으나, 도입 비용 및 기술적 한계로 휴머노이드가 단시일 내에 도입되기는 어렵다고 말했다. 특히, 생산가능 인구 감소로 인력난이 있을 분야, 위험한 작업 등에 로봇 투입이 도움이 될 수 있으며, 로봇과 관련된 일자리가 새로이 창출되는 등 피지컬 AI가 일자리에 부정적으로만 작용하지는 않을 것으로 설명했다.\n\n이어 김주영 의원(더불어민주당)이 직접 좌장을 맡은 토론회에서 노사 및 전문가 등 토론자들은 AI 전환을 피할 수 없는 상황에서 직무전환 지원, AI 직무 역량 강화 및 사회안전망 강화 등 정부의 역할에 대하여 공통적으로 제언했다.\n\n김영훈 고용노동부장관은 “최근 중동지역 군사적 충돌은 AI가 산업적 도구를 넘어 국가의 전략 및 안보 자산이라는 것을 시사하고 있다.”라면서 “세계 주요국들이 앞다투어 AI를 발전시키는 상황에서 AI 도입과 발전을 주저할 수는 없다.”라고 밝혔다. 그럼에도, “‘사람을 위한 AI, 모두의 AI’라는 원칙”을 강조하면서 “AI는 인간을 대체하지 않지만, AI를 사용하는 사람이 그렇지 않은 사람을 대체할 것이다.”라는 카림 카리니 하버드대 교수의 말을 인용해 “국민들이 AI 기술을 가진 인력으로 성장하고, 고용안전망을 확충하여 직무전환 과정이 일자리 양극화로 연결되지 않도록 정부도 적극 지원하겠다.”라고 강조했다.\n\n---\n\n### 담당부서\n\n- 고용노동부 노동시장정책관 고용정책총괄과 책임자: 과장 이상임 (044-202-7210)\n- 고용노동부 노동시장정책관 고용정책총괄과 담당자: 서기관 이상혁 (044-202-7292)\n---\n\n## 붙임1 ‘AI 전환과 노동의 미래’토론회 개요\n\n### 일시 : ’26. 4. 13. (월) 10:00∼12:00\n\n### 장소 : 국회 의원회관 제1세미나실\n\n### 주최 : 고용노동부ㆍ더불어민주당 기후에너지환경노동위원회ㆍ국회 내일의 공공과 에너지·노동을 생각하는 의원모임 공동주최\n\n### 후원 : 과학기술정보통신부, 산업통상부\n\n### 참석자 : [좌장] 김주영 의원(민주당)\n\n- [발제] 장영재 교수(카이스트), 김준하 대표(디든로보틱스)\n- [토론] 박수민 한국노동연구원 박사우상범 한국노총 중앙연구원 박사오삼일 한국은행 조사국 고용분석팀장김동희 경총 근로기준정책팀장김형민 ㈜좋은일자리 고용지원사업부장\n- [정부] 김형광 고용노동부 노동시장정책관최우석 과학기술정보통신부 인공지능안전신뢰지원과장권순목 산업통상부 산업인공지능정책과장\n\n### 행사 주요 순서\n\n| 시 간 | | 내 용 | 비고 |\n| --- | --- | --- | --- |\n| 10:00~10:20 | `20 | 개회 및 인사말, 축사 | 장관<br>더불어민주당 의원 |\n| 10:20~10:30 | `10 | 기념촬영 및 장내정리 | |\n| 10:30~11:00 | `15 | 【발제1】 피지컬 AI 시대 산업 인력 전략 | 장영재 교수 |\n| 10:30~11:00 | `15 | 【발제2】 피지컬 AI의 현재와 미래 | 김준하 대표 |\n| 11:00~11:45 | `45 | 토론 | |\n| 11:45~12:00 | ‘15 | 정부발언 | 고용노동부<br>과학기술정보통신부<br>산업통상부 |\n| 11:50~12:00 | `10 | 마무리 | |\n\n---\n\n## 붙임2 고용노동부장관 축사 * 현장발언은 이와 다를 수 있음 안녕하십니까.\n\n고용노동부장관 김영훈입니다.\nAI가 우리 사회, 우리 삶에 가져오는 변화를\n직접 체감하고 있는 이 시점에\n토론회를 같이 준비해주신\n기후노동위 더불어민주당 그리고 국회 내일의 공공과 에너지·노동을 생각하는 의원모임\n소속 의원님들 모두에 감사말씀을 드립니다.\n아울러 발제를 맡아주신 장영재 카이스트 교수님,\n김준하 디든로보틱스 대표님은 물론,\n열띤 토론을 해주실 참석자 여러분들에게도\n깊이 감사드립니다.\n최근 중동 지역의 군사적 충돌로 인해 정세 불안이 심화되고 있습니다.\n이런 충돌은 글로벌 공급망의 불안정성을 넘어,\n우리가 이번 사태에서 직시해야 할\n새로운 모습을 보여주고 있습니다.\n미국 등 AI 선진국들은 본격적으로\n전황을 AI로 분석하여 의사 결정에 참고하고 있으며,\n중동의 AI 기업과 데이터센터와 같은\n첨단 기술 인프라가\n주요 공격대상이 되고 있는 상황입니다.\n이는 AI가 단순한 산업적 도구를 넘어,\n국가의 핵심 전략 자산이자 안보의 최전선이 되었음을\n전 세계에 강력하게 시사하고 있습니다.\n이러한 AI 경쟁의 파고는\n국경 너머의 일만이 아닙니다.\nAI 기술의 급격한 발전은\n우리 산업의 변화를 가져오는 동시에, 노동시장에도 구조적 변화를 일으키고 있습니다.\n많은 국민들께서 생성형 AI를 넘어 자율주행 자동차, 휴머노이드 로봇과 같은\n피지컬 AI의 도입을 지켜보며\n일자리의 미래를 걱정하고 계십니다.\n특히, 사회에 첫발을 내디뎌야 할\n우리 청년들의 우려는 실로 지대합니다.\n내가 애써 준비한 직무가\n당장 AI로 대체되어\n일할 기회조차 갖지 못하는 것이 아닐지,\n기술의 발전 속도에 잘 적응할 수 있을지,\n청년들이 현장에서 느끼실\n막막함과 불안감을\n정부도 매우 무겁고 엄중하게 받아들이고 있습니다.\n그러나, AI 전환은 선택의 문제가 아닙니다.\n세계 주요국들이 앞다투어\nAI를 발전시키는 상황에서\nAI 도입과 발전을 주저할 순 없습니다.\n이러한 상황에서 우리가 나아갈 방향은 명확합니다.\nAI의 혜택이 모두에게 돌아가고, AI로 발생하는 비용은 함께 분담할 수 있도록\n'사람을 위한 AI, 모두의 AI'를 위한\n패러다임을 구축해야 합니다.\n카림 카리니 하버드대 교수의\n“AI는 인간을 대체하지 않지만,\nAI를 사용하는 사람이 그렇지 않은\n사람을 대체할 것이다.”라는 말처럼\n국민들이 AI 기술을 가진 인력으로 성장하여\nAI와 인간이 협력·공존하며\n지속가능한 성장을 이끌어낼 수 있도록\n정부도 적극 지원하겠습니다.\n이를 위해 고용노동부는\n국민 누구나 AI와 함께 일하는 인력이 될 수 있도록\n전폭적인 지원과 정책적 역량을 집중하고 있습니다.\n우선, 지난 12월 발표한 AI 인재육성 방안에 따라\n청년들이 AI 시대의\n핵심 인재로 도약할 수 있도록\n'K-디지털 트레이닝' 등 첨단 산업 분야 직업훈련을\n대폭 확대하고 그 질을 고도화하고 있습니다.\n나아가, 기술 격차가 일자리 양극화로 연결되지 않도록\n취약계층을 보듬는 튼튼한 고용안전망을\n지속적으로 확충해 나갈 것입니다.\n그 첫걸음으로 고용보험 기준을\n근로시간에서 소득기반으로 개편하고 있고\nAI가 노동현장에 가져올 수 있는\n알고리즘 편향 등 부작용을 방지하기 위한\n‘노동분야AI윤리가이드라인’도 마련할 예정입니다.\n정부는 이러한 내용들을 포함하여\n‘산업전환 고용안정 기본계획’을 마련 중에 있습니다.\nAI 대전환 과정에서\n더 많은 일자리를 유지·창출하기 위한 대책들이\n기본계획에 담길 수 있도록\n다양한 이해관계자들의 의견을 경청할 예정입니다.\n그러한 점에서,\n오늘 국회에서 열리는 이 토론회의 의미는\n참으로 각별합니다.\n이 자리에 함께하신 여러 의원님과\n각계 전문가 여러분의 혜안이 모여\n우리 국민과 청년들의 불안을\n희망으로 바꿀 수 있는\n깊이 있는 논의가 이루어지기를 진심으로 기대합니다.\n고용노동부 역시 오늘 제시된\n소중한 고견들을 정책에 적극 반영하여\n국민 모두가 AI 시대에 안심하고 든든한 일자리를 영위할 수 있도록\n최선을 다하겠습니다.\n경청해 주셔서 감사합니다.\n",
      "opendataloader_markdown": "|고용노동부<br><br>보도자료|\n|---|\n\n\n보도시점 2026. 4. 13.(월) 10:00 (2026. 4. 13.(월) 석간)\n\n|인공지능(AI) 전환 과정에서 일자리와 공존을 위해 지혜를 모으다.<br><br>- ‘AI 전환과 노동의 미래 토론회’ 4.13.(월) 개최|\n|---|\n\n\n## 고용노동부(장관 김영훈)는 기후노동위 더불어민주당과 공동으로 4월 13일(월) 10시 국회 의원회관에서 ｢AI 전환과 노동의 미래｣ 토론회를 개최했다.\n\n## 생성형 AI의 발전이 신규 사무직 종사자들의 일자리에 영향을 미치는 와중 휴머노이드 등 피지컬 AI까지 등장함에 따라 제조업·물류업 종사자 등 광범위한 분야로 일자리에 대한 우려가 확산되고 있다. 이번 토론회는 산업 현장의 AI 도입 상황 및 전망을 살펴보고 AI와 일자리가 서로 공존할 수 있는 방안을 논의하기 위해 마련하였다.\n\n이날 토론회는 ‘피지컬 AI시대 산업인력 전략’(카이스트 장영재 교수)과 ‘피지컬 AI의 현재와 미래’(디든로보틱스 김준하 대표)에 대한 발제로 시작되었다.\n\n## 먼저 첫 번째 발제를 맡은 장영재 교수는 AI로 사라질 직업을 걱정하기보다, AI로 창출되는 일자리와 기회에 집중할 필요가 있다고 강조하였다. 특히 피지컬 AI 도입 초기 창업 지원 및 인력양성을 위한 정부의 역할이 필요하다고 설명 하였다. 아울러, 우리나라의 제조업 역량을 활용해 피지컬 AI 생태계를 구축하고, AI 기반의 ‘제조 소프트웨어 기반 공장 구축 운영 노하우’ 수출을 새로운 먹거리로 삼을 필요가 있다고 하였다.\n\n두 번째 발제를 진행한 김준하 대표는 피지컬 AI 도입 상황과 일자리 전망을 설명했다. 현재 피지컬 AI가 상용화 단계에 도달한 것은 맞으나, 도입 비용 및 기술적 한계로 휴머노이드가 단시일 내에 도입되기는 어렵다고 말했다.\n\n특히, 생산가능 인구 감소로 인력난이 있을 분야, 위험한 작업 등에 로봇 투입이 도움이 될 수 있으며, 로봇과 관련된 일자리가 새로이 창출되는 등 피지컬 AI가 일자리에 부정적으로만 작용하지는 않을 것으로 설명했다.\n\n## 이어 김주영 의원(더불어민주당)이 직접 좌장을 맡은 토론회에서 노사 및 전문가 등 토론자들은 AI 전환을 피할 수 없는 상황에서 직무전환 지원, AI 직무 역량 강화 및 사회안전망 강화 등 정부의 역할에 대하여 공통적으로 제언했다.\n\n김영훈 고용노동부 장관은 “최근 중동지역 군사적 충돌은 AI가 산업적 도구를 넘어 국가의 전략 및 안보 자산이라는 것을 시사하고 있다.”라면서 “세계 주요국들이 앞다투어 AI를 발전시키는 상황에서 AI 도입과 발전을 주저할 수는 없다.”라고 밝혔다. 그럼에도, “‘사람을 위한 AI, 모두의 AI’라는 원칙”을 강조 하면서 “AI는 인간을 대체하지 않지만, AI를 사용하는 사람이 그렇지 않은 사람을 대체할 것이다.”라는 카림 카리니 하버드대 교수의 말을 인용해 “국민 들이 AI 기술을 가진 인력으로 성장하고, 고용안전망을 확충하여 직무전환 과정이 일자리 양극화로 연결되지 않도록 정부도 적극 지원하겠다.”라고 강조했다.\n\n|담당 부서|고용노동부 노동시장정책관 고용정책총괄과|책임자|과 장 이상임 (044-202-7210)|\n|---|---|---|---|\n| | |담당자|서기관 이상혁 (044-202-7292)|\n\n\n|붙임1|\n|---|\n\n\n|‘AI 전환과 노동의 미래’토론회 개요|\n|---|\n\n\n- □ 일시 : ’26. 4. 13. (월) 10:00∼12:00\n- □ 장소 : 국회 의원회관 제1세미나실\n- □ 주최 : 고용노동부ㆍ더불어민주당 기후에너지환경노동위원회ㆍ 국회 내일의 공공과 에너지·노동을 생각하는 의원모임 공동주최\n- □ 후원 : 과학기술정보통신부, 산업통상부\n- □ 참석자 : [좌장] 김주영 의원(민주당)\n\n- ㅇ [발제] 장영재 교수(카이스트), 김준하 대표(디든로보틱스)\n- ㅇ [토론] 박수민 한국노동연구원 박사 우상범 한국노총 중앙연구원 박사 오삼일 한국은행 조사국 고용분석팀장 김동희 경총 근로기준정책팀장 김형민 ㈜좋은일자리 고용지원사업부장\n- ㅇ [정부] 김형광 고용노동부 노동시장정책관 최우석 과학기술정보통신부 인공지능안전신뢰지원과장 권순목 산업통상부 산업인공지능정책과장\n\n\n- □ 행사 주요 순서 시 간 내 용 비고\n\n\n- 10:00~10:20 `20 개회 및 인사말, 축사\n\n장관 더불어민주당 의원\n\n- 10:20~10:30 `10 기념촬영 및 장내정리\n\n- 10:30~11:00\n\n- `15 【 발제1 】 피지컬 AI 시대 산업 인력 전략 장영재 교수\n- `15 【 발제2 】 피지컬 AI의 현재와 미래 김준하 대표\n\n\n- 11:00~11:45 `45 토론\n\n\n- 11:45~12:00 ‘15 정부발언\n\n\n고용노동부 과학기술정보통신부 산업통상부\n\n- 11:50~12:00 `10 마무리\n\n\n|붙임2|\n|---|\n\n\n|고용노동부 장관 축사 * 현장발언은 이와 다를 수 있음|\n|---|\n\n\n안녕하십니까. 고용노동부 장관 김영훈입니다.\n\nAI가 우리 사회, 우리 삶에 가져오는 변화를 직접 체감하고 있는 이 시점에 토론회를 같이 준비해주신\n\n기후노동위 더불어민주당 그리고 국회 내일의 공공과 에너지·노동을 생각하는 의원모임 소속 의원님들 모두에 감사말씀을 드립니다.\n\n아울러 발제를 맡아주신 장영재 카이스트 교수님, 김준하 디든로보틱스 대표님은 물론, 열띤 토론을 해주실 참석자 여러분들에게도 깊이 감사드립니다.\n\n최근 중동 지역의 군사적 충돌로 인해 정세 불안이 심화되고 있습니다.\n\n이런 충돌은 글로벌 공급망의 불안정성을 넘어, 우리가 이번 사태에서 직시해야 할 새로운 모습을 보여주고 있습니다.\n\n미국 등 AI 선진국들은 본격적으로 전황을 AI로 분석하여 의사 결정에 참고하고 있으며, 중동의 AI 기업과 데이터센터와 같은 첨단 기술 인프라가 주요 공격대상이 되고 있는 상황입니다.\n\n이는 AI가 단순한 산업적 도구를 넘어, 국가의 핵심 전략 자산이자 안보의 최전선이 되었음을 전 세계에 강력하게 시사하고 있습니다.\n\n이러한 AI 경쟁의 파고는 국경 너머의 일만이 아닙니다. AI 기술의 급격한 발전은 우리 산업의 변화를 가져오는 동시에, 노동시장에도 구조적 변화를 일으키고 있습니다.\n\n많은 국민들께서 생성형 AI를 넘어 자율주행 자동차, 휴머노이드 로봇과 같은 피지컬 AI의 도입을 지켜보며 일자리의 미래를 걱정하고 계십니다.\n\n특히, 사회에 첫발을 내디뎌야 할 우리 청년들의 우려는 실로 지대합니다.\n\n내가 애써 준비한 직무가 당장 AI로 대체되어 일할 기회조차 갖지 못하는 것이 아닐지, 기술의 발전 속도에 잘 적응할 수 있을지, 청년들이 현장에서 느끼실 막막함과 불안감을 정부도 매우 무겁고 엄중하게 받아들이고 있습니다.\n\n그러나, AI 전환은 선택의 문제가 아닙니다. 세계 주요국들이 앞다투어 AI를 발전시키는 상황에서 AI 도입과 발전을 주저할 순 없습니다.\n\n이러한 상황에서 우리가 나아갈 방향은 명확합니다. AI의 혜택이 모두에게 돌아가고, AI로 발생하는 비용은 함께 분담할 수 있도록 '사람을 위한 AI, 모두의 AI'를 위한 패러다임을 구축해야 합니다.\n\n- 카림 카리니 하버드대 교수의 “AI는 인간을 대체하지 않지만, AI를 사용하는 사람이 그렇지 않은 사람을 대체할 것이다.”라는 말처럼\n\n\n국민들이 AI 기술을 가진 인력으로 성장하여 AI와 인간이 협력·공존하며 지속가능한 성장을 이끌어낼 수 있도록 정부도 적극 지원하겠습니다.\n\n이를 위해 고용노동부는 국민 누구나 AI와 함께 일하는 인력이 될 수 있도록 전폭적인 지원과 정책적 역량을 집중하고 있습니다.\n\n우선, 지난 12월 발표한 AI 인재육성 방안에 따라 청년들이 AI 시대의 핵심 인재로 도약할 수 있도록 'K-디지털 트레이닝' 등 첨단 산업 분야 직업훈련을 대폭 확대하고 그 질을 고도화하고 있습니다.\n\n나아가, 기술 격차가 일자리 양극화로 연결되지 않도록 취약계층을 보듬는 튼튼한 고용안전망을 지속적으로 확충해 나갈 것입니다.\n\n그 첫걸음으로 고용보험 기준을 근로시간에서 소득기반으로 개편하고 있고 AI가 노동현장에 가져올 수 있는 알고리즘 편향 등 부작용을 방지하기 위한 ‘노동분야AI윤리가이드라인’도 마련할 예정입니다.\n\n정부는 이러한 내용들을 포함하여 ‘산업전환 고용안정 기본계획’을 마련 중에 있습니다.\n\nAI 대전환 과정에서\n\n- 더 많은 일자리를 유지·창출하기 위한 대책들이 기본계획에 담길 수 있도록 다양한 이해관계자들의 의견을 경청할 예정입니다.\n\n\n그러한 점에서, 오늘 국회에서 열리는 이 토론회의 의미는 참으로 각별합니다.\n\n이 자리에 함께하신 여러 의원님과 각계 전문가 여러분의 혜안이 모여 우리 국민과 청년들의 불안을 희망으로 바꿀 수 있는 깊이 있는 논의가 이루어지기를 진심으로 기대합니다.\n\n고용노동부 역시 오늘 제시된 소중한 고견들을 정책에 적극 반영하여 국민 모두가 AI 시대에 안심하고 든든한 일자리를 영위할 수 있도록 최선을 다하겠습니다.\n\n경청해 주셔서 감사합니다.\n\n"
    },
    {
      "document_id": "156754259",
      "title": "소비로 꽃피우는 4월, 2026 동행축제 개막",
      "department": "중소벤처기업부",
      "approve_date": "04/13/2026 13:44:07",
      "readhim": {
        "overall": 0.6480914895815524,
        "nid": 0.9033733562035448,
        "teds": null,
        "mhs": 0.39280962295956,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.42513996749142136,
        "nid": 0.8502799349828427,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 소비로 꽃피우는 4월, 2026 동행축제 개막\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 중소벤처기업부\n- 게시 시각: 04/13/2026 13:44:07\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754259&call_from=openData\n- HWPX 첨부: 20260413_소비로_꽃피우는_4월,_2026_동행축제_개막.hwpx\n- PDF 첨부: 20260413_소비로_꽃피우는_4월,_2026_동행축제_개막.pdf\n\n## 본문\n\n## 소비로 꽃피우는 4월, 2026 동행축제 개막\n- 4.11(토) 전주시민, 관광객이 어우러져 개막식 성황리 개최 - 중동전쟁 등 국민 경제 어려움 속, “지역상권, 지역소비” 중요성 강조\n\n중소벤처기업부(장관 한성숙, 이하 중기부)는 4월 11일 전주실내체육관에서 전주 시민들과 관광객들이 참석한 가운데 ‘4월 동행축제’의 시작을 알리는 개막식을 개최하였다고 밝혔다.\n\n이로써 5월 10일까지 30일간 전국에서 열리는 동행축제가 공식 시작되 었으며, 지역상권에 활력을 불어넣기 위한 대규모 소비촉진 프로그램이 본격 가동된다.\n\n이날 개막식에는 축사를 맡은 김민석 국무총리를 비롯해 소상공인 협· 단체 장, 유 통기업 관계자들이 참석하였으며, 중동전쟁 상황을 고려하여 화려한 개막 세리머니를 생략하고 간소한 방식으로 운영되었다.\n\n개막식과 연계하여 전북대 알림의거리와 대학로 상점가 일원에서는 4월 11 일부터 12 일까지 전국의 우수 소상공인과 전북지역 로컬 소상공인이 참여 하는 개막판매전이 열렸으며, 다양한 먹거리, 체험, 문화행사가 함께 진행되어 제품을 구매하고 이벤트를 즐기는 시민들로 활기를 띠었다.\n\n특히 상생콘서트는 3 천석 규모의 좌석이 모두 채워질 정도로 높은 관심을 모 았으며 멜로망스, 김연우, 소향 등 인기 가수들의 열정적인 무대가 더해져 축제의 분위기를 한층 고조시켰다.\n\n개막 판매전에 참여한 소상공인들은 “대규모 소비촉진 행사는 가게 매출에 큰 도움이 된다”라며, “지역상권 살리는 이러한 행사가 지속적으로 확대 되기를 바란다”라고 말하며 만족감과 기대감을 나타냈다.\n\n동행축제는 개막식을 시작으로 5월 10 일까지 200 개 온· 오프라인 유통채널에서 다채로운 할인행사와 이벤트가 진행된다.\n\n네이버, 카카오, 지마켓, 컬리 등 93 개 온라인 플랫폼에서는 K- 뷰티· 패션· 식품 등 1만 8천여 소상공인의 제품에 대한 다양한 할인전이 진행된다.\n\n특히, 3:1의 경쟁을 통해 선정된 동행축제 대표 300개 제품에 대해서는 네 이버에서 “동행 300 기획전”이 30 일간 개최되며, 최대 50% 의 자체 할인 전에 더해 20% 할인쿠폰이 등이 지원되어 최대 70% 할인된 가격에 상품을 만나볼 수 있다.\n\n공영홈쇼핑과 홈앤쇼핑에서도 TV 방송 상품에 대해 최대 5 만 원의 적립금 지급과 기프티콘 지급 등 5월 가정의달과 연계한 프로모션을 진행한다.\n\n지역과 연계한 오프라인 프로그램도 전국적으로 펼쳐진다.\n\nK- 컬처 열풍으로 증가하는 외국인과 내국인의 지역 방문을 유도하고 지역 소비로도 이어지도록 전국 50개 지역축제와 연계하고, 대형 유통사, 지역 소상공인과 협력하여 준비한 우수 소상공인 판매전과 이벤트가 전국 방방곡곡에서 펼쳐진다.\n\n4월 17일부터 26일까지 인천 부평르네상스상권에서는 “부평블랙데이” 행사가 열려 라이브커머스와 연계한 판매전을 진행하고, 할인쿠폰 제공, 기념품 증정과 함께 인천항 크루즈 입항 관광객 유치를 위한 투어버스도 운행한다.\n\n5월 1일부터 2일까지 수제버거로 유명한 대구에서는 예스24 반월당점 일원에서 “대구 수제버거페스티벌”이 개최된다. 탄산음료와 캔맥주를 1,000원에 제공하는 이벤트와 시식행사, 디제잉, 버스킹 공연 등 다양한 볼거리로 소상공인 제품 판촉을 지원한다.\n\n5월 1 일부터 3 일까지 스타필드 안성점에서는 뷰티, 리빙, 공예품, 먹기리 등 50 개사 우수 소상공인의 플리마켓이 개최된다. 대형 아트벌룬 전시, 버스 킹, 어 린이 공연, 태권도, K-POP 커버댄스 등 다채로운 문화공연도 열려가 족 단위 고객에게 쇼핑과 여가를 제공한다.\n\n특별한 “기빙 플러스” 의류 할인행사도 개최된다. 의류환경협의체와의 협업을 통해, 동행축제 기간 2차례 최대 90% 할인된 가격에 16개사 4만 7 천여 의류를 대규모 할인 판매하고, 수익금은 취약계층 일자리 자립 지원에 기부하는 사회 공헌 활동도 연계한다.\n\n* (1차) 4.26~27, 이천도자기 축제 판매장, (2차) 5.8~10, 행복한 백화점\n\n한살림생협 230 개 지점에서는 동행축제 기간 내 누구나 10% 할인된 회원 가로 물품을 구매할 수 있으며, 신규 가입 시 3,000원 할인쿠폰과 사은품 증정 등 다양한 이벤트도 진행한다.\n\n중기부 한성숙 장관은 “우리의 소비가 모여 지역경제를 살리는 힘이 된다” 라며 “30일간 이어지는 동행축제 기간 대중교통을 이용하여 전국 곳곳을 찾는 여행과 소비가 함께 이루어져 실질적인 소비활성화로 이어지기를 기대한다”라고 밝혔다.\n\n## 담당 부서\n\n- 담당 부서: 소상공인성장촉진과 / 책임자 과장 김혜남 / (044-204-7290)\n- 담당자: 사무관 / 박미란(044-204-7266)\n- 사무관 / 강주실 / (044-204-7795)\n- 주무관 / 박성아 / (044-204-7291)\n- 주무관 / 박찬영 / (044-204-7830)\n\n## 붙임1 4월 동행축제 연계 지역축제 및 행사\n\n## 첨부파일\n\n- 20260413_소비로_꽃피우는_4월,_2026_동행축제_개막.hwpx\n- 20260413_소비로_꽃피우는_4월,_2026_동행축제_개막.pdf\n",
      "readhim_markdown": "# 소비로 꽃피우는 4월, 2026 동행축제 개막\n\n중소벤처기업부 보도자료 /\n보도시점: 2026. 4. 13.(월) / 조간 < 2026. 4. 12.(일) 12:00 >\n\n> - 4.11(토) 전주시민, 관광객이 어우러져 개막식 성황리 개최\n> - 중동전쟁 등 국민 경제 어려움 속, “지역상권, 지역소비” 중요성 강조\n---\n중소벤처기업부(장관 한성숙, 이하 중기부)는 4월 11일 전주실내체육관에서 전주 시민들과 관광객들이 참석한 가운데 ‘4월 동행축제’의 시작을 알리는 개막식을 개최하였다고 밝혔다.\n\n이로써 5월 10일까지 30일간 전국에서 열리는 동행축제가 공식 시작되었으며, 지역상권에 활력을 불어넣기 위한 대규모 소비촉진 프로그램이 본격 가동된다.\n\n이날 개막식에는 축사를 맡은 김민석 국무총리를 비롯해 소상공인 협·단체장, 유통기업 관계자들이 참석하였으며, 중동전쟁 상황을 고려하여 화려한 개막 세리머니를 생략하고 간소한 방식으로 운영되었다.\n\n개막식과 연계하여 전북대 알림의거리와 대학로 상점가 일원에서는 4월 11일부터 12일까지 전국의 우수 소상공인과 전북지역 로컬 소상공인이 참여하는 개막판매전이 열렸으며, 다양한 먹거리, 체험, 문화행사가 함께 진행되어 제품을 구매하고 이벤트를 즐기는 시민들로 활기를 띠었다.\n\n특히 상생콘서트는 3천석 규모의 좌석이 모두 채워질 정도로 높은 관심을 모았으며 멜로망스, 김연우, 소향 등 인기 가수들의 열정적인 무대가 더해져 축제의 분위기를 한층 고조시켰다.\n\n개막 판매전에 참여한 소상공인들은 “대규모 소비촉진 행사는 가게 매출에 큰 도움이 된다”라며, “지역상권 살리는 이러한 행사가 지속적으로 확대 되기를 바란다”라고 말하며 만족감과 기대감을 나타냈다.\n\n동행축제는 개막식을 시작으로 5월 10일까지 200개 온·오프라인 유통채널에서 다채로운 할인행사와 이벤트가 진행된다.\n\n네이버, 카카오, 지마켓, 컬리 등 93개 온라인 플랫폼에서는 K-뷰티·패션·식품 등 1만 8천여 소상공인의 제품에 대한 다양한 할인전이 진행된다.\n\n특히, 3:1의 경쟁을 통해 선정된 동행축제 대표 300개 제품에 대해서는 네이버에서 “동행 300 기획전”이 30일간 개최되며, 최대 50%의 자체 할인전에 더해 20% 할인쿠폰이 등이 지원되어 최대 70% 할인된 가격에 상품을 만나볼 수 있다.\n\n공영홈쇼핑과 홈앤쇼핑에서도 TV 방송 상품에 대해 최대 5만원의 적립금 지급과 기프티콘 지급 등 5월 가정의달과 연계한 프로모션을 진행한다.\n\n지역과 연계한 오프라인 프로그램도 전국적으로 펼쳐진다.\n\nK-컬처 열풍으로 증가하는 외국인과 내국인의 지역 방문을 유도하고 지역 소비로도 이어지도록 전국 50개 지역축제와 연계하고, 대형 유통사, 지역 소상공인과 협력하여 준비한 우수 소상공인 판매전과 이벤트가 전국 방방곡곡에서 펼쳐진다.\n\n4월 17일부터 26일까지 인천 부평르네상스상권에서는 “부평블랙데이” 행사가 열려 라이브커머스와 연계한 판매전을 진행하고, 할인쿠폰 제공, 기념품 증정과 함께 인천항 크루즈 입항 관광객 유치를 위한 투어버스도 운행한다.\n\n5월 1일부터 2일까지 수제버거로 유명한 대구에서는 예스24 반월당점 일원에서 “대구 수제버거페스티벌”이 개최된다. 탄산음료와 캔맥주를 1,000원에 제공하는 이벤트와 시식행사, 디제잉, 버스킹 공연 등 다양한 볼거리로 소상공인 제품 판촉을 지원한다.\n\n5월 1일부터 3일까지 스타필드 안성점에서는 뷰티, 리빙, 공예품, 먹기리 등 50개사 우수 소상공인의 플리마켓이 개최된다. 대형 아트벌룬 전시, 버스킹, 어린이 공연, 태권도, K-POP 커버댄스 등 다채로운 문화공연도 열려 가족단위 고객에게 쇼핑과 여가를 제공한다.\n\n특별한 “기빙 플러스” 의류 할인행사도 개최된다. 의류환경협의체와의 협업을 통해, 동행축제 기간 2차례 최대 90% 할인된 가격에 16개사 4만 7천여 의류를 대규모 할인 판매하고, 수익금은 취약계층 일자리 자립 지원에 기부하는 사회 공헌 활동도 연계한다.\n> * (1차) 4.26~27, 이천도자기 축제 판매장, (2차) 5.8~10, 행복한 백화점\n\n한살림생협 230개 지점에서는 동행축제 기간 내 누구나 10% 할인된 회원가로 물품을 구매할 수 있으며, 신규 가입 시 3,000원 할인쿠폰과 사은품 증정 등 다양한 이벤트도 진행한다.\n\n중기부 한성숙 장관은 “우리의 소비가 모여 지역경제를 살리는 힘이 된다”라며 “30일간 이어지는 동행축제 기간 대중교통을 이용하여 전국 곳곳을 찾는 여행과 소비가 함께 이루어져 실질적인 소비활성화로 이어지기를 기대한다”라고 밝혔다.\n\n---\n\n### 담당부서\n\n- 소상공인성장촉진과 책임자: 과장 김혜남 (044-204-7290)\n- 소상공인성장촉진과 담당자: 사무관 박미란 (044-204-7266)\n- 소상공인성장촉진과 담당자: 사무관 강주실 (044-204-7795)\n- 소상공인성장촉진과 담당자: 주무관 박성아 (044-204-7291)\n- 소상공인성장촉진과 담당자: 주무관 박찬영 (044-204-7830)\n---\n\n## 붙임1 4월 동행축제 연계 지역축제 및 행사\n\n---\n\n## 붙임2 4월 동행축제 이벤트\n",
      "opendataloader_markdown": "|보도자료<br><br>|\n|---|\n\n\n보도시점 2026. 4. 13.(월) 조간 < 2026. 4. 12.(일) 12:00 >\n\n|소비로 꽃피우는 4월, 2026 동행축제 개막<br><br>- 4.11(토) 전주시민, 관광객이 어우러져 개막식 성황리 개최<br>- 중동전쟁 등 국민 경제 어려움 속, “지역상권, 지역소비” 중요성 강조<br>|\n|---|\n\n\n중소벤처기업부(장관 한성숙, 이하 중기부)는 4월 11일 전주실내체육관 에서 전주 시민들과 관광객들이 참석한 가운데 ‘4월 동행축제’의 시작을 알리는 개막식을 개최하였다고 밝혔다.\n\n이로써 5월 10일까지 30일간 전국에서 열리는 동행축제가 공식 시작되 었으며, 지역상권에 활력을 불어넣기 위한 대규모 소비촉진 프로그램이 본격 가동된다.\n\n이날 개막식에는 축사를 맡은 김민석 국무총리를 비롯해 소상공인 협·단체장, 유통기업 관계자들이 참석하였으며, 중동전쟁 상황을 고려하여 화려한 개막 세리머니를 생략하고 간소한 방식으로 운영되었다.\n\n개막식과 연계하여 전북대 알림의거리와 대학로 상점가 일원에서는 4월 11일부터 12일까지 전국의 우수 소상공인과 전북지역 로컬 소상공인이 참여 하는 개막판매전이 열렸으며, 다양한 먹거리, 체험, 문화행사가 함께 진행 되어 제품을 구매하고 이벤트를 즐기는 시민들로 활기를 띠었다.\n\n특히 상생콘서트는 3천석 규모의 좌석이 모두 채워질 정도로 높은 관심을 모았으며 멜로망스, 김연우, 소향 등 인기 가수들의 열정적인 무대가 더해져 축제의 분위기를 한층 고조시켰다.\n\n- 1 -\n\n개막 판매전에 참여한 소상공인들은 “대규모 소비촉진 행사는 가게 매출에 큰 도움이 된다”라며, “지역상권 살리는 이러한 행사가 지속적으로 확대 되기를 바란다”라고 말하며 만족감과 기대감을 나타냈다.\n\n동행축제는 개막식을 시작으로 5월 10일까지 200개 온·오프라인 유통채널 에서 다채로운 할인행사와 이벤트가 진행된다.\n\n네이버, 카카오, 지마켓, 컬리 등 93개 온라인 플랫폼에서는 K-뷰티·패션· 식품 등 1만 8천여 소상공인의 제품에 대한 다양한 할인전이 진행된다.\n\n특히, 3:1의 경쟁을 통해 선정된 동행축제 대표 300개 제품에 대해서는 네이버에서 “동행 300 기획전”이 30일간 개최되며, 최대 50%의 자체 할인전에 더해 20% 할인쿠폰이 등이 지원되어 최대 70% 할인된 가격에 상품을 만나볼 수 있다.\n\n공영홈쇼핑과 홈앤쇼핑에서도 TV 방송 상품에 대해 최대 5만 원의 적립금 지급과 기프티콘 지급 등 5월 가정의달과 연계한 프로모션을 진행한다.\n\n지역과 연계한 오프라인 프로그램도 전국적으로 펼쳐진다.\n\nK-컬처 열풍으로 증가하는 외국인과 내국인의 지역 방문을 유도하고 지역 소비로도 이어지도록 전국 50개 지역축제와 연계하고, 대형 유통사, 지역 소상공인과 협력하여 준비한 우수 소상공인 판매전과 이벤트가 전국 방방 곡곡에서 펼쳐진다.\n\n4월 17일부터 26일까지 인천 부평르네상스상권에서는 “부평블랙데이” 행사가 열려 라이브커머스와 연계한 판매전을 진행하고, 할인쿠폰 제공, 기념품 증정과 함께 인천항 크루즈 입항 관광객 유치를 위한 투어버스도 운행한다.\n\n- 2 -\n\n- 5월 1일부터 2일까지 수제버거로 유명한 대구에서는 예스24 반월당점\n\n일원에서 “대구 수제버거페스티벌”이 개최된다. 탄산음료와 캔맥주를 1,000원에 제공하는 이벤트와 시식행사, 디제잉, 버스킹 공연 등 다양한 볼거리로 소상공인 제품 판촉을 지원한다.\n\n- 5월 1일부터 3일까지 스타필드 안성점에서는 뷰티, 리빙, 공예품, 먹기리\n\n\n등 50개사 우수 소상공인의 플리마켓이 개최된다. 대형 아트벌룬 전시, 버스킹, 어린이 공연, 태권도, K-POP 커버댄스 등 다채로운 문화공연도 열려 가족 단위 고객에게 쇼핑과 여가를 제공한다.\n\n특별한 “기빙 플러스” 의류 할인행사도 개최된다. 의류환경협의체와의 협업을 통해, 동행축제 기간 2차례 최대 90% 할인된 가격에 16개사 4만 7천여 의류를 대규모 할인 판매하고, 수익금은 취약계층 일자리 자립 지원에 기부하는 사회 공헌 활동도 연계한다.\n\n* (1차) 4.26~27, 이천도자기 축제 판매장, (2차) 5.8~10, 행복한 백화점\n\n한살림생협 230개 지점에서는 동행축제 기간 내 누구나 10% 할인된 회원 가로 물품을 구매할 수 있으며, 신규 가입 시 3,000원 할인쿠폰과 사은품 증정 등 다양한 이벤트도 진행한다.\n\n중기부 한성숙 장관은 “우리의 소비가 모여 지역경제를 살리는 힘이 된다” 라며 “30일간 이어지는 동행축제 기간 대중교통을 이용하여 전국 곳곳을 찾는 여행과 소비가 함께 이루어져 실질적인 소비활성화로 이어지기를 기대 한다”라고 밝혔다.\n\n|담당 부서|소상공인성장촉진과|책임자|과 장 김혜남 (044-204-7290)|\n|---|---|---|---|\n| | |담당자|사무관 박미란 (044-204-7266) 사무관 강주실 (044-204-7795) 주무관 박성아 (044-204-7291) 주무관 박찬영 (044-204-7830)|\n\n\n- 3 -\n\n|붙임1|\n|---|\n\n\n|4월 동행축제 연계 지역축제 및 행사|\n|---|\n\n\n- 4 -\n\n|붙임2|\n|---|\n\n\n|4월 동행축제 이벤트|\n|---|\n\n\n- 5 -\n\n"
    },
    {
      "document_id": "156754205",
      "title": "보훈부, 성과 중심 공직문화 확산 추진 특별성과 포상 실시",
      "department": "국가보훈부",
      "approve_date": "04/13/2026 10:55:02",
      "readhim": {
        "overall": 0.5979142669912563,
        "nid": 0.8267498267498268,
        "teds": null,
        "mhs": 0.36907870723268577,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.38237221494102225,
        "nid": 0.7647444298820445,
        "teds": null,
        "mhs": 0.0,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 보훈부, 성과 중심 공직문화 확산 추진 특별성과 포상 실시\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 국가보훈부\n- 게시 시각: 04/13/2026 10:55:02\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754205&call_from=openData\n- HWPX 첨부: 260412 보도자료(보훈부， 성과 중심 공직문화 확산 추진 특별성과 포상 실시)최종.hwpx\n- PDF 첨부: 260412 보도자료(보훈부， 성과 중심 공직문화 확산 추진 특별성과 포상 실시)최종.pdf\n\n## 본문\n\n국가보훈부(장관 권오을) 는 성과 중심의 공직문화 확산을 위해 보훈가족과 국민이 체감할 수 있는 성과를 창출한 팀과 공무원을 포상하는 ‘제 1 회 특별성과 포상식’ 을 지난 10일(금) 서울지방보훈청에서 진행했다고 밝혔다.\n\n이번 포상은 제도 개선과 위기 대응, 복지 확대 등 다양한 분야에서 정책의 구조적 개선을 이끈 우수한 성과를 창출한 팀과 공무원을 선정, 포상금과장관 표창 수여를 통해 성과를 내는 조직문화를 정착시켜 나가기 위해 시행됐다.\n\n첫 번째 팀 성과로, 고시원과 반지하 등 열악한 환경에 거주하는 독립유공자 후손에게 공공임대주택을 지원하는 ‘보훈보금자리’ 사업을 통해 주거 취약 보훈가족의 삶의 질을 실질적으로 개선하는데 기여한 생활안정과 주택지원팀에게 300 만 원의 포상금이 수여됐다.\n\n또한, 의사 집단행동에 따른 의료 공백 상황에서 보훈병원 비상진료체계를 운영하여 보훈대상자의 진료 공백을 최소화하고, 국가 책임형 보훈의료 체계의 안정성을 확보한 성과로 보훈의료정책과 의료지원팀에게 포상금 200 만 원을 수여했다.\n\n개인으로는, 국가유공자 고령화에 따라 회원자격을 유족까지 확대하여 보훈단체(재일학도의용군, 6 ‧ 25 참전유공자회, 월남전참전유공자회) 의 지속가능성을 확보하고, 호국정신을 미래세대로 계승할 수 있는 기반을 마련한 보훈단체 협력담당관실 사무관과 친일귀속재산 관리체계 재정비와 채권관리 및 환수 기반 강화를 통해 공공자산의 투명성과 재정 건전성, 그리고 역사적 정의 실현을 뒷받침하는 제도적 기반을 마련한 보훈문화정책과 사무관이 각각 특별 성과 포상(각 100 만 원) 을 받았다.\n\n권오을 국가보훈부 장관은 “이번 특별성과 포상은 국민이 체감하는 변화를 만들어낸 공직자에게 합당한 보상을 제공하는 첫 사례로, 성과를 내면 반드시 보상받는다는 분명한 기준을 제시 하는 것”이라며 “보훈은 단순한 행정을 넘어 국민의 역사와 국가 정체성을 유지‧발전시키는 업무인 만큼, 특별성과 포상 확대와 정책 적용을 통해 수요자인 보훈 가족과 국민 중심의 보훈행정 혁신을 추진 해 나가겠다”고 밝혔다. < 끝 >\n\n별첨. 특별성과 포상식 사진.\n\n## 담당 부서\n\n- 담당 부서: 혁신행정담당관 / 책임자 과장 최 남임 / 044-202-5230\n- 담당자: 사무관 / 정 유 진 044-202-5239\n\n## 첨부파일\n\n- 260412 보도자료(보훈부， 성과 중심 공직문화 확산 추진 특별성과 포상 실시)최종.hwpx\n- 260412 보도자료(보훈부， 성과 중심 공직문화 확산 추진 특별성과 포상 실시)최종.pdf\n",
      "readhim_markdown": "# 보훈부 “성과중심 공직문화 확산 추진”... 제1회 특별성과 포상 실시\n\n국가보훈부 보도자료 /\n보도시점: 2026. 4. 12.(일) / 배포 2026. 4. 12.(일)\n\n> - 독립유공자 후손 공공임대주택 지원, 보훈단체 회원자격 확대 등 네 가지 성과 포상\n> - 보훈부, 특별성과 포상 확대 및 우수사례 확산 통해 국민 중심 보훈행정 혁신 추진\n---\n국가보훈부(장관 권오을)는 성과 중심의 공직문화 확산을 위해 보훈가족과 국민이 체감할 수 있는 성과를 창출한 팀과 공무원을 포상하는 ‘제1회 특별성과 포상식’을 지난 10일(금) 서울지방보훈청에서 진행했다고 밝혔다.\n\n이번 포상은 제도 개선과 위기 대응, 복지 확대 등 다양한 분야에서 정책의 구조적 개선을 이끈 우수한 성과를 창출한 팀과 공무원을 선정, 포상금과장관표창 수여를 통해 성과를 내는 조직문화를 정착시켜 나가기 위해 시행됐다.\n\n첫 번째 팀 성과로, 고시원과 반지하 등 열악한 환경에 거주하는 독립유공자 후손에게 공공임대주택을 지원하는 ‘보훈보금자리’ 사업을 통해 주거 취약 보훈가족의 삶의 질을 실질적으로 개선하는데 기여한 생활안정과 주택지원팀에게 300만 원의 포상금이 수여됐다.\n\n또한, 의사 집단행동에 따른 의료 공백 상황에서 보훈병원 비상진료체계를 운영하여 보훈대상자의 진료 공백을 최소화하고, 국가 책임형 보훈의료 체계의 안정성을 확보한 성과로 보훈의료정책과 의료지원팀에게 포상금 200만 원을 수여했다.\n\n개인으로는, 국가유공자 고령화에 따라 회원자격을 유족까지 확대하여 보훈단체(재일학도의용군, 6‧25참전유공자회, 월남전참전유공자회)의 지속가능성을 확보하고, 호국정신을 미래세대로 계승할 수 있는 기반을 마련한 보훈단체협력담당관실 사무관과 친일귀속재산 관리체계 재정비와 채권관리 및 환수 기반 강화를 통해 공공자산의 투명성과 재정 건전성, 그리고 역사적 정의 실현을 뒷받침하는 제도적 기반을 마련한 보훈문화정책과 사무관이 각각 특별성과 포상(각 100만 원)을 받았다.\n권오을 국가보훈부장관은 “이번 특별성과 포상은 국민이 체감하는 변화를 만들어낸 공직자에게 합당한 보상을 제공하는 첫 사례로, 성과를 내면 반드시 보상받는다는 분명한 기준을 제시하는 것”이라며 “보훈은 단순한 행정을 넘어 국민의 역사와 국가 정체성을 유지‧발전시키는 업무인 만큼, 특별성과 포상 확대와 정책 적용을 통해 수요자인 보훈가족과 국민 중심의 보훈행정 혁신을 추진해 나가겠다”고 밝혔다.\n\n#### <끝>\n\n별첨. 특별성과 포상식 사진.\n\n---\n\n### 담당부서\n\n- 혁신행정담당관 책임자: 과장 최 남 임 044-202-5230\n- 혁신행정담당관 담당자: 사무관 정 유 진 044-202-5239\n",
      "opendataloader_markdown": "|보도자료|\n|---|\n\n\n보도시점 2026. 4. 12.(일) 배포 2026. 4. 12.(일)\n\n|보훈부 “성과중심 공직문화 확산 추진”... 제1회 특별성과 포상 실시<br><br>- 독립유공자 후손 공공임대주택 지원, 보훈단체 회원자격 확대 등 네 가지 성과 포상<br>- 보훈부, 특별성과 포상 확대 및 우수사례 확산 통해 국민 중심 보훈행정 혁신 추진<br>|\n|---|\n\n\n국가보훈부(장관 권오을)는 성과 중심의 공직문화 확산을 위해 보훈가족과 국민이 체감할 수 있는 성과를 창출한 팀과 공무원을 포상하는 ‘제1회 특별 성과 포상식’을 지난 10일(금) 서울지방보훈청에서 진행했다고 밝혔다.\n\n이번 포상은 제도 개선과 위기 대응, 복지 확대 등 다양한 분야에서 정책의 구조적 개선을 이끈 우수한 성과를 창출한 팀과 공무원을 선정, 포상금과 장관 표창 수여를 통해 성과를 내는 조직문화를 정착시켜 나가기 위해 시행됐다.\n\n첫 번째 팀 성과로, 고시원과 반지하 등 열악한 환경에 거주하는 독립유 공자 후손에게 공공임대주택을 지원하는 ‘보훈보금자리’ 사업을 통해 주거 취약 보훈가족의 삶의 질을 실질적으로 개선하는데 기여한 생활안정과 주택 지원팀에게 300만 원의 포상금이 수여됐다.\n\n또한, 의사 집단행동에 따른 의료 공백 상황에서 보훈병원 비상진료체계를 운영하여 보훈대상자의 진료 공백을 최소화하고, 국가 책임형 보훈의료 체계의 안정성을 확보한 성과로 보훈의료정책과 의료지원팀에게 포상금 200만 원을 수여했다.\n\n개인으로는, 국가유공자 고령화에 따라 회원자격을 유족까지 확대하여 보훈 단체(재일학도의용군, 6‧25참전유공자회, 월남전참전유공자회)의 지속가능성을 확보하고, 호국정신을 미래세대로 계승할 수 있는 기반을 마련한 보훈단체 협력담당관실 사무관과 친일귀속재산 관리체계 재정비와 채권관리 및 환수 기반 강화를 통해 공공자산의 투명성과 재정 건전성, 그리고 역사적 정의 실현을 뒷받침하는 제도적 기반을 마련한 보훈문화정책과 사무관이 각각 특별성과 포상(각 100만 원)을 받았다.\n\n권오을 국가보훈부 장관은 “이번 특별성과 포상은 국민이 체감하는 변화를 만들어낸 공직자에게 합당한 보상을 제공하는 첫 사례로, 성과를 내면 반드시 보상받는다는 분명한 기준을 제시하는 것”이라며 “보훈은 단순한 행정을 넘어 국민의 역사와 국가 정체성을 유지‧발전시키는 업무인 만큼, 특별성과 포상 확대와 정책 적용을 통해 수요자인 보훈가족과 국민 중심의 보훈행정 혁신을 추진해 나가겠다”고 밝혔다. <끝>\n\n별첨. 특별성과 포상식 사진.\n\n|담당 부서|혁신행정담당관|책임자|과 장 최 남 임 044-202-5230|\n|---|---|---|---|\n| | |담당자|사무관 정 유 진 044-202-5239|\n\n\n"
    },
    {
      "document_id": "156754178",
      "title": "제266차 대외경제장관회의 개최",
      "department": "재정경제부",
      "approve_date": "04/13/2026 00:00:00",
      "readhim": {
        "overall": 0.23283545153136803,
        "nid": 0.3758506368871052,
        "teds": null,
        "mhs": 0.08982026617563088,
        "prediction_available": true,
        "table_timed_out": false
      },
      "opendataloader": {
        "overall": 0.43475943288256663,
        "nid": 0.78599487617421,
        "teds": null,
        "mhs": 0.08352398959092322,
        "prediction_available": true
      },
      "ground_truth_markdown": "# 제266차 대외경제장관회의 개최\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 재정경제부\n- 게시 시각: 04/13/2026 00:00:00\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754178&call_from=openData\n- HWPX 첨부: [별첨] (모두말씀) 제266차 대경장 겸 제157차 EDCF 기금위_최종.hwpx\n- PDF 첨부: 2. (보도자료) 제266차 대외경제장관회의.pdf\n- HWPX 첨부: 2. (보도자료) 제266차 대외경제장관회의.hwpx\n- PDF 첨부: [별첨] (모두말씀) 제266차 대경장 겸 제157차 EDCF 기금위_최종.pdf\n\n## 본문\n\n## 구윤철 부총리, 대외경제장관회의에서 대외경제 리스크 대응 및 전략적 대응체계 강화\n- 미 무역법 301조 조사개시 대응 전략 마련-\n- 민간재원 활용한 한국형 개발금융 추진방안 논의 -\n- 글로벌 통상질서 재편 대응 위한 통상협정 전략 점검 -\n- 중동전쟁 관련 주요국 대응사례 점검을 통한 시사점 검토 -\n\n구윤철 부총리 겸 재정경제부장관은 4.13일(월) 08:00 정부서울청사에서 제266차 대외경제장관회의를 주재하였다.\n\n* 참석자: 경제부총리(주재), 과기부, 농식품부, 산업부, 기후부, 국토부, 중기부, 기획처 등 관계부처 장차관\n\n이번 회의에서는 ➊ 무역법 301조 조사 대응경과 및 향후 대응계획, ➋ 한국형 개발금융 추진방안, ➌ 글로벌 통상질서 전환기 新 통상협정 추진 전략, ➍ 중동전쟁 주요국 대응사례 및 시사점 등 주요 대외경제 현안을 폭넓게 논의하였다.\n\n먼저, 최근 미국 정부가 과잉생산 및 강제노동 문제를 중심으로 무역법 301조 조사개시를 발표한 것과 관련하여 대응계획을 논의하였다. 정부는 민관합동 301조 대응 TF를 통해 업계 및 관계부처 의견을 수렴하고 우리 입장을 반영한 대응논리를 마련해 왔다. 과잉생산 관련 우리 설비 가동의 적정성과 한미 공급망 연계를 통한 상호 이익, 기술력 기반 수출 구조 등을 적극 설명하고, 강제노동과 관련하여서는 ILO 협약 준수, 한미 FTA 이행 등을 통한 엄정 대응을 토대로 우리 입장을 명확히 전달해 나가기로 하였다. 이번 조사는 우리 기업과 산업에 영향을 미칠 수 있는 사안으로, 한미간 기존 합의의 틀 내에서 우리 기업의 이익이 훼손되지 않도록 정부는 총력을 다할 계획이다.\n\n아울러 우리 경제의 글로벌사우스 신시장 진출 등을 지원하기 위한 한국형 개발금융 추진방안을 논의하였다. 그간 우리나라는 대외경제협력기금(EDCF) 등을 통해 협력국의 경제개발을 지원하고 우리 기업의 해외진출을 뒷받침해왔으나, ODA 재원만으로는 개도국 협력 수요에 충분히 대응하기 어려운 상황이다. 이에 따라, 타 선진국과 같이 민간재원을 활용하여 다양한 금융수단으로 개발 도상국 개발을 지원하는 개발금융 방식을 도입하고, 이를 글로벌사우스와의 전략적 협력수단으로 활용해 나갈 계획이다. 정부는 올해 범부처 TF 를 출범하여 개발금융 세부 추진체계를 수립하고, 해외 주요 개발금융 기관과 양・ 다자 협력을 통해 우리나라의 개발금융 수행 역량도 단계적으로 강화해 나갈 계획이다.\n\n한편, 글로벌 통상질서 전환기 통상협정 추진계획도 공유하였다. 최근 다자무역 규범의 약화와 주요국 간 경쟁 심화로 통상환경이 구조적으로 변화하는 가운데, 정부는 FTA 네트워크를 지속 확장하고 전략적으로 고도화해 나갈 필요가 있다고 평가하였다. 이에 따라, 신남방・중남미・아프리카 등 유망 지역 과의 협력을 확대하고, 디지털・공급망 등 신통상 분야를 중심으로 모듈형・단계적 협정 등 유연한 협상 전략을 추진할 계획이다.\n\n마지막으로 중동전쟁 관련 주요국 대응사례를 점검하였다. 주요국들은 중동전쟁 장기화에 따른 불확실성에 대응하여 ① 비상대응체계 구축, ② 에너지 가격 안정화, ③ 수급 안정화, ④ 국제협력 등을 추진하고 있는 것으로 나타났다. 특히 중동 의존도가 높은 아시아 국가 중심으로 연료가격 상한제 등 적극적인 에너지 가격· 수급 안정화 정책을 시행하고 있는 것으로 평가되었다. 우리나라도 비상대응체계를 구축하고 에너지 가격 및 수급 안정화 정책, 국제협력을 신속히 추진 중으로 앞으로도 주요국 동향을 면밀히 점검하며 필요한 대응 조치를 보완 해 나가기로 하였다.\n\n부총리는 “ 대외 여건의 불확실성이 확대되는 상황에서도 우리 경제는 견조한 수출 흐름을 유지하고 있다”고 평가하면서 “범정부가 원팀으로 대응하여 대외리스크를 안정적으로 관리하는 한편, 새로운 성장 기회를 적극 창출 해 나가겠다”고 밝혔다.\n\n## [ 총괄 ]\n\n## 담당 부서\n\n- 담당 부서 <대경장>: 대외경제국 대외경제총괄과 / 책임자 과장 최지영 / (044-215-7610)\n- 담당자: 사무관 / 우지완 woojw94@korea.kr\n\n## [ 제266차 대외경제장관회의 ]\n\n## 안건\n\n- ➊ 무역법 301조 조사 대응경과 및 향후 대응계획\n  - 담당: 산업통상부 미주통상과\n  - 연락: 구진경 과장 김태우 서기관 / 044-203-5650 044-203-5651\n- ➋ 개발금융 추진방안\n  - 담당: 재정경제부 개발금융총괄과\n  - 연락: 박정현 과장 김지현 사무관 / 044-215-8710 jhkim1229@korea.kr\n- ➌ 글로벌 통상질서 전환기 新통상협정 추진전략\n  - 담당: 산업통상부 통상협정정책기획과\n  - 연락: 박정미 과장 신서현 사무관 / 044-203-5740 044-203-5732\n- ➍ 중동전쟁 주요국 대응사례 및 시사점\n  - 담당: 재정경제부 대외경제총괄과\n  - 연락: 최지영 과장 이상민 사무관 / 044-215-7610 sangm25@korea.kr\n\n## 첨부파일\n\n- [별첨] (모두말씀) 제266차 대경장 겸 제157차 EDCF 기금위_최종.hwpx\n- 2. (보도자료) 제266차 대외경제장관회의.pdf\n- 2. (보도자료) 제266차 대외경제장관회의.hwpx\n- [별첨] (모두말씀) 제266차 대경장 겸 제157차 EDCF 기금위_최종.pdf\n",
      "readhim_markdown": "# 제266차 대외경제장관회의 겸 제157차 EDCF 기금운용위원회 모두발언(4.13일)\n\n### 지금부터 제266차 대외경제장관회의 겸 제157차 EDCF 기금운용위원회를 시작하겠습니다.\n\n1. 대외경제장관회의\n\n### 현재 우리나라를 둘러싼 대외환경은 보호무역 확산과 지정학적 긴장 등으로 전례없이 급변하고 있습니다.\n\n- 특히, 미국의 무역법 301조 조사개시, 중동의 지정학적 긴장 고조로 대외불확실성이 더욱 확대되고 있습니다.\n- 변화의 바람이 거셀때 누군가는 장벽을 쌓지만, 누군가는 풍차를 세운다’는 격언이 있습니다. 정부는 대외리스크 대응에 필요한 ‘장벽’을 쌓는 한편, 통상 전략과 개발금융 등 중장기 대응 기반인 ‘풍차’도 함께 마련해 나가겠습니다.\n[ 무역법 301조 조사 대응경과 및 향후 대응계획 ]\n\n### 먼저, 美무역법 301조 조사에 전략적으로 대응하겠습니다.\n\n- 정부는 미국 정부와의 긴밀한 소통과 협의를 지속하면서 우리 기업의 이익이 훼손되지 않도록 총력을 다하겠습니다.\n- 미측 지적과 달리 과잉생산은 우리 제조업 설비 가동률이 적정 수준이며, 우리 자본재 수출이 미 제조업 부흥에 기여하는 점 등을 적극 설명하겠습니다.\n- 아울러, 우리나라는 강제노동 금지에 대한 ILO 협약 및 국내법 등 확고한 기반을 두고 있으며, 이에 대해 엄정히 대응하고 있음을 전달하고자 합니다.\n[ 개발금융 추진방안 ]\n\n### 다음으로 우리 경제의 글로벌사우스 신시장 진출을 뒷받침하기 위해 “한국형 개발금융”을 추진하겠습니다.\n\n- 그간 EDCF 등 유상원조를 통해 개도국의 경제개발과우리 기업들의 해외 진출을 지원해 왔으나, ODA 예산을 지속 확대하기는 어려운 상황입니다.\n- 이에 우리나라도 다른 선진국들과 같이 시장 차입, 투자 펀드 등 민간재원을 동원하여대출, 보증·보험, 지분투자 등 다양한 금융수단으로 개도국 개발을 지원하는 “새로운 개발금융”을 도입하고자 합니다.\n\n### 올해 상반기중 개발금융 추진을 위한 범부처 T/F를 출범하여 세부 추진체계를 수립할 계획이며,\n\n- 이와 동시에 해외 개발금융기관들과의 협력 등을 통해 개발금융 수행 역량을 보강해 나가겠습니다.\n[ 글로벌 통상질서 전환기 新통상협정 추진전략 ]\n\n### 정부는 통상현안 대응에 그치지 않고, FTA 네트워크를 확장하여 수출 성장세를 뒷받침하겠습니다.\n\n- 보호무역주의 강화 속에서도 우리 수출은 지난 3월 861억 3천만 달러로 전년동월 대비 48.3% 증가한 사상 최대 실적을 기록한 바 있습니다.\n- 지난 20년간 구축해온 FTA 네트워크가 우리 경제의 든든한 버팀목이 되어준 결과입니다.\n- 향후 FTA 지도를 신남방·중남미·아프리카 등 신흥시장으로 촘촘히 확대하여 글로벌 공급망을 다변화하겠습니다.\n- 전략적으로도 FTA 모델을 유연화하여 디지털·그린·공급망 등 모듈형 통상협정, 산업·투자연계형 협정 등 통상 전략을 고도화해 나가겠습니다.\n[ 중동전쟁 주요국 대응사례 및 시사점]\n\n### 중동전쟁 관련 주요국 대응을 해외파견 재경관 등을 통해 점검하였습니다.\n\n- 대다수의 국가들이\n\n    1. 비상대응체계를 구축하고,\n    2. 가격 안정화 정책,\n    3. 수급 안정화 정책,\n    4. 국제협력 등을 추진하고 있으며,\n  - 특히, 중동 의존도가 높은 아시아 국가 중심으로 적극적인 에너지 가격 및 수급 안정화 정책을 시행*하고 있습니다.\n    > 예: (日) 보조금 연계하여 휘발유 가격 상한, (中) 휘발유·경유 가격 인상폭 조정 등\n\n  - 우리나라도 선제적으로 가격·수급·보조금·국제협력 등 다양한 정책을 신속히 추진중에 있습니다. 앞으로도 주요국 동향을 면밀히 점검하며 필요한 대응을 보완해 나가겠습니다.\n*\n\n    1. (대응체계) 대통령 주재 ‘비상경제점검회의’ 개최②(가격 안정화) 석유 최고가격제 시행, 유류세 인하, 취약계층 지원 등③(수급 안정화) 수입 다변화, 비축유 방출, 공공부문 차량 2부제 등 에너지 절약④(국제협력) 美 재무부 협의를 통해 러시아산 나프타 수입, 주요국과 양·다자협력 지속\n    2. EDCF 기금운용위원회\n\n### 제157차 대외경제협력기금(EDCF) 운용위원회 안건은 2026~2028년간 EDCF 중기운용방향입니다.\n\n[ ’26~’28년 EDCF 중기운용방향 ]\n\n### 최근의 대내외 ODA 환경을 살펴보면\n\n- 주요 공여국들은 ODA와 경제‧안보 이익간 연계를 강화하면서, 전반적으로는 개발재원 공급을 축소하는 모습을 보이고 있습니다.\n- 한편, 대내적으로는 다양한 ODA 수단의 통합적 운용과 국민에 대한 신뢰 확보 등 ODA의 질적 내실화에 대한 요구가 높아지고 있습니다.\n\n### 이러한 대내외 ODA 환경을 종합적으로 고려하여, 정부는 향후 3년간 EDCF 운용방향을 마련하였습니다.\n\n- ‘국민의 신뢰를 바탕으로, 우리나라와 수원국의 상생발전에 대한 기여’를 비전으로 수립하고\n- 향후 3년간 연평균 약 3조원 규모의 신규사업 승인이라는 목표를 설정하였습니다.\n\n### 그리고 이러한 비전과 목표를 달성하기 위하여 4대 분야에 걸친 중점 추진과제를 마련하였습니다.\n\n➊ 먼저, 우리 산업과 기업이 강점을 보유하고 개도국의 지원수요도 높은 AI‧디지털, 문화, 그린, 공급망을 중점분야로 설정하여 집중 지원할 계획입니다.\n➋ 다음으로, 작년 12월에 발표한 투명성‧공정성 제고방안을 본격 시행하여 국민의 신뢰를 공고히 하고 사업 품질을 지속적으로 높여나가겠습니다.\n➌ 이와 더불어, 여러 무상 ODA 수단과 EDCF를 통합적으로 기획‧운용하여, 개발효과성을 극대화하겠습니다.\n➍ 마지막으로, 장기지연 사업에 대한 승인 취소 등으로 EDCF 사업 구조조정을 추진하고\n- 전략수출금융기금을 활용한 이익 환류 체계를 마련하여 국내의 수출 생태계 강화에도 동참하겠습니다.\n\n### 감사합니다.\n",
      "opendataloader_markdown": "|보도자료|\n|---|\n\n\n보도시점 2026. 4. 13.(월) 9:30 배포 2026. 4. 13.(월) 8:30\n\n|구윤철 부총리, 대외경제장관회의에서 대외경제 리스크 대응 및 전략적 대응체계 강화<br><br>- 미 무역법 301조 조사개시 대응 전략 마련-<br><br>- 민간재원 활용한 한국형 개발금융 추진방안 논의-<br>- 글로벌 통상질서 재편 대응 위한 통상협정 전략 점검 -<br><br><br>- 중동전쟁 관련 주요국 대응사례 점검을 통한 시사점 검토 -|\n|---|\n\n\n## 구윤철 부총리 겸 재정경제부장관은 4.13일(월) 08:00 정부서울청사에서 제266차 대외경제장관회의를 주재하였다.\n\n* 참석자: 경제부총리(주재), 과기부, 농식품부, 산업부, 기후부, 국토부, 중기부, 기획처 등 관계부처 장차관\n\n## 이번 회의에서는 ➊무역법 301조 조사 대응경과 및 향후 대응계획, ➋한국형 개발금융 추진방안, ➌글로벌 통상질서 전환기 新 통상협정 추진 전략, ➍중동전쟁 주요국 대응사례 및 시사점 등 주요 대외경제 현안을 폭넓게 논의하였다.\n\n먼저, 최근 미국 정부가 과잉생산 및 강제노동 문제를 중심으로 무역법 301조 조사개시를 발표한 것과 관련하여 대응계획을 논의하였다. 정부는 민관합동 301조 대응 TF를 통해 업계 및 관계부처 의견을 수렴하고 우리 입장을 반영한 대응논리를 마련해 왔다. 과잉생산 관련 우리 설비 가동의 적정성과 한미 공급망 연계를 통한 상호 이익, 기술력 기반 수출 구조 등을 적극 설명하고, 강제노동과 관련하여서는 ILO 협약 준수, 한미 FTA 이행 등을 통한 엄정 대응을 토대로 우리 입장을 명확히 전달해 나가기로 하였다. 이번 조사는 우리 기업과 산업에 영향을 미칠 수 있는 사안으로, 한미간 기존 합의의 틀 내에서 우리 기업의 이익이 훼손되지 않도록 정부는 총력을 다할 계획이다.\n\n아울러 우리 경제의 글로벌사우스 신시장 진출 등을 지원하기 위한 한국형 개발금융 추진방안을 논의하였다. 그간 우리나라는 대외경제협력기금 (EDCF) 등을 통해 협력국의 경제개발을 지원하고 우리 기업의 해외진출을 뒷받침해왔으나, ODA 재원만으로는 개도국 협력 수요에 충분히 대응하기 어려운 상황이다. 이에 따라, 타 선진국과 같이 민간재원을 활용하여 다양한 금융수단으로 개발도상국 개발을 지원하는 개발금융 방식을 도입하고, 이를 글로벌사우스와의 전략적 협력수단으로 활용해 나갈 계획이다. 정부는 올해 범부처 TF를 출범하여 개발금융 세부 추진체계를 수립하고, 해외 주요 개발금융 기관과 양・다자 협력을 통해 우리나라의 개발금융 수행 역량도 단계적으로 강화해 나갈 계획이다.\n\n## 한편, 글로벌 통상질서 전환기 통상협정 추진계획도 공유하였다. 최근 다자무역 규범의 약화와 주요국 간 경쟁 심화로 통상환경이 구조적으로 변화하는 가운데, 정부는 FTA 네트워크를 지속 확장하고 전략적으로 고도화해 나갈 필요가 있다고 평가하였다. 이에 따라, 신남방・중남미・아프리카 등 유망 지역과의 협력을 확대하고, 디지털・공급망 등 신통상 분야를 중심으로 모듈형・단계적 협정 등 유연한 협상 전략을 추진할 계획이다.\n\n## 마지막으로 중동전쟁 관련 주요국 대응사례를 점검하였다. 주요국들은 중동전쟁 장기화에 따른 불확실성에 대응하여 ①비상대응체계 구축, ②에너지 가격 안정화, ③수급 안정화, ④국제협력 등을 추진하고 있는 것으로 나타났다. 특히 중동 의존도가 높은 아시아 국가 중심으로 연료가격 상한제 등 적극적인 에너지 가격·수급 안정화 정책을 시행하고 있는 것으로 평가되었다. 우리나라도 비상대응체계를 구축하고 에너지 가격 및 수급 안정화 정책, 국제협력을 신속히 추진 중으로 앞으로도 주요국 동향을 면밀히 점검하며 필요한 대응 조치를 보완해 나가기로 하였다.\n\n부총리는 “대외여건의 불확실성이 확대되는 상황에서도 우리 경제는 견조한 수출 흐름을 유지하고 있다”고 평가하면서 “범정부가 원팀으로 대응하여 대외리스크를 안정적으로 관리하는 한편, 새로운 성장 기회를 적극 창출해 나가겠다”고 밝혔다.\n\n## [ 총괄 ]\n\n|담당 부서 <대경장>|대외경제국 대외경제총괄과|책임자|과 장 최지영 (044-215-7610)|\n|---|---|---|---|\n| | |담당자|사무관 우지완 woojw94@korea.kr|\n\n\n## [ 제266차 대외경제장관회의 ]\n\n|안건<br><br>| |담당자<br><br>|연락처<br><br>|\n|---|---|---|---|\n|➊ 무역법 301조 조사 대응경과 및 향후 대응계획|산업통상부 미주통상과|구진경 과장 김태우 서기관|044-203-5650<br>044-203-5651<br>|\n|➋ 개발금융 추진방안|재정경제부 개발금융총괄과|박정현 과장 김지현 사무관|044-215-8710 jhkim1229@korea.kr|\n|➌ 글로벌 통상질서 전환기 新통상 협정 추진전략|산업통상부 통상협정정책기획과|박정미 과장 신서현 사무관|044-203-5740 044-203-5732|\n|➍ 중동전쟁 주요국 대응사례 및 시사점|재정경제부 대외경제총괄과|최지영 과장 이상민 사무관|044-215-7610 sangm25@korea.kr|\n\n\n"
    }
  ],
  "source_notes": [
    {
      "label": "OpenDataLoader Benchmark 문서",
      "url": "https://opendataloader.org/docs/benchmark",
      "description": "NID, TEDS, MHS 정의와 공식 벤치 재현 방법의 기준 문서."
    },
    {
      "label": "opendataloader-bench 저장소",
      "url": "https://github.com/opendataloader-project/opendataloader-bench",
      "description": "이번 비교에서 사용한 evaluator의 원본 저장소. 지표 구현과 출력 형식의 출처입니다."
    },
    {
      "label": "GovPress_PDF_MD",
      "url": "https://github.com/wavelen-jw/GovPress_PDF_MD",
      "description": "정책브리핑 ground truth 생성, 읽힘/ODL 실행, 정적 리포트 생성 코드를 추가한 실행 리포지토리."
    }
  ],
  "metric_help": [
    {
      "label": "Overall",
      "description": "문서별 NID, TEDS, MHS의 평균입니다. 표가 없는 문서는 있는 지표만으로 평균합니다.",
      "source_url": "https://opendataloader.org/docs/benchmark"
    },
    {
      "label": "NID",
      "description": "본문 읽기 순서와 텍스트 보존 정도를 보는 지표입니다.",
      "source_url": "https://opendataloader.org/docs/benchmark"
    },
    {
      "label": "TEDS",
      "description": "표 구조와 셀 내용을 함께 비교하는 지표입니다.",
      "source_url": "https://opendataloader.org/docs/benchmark"
    },
    {
      "label": "MHS",
      "description": "제목 계층과 섹션 구조 보존 정도를 보는 지표입니다.",
      "source_url": "https://opendataloader.org/docs/benchmark"
    }
  ],
  "failure_notes": [
    {
      "news_item_id": "156754218",
      "title": "조선왕실 여성의 의례, 뮤지컬로 되살아나다",
      "error": "SystemExit('docViewer iframe src not found')"
    }
  ]
};
