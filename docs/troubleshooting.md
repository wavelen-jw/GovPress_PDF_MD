# Troubleshooting

## `java`를 찾지 못하는 경우

- Java 11 이상 설치 여부를 확인합니다.
- 환경 변수 `PATH`에 Java 실행 파일 경로가 포함되어 있는지 확인합니다.

## `opendataloader-pdf`를 찾지 못하는 경우

- `pip install -U opendataloader-pdf`를 다시 실행합니다.
- 가상환경을 사용 중이면 동일한 가상환경에서 앱을 실행합니다.

## 빌드가 실패하는 경우

- `packaging\build_windows.bat`를 실행한 쉘에서 Python 버전이 3.10 이상인지 확인합니다.
- Inno Setup을 쓰는 경우 `ISCC`가 PATH에 있는지 확인합니다.

## 변환 결과가 비어 있는 경우

- PDF가 스캔본이거나 암호화되어 있는지 확인합니다.
- `opendataloader-pdf` 출력 디렉터리에 `.json` 또는 `.md`가 생성되는지 확인합니다.
