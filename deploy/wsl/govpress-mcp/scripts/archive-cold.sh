#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

ARCHIVE_DIR="${ARCHIVE_DIR:-/mnt/d/govpress-mcp-archives}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$ARCHIVE_DIR/govpress-mcp-data-$STAMP.tar.gz.gpg"

if ! command -v gpg >/dev/null 2>&1; then
  echo "gpg is required for encrypted cold archives" >&2
  exit 1
fi

mkdir -p "$ARCHIVE_DIR"

tar -czf - \
  docker-compose.yml \
  README.md \
  data/md \
  data/raw \
  data/fetch-log \
  data/govpress.db \
  | gpg --symmetric --cipher-algo AES256 --output "$OUT"

chmod 600 "$OUT"
echo "$OUT"
