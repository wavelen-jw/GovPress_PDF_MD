from __future__ import annotations

import runpy
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


if __name__ == "__main__":
    runpy.run_path(str(REPO_ROOT / "scripts" / "openclaw_ops.py"), run_name="__main__")
