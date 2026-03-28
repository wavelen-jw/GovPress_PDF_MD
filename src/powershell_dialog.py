"""
Windows 네이티브 파일 다이얼로그 — PowerShell 서브프로세스 방식.

pywebview의 create_file_dialog 및 Win32 ctypes 직접 호출은 모두
PyInstaller one-file 빌드에서 WinForms/COM 스레드 문제로 실패한다.
여기서는 powershell.exe 서브프로세스를 통해 System.Windows.Forms 다이얼로그를
완전히 독립적인 프로세스에서 실행하여 이 문제를 우회한다.

결과 파일명은 UTF-8 Base64로 인코딩하여 Korean/Unicode 경로를 안전하게 처리한다.
"""
from __future__ import annotations

import base64
import logging
import subprocess
import sys

_log = logging.getLogger("GovPress_PDF_MD.dialog")

# PowerShell 실행 가능 여부 캐시 (None = 미확인, bool = 확인됨)
_ps_available: bool | None = None


def _check_ps() -> bool:
    """powershell.exe 사용 가능 여부 확인."""
    global _ps_available
    if _ps_available is not None:
        return _ps_available
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", "exit 0"],
            capture_output=True, timeout=5
        )
        _ps_available = (r.returncode == 0)
    except Exception:
        _ps_available = False
    _log.info("powershell.exe 사용 가능: %s", _ps_available)
    return _ps_available


def open_file_dialog(
    title: str = "파일 선택",
    file_types: str = "PDF Files (*.pdf)|*.pdf|All Files (*.*)|*.*",
) -> str | None:
    """네이티브 파일 열기 다이얼로그. 선택된 경로 또는 None 반환."""
    if sys.platform != "win32":
        return None
    if not _check_ps():
        _log.warning("PowerShell 미사용 가능 — 다이얼로그 생략")
        return None

    # Base64로 title과 filter를 전달하여 특수문자/한글 처리
    title_b64 = base64.b64encode(title.encode("utf-8")).decode("ascii")
    filter_b64 = base64.b64encode(file_types.encode("utf-8")).decode("ascii")

    ps_script = f"""
$t   = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{title_b64}'))
$flt = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{filter_b64}'))
Add-Type -AssemblyName System.Windows.Forms | Out-Null
$d = New-Object System.Windows.Forms.OpenFileDialog
$d.Title   = $t
$d.Filter  = $flt
$d.TopMost = $true
$null = $d.ShowDialog()
if ($d.FileName) {{
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($d.FileName)
    [Convert]::ToBase64String($bytes)
}}
""".strip()

    return _run_ps(ps_script)


def save_file_dialog(
    title: str = "파일 저장",
    file_types: str = "Markdown Files (*.md)|*.md|All Files (*.*)|*.*",
    default_name: str = "",
    default_ext: str = "",
) -> str | None:
    """네이티브 파일 저장 다이얼로그. 선택된 경로 또는 None 반환."""
    if sys.platform != "win32":
        return None
    if not _check_ps():
        _log.warning("PowerShell 미사용 가능 — 다이얼로그 생략")
        return None

    title_b64 = base64.b64encode(title.encode("utf-8")).decode("ascii")
    filter_b64 = base64.b64encode(file_types.encode("utf-8")).decode("ascii")
    name_b64 = base64.b64encode(default_name.encode("utf-8")).decode("ascii")
    ext_b64 = base64.b64encode(default_ext.encode("utf-8")).decode("ascii")

    ps_script = f"""
$t   = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{title_b64}'))
$flt = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{filter_b64}'))
$fn  = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{name_b64}'))
$ext = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{ext_b64}'))
Add-Type -AssemblyName System.Windows.Forms | Out-Null
$d = New-Object System.Windows.Forms.SaveFileDialog
$d.Title      = $t
$d.Filter     = $flt
$d.FileName   = $fn
$d.DefaultExt = $ext
$d.TopMost    = $true
$null = $d.ShowDialog()
if ($d.FileName) {{
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($d.FileName)
    [Convert]::ToBase64String($bytes)
}}
""".strip()

    return _run_ps(ps_script)


# ── 내부 구현 ──────────────────────────────────────────────────────────────


def _run_ps(script: str) -> str | None:
    """PowerShell 스크립트를 실행하고 결과 경로(Base64 디코딩)를 반환한다."""
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive",
             "-WindowStyle", "Hidden", "-Command", script],
            capture_output=True,
            timeout=120,
        )
        raw = result.stdout.strip()
        if not raw:
            _log.info("PowerShell 다이얼로그: 취소됨 또는 빈 결과")
            return None
        # Base64 디코딩
        path = base64.b64decode(raw).decode("utf-8")
        _log.info("PowerShell 다이얼로그: 선택됨 → %s", path)
        return path
    except subprocess.TimeoutExpired:
        _log.error("PowerShell 다이얼로그 120초 타임아웃")
        return None
    except Exception as exc:
        _log.error("PowerShell 다이얼로그 오류: %s", exc, exc_info=True)
        return None
