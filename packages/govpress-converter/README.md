# govpress-converter

## 설치

```bash
pip install govpress-converter
```

이 디렉터리는 공개 서비스 repo가 기대하는 **패키지 인터페이스 계약**만 제공합니다.
실제 운영용 변환 엔진 구현과 QC 자동화는 별도 비공개 저장소/패키지인 `gov-md-converter`에서 관리합니다.
즉 이 repo는 소비자 역할만 하고, 변환 규칙/회귀샘플/QC 로직의 source of truth는 private 엔진 repo입니다.

## 사용법

```python
from govpress_converter import convert_hwpx, convert_pdf

# HWPX → Markdown
md = convert_hwpx("문서.hwpx")
md = convert_hwpx("문서.hwpx", table_mode="html")

# PDF → Markdown
md = convert_pdf("문서.pdf")
md = convert_pdf("문서.pdf", timeout=120)

print(md)
```

## 라이선스

MIT
