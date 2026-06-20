from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert HWP to HWPX with Hancom HWP SDK Python binding.")
    parser.add_argument("input")
    parser.add_argument("output")
    parser.add_argument("--sdk-dir", default=os.environ.get("HANCOM_SDK_DIR", ""))
    return parser.parse_args()


def add_sdk_path(sdk_dir: str) -> Path:
    if not sdk_dir:
        raise RuntimeError("--sdk-dir or HANCOM_SDK_DIR is required")
    root = Path(sdk_dir)
    candidates = [root, root / "Bin64", root / "Bin", root / "bin"]
    for candidate in candidates:
        if (candidate / "hwpsdk.py").exists():
            sys.path.insert(0, str(candidate))
            os.environ["PATH"] = str(candidate) + os.pathsep + os.environ.get("PATH", "")
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(str(candidate))
            return candidate
    raise RuntimeError(f"hwpsdk.py was not found under {sdk_dir}")


@contextmanager
def pushd(path: Path):
    prev = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev)


def initialize_app(hwpsdk, sdk_dir: Path):
    app = hwpsdk.Application
    for name in ("Initialize", "InitInstance"):
        fn = getattr(app, name, None)
        if callable(fn):
            with pushd(sdk_dir):
                rc = fn()
            if isinstance(rc, int) and rc <= 0:
                raise RuntimeError(f"Hancom SDK {name} failed: {rc}")
            return app
    raise RuntimeError("Hancom SDK Application has no Initialize/InitInstance method")


def finalize_app(app) -> None:
    for name in ("Finalize", "ExitInstance"):
        fn = getattr(app, name, None)
        if callable(fn):
            try:
                fn()
            except Exception:
                pass
            return


def convert_with_document_object(hwp_object, input_path: Path, output_path: Path) -> None:
    document = hwp_object.CreateDocument()
    try:
        open_fn = getattr(document, "Open", None)
        if not callable(open_fn):
            raise RuntimeError("Document.Open is not available")
        open_rc = open_fn(str(input_path))
        if isinstance(open_rc, int) and open_rc < 0:
            raise RuntimeError(f"Document.Open failed: {open_rc}")
        save_rc = document.SaveAs(str(output_path), "HWPX", "")
        if isinstance(save_rc, int) and save_rc < 0:
            raise RuntimeError(f"Document.SaveAs failed: {save_rc}")
    finally:
        release = getattr(hwp_object, "ReleaseDocument", None)
        if callable(release):
            try:
                release(document)
            except Exception:
                pass


def main() -> int:
    args = parse_args()
    sdk_dir = add_sdk_path(args.sdk_dir)

    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    import hwpsdk  # type: ignore

    app = initialize_app(hwpsdk, sdk_dir)
    hwp_object = None
    try:
        with pushd(sdk_dir):
            hwp_object = app.GetHwpObject()
        with tempfile.TemporaryDirectory(prefix="govpress-hwp2hwpx-") as tmp:
            tmp_input = Path(tmp) / input_path.name
            tmp_output = Path(tmp) / (input_path.stem + ".hwpx")
            shutil.copy2(input_path, tmp_input)
            convert_with_document_object(hwp_object, tmp_input, tmp_output)
            if not tmp_output.exists() or tmp_output.stat().st_size == 0:
                raise RuntimeError(f"Hancom SDK did not create output: {tmp_output}")
            shutil.copy2(tmp_output, output_path)
    finally:
        if hwp_object is not None:
            release = getattr(hwp_object, "Release", None)
            if callable(release):
                try:
                    release()
                except Exception:
                    pass
        finalize_app(app)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
