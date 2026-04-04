from __future__ import annotations

from difflib import SequenceMatcher
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.converter import convert_pdf_to_markdown
from src.hwpx_converter import convert_hwpx


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _find_neighbor(problem_dir: Path, prefix: str, suffix: str) -> Path | None:
    candidates = sorted(
        path
        for path in problem_dir.iterdir()
        if path.is_file() and path.suffix.lower() == suffix and path.name.startswith(prefix)
    )
    return candidates[0] if candidates else None


def main() -> int:
    problem_dir = Path(__file__).with_name("problem")
    md_files = sorted(path for path in problem_dir.glob("*.md") if path.is_file())
    if not md_files:
        print("No golden markdown files found in tests/problem")
        return 0

    for md_path in md_files:
        prefix = md_path.name[:6]
        golden = md_path.read_text(encoding="utf-8")
        print(f"[{prefix}] {md_path.name}")

        hwpx_path = _find_neighbor(problem_dir, prefix, ".hwpx")
        if hwpx_path is not None:
            hwpx_md = convert_hwpx(hwpx_path, table_mode="text")
            print(f"  HWPX ratio: {_ratio(golden, hwpx_md):.4%}  {hwpx_path.name}")
        else:
            print("  HWPX ratio: missing input")

        pdf_path = _find_neighbor(problem_dir, prefix, ".pdf")
        if pdf_path is not None:
            pdf_md = convert_pdf_to_markdown(pdf_path)
            print(f"  PDF  ratio: {_ratio(golden, pdf_md):.4%}  {pdf_path.name}")
        else:
            print("  PDF  ratio: missing input")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
