# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_dir = Path.cwd()
icon_path = project_dir / "assets" / "icons" / "govpress.ico"
version_info_path = project_dir / "windows_version_info.txt"
datas = [
    (str(project_dir / "assets" / "styles" / "preview.css"), "assets/styles"),
    (str(icon_path), "assets/icons"),
]
datas += collect_data_files("opendataloader_pdf")
hiddenimports = collect_submodules("opendataloader_pdf")


a = Analysis(
    ["app.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
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
    strip=False,
    upx=True,
    upx_exclude=[],
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
