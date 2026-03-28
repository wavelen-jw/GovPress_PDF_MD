# Packaging

## Windows 빌드

PyInstaller 빌드는 아래 스크립트를 사용합니다.

```bat
packaging\build_windows.bat
```

이 스크립트는 다음을 수행합니다.

- `.venv-build` 생성
- `requirements.txt` 설치
- `pyinstaller`, `opendataloader-pdf` 설치
- 아이콘 생성
- PyInstaller 빌드
- Inno Setup(`ISCC`)가 있으면 설치 파일 생성

## Nuitka 빌드

```bat
packaging\build_windows_nuitka.bat
```

## 패키징 자산 위치

- PyInstaller spec: [packaging/pyinstaller/GovPress_PDF_MD.spec](/home/wavel/GovPress_PDF_MD/packaging/pyinstaller/GovPress_PDF_MD.spec)
- 버전 정보: [packaging/pyinstaller/windows_version_info.txt](/home/wavel/GovPress_PDF_MD/packaging/pyinstaller/windows_version_info.txt)
- Inno Setup: [packaging/inno/GovPress_PDF_MD.iss](/home/wavel/GovPress_PDF_MD/packaging/inno/GovPress_PDF_MD.iss)

## 빌드 결과

- 포터블 실행 파일: `dist\GovPress_PDF_MD.exe`
- 설치 파일: `dist_installer\GovPress_PDF_MD_Setup.exe`
- Nuitka 빌드: `dist_nuitka\app.dist\app.exe`
