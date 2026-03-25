@echo off
setlocal

cd /d %~dp0

if not exist .venv-build (
    py -3.10 -m venv .venv-build
)

call .venv-build\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller opendataloader-pdf

pyinstaller --noconfirm GovPress_PDF_MD.spec

if exist dist\GovPress_PDF_MD\runtime rmdir /s /q dist\GovPress_PDF_MD\runtime
if exist dist\GovPress_PDF_MD\licenses rmdir /s /q dist\GovPress_PDF_MD\licenses
python -m venv dist\GovPress_PDF_MD\runtime\python
call dist\GovPress_PDF_MD\runtime\python\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install opendataloader-pdf

mkdir dist\GovPress_PDF_MD\licenses
copy /y licenses\THIRD_PARTY_NOTICES.txt dist\GovPress_PDF_MD\licenses\THIRD_PARTY_NOTICES.txt >nul
copy /y licenses\README.md dist\GovPress_PDF_MD\licenses\README.txt >nul

for %%F in (
    ".venv-build\Lib\site-packages\opendataloader_pdf-2.0.2.dist-info\METADATA"
    "dist\GovPress_PDF_MD\runtime\python\Lib\site-packages\opendataloader_pdf-2.0.2.dist-info\METADATA"
) do (
    if exist %%~F copy /y %%~F dist\GovPress_PDF_MD\licenses\opendataloader-pdf-METADATA.txt >nul
)

if "%JAVA_HOME%"=="" (
    echo ERROR: JAVA_HOME is not set.
    echo Set JAVA_HOME to a Java 11+ installation before running this script.
    exit /b 1
)

if exist dist\GovPress_PDF_MD\runtime\java rmdir /s /q dist\GovPress_PDF_MD\runtime\java
xcopy /e /i /y "%JAVA_HOME%" "dist\GovPress_PDF_MD\runtime\java" >nul

if exist "%JAVA_HOME%\legal" xcopy /e /i /y "%JAVA_HOME%\legal" "dist\GovPress_PDF_MD\licenses\java-legal" >nul
if exist "%JAVA_HOME%\NOTICE" copy /y "%JAVA_HOME%\NOTICE" "dist\GovPress_PDF_MD\licenses\java-NOTICE.txt" >nul
if exist "%JAVA_HOME%\LICENSE" copy /y "%JAVA_HOME%\LICENSE" "dist\GovPress_PDF_MD\licenses\java-LICENSE.txt" >nul

where ISCC >nul 2>nul
if %ERRORLEVEL%==0 (
    ISCC installer\GovPress_PDF_MD.iss
)

echo.
echo Build complete.
echo Output: %CD%\dist\GovPress_PDF_MD\GovPress_PDF_MD.exe
if exist dist_installer\GovPress_PDF_MD_Setup.exe echo Installer: %CD%\dist_installer\GovPress_PDF_MD_Setup.exe
endlocal
