#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import subprocess
import sys
from pathlib import Path


def _hash_text(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, check=True, text=True, capture_output=True)
    return proc.stdout.strip()


def _local_payload(deploy_dir: Path, sample_rel: str) -> dict[str, str]:
    sample_path = deploy_dir / sample_rel
    script = """
import hashlib
import json
from pathlib import Path
from govpress_converter import convert_hwpx

sample_path = Path(__import__("sys").argv[1])
text = convert_hwpx(sample_path)
print(json.dumps({
  "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
  "length": len(text),
}, ensure_ascii=False))
"""
    out = _run([str(deploy_dir / ".venv/bin/python"), "-c", script, str(sample_path)])
    return json.loads(out)


def _remote_payload(alias: str, sample_rel: str) -> dict[str, str]:
    quoted_rel = shlex.quote(sample_rel)
    remote_script = """
set -euo pipefail
sample_rel={sample_rel}
docker exec govpress-api python - "$sample_rel" <<'PY'
import hashlib
import json
import sys
from pathlib import Path
from govpress_converter import convert_hwpx

sample_rel = sys.argv[1]
sample_path = Path("/app") / sample_rel
text = convert_hwpx(sample_path)
print(json.dumps({{
  "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
  "length": len(text),
}}, ensure_ascii=False))
PY
""".format(sample_rel=quoted_rel)
    out = _run(["ssh", alias, "bash", "-lc", remote_script])
    return json.loads(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare converter output hashes via serverV direct conversion and ssh")
    parser.add_argument("--deploy-dir", required=True)
    parser.add_argument("--sample-rel", required=True)
    args = parser.parse_args()

    deploy_dir = Path(args.deploy_dir).resolve()
    results = [
        {"name": "serverV", **_local_payload(deploy_dir, args.sample_rel)},
        {"name": "serverH", **_remote_payload("h", args.sample_rel)},
        {"name": "serverW", **_remote_payload("w", args.sample_rel)},
    ]
    text_hashes = {row["text_sha256"] for row in results}
    print(json.dumps({"sample_rel": args.sample_rel, "results": results}, ensure_ascii=False, indent=2))
    if len(text_hashes) != 1:
        raise SystemExit("converter output hash mismatch across servers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
