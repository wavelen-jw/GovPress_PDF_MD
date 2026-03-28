"""
Win32 native file dialogs via ctypes (Windows only).

pywebview의 create_file_dialog는 pywebview JS-API 스레드에서 호출할 때
WinForms UI 스레드 마샬링이 데드락되는 문제가 있다.
여기서는 COMDLG32.GetOpenFileNameW / GetSaveFileNameW 를 독립적인
STA(Single-Threaded Apartment) 스레드에서 직접 호출하여 이 문제를 우회한다.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import sys
import threading

_log = logging.getLogger("GovPress_PDF_MD.dialog")


def open_file_dialog(
    title: str = "파일 선택",
    filter_str: str = "모든 파일\0*.*\0",
    initial_dir: str | None = None,
) -> str | None:
    """네이티브 파일 열기 대화창을 표시한다. 선택한 경로 또는 None 반환."""
    return _show_ofn(
        title=title,
        filter_str=filter_str,
        initial_dir=initial_dir,
        save=False,
    )


def save_file_dialog(
    title: str = "파일 저장",
    filter_str: str = "모든 파일\0*.*\0",
    initial_dir: str | None = None,
    default_name: str = "",
    default_ext: str = "",
) -> str | None:
    """네이티브 파일 저장 대화창을 표시한다. 선택한 경로 또는 None 반환."""
    return _show_ofn(
        title=title,
        filter_str=filter_str,
        initial_dir=initial_dir,
        save=True,
        default_name=default_name,
        default_ext=default_ext,
    )


# ── 내부 구현 ──────────────────────────────────────────────────────────────

class _OPENFILENAMEW(ctypes.Structure):
    """OPENFILENAMEW 구조체 (CommDlg.h)."""
    _fields_ = [
        ("lStructSize",       ctypes.c_uint32),
        ("hwndOwner",         ctypes.c_void_p),
        ("hInstance",         ctypes.c_void_p),
        ("lpstrFilter",       ctypes.c_wchar_p),
        ("lpstrCustomFilter", ctypes.c_void_p),
        ("nMaxCustFilter",    ctypes.c_uint32),
        ("nFilterIndex",      ctypes.c_uint32),
        ("lpstrFile",         ctypes.c_wchar_p),
        ("nMaxFile",          ctypes.c_uint32),
        ("lpstrFileTitle",    ctypes.c_void_p),
        ("nMaxFileTitle",     ctypes.c_uint32),
        ("lpstrInitialDir",   ctypes.c_wchar_p),
        ("lpstrTitle",        ctypes.c_wchar_p),
        ("Flags",             ctypes.c_uint32),
        ("nFileOffset",       ctypes.c_uint16),
        ("nFileExtension",    ctypes.c_uint16),
        ("lpstrDefExt",       ctypes.c_wchar_p),
        ("lCustData",         ctypes.c_void_p),
        ("lpfnHook",          ctypes.c_void_p),
        ("lpTemplateName",    ctypes.c_wchar_p),
        ("pvReserved",        ctypes.c_void_p),
        ("dwReserved",        ctypes.c_uint32),
        ("FlagsEx",           ctypes.c_uint32),
    ]


_OFN_HIDEREADONLY     = 0x00000004
_OFN_NOCHANGEDIR      = 0x00000008
_OFN_OVERWRITEPROMPT  = 0x00000002
_OFN_FILEMUSTEXIST    = 0x00001000
_OFN_PATHMUSTEXIST    = 0x00000800
_OFN_NOREADONLYRETURN = 0x00008000
_COINIT_APARTMENTTHREADED = 2


def _show_ofn(
    title: str,
    filter_str: str,
    initial_dir: str | None,
    save: bool,
    default_name: str = "",
    default_ext: str = "",
) -> str | None:
    """STA 스레드에서 GetOpenFileNameW / GetSaveFileNameW 를 호출한다."""
    if sys.platform != "win32":
        _log.warning("_show_ofn: non-Windows platform, skipping")
        return None

    _log.info("_show_ofn: start (save=%s, title=%r)", save, title)

    result: list[str | None] = [None]
    done = threading.Event()

    def _sta_worker() -> None:
        _log.info("_sta_worker: thread started (tid=%d)", threading.get_ident())
        # CoInitializeEx를 호출하지 않음:
        # GetOpenFileNameW 는 내부적으로 COM을 초기화하며,
        # 외부에서 COINIT_APARTMENTTHREADED로 먼저 초기화하면
        # 내부 apartment 충돌로 hang이 발생할 수 있음.
        try:
            buf = ctypes.create_unicode_buffer(32768)
            if default_name:
                buf.value = default_name

            # hwndOwner: 현재 포어그라운드 창을 부모로 설정하여
            # 다이얼로그가 앱 창 뒤에 숨지 않도록 한다
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            _log.info("_sta_worker: hwndOwner=0x%X", hwnd or 0)

            ofn = _OPENFILENAMEW()
            ofn.lStructSize  = ctypes.sizeof(_OPENFILENAMEW)
            ofn.hwndOwner    = hwnd
            ofn.lpstrFilter  = filter_str
            ofn.nFilterIndex = 1
            ofn.lpstrFile    = ctypes.cast(buf, ctypes.c_wchar_p)
            ofn.nMaxFile     = 32768
            ofn.lpstrTitle   = title
            if initial_dir:
                ofn.lpstrInitialDir = initial_dir
            if default_ext:
                ofn.lpstrDefExt = default_ext

            if save:
                ofn.Flags = (
                    _OFN_PATHMUSTEXIST | _OFN_NOCHANGEDIR
                    | _OFN_OVERWRITEPROMPT | _OFN_NOREADONLYRETURN
                )
                fn = ctypes.windll.comdlg32.GetSaveFileNameW
            else:
                ofn.Flags = (
                    _OFN_FILEMUSTEXIST | _OFN_PATHMUSTEXIST
                    | _OFN_NOCHANGEDIR | _OFN_HIDEREADONLY
                )
                fn = ctypes.windll.comdlg32.GetOpenFileNameW

            _log.info("_sta_worker: calling %s", fn.__name__ if hasattr(fn, '__name__') else ('GetSaveFileNameW' if save else 'GetOpenFileNameW'))
            ok = fn(ctypes.byref(ofn))
            _log.info("_sta_worker: dialog returned ok=%d", ok)

            if ok:
                result[0] = buf.value
                _log.info("_sta_worker: selected path=%r", result[0])
            else:
                err = ctypes.windll.comdlg32.CommDlgExtendedError()
                _log.info("_sta_worker: cancelled or error, CommDlgExtendedError=0x%X", err)

        except Exception as exc:
            _log.error("_sta_worker: exception: %s", exc, exc_info=True)
        finally:
            done.set()
            _log.info("_sta_worker: done.set() called")

    t = threading.Thread(target=_sta_worker, daemon=True, name="win32-dialog")
    t.start()
    _log.info("_show_ofn: waiting for dialog thread (timeout=120s)")
    completed = done.wait(timeout=120)
    _log.info("_show_ofn: wait returned completed=%s, result=%s", completed, result[0])
    return result[0]
