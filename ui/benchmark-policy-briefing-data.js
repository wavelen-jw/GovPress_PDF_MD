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
      "ground_truth_markdown": "# 1937년과 2020년 경주 월성 수습 비편들(돌비석 조각) 원래 하나였다\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 국가유산청\n- 게시 시각: 04/13/2026 11:10:18\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754214&call_from=openData\n- PDF 첨부: 0413 1937년과 2020년 경주 월성 수습 비편들(돌비석 조각) 원래 하나였다(붙임1,2).pdf\n- HWPX 첨부: 0413 1937년과 2020년 경주 월성 수습 비편들(돌비석 조각) 원래 하나였다(본문).hwpx\n\n## 본문\n\n## 보도 자료\n\n국가유산청 국립문화유산연구원 국립경주문화유산연구소(소장 임승경, 이하 ‘경주연구소’) 와 국립경주박물관(관장 윤상덕, 이하 ‘경주박물관’) 은 오는 4월 13일(월) 오전 10시 경주박물관 신라 천년보고에서 ‘경주 월성 서편 수습 비편’을 특별 공개한다.\n\n* 비편(碑片): 돌비석(석비, 石碑) 의 조각\n\n이번 특별 공개에서는 경주연구소가 지난 2020 년 경주 월성 주변에서 수습한 비편 한 점과 경주박물관이 일제강점기부터 소장하고 있는 비편 한 점이 하나로 합쳐진 모습으로 공개된다.\n\n경주연구소가 수습한 비편은 가로 16.47cm, 세로 16.58cm, 두께 13.67cm, 무게는 약 2.7kg 으로, 지난 2020 년 경주 계림 ~ 월성 진입로 구간 발굴조사 과정에서 출토되었다.\n\n경주박물관 소장 비편은 가로 13.62cm, 세로 11.13cm, 두께 9.75cm, 무게는 약 1.23kg 이다. 이 비편 뒷면에는 ‘昭和 (소화) 一二 (일이) 六 (육) 二七 (이칠) 西月城址 (서월성지) 崔 (최) ’라는 글자가 쓰여 있는데, 이는 1 937 년 6월 27 일에 서월성지에서 수습된 유물이며, 수습한 사람은 당시 조선 총독부박물관 경주분관 직원이던 최남주(崔南柱) 였다는 점을 기록해둔 것으로 추정된다.\n\n경주연구소는 수습한 비편을 정밀 조사하는 과정에서 경주박물관이 소장하고 있는 비편과의 관련성이 제기되어, 두 기관이 비편의 석재(石材) 산지(産地) 를 공동 분석한 결과, 두 비편 모두 경주 남산 알칼리 화강암으로 제작 되었음이 밝혀졌으며, 이후 3 차원(3D) 스캔 결과물을 검토하는 과정에서 두 비편의 한쪽 면이 서로 합쳐지는 것으로 드러나 다시금 주목받게되었다.\n\n특히 비편에 사용된 서체는 신라비에서 일반적으로 사용된해서(楷書) 가 아니라 예서(隸書) 라는 점이 눈길을 끈다.\n\n* 해서(楷書): 글씨를 흘려 쓰지 않고 정자로 반듯하게 쓴 글자체. 즉, 점 찍기, 가로 긋기, 내려 긋기, 갈고리, 오른쪽 삐침, 왼쪽 길게 삐침, 왼쪽 짧게 삐침, 파임 등 8 개의 방식으로 획을 그은 서체\n\n* 예서(隸書): 도장 등에 흔히 쓰이는 획이 복잡한 전서(篆書) 의 획을 간략화하여 일상적으로 편리하게 쓸 수 있도록 바꾼 서체\n\n이와 관련하여 지난 2월 11 일에는 신라사 및 고구려사, 금석문, 서체 등 다양한 방면의 전문 연구자들이 모여 비편의 실물을 살펴보고 향후 연구 방향을 모색하는 ‘월성 서편 수습 비편 전문가 포럼’이 개최된 바 있다. 당시 포럼에서는 고구려사 연구자들을 중심으로 비편의 서체가 광개토왕릉비의 것과 유사하다는 점에 주목하여 비석의 건립 주체를 고구려로 보는 견해가 제기되기도했다. 즉 예서로 쓰인 신라 금석문이 현재까지 발견되지 않은데 반해, 광개토왕릉비의 서체가 예서이며, 비편에서 확실하게 판독되는 글자인 백(白), 천(天), 공(貢), 불(不), 도(渡) 가 광개토왕릉비에도 확인된다는 점이이 견해의 주요한 근거이다.\n\n반면 신라사 연구자들은 서체만으로 건립 주체를 확정하기에는 서체가 특정 시대나 국가 혹은 지역의 전유물로 볼 수는 없다는 점을 지적하며, 이들 비편이 경주 월성에서 출토되었다는 점에서 비의 건립과 그 내용 작성 주체를 신라인들로 고려해 볼 수도 있다는 견해를 제기하는 등 활발한 논의가 있었다.\n\n전문가들의 다양한 의견과는 별개로 이번 특별 공개는 1937 년과 2020 년이라는 수습 시간 차이에도 불구하고 서로 떨어져 있던 비편이 합쳐진 모습으로 공개된다는 점만으로도 관람객들의 흥미를 끌 것으로 기대된다.\n\n이번 특별 공개는 오는 8월 17 일까지 진행되며, 일 ~ 금요일까지는 오전 10시 ~ 오후 6 시까지, 토요일은 오전 10시 ~ 오후 8 시까지 누구나 관람 가능하다. 전시와 단행본에 대한 문의는 국립경주문화유산연구소로 전화(☎054-778-8714)하면 된다.\n\n한편, 경주연구소는 이번 특집 공개 이후 4월 중으로 비편의 조사 경위, 3 차원(3D) 스캔 기술을 활용한 디지털 탁본 자료, 광개토왕릉비의 서체와 비교 자료 등 관련 정보가 수록된 ‘경주 월성 서편 수습 비편’ 기초조사 자료집과 ‘월성 서편 수습 비편 전문가 포럼’에서의 논의 내용이 수록된 단행본을 국가유산 지식이음(https://portal.nrich.go.kr) 을 통해 전자 파일(PDF) 형태로 공개 배포한다.\n\n국립문화유산연구원 국립경주문화유산연구소는 앞으로도 유관기관 및 학계 와의 협력을 통해 출토 유물에 대한 융·복합 연구를 지속적으로 추진하고, 그 성과를 국민과 함께 공유하는 열린 적극행정을 이어갈 예정이다.\n\n## 붙임 1. 사진 자료.\n\n2. 비편 판독문. 끝.\n\n## 담당 부서\n\n- 담당 부서: 국립문화유산연구원 / 책임자 연구관 이희준 / (054-778-8701)\n- 국립경주문화유산연구소: 담당자 / 주무관 전경효\n\n## 첨부파일\n\n- 0413 1937년과 2020년 경주 월성 수습 비편들(돌비석 조각) 원래 하나였다(붙임1,2).pdf\n- 0413 1937년과 2020년 경주 월성 수습 비편들(돌비석 조각) 원래 하나였다(본문).hwpx\n",
      "readhim_markdown": "# 1937년과 2020년 경주 월성 수습 비편들(돌비석 조각) 원래 하나였다\n\n국가유산청 보도자료 /\n보도시점: 배포 즉시 보도 가능 / 배포 2026. 4. 13.(월) 09:00\n\n> - 국립경주문화유산연구소 수습 비편과 국립경주박물관 소장 비편 합친 모습 첫 공개(4.13.~8.17.)… 비편 기초조사 자료집 등도 온라인 공개\n---\n국가유산청 국립문화유산연구원 국립경주문화유산연구소(소장 임승경, 이하 ‘경주연구소’)와 국립경주박물관(관장 윤상덕, 이하 ‘경주박물관’)은 오는 4월 13일(월) 오전 10시 경주박물관 신라 천년보고에서 ‘경주 월성 서편 수습 비편’을 특별 공개한다.\n> * 비편(碑片) : 돌비석(석비,石碑)의 조각\n\n이번 특별 공개에서는 경주연구소가 지난 2020년 경주 월성 주변에서 수습한 비편 한 점과 경주박물관이 일제강점기부터 소장하고 있는 비편 한 점이 하나로 합쳐진 모습으로 공개된다.\n\n경주연구소가 수습한 비편은 가로 16.47cm, 세로 16.58cm, 두께 13.67cm, 무게는 약 2.7kg으로, 지난 2020년 경주 계림~월성 진입로 구간 발굴조사 과정에서 출토되었다.\n\n경주박물관 소장 비편은 가로 13.62cm, 세로 11.13cm, 두께 9.75cm, 무게는 약 1.23kg이다. 이 비편 뒷면에는 ‘昭和(소화) 一二(일이) 六(육) 二七(이칠) 西月城址(서월성지) 崔(최)’라는 글자가 쓰여 있는데, 이는 1937년 6월 27일에 서월성지에서 수습된 유물이며, 수습한 사람은 당시 조선총독부박물관 경주분관 직원이던 최남주(崔南柱)였다는 점을 기록해둔 것으로 추정된다.\n\n경주연구소는 수습한 비편을 정밀 조사하는 과정에서 경주박물관이 소장하고 있는 비편과의 관련성이 제기되어, 두 기관이 비편의 석재(石材) 산지(産地)를 공동 분석한 결과, 두 비편 모두 경주 남산 알칼리 화강암으로 제작되었음이 밝혀졌으며, 이후 3차원(3D) 스캔 결과물을 검토하는 과정에서 두 비편의 한쪽 면이 서로 합쳐지는 것으로 드러나 다시금 주목받게 되었다.\n\n특히 비편에 사용된 서체는 신라비에서 일반적으로 사용된 해서(楷書)가 아니라 예서(隸書)라는 점이 눈길을 끈다.\n> * 해서(楷書) : 글씨를 흘려 쓰지 않고 정자로 반듯하게 쓴 글자체. 즉, 점 찍기, 가로 긋기, 내려 긋기, 갈고리, 오른쪽 삐침, 왼쪽 길게 삐침, 왼쪽 짧게 삐침, 파임 등 8개의 방식으로 획을 그은 서체\n> * 예서(隸書) : 도장 등에 흔히 쓰이는 획이 복잡한 전서(篆書)의 획을 간략화하여 일상적으로 편리하게 쓸 수 있도록 바꾼 서체\n\n이와 관련하여 지난 2월 11일에는 신라사 및 고구려사, 금석문, 서체 등 다양한 방면의 전문 연구자들이 모여 비편의 실물을 살펴보고 향후 연구 방향을 모색하는 ‘월성 서편 수습 비편 전문가 포럼’이 개최된 바 있다. 당시 포럼에서는 고구려사 연구자들을 중심으로 비편의 서체가 광개토왕릉비의 것과 유사하다는 점에 주목하여 비석의 건립 주체를 고구려로 보는 견해가 제기되기도 했다. 즉 예서로 쓰인 신라 금석문이 현재까지 발견되지 않은데 반해, 광개토왕릉비의 서체가 예서이며, 비편에서 확실하게 판독되는 글자인 백(白), 천(天), 공(貢), 불(不), 도(渡)가 광개토왕릉비에도 확인된다는 점이 이 견해의 주요한 근거이다.\n\n반면 신라사 연구자들은 서체만으로 건립 주체를 확정하기에는 서체가 특정 시대나 국가 혹은 지역의 전유물로 볼 수는 없다는 점을 지적하며, 이들 비편이 경주 월성에서 출토되었다는 점에서 비의 건립과 그 내용 작성 주체를 신라인들로 고려해 볼 수도 있다는 견해를 제기하는 등 활발한 논의가 있었다.\n\n전문가들의 다양한 의견과는 별개로 이번 특별 공개는 1937년과 2020년이라는 수습 시간 차이에도 불구하고 서로 떨어져 있던 비편이 합쳐진 모습으로 공개된다는 점만으로도 관람객들의 흥미를 끌 것으로 기대된다.\n\n이번 특별 공개는 오는 8월 17일까지 진행되며, 일~금요일까지는 오전 10시~오후 6시까지, 토요일은 오전 10시~오후 8시까지 누구나 관람 가능하다. 전시와 단행본에 대한 문의는 국립경주문화유산연구소로 전화(☎054-778-8714)하면 된다.\n\n한편, 경주연구소는 이번 특집 공개 이후 4월 중으로 비편의 조사 경위, 3차원(3D) 스캔 기술을 활용한 디지털 탁본 자료, 광개토왕릉비의 서체와 비교 자료 등 관련 정보가 수록된 ‘경주 월성 서편 수습 비편’ 기초조사 자료집과 ‘월성 서편 수습 비편 전문가 포럼’에서의 논의 내용이 수록된 단행본을 국가유산 지식이음(https://portal.nrich.go.kr)을 통해 전자 파일(PDF) 형태로 공개 배포한다.\n\n국립문화유산연구원 국립경주문화유산연구소는 앞으로도 유관기관 및 학계와의 협력을 통해 출토 유물에 대한 융·복합 연구를 지속적으로 추진하고, 그 성과를 국민과 함께 공유하는 열린 적극행정을 이어갈 예정이다.\n\n### 붙임\n\n1. 사진 자료.\n\n2. 비편 판독문. 끝.\n\n---\n\n### 담당부서\n\n- 국립문화유산연구원 국립경주문화유산연구소 책임자: 연구관 이희준 (054-778-8701)\n- 국립문화유산연구원 국립경주문화유산연구소 담당자: 주무관 전경효 (054-778-8714)\n",
      "opendataloader_markdown": "- (붙임 1)\n\n\n|사 진 자 료|\n|---|\n\n\n특별 공개 포스터\n\n비편 전체 사진(왼쪽 : 경주연구소 수습 비편, 오른쪽 : 경주박물관 소장 비편)\n\n경주연구소 소장 비편 앞면 경주박물관 소장 비편 뒷면\n\n경주연구소 소장 비편 수습 배수로 경주연구소 소장 비편 수습 당시 모습\n\n3차원(3D) 스캔 명암 효과 3차원(3D) 스캔 손탁본 효과\n\n기초조사 자료집 표지 전문가 포럼 단행본 표지\n\n- (붙임 2)\n\n\n|비편 판독문|\n|---|\n\n\n|Ⅵ|Ⅴ|Ⅳ|Ⅲ|Ⅱ|Ⅰ| |\n|---|---|---|---|---|---|---|\n| |□1)|跪(?)| | | |1|\n|□2)|貢|白|稱|存|萬(?)|2|\n|渡|不|天|天(?)3)|社(?)|□|3|\n|4)|□5)| | | | |4|\n\n\n- 1) 광개토대왕릉비의 樂 아랫부분과 비슷함.\n- 2) 再 또는 冉\n- 3) 于? 앞의 부분은 정동(晶洞 : 암석이나 광맥 따위의 속이 빈 곳의 내면(內面)에 결정(結晶)을 이룬 광물이 빽빽하게 덮여 있 는 것)\n- 4) 일부 획만 남아 있음.\n- 5) 門을 부수로 하는 글자.\n\n\n"
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
      "ground_truth_markdown": "# 국립문화유산연구원-한국고고학회 『2026 여름 발굴캠프』 참가자 모집\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 국가유산청\n- 게시 시각: 04/13/2026 11:06:51\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754212&call_from=openData\n- PDF 첨부: 0413 국립문화유산연구원-한국고고학회 『2026 여름 발굴캠프』 참가자 모집(붙임).pdf\n- HWPX 첨부: 0413 국립문화유산연구원-한국고고학회 『2026 여름 발굴캠프』 참가자 모집(본문).hwpx\n\n## 본문\n\n## 보도 자료\n\n국가유산청 국립문화유산연구원(원장 임종덕) 은 한국고고학회(회장 최종택) 와 고고학 전공 대학생들에게 현장 발굴조사 경험을 제공하기 위해 『 2026 여름 발굴캠프』를 7월 1일(수) 부터 16일(목) 까지 총 12 일간 운영하며, 참가자 모집을 4월 13일(월) 부터 24일(금) 까지 실시한다.\n\n여름 발굴캠프는 전국 대학의 고고학 관련학과 3·4 학년 재학생(5 학기 이상 등록자) 을 대상으로하며, 한국고고학회의 심사를 거쳐 총 50 명을 선발한다. 참가를 희망하는 학생은 한국고고학회 누리집(http://kras.or.kr) 에서 지원서를 내려받아 작성한 뒤 교수 추천서, 재학증명서와 함께 전자우편(kras1976@naver.com) 으로 제출하면 된다. 선발 결과는 5월 14 일과 15일 중 개별 연락을 통해 안내될 예정이다.\n\n발굴캠프의 첫 3일(7.1.~7.3.) 은 KT 대전인재개발원(대전 서구) 에서 입교식과 공통교육 과정을 운영하며, 발굴조사 방법론, GIS 를 활용한 고고자료 분석, 수중고고학 등 이론 교육과 진로 교육이 이루어진다.\n\n이후 7월 6일(월) 부터 15일(수) 까지는 전국 7 개 지방연구소가 주관하는 12 개 주요 유적에서 측량, 유구 조사, 토층 기록, 사진 촬영 및 실측, 유물 수습과 정리, 디지털기록 등 발굴조사의 전 과정을 체험할 수 있는 현장실습이 진행된다. 올해 실습 유적은 경주 대릉원 일원, 경주 월성, 경주 동궁과 월지, 부여 부소산성, 부여 관북리 유적, 공주 무령왕릉과 왕릉원, 김해 봉황동 유적, 함안 가야리 유적, 나주 복암리 유적, 충주 장미산성, 서울 풍납토성 창의마을, 장수 합미성까지 총 12 곳이다.\n\n발굴캠프 마지막 날인 7월 16일(목) 에는 국립문화유산연구원(대전 유성구) 에서 수료식을 진행하며, 모든 발굴캠프 일정에 참여한 참가자들에게는 국립문화유산연구원장과 한국고고학회장 명의의 수료증이 발급된다.\n\n국가유산청 국립문화유산연구원과 한국고고학회는 앞으로도 긴밀한 협력을 통해 ‘여름 발굴캠프’를 고도화하여 전문성을 갖춘 문화유산 조사연구 인력 양성에 기여해 나갈 것이다.\n\n## 붙임 1. 홍보물(포스터) 1부.\n\n2. 사진 자료. 끝.\n\n## 담당 부서\n\n- 담당 부서: 국립문화유산연구원 / 책임자 연구관 김혜정 / (042-860-9171)\n- 고고연구실: 담당자 / 연구사전세원\n\n## 첨부파일\n\n- 0413 국립문화유산연구원-한국고고학회 『2026 여름 발굴캠프』 참가자 모집(붙임).pdf\n- 0413 국립문화유산연구원-한국고고학회 『2026 여름 발굴캠프』 참가자 모집(본문).hwpx\n",
      "readhim_markdown": "# 국립문화유산연구원-한국고고학회 『2026 여름 발굴캠프』 참가자 모집\n\n국가유산청 보도자료 /\n보도시점: 배포 즉시 보도 가능 / 배포 2026. 4. 13.(월) 09:00\n\n> - 전국 12개 주요 유적에서 12일간 현장 발굴 실습 기회 제공 (7.1.~7.16.)… 대학생 참가자 모집(4.13.~4.24.)\n---\n국가유산청 국립문화유산연구원(원장 임종덕)은 한국고고학회(회장 최종택)와 고고학 전공 대학생들에게 현장 발굴조사 경험을 제공하기 위해 『2026 여름 발굴캠프』를 7월 1일(수)부터 16일(목)까지 총 12일간 운영하며, 참가자 모집을 4월 13일(월)부터 24일(금)까지 실시한다.\n\n여름 발굴캠프는 전국 대학의 고고학 관련학과 3·4학년 재학생(5학기 이상 등록자)을 대상으로 하며, 한국고고학회의 심사를 거쳐 총 50명을 선발한다. 참가를 희망하는 학생은 한국고고학회 누리집(http://kras.or.kr)에서 지원서를 내려받아 작성한 뒤 교수 추천서, 재학증명서와 함께 전자우편(kras1976@naver.com)으로 제출하면 된다. 선발 결과는 5월 14일과 15일 중 개별 연락을 통해 안내될 예정이다.\n\n발굴캠프의 첫 3일(7.1.~7.3.)은 KT대전인재개발원(대전 서구)에서 입교식과 공통교육 과정을 운영하며, 발굴조사 방법론, GIS를 활용한 고고자료 분석, 수중고고학 등 이론 교육과 진로 교육이 이루어진다.\n\n이후 7월 6일(월)부터 15일(수)까지는 전국 7개 지방연구소가 주관하는 12개 주요 유적에서 측량, 유구 조사, 토층 기록, 사진 촬영 및 실측, 유물 수습과 정리, 디지털기록 등 발굴조사의 전 과정을 체험할 수 있는 현장실습이 진행된다. 올해 실습 유적은 경주 대릉원 일원, 경주 월성, 경주 동궁과 월지, 부여 부소산성, 부여 관북리 유적, 공주 무령왕릉과 왕릉원, 김해 봉황동 유적, 함안 가야리 유적, 나주 복암리 유적, 충주 장미산성, 서울 풍납토성 창의마을, 장수 합미성까지 총 12곳이다.\n\n발굴캠프 마지막 날인 7월 16일(목)에는 국립문화유산연구원(대전 유성구)에서 수료식을 진행하며, 모든 발굴캠프 일정에 참여한 참가자들에게는 국립문화유산연구원장과 한국고고학회장 명의의 수료증이 발급된다.\n\n국가유산청 국립문화유산연구원과 한국고고학회는 앞으로도 긴밀한 협력을 통해 ‘여름 발굴캠프’를 고도화하여 전문성을 갖춘 문화유산 조사연구 인력 양성에 기여해 나갈 것이다.\n\n### 붙임\n\n1. 홍보물(포스터) 1부.\n\n2. 사진 자료. 끝.\n\n---\n\n### 담당부서\n\n- 국립문화유산연구원 고고연구실 책임자: 연구관 김혜정 (042-860-9171)\n- 국립문화유산연구원 고고연구실 담당자: 연구사 전세원 (042-860-9180)\n",
      "opendataloader_markdown": "- (붙임 1)\n\n\n|홍 보 물|\n|---|\n\n\n< 2026년 여름 발굴캠프 참가자 모집 포스터 >\n\n- (붙임 2)\n\n\n|사 진 자 료|\n|---|\n\n\n< 2025년 여름 발굴캠프 현장(‘25.7.2. 나주 복암리 유적) >\n\n< 2025년 여름 발굴캠프 현장(’25.7.2. 함안 가야리 유적) >\n\n"
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
      "ground_truth_markdown": "# 회화와 유적으로 만나는 '조선 왕실의 말(馬)'\n\n- 출처: 대한민국 정책브리핑 보도자료\n- 부처: 국가유산청\n- 게시 시각: 04/13/2026 11:13:08\n- 기사 URL: https://www.korea.kr/briefing/pressReleaseView.do?newsId=156754216&call_from=openData\n- PDF 첨부: 0413 회화와 유적으로 만나는 ‘조선 왕실의 말(馬)’(붙임1,2).pdf\n- HWPX 첨부: 0413 회화와 유적으로 만나는 ‘조선 왕실의 말(馬)’(본문).hwpx\n\n## 본문\n\n## 보도 자료\n\n국가유산청 국립문화유산연구원 국립서울문화유산연구소(소장 최인화)는 오는 4월 28일 오후 2 시부터 4 시까지 덕수궁 중명전(서울 중구)에서 2026년 「도란도란 궁궐 가회(嘉會)」 상반기 시민강좌를 개최한다.\n\n* 가회(嘉會): 기쁘고 즐거운 모임 혹은 좋은 만남\n\n올해로 세 번째를 맞이하는 「도란도란 궁궐 가회」는 조선시대 궁궐과 관련된 다양한 이야기를 시민들과 함께 나누는 프로그램으로 이번 상반기 주제는 ‘붉은 말의 해’인 병오년을 맞아 ‘조선 왕실의 말(馬) ’과 관련된 강좌를 기획하였다.\n\n오는 4월 28일 열리는 상반기 강좌에서는 ▲ ‘조선시대 회화로 본 왕실의 말(馬) ’을 주제로 한 서윤정(명지대학교) 교수의 강의와 ▲ ‘서울 수송동 사복시 발굴’과 관련된 오경택(수도문물연구원) 원장의 강의가 진행된다.\n\n* 사복시(司僕寺): 조선시대 왕이 타는 말, 수레 및 마구, 목축에 관한 일을 담당한 관청.\n\n2023년 서울 수송동(146-2번지) 발굴조사에서 사복시의 건물지, 마장기초 등이 확인됨\n\n상반기 시민강좌에 참여를 희망하는 국민은 4월 14일 오전 10 시부터 20일 오후 5 시까지 국립서울문화유산연구소 누리집(www.nrich.go.kr/seoul/index.do) 을 통해 선착순 40 명까지 신청할 수 있다. 궁금한 사항은 전화(☎ 02-739-6913) 로 문의하면 된다.\n\n국립문화유산연구원 국립서울문화유산연구소는 앞으로도 국가유산을 함께 누리고 가치를 공유할 수 있는 적극행정을 지속할 계획이다.\n\n## 붙임 1. 홍보물.\n\n2. 사진 자료. 끝.\n\n## 담당 부서\n\n- 담당 부서: 국립문화유산연구원 / 책임자 연구관 도의철 / (02-739-6911)\n- 국립서울문화유산연구소: 담당자 / 연구사 정여선\n\n## 첨부파일\n\n- 0413 회화와 유적으로 만나는 ‘조선 왕실의 말(馬)’(붙임1,2).pdf\n- 0413 회화와 유적으로 만나는 ‘조선 왕실의 말(馬)’(본문).hwpx\n",
      "readhim_markdown": "# 회화와 유적으로 만나는 ‘조선 왕실의 말(馬)’\n\n국가유산청 보도자료 /\n보도시점: 배포 즉시 보도 가능 / 배포 2026. 4. 13.(월) 09:00\n\n> - 국립서울문화유산연구소, 「도란도란 궁궐 가회(嘉會)」 시민강좌 개최(4.28, 덕수궁 중명전)… 선착순 신청(4.14.~4.20.)\n---\n국가유산청 국립문화유산연구원 국립서울문화유산연구소(소장 최인화)는 오는 4월 28일 오후 2시부터 4시까지 덕수궁 중명전(서울 중구)에서 2026년 「도란도란 궁궐 가회(嘉會)」 상반기 시민강좌를 개최한다.\n> * 가회(嘉會) : 기쁘고 즐거운 모임 혹은 좋은 만남\n\n올해로 세 번째를 맞이하는 「도란도란 궁궐 가회」는 조선시대 궁궐과 관련된 다양한 이야기를 시민들과 함께 나누는 프로그램으로 이번 상반기 주제는 ‘붉은 말의 해’인 병오년을 맞아 ‘조선 왕실의 말(馬)’과 관련된 강좌를 기획하였다.\n\n오는 4월 28일 열리는 상반기 강좌에서는 ▲ ‘조선시대 회화로 본 왕실의 말(馬)’을 주제로 한 서윤정(명지대학교) 교수의 강의와 ▲ ‘서울 수송동 사복시 발굴’과 관련된 오경택(수도문물연구원) 원장의 강의가 진행된다.\n> * 사복시(司僕寺) : 조선시대 왕이 타는 말, 수레 및 마구, 목축에 관한 일을 담당한 관청.\n\n2023년 서울 수송동(146-2번지) 발굴조사에서 사복시의 건물지, 마장기초 등이 확인됨\n상반기 시민강좌에 참여를 희망하는 국민은 4월 14일 오전 10시부터 20일 오후 5시까지 국립서울문화유산연구소 누리집(www.nrich.go.kr/seoul/index.do)을 통해 선착순 40명까지 신청할 수 있다. 궁금한 사항은 전화(☎ 02-739-6913)로 문의하면 된다.\n\n국립문화유산연구원 국립서울문화유산연구소는 앞으로도 국가유산을 함께 누리고 가치를 공유할 수 있는 적극행정을 지속할 계획이다.\n\n### 붙임\n\n1. 홍보물.\n\n2. 사진 자료. 끝.\n\n---\n\n### 담당부서\n\n- 국립문화유산연구원 국립서울문화유산연구소 책임자: 연구관 도의철 (02-739-6911)\n- 국립문화유산연구원 국립서울문화유산연구소 담당자: 연구사 정여선 (02-739-6913)\n",
      "opendataloader_markdown": "- (붙임 1)\n\n\n|홍 보 물|\n|---|\n\n\n<웹포스터>\n\n- (붙임 2)\n\n\n|사진자료|\n|---|\n\n\n- < 2024년 하반기 시민강좌 모습 (‘24.9.25.) >\n\n- < 2025년 상반기 시민강좌 모습 (‘25.4.30.) >\n\n\n"
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
