#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  echo "Usage: GPG_PASSPHRASE_FILE=~/.govpress-mcp-archive.pass $0 YYYY-MM" >&2
  exit 2
}

YM="${1:-}"
[[ "$YM" =~ ^[0-9]{4}-[0-9]{2}$ ]] || usage

YEAR="${YM%-*}"
MONTH="${YM#*-}"
RAW_DIR="data/raw/$YEAR/$MONTH"
FETCH_LOG_DIR="data/fetch-log"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-/mnt/d/govpress-mcp-archives}"
ARCHIVE_DIR="$ARCHIVE_ROOT/$YEAR"
OUT="$ARCHIVE_DIR/govpress-mcp-raw-$YM.tar.gz.gpg"
SHA_OUT="$OUT.sha256"
MANIFEST="$FETCH_LOG_DIR/archive-$YM-sha256.txt"

if [[ ! -d "$RAW_DIR" ]]; then
  echo "Missing monthly raw directory: $RAW_DIR" >&2
  exit 1
fi

if [[ -e "$OUT" && "${FORCE:-0}" != "1" ]]; then
  echo "Archive already exists: $OUT" >&2
  exit 1
fi

if [[ -z "${GPG_PASSPHRASE_FILE:-}" || ! -f "$GPG_PASSPHRASE_FILE" ]]; then
  echo "Missing GPG_PASSPHRASE_FILE. Create a chmod 600 passphrase file before archiving." >&2
  exit 1
fi

command -v gpg >/dev/null 2>&1 || {
  echo "gpg is required for encrypted archives" >&2
  exit 1
}

mkdir -p "$ARCHIVE_DIR" "$FETCH_LOG_DIR"
find "$RAW_DIR" -type f -print0 | sort -z | xargs -0 sha256sum > "$MANIFEST"

tmp_out="$OUT.tmp"
rm -f "$tmp_out" "$SHA_OUT"

tar -czf - \
  docker-compose.yml \
  README.md \
  "$RAW_DIR" \
  "$MANIFEST" \
  "$FETCH_LOG_DIR" \
  | gpg --batch --yes --pinentry-mode loopback \
      --passphrase-file "$GPG_PASSPHRASE_FILE" \
      --symmetric --cipher-algo AES256 \
      --output "$tmp_out"

chmod 600 "$tmp_out"
mv "$tmp_out" "$OUT"
sha256sum "$OUT" > "$SHA_OUT"

gpg --batch --yes --pinentry-mode loopback \
  --passphrase-file "$GPG_PASSPHRASE_FILE" \
  --decrypt "$OUT" \
  | tar -tzf - >/dev/null

echo "$OUT"
