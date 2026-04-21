from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server.app.core.notify import send_telegram


def build_message(*, run_url: str, run_id: str, sha: str, branch: str, repo: str, results: dict[str, str]) -> str:
    lines = ["[Deploy Alert]", f"repo: {repo}", f"branch: {branch}", f"sha: {sha}", f"run: {run_id}", f"url: {run_url}"]
    failed = []
    for label, result in results.items():
        lines.append(f"{label}: {result}")
        if result == "failure":
            failed.append(label)
    if failed:
        lines.insert(1, "status: failed")
        lines.insert(2, "failed_targets: " + ", ".join(failed))
    else:
        lines.insert(1, "status: unknown")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Send deploy failure alert to Telegram")
    parser.add_argument("--run-url", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--results-json", required=True, help="JSON object of deploy target -> job result")
    args = parser.parse_args()

    results = json.loads(args.results_json)
    if not isinstance(results, dict):
        raise SystemExit("results-json must decode to an object")
    normalized_results = {str(key): str(value) for key, value in results.items()}
    if not any(value == "failure" for value in normalized_results.values()):
        return 0
    message = build_message(
        run_url=args.run_url,
        run_id=args.run_id,
        sha=args.sha,
        branch=args.branch,
        repo=args.repo,
        results=normalized_results,
    )
    send_telegram(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
