#!/usr/bin/env bash
set -Eeuo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
WHEEL="${1:?usage: $0 WHEEL [BASE_IMAGE]}"
BASE_IMAGE="${2:-govpress-mcp-converter:latest}"
VERSION="${CONVERTER_VERSION:-0.4.7}"
COMMIT="${CONVERTER_COMMIT:-c2960871aa22e3d369dc10f05558767d8f272259}"
TAG="${CONVERTER_IMAGE_TAG:-govpress-mcp-converter:0.4.7-c2960871}"

[[ -f "$WHEEL" ]] || { echo "wheel not found: $WHEEL" >&2; exit 1; }
WHEEL_SHA256="$(sha256sum "$WHEEL" | awk '{print $1}')"
python3 - "$WHEEL" "$VERSION" <<'PY'
from email.parser import Parser
from pathlib import Path
import sys
import zipfile

wheel, expected = Path(sys.argv[1]), sys.argv[2]
with zipfile.ZipFile(wheel) as archive:
    metadata_name = next(
        name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
    )
    package = Parser().parsestr(archive.read(metadata_name).decode("utf-8"))
if package["Name"] != "govpress-converter" or package["Version"] != expected:
    raise SystemExit(
        f"unexpected wheel metadata: {package['Name']} {package['Version']}"
    )
PY

CONTEXT="$(mktemp -d)"
trap 'rm -rf "$CONTEXT"' EXIT
install -m 644 "$ROOT/deploy/mcp-converter-fixed/Dockerfile" "$CONTEXT/Dockerfile"
install -m 644 "$ROOT/deploy/mcp-converter-fixed/preflight.py" "$CONTEXT/preflight.py"
install -m 644 "$WHEEL" "$CONTEXT/govpress_converter-0.4.7-py3-none-any.whl"

docker build \
  --pull=false \
  --build-arg "BASE_IMAGE=$BASE_IMAGE" \
  --build-arg "CONVERTER_VERSION=$VERSION" \
  --build-arg "CONVERTER_COMMIT=$COMMIT" \
  --build-arg "CONVERTER_WHEEL_SHA256=$WHEEL_SHA256" \
  --tag "$TAG" \
  "$CONTEXT"

printf 'image=%s\nversion=%s\ncommit=%s\nwheel_sha256=%s\n' \
  "$TAG" "$VERSION" "$COMMIT" "$WHEEL_SHA256"
