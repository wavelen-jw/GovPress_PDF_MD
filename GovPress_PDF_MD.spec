# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

project_dir = Path.cwd()
icon_path = project_dir / "assets" / "icons" / "govpress.ico"
version_info_path = project_dir / "windows_version_info.txt"

datas = [
    (str(project_dir / "assets"), "assets"),
    (str(project_dir / "ui"), "ui"),
]
datas += collect_data_files("opendataloader_pdf")
datas += collect_data_files("webview")

hiddenimports = collect_submodules("opendataloader_pdf")
hiddenimports += collect_submodules("webview")
hiddenimports += ["clr_loader", "pythonnet"]

excludes = [
    # Unused stdlib
    "tkinter",
    "unittest",
    "test",
    "pydoc",
    "doctest",
    "pdb",
    "ensurepip",
    "lib2to3",
    "curses",
    "turtle",
    "turtledemo",
    "idlelib",
    "ftplib",
    "imaplib",
    "smtplib",
    "xmlrpc",
    # Entire PySide6 / Qt (no longer needed)
    "PySide6",
    "shiboken6",
    # Other heavy GUI/science libs that may be present
    "PyQt5",
    "PyQt6",
    "wx",
    "numpy",
    "scipy",
    "pandas",
    "matplotlib",
    "PIL",
    "cv2",
]

a = Analysis(
    ["app.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="GovPress_PDF_MD",
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=["vcruntime140.dll", "python3*.dll"],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
    version=str(version_info_path) if version_info_path.exists() else None,
)
