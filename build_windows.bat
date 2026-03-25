@echo off
setlocal

cd /d %~dp0

rem --------------------------------------------------
rem 0) Find Python
rem --------------------------------------------------
py -3.14 -c "import sys; print(sys.version)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=py -3.14"
    goto :python_found
)

py -3.13 -c "import sys; print(sys.version)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=py -3.13"
    goto :python_found
)

py -3.12 -c "import sys; print(sys.version)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=py -3.12"
    goto :python_found
)

py -3.11 -c "import sys; print(sys.version)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=py -3.11"
    goto :python_found
)

py -3.10 -c "import sys; print(sys.version)" >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=py -3.10"
    goto :python_found
)

echo ERROR: No suitable Python runtime found.
echo Install Python 3.10 or later and ensure py launcher is available.
exit /b 1

:python_found
echo Using Python launcher: %PY_CMD%

rem --------------------------------------------------
rem 1) Build virtual environment
rem --------------------------------------------------
if not exist .venv-build (
    %PY_CMD% -m venv .venv-build
    if errorlevel 1 (
        echo ERROR: Failed to create build virtual environment.
        exit /b 1
    )
)

if not exist .venv-build\Scripts\python.exe (
    echo ERROR: Build virtual environment is invalid.
    exit /b 1
)

call .venv-build\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate build virtual environment.
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip in build environment.
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements.txt.
    exit /b 1
)

python -m pip install pyinstaller opendataloader-pdf
if errorlevel 1 (
    echo ERROR: Failed to install pyinstaller or opendataloader-pdf.
    exit /b 1
)

python -m PyInstaller --noconfirm GovPress_PDF_MD.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

rem --------------------------------------------------
rem 2) Runtime Python environment
rem --------------------------------------------------
if exist dist\GovPress_PDF_MD\runtime rmdir /s /q dist\GovPress_PDF_MD\runtime

.venv-build\Scripts\python.exe -m venv dist\GovPress_PDF_MD\runtime\python
if errorlevel 1 (
    echo ERROR: Failed to create runtime Python environment.
    exit /b 1
)

if not exist dist\GovPress_PDF_MD\runtime\python\Scripts\python.exe (
    echo ERROR: Runtime Python environment is invalid.
    exit /b 1
)

call dist\GovPress_PDF_MD\runtime\python\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate runtime Python environment.
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip in runtime environment.
    exit /b 1
)

python -m pip install opendataloader-pdf
if errorlevel 1 (
    echo ERROR: Failed to install opendataloader-pdf in runtime environment.
    exit /b 1
)

rem --------------------------------------------------
rem 3) Java runtime copy
rem --------------------------------------------------
if "%JAVA_HOME%"=="" (
    echo ERROR: JAVA_HOME is not set.
    echo Set JAVA_HOME to a Java 11+ installation before running this script.
    exit /b 1
)

if not exist "%JAVA_HOME%\bin\java.exe" (
    echo ERROR: JAVA_HOME does not point to a valid Java installation.
    echo Current JAVA_HOME: %JAVA_HOME%
    exit /b 1
)

if exist dist\GovPress_PDF_MD\runtime\java rmdir /s /q dist\GovPress_PDF_MD\runtime\java
xcopy /e /i /y "%JAVA_HOME%" "dist\GovPress_PDF_MD\runtime\java" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy Java runtime.
    exit /b 1
)

rem --------------------------------------------------
rem 4) Optional installer build
rem --------------------------------------------------
where ISCC >nul 2>nul
if %ERRORLEVEL%==0 (
    ISCC installer\GovPress_PDF_MD.iss
    if errorlevel 1 (
        echo ERROR: Inno Setup build failed.
        exit /b 1
    )
)

echo.
echo Build complete.
echo Output: %CD%\dist\GovPress_PDF_MD\GovPress_PDF_MD.exe
if exist dist_installer\GovPress_PDF_MD_Setup.exe echo Installer: %CD%\dist_installer\GovPress_PDF_MD_Setup.exe

endlocal
