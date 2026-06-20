#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

usage() {
  echo "Usage: $0 YYYY-MM" >&2
  echo "For legacy encrypted archives, pass GPG_PASSPHRASE_FILE=..." >&2
  exit 2
}

YM="${1:-}"
[[ "$YM" =~ ^[0-9]{4}-[0-9]{2}$ ]] || usage

YEAR="${YM%-*}"
MONTH="${YM#*-}"
RAW_DIR="data/raw/$YEAR/$MONTH"
ARCHIVE_ROOT="${ARCHIVE_ROOT:-/mnt/d/govpress-mcp-archives}"
PLAIN_OUT="$ARCHIVE_ROOT/$YEAR/govpress-mcp-raw-$YM.tar.gz"
ENCRYPTED_OUT="$ARCHIVE_ROOT/$YEAR/govpress-mcp-raw-$YM.tar.gz.gpg"
if [[ -f "$PLAIN_OUT" ]]; then
  OUT="$PLAIN_OUT"
  ARCHIVE_ENCRYPT=0
else
  OUT="$ENCRYPTED_OUT"
  ARCHIVE_ENCRYPT=1
fi
SHA_OUT="$OUT.sha256"

if [[ ! -d "$RAW_DIR" ]]; then
  echo "Nothing to prune: $RAW_DIR"
  exit 0
fi

if [[ ! -f "$OUT" || ! -f "$SHA_OUT" ]]; then
  echo "Archive and checksum are required before pruning: $OUT" >&2
  exit 1
fi

if [[ "$ARCHIVE_ENCRYPT" == "1" ]]; then
  if [[ -z "${GPG_PASSPHRASE_FILE:-}" || ! -f "$GPG_PASSPHRASE_FILE" ]]; then
    echo "Missing GPG_PASSPHRASE_FILE. Refusing to prune encrypted archive without verification." >&2
    exit 1
  fi
fi

(cd "$(dirname "$OUT")" && sha256sum -c "$(basename "$SHA_OUT")")

if [[ "$ARCHIVE_ENCRYPT" == "1" ]]; then
  gpg --batch --yes --pinentry-mode loopback \
    --passphrase-file "$GPG_PASSPHRASE_FILE" \
    --decrypt "$OUT" \
    | tar -tzf - >/dev/null
else
  tar -tzf "$OUT" >/dev/null
fi

rm -rf "$RAW_DIR"
echo "pruned $RAW_DIR"
