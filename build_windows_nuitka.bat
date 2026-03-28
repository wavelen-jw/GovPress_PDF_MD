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
if not exist .venv-nuitka (
    %PY_CMD% -m venv .venv-nuitka
    if errorlevel 1 (
        echo ERROR: Failed to create Nuitka build virtual environment.
        exit /b 1
    )
)

if not exist .venv-nuitka\Scripts\python.exe (
    echo ERROR: Nuitka build virtual environment is invalid.
    exit /b 1
)

call .venv-nuitka\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate Nuitka build virtual environment.
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 (
    echo ERROR: Failed to upgrade pip in Nuitka build environment.
    exit /b 1
)

python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements.txt.
    exit /b 1
)

python -m pip install nuitka ordered-set zstandard opendataloader-pdf
if errorlevel 1 (
    echo ERROR: Failed to install Nuitka build dependencies.
    exit /b 1
)

python tools\generate_icon.py
if errorlevel 1 (
    echo ERROR: Failed to generate application icon.
    exit /b 1
)

if exist build_nuitka rmdir /s /q build_nuitka
if exist dist_nuitka rmdir /s /q dist_nuitka

python -m nuitka ^
    --standalone ^
    --assume-yes-for-downloads ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --include-package=opendataloader_pdf ^
    --include-data-dir=assets=assets ^
    --output-dir=dist_nuitka ^
    --remove-output ^
    --company-name="wavelen-jw" ^
    --product-name="GovPress_PDF_MD" ^
    --file-description="Government press-release PDF to Markdown converter and editor." ^
    --file-version=1.0.0 ^
    --product-version=1.0.0 ^
    --copyright="Copyright (c) 2026 wavelen-jw" ^
    --trademarks="https://github.com/wavelen-jw/GovPress_PDF_MD" ^
    --windows-icon-from-ico=assets\icons\govpress.ico ^
    --nofollow-import-to=unittest,test,pydoc,doctest,pdb ^
    app.py
if errorlevel 1 (
    echo ERROR: Nuitka build failed.
    exit /b 1
)

where ISCC >nul 2>nul
if %ERRORLEVEL%==0 (
    set "APP_SOURCE=dist_nuitka\app.dist"
    if exist dist_nuitka\app.dist (
        ISCC /DAppSourceDir="%CD%\dist_nuitka\app.dist" /DOutputBaseFilename=GovPress_PDF_MD_Nuitka_Setup installer\GovPress_PDF_MD.iss
        if errorlevel 1 (
            echo ERROR: Inno Setup build failed.
            exit /b 1
        )
    )
)

echo.
echo Nuitka build complete.
echo Output: %CD%\dist_nuitka\app.dist\app.exe
if exist dist_installer\GovPress_PDF_MD_Nuitka_Setup.exe echo Installer: %CD%\dist_installer\GovPress_PDF_MD_Nuitka_Setup.exe

endlocal
