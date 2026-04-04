# govpress-converter

한국 정부 문서(HWPX, PDF)를 Markdown으로 변환하는 Python 라이브러리입니다.

## 설치

```bash
pip install govpress-converter
```

PDF 변환을 사용하려면 **Java 11 이상**이 필요합니다.

## 사용법

```python
from govpress_converter import convert_hwpx, convert_pdf

# HWPX → Markdown (Java 불필요, 순수 Python)
md = convert_hwpx("문서.hwpx")

# PDF → Markdown (Java 11+ 필요)
md = convert_pdf("문서.pdf")
md = convert_pdf("문서.pdf", timeout=120)  # 타임아웃 지정 (초)

print(md)
```

## 특징

- **HWPX**: 표, 병합 셀, 보도자료 구조, 참고/부록 보존
- **PDF**: OpenDataLoader 기반 텍스트 추출 + 한국 공공문서 특화 후처리
- 보도자료(□ ○ 구조), 보고서(로마자 장 번호), 서비스 안내문 자동 감지
- 연락처 블록, 표, 요약표 Markdown 복원

## 요구사항

| 기능 | 요구사항 |
|------|----------|
| HWPX 변환 | Python 3.10+ |
| PDF 변환 | Python 3.10+ + Java 11+ |

## 라이선스

MIT
