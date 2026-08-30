#!/usr/bin/env python3
"""Assemble and validate the static artifact served by Cloudflare Pages."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import tempfile


MAX_FILES = 20_000
MAX_FILE_BYTES = 25 * 1024 * 1024
ANALYTICS_SNIPPET = (
    "<!-- Cloudflare Web Analytics -->"
    "<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
    "data-cf-beacon='{\"token\": \"4ed8f833f5354d4d8b630744932bcf98\"}'></script>"
    "<!-- End Cloudflare Web Analytics -->"
)
APP_META = "\n".join(
    [
        '    <meta name="description" content="정부문서 HWP/HWPX를 Markdown으로 변환합니다" />',
        '    <meta property="og:site_name" content="읽힘" />',
        '    <meta property="og:type" content="website" />',
        '    <meta property="og:title" content="읽힘 — 정부문서를 사람도 AI도 읽게 한다" />',
        '    <meta property="og:description" content="정부문서 HWP/HWPX를 Markdown으로 변환합니다" />',
        '    <meta property="og:url" content="https://govpress.cloud/app/" />',
        '    <meta property="og:image" content="https://govpress.cloud/assets/social-preview.png" />',
        '    <meta property="og:image:width" content="1200" />',
        '    <meta property="og:image:height" content="630" />',
        '    <meta property="og:image:type" content="image/png" />',
        '    <meta name="twitter:card" content="summary_large_image" />',
        '    <meta name="twitter:title" content="읽힘 — 정부문서를 사람도 AI도 읽게 한다" />',
        '    <meta name="twitter:description" content="정부문서 HWP/HWPX를 Markdown으로 변환합니다" />',
        '    <meta name="twitter:image" content="https://govpress.cloud/assets/social-preview.png" />',
    ]
) + "\n"

STATIC_PAGES = (
    ("ui/benchmark-curated.html", "benchmark-curated/index.html"),
    ("ui/benchmark-curated-data.js", "benchmark-curated/benchmark-curated-data.js"),
    ("ui/benchmark-official.html", "benchmark-official/index.html"),
    ("ui/benchmark-official-data.js", "benchmark-official/benchmark-official-data.js"),
    ("ui/benchmark-policy-briefing.html", "benchmark-policy-briefing/index.html"),
    ("ui/benchmark-policy-briefing-data.js", "benchmark-policy-briefing/benchmark-policy-briefing-data.js"),
    ("ui/comparison-goilyuga.html", "comparison-goilyuga/index.html"),
    ("ui/comparison-goilyuga-data.js", "comparison-goilyuga/comparison-goilyuga-data.js"),
    ("ui/hardest-policy-briefings.html", "hardest-policy-briefings/index.html"),
    ("ui/hardest-policy-briefings-data.js", "hardest-policy-briefings/hardest-policy-briefings-data.js"),
)
COMPARISON_DOWNLOADS = (
    ("artifacts/policy_briefing_benchmark/corpus_latest100/hwpxs/156754095.hwpx", "156754095.hwpx"),
    ("artifacts/policy_briefing_benchmark/corpus_latest100/pdfs/156754095.pdf", "156754095.pdf"),
    ("artifacts/policy_briefing_benchmark/corpus_latest100/prediction/readhim/markdown/156754095.md", "readhim-156754095.md"),
    ("artifacts/policy_briefing_benchmark/corpus_latest100/prediction/opendataloader/markdown/156754095.md", "opendataloader-156754095.md"),
)


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise RuntimeError(f"required file is missing: {path}")
    return path


def copy_file(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(require_file(source), destination)


def inject_analytics(root: Path) -> None:
    for path in root.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if "static.cloudflareinsights.com/beacon.min.js" in text:
            continue
        if "</body>" in text:
            text = text.replace("</body>", f"{ANALYTICS_SNIPPET}\n</body>")
        else:
            text = f"{text}\n{ANALYTICS_SNIPPET}\n"
        path.write_text(text, encoding="utf-8")


def validate_artifact(root: Path) -> tuple[int, int, Path, int]:
    require_file(root / "index.html")
    require_file(root / "app" / "index.html")
    if not (root / "app" / "_expo").is_dir():
        raise RuntimeError("app/_expo bundle is missing")
    if (root / "_expo").exists():
        raise RuntimeError("raw top-level _expo directory must not remain")

    files = [path for path in root.rglob("*") if path.is_file()]
    if len(files) > MAX_FILES:
        raise RuntimeError(f"artifact has {len(files)} files; Pages limit is {MAX_FILES}")

    total = 0
    largest_path = root
    largest_size = 0
    for path in files:
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise RuntimeError(
                f"file exceeds Pages 25 MiB limit: {path.relative_to(root)} ({size} bytes)"
            )
        total += size
        if size > largest_size:
            largest_path = path
            largest_size = size
    return len(files), total, largest_path, largest_size


def assemble(source: Path, destination: Path) -> tuple[int, int, Path, int]:
    source = source.resolve()
    destination = destination.resolve()
    dist = source / "mobile" / "dist"
    require_file(source / "ui" / "landing.html")
    require_file(dist / "index.html")
    if not (dist / "_expo").is_dir():
        raise RuntimeError(f"built Expo bundle is missing: {dist / '_expo'}")
    if destination.exists():
        raise RuntimeError(f"destination already exists: {destination}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        shutil.copytree(dist, stage, dirs_exist_ok=True)
        app = stage / "app"
        app.mkdir()
        for name in ("_expo", "index.html", "metadata.json", "manifest.webmanifest", "sw.js", "icons"):
            path = stage / name
            if path.exists():
                shutil.move(str(path), app / name)

        app_index = require_file(app / "index.html")
        text = app_index.read_text(encoding="utf-8")
        text = text.replace('src="/GovPress_PDF_MD/app/_expo/', 'src="./_expo/')
        if 'property="og:title"' not in text:
            title = "    <title>읽힘 — 정부문서를 사람도 AI도 읽게 한다</title>\n"
            if title in text:
                text = text.replace(title, title + APP_META)
            else:
                text = text.replace("</head>", f"{APP_META}</head>")
        app_index.write_text(text, encoding="utf-8")

        copy_file(source / "ui" / "landing.html", stage / "index.html")
        copy_file(source / "ui" / "assets" / "social-preview.png", stage / "assets" / "social-preview.png")
        for source_name, destination_name in STATIC_PAGES:
            copy_file(source / source_name, stage / destination_name)
        for source_name, destination_name in COMPARISON_DOWNLOADS:
            copy_file(source / source_name, stage / "comparison-goilyuga" / "downloads" / destination_name)

        hardest_outputs = source / "artifacts" / "hardest_policy_briefings" / "outputs"
        if hardest_outputs.is_dir():
            shutil.copytree(hardest_outputs, stage / "hardest-policy-briefings" / "outputs", dirs_exist_ok=True)

        (stage / ".nojekyll").touch()
        (stage / "_redirects").write_text("/app /app/ 301\n", encoding="utf-8")
        (stage / "_headers").write_text(
            "/*\n"
            "  X-Content-Type-Options: nosniff\n"
            "  Referrer-Policy: strict-origin-when-cross-origin\n"
            "/app/_expo/*\n"
            "  Cache-Control: public, max-age=31536000, immutable\n"
            "/*.html\n"
            "  Cache-Control: public, max-age=0, must-revalidate\n",
            encoding="utf-8",
        )
        inject_analytics(stage)
        count, total, largest_path, largest_size = validate_artifact(stage)
        largest_relative = largest_path.relative_to(stage)
        os.replace(stage, destination)
        return count, total, destination / largest_relative, largest_size
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    count, total, largest_path, largest_size = assemble(args.source, args.destination)
    print(f"artifact={args.destination.resolve()}")
    print(f"files={count}")
    print(f"bytes={total}")
    print(f"largest={largest_path.name}:{largest_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
