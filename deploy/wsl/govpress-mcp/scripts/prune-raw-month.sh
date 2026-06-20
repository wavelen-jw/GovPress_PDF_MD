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
ARCHIVE_ROOT="${ARCHIVE_ROOT:-/mnt/d/govpress-mcp-archives}"
OUT="$ARCHIVE_ROOT/$YEAR/govpress-mcp-raw-$YM.tar.gz.gpg"
SHA_OUT="$OUT.sha256"

if [[ ! -d "$RAW_DIR" ]]; then
  echo "Nothing to prune: $RAW_DIR"
  exit 0
fi

if [[ ! -f "$OUT" || ! -f "$SHA_OUT" ]]; then
  echo "Archive and checksum are required before pruning: $OUT" >&2
  exit 1
fi

if [[ -z "${GPG_PASSPHRASE_FILE:-}" || ! -f "$GPG_PASSPHRASE_FILE" ]]; then
  echo "Missing GPG_PASSPHRASE_FILE. Refusing to prune without archive verification." >&2
  exit 1
fi

(cd "$(dirname "$OUT")" && sha256sum -c "$(basename "$SHA_OUT")")

gpg --batch --yes --pinentry-mode loopback \
  --passphrase-file "$GPG_PASSPHRASE_FILE" \
  --decrypt "$OUT" \
  | tar -tzf - >/dev/null

rm -rf "$RAW_DIR"
echo "pruned $RAW_DIR"
